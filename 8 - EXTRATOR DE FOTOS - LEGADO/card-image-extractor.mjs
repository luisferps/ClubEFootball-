#!/usr/bin/env node

import { createHash } from "node:crypto";
import { appendFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { extname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import {
  APPLY_RUN_FORMAT,
  applyManifestDocument,
  DATABASE_TARGET,
  PHOTO_MANIFEST_FORMAT,
  sealManifest,
  validateManifestDocument
} from "./photo-manifest.mjs";

const DEFAULT_CLOUD_NAME = "demsusjwf";
const DEFAULT_UPLOAD_PRESET = "clubefutebol_cards_no_overwrite";
const DEFAULT_ASSET_FOLDER = "clubefutebol/cards/efootballhub";
const DEFAULT_OUTPUT = resolve("output");
const SUPABASE_SCHEMA = "clube_novo";
const SUPABASE_TABLE = "carta_jogo";
const SUPABASE_URL_COLUMN = "foto_url_cloudinary";
const SOURCE_PREFIX = "https://efimg.com/efootballhub22/images/player_cards/";
const MAX_BATCH = 100;
const MAX_CONCURRENCY = 8;
export const DISCOVERY_STATEMENT_TIMEOUT_MS = 5 * 60 * 1000;

export function assertCardId(value) {
  const id = String(value ?? "").trim();
  if (!/^\d+$/.test(id)) throw new Error(`card_id invalido: ${JSON.stringify(value)}`);
  return id;
}

export function sourceUrl(cardId) {
  return `${SOURCE_PREFIX}${assertCardId(cardId)}_l.png`;
}

export function deliveryUrl(cloudName, cardId) {
  return `https://res.cloudinary.com/${cloudName}/image/upload/${assertCardId(cardId)}.png`;
}

export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  const input = text.replace(/^\uFEFF/, "");

  for (let i = 0; i < input.length; i += 1) {
    const char = input[i];
    if (quoted) {
      if (char === '"' && input[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }

  if (quoted) throw new Error("CSV invalido: aspas nao encerradas");
  if (field.length || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows;
}

export function idsFromCsv(text) {
  const rows = parseCsv(text);
  if (!rows.length) return [];
  const headers = rows[0].map((item) => item.trim().toLowerCase());
  const idIndex = headers.indexOf("card_id") >= 0 ? headers.indexOf("card_id") : headers.indexOf("id");
  if (idIndex < 0) throw new Error("CSV precisa de coluna card_id ou id");
  return rows.slice(1).filter((row) => row.some((item) => item.trim())).map((row) => assertCardId(row[idIndex]));
}

export function uniqueCardIds(values) {
  const result = [];
  const seen = new Set();
  for (const value of values) {
    const id = assertCardId(value);
    if (!seen.has(id)) {
      seen.add(id);
      result.push(id);
    }
  }
  return result;
}

export function parsePng(buffer) {
  const bytes = Buffer.from(buffer);
  const signature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  if (bytes.length < 24 || !bytes.subarray(0, 8).equals(signature)) {
    throw new Error("arquivo recebido nao e PNG");
  }
  if (bytes.toString("ascii", 12, 16) !== "IHDR") throw new Error("PNG sem IHDR canonico");
  const width = bytes.readUInt32BE(16);
  const height = bytes.readUInt32BE(20);
  if (width < 1 || height < 1) throw new Error("dimensoes PNG invalidas");
  return { width, height };
}

export function auditImageContent(buffer) {
  const bytes = Buffer.from(buffer);
  let dimensions = { width: null, height: null };
  let contentAudit = "nao_png";
  try {
    dimensions = parsePng(bytes);
    contentAudit = "png_valido";
  } catch {
    // Auditoria informativa: nao decide identidade nem bloqueia upload.
  }
  return {
    byteSize: bytes.length,
    contentAudit,
    sha256: createHash("sha256").update(bytes).digest("hex"),
    ...dimensions
  };
}

function jsonIds(value) {
  const rows = Array.isArray(value) ? value : Array.isArray(value?.cards) ? value.cards : Array.isArray(value?.players) ? value.players : null;
  if (!rows) throw new Error("JSON precisa ser array ou conter cards/players");
  return rows.map((row) => assertCardId(typeof row === "object" ? row.card_id ?? row.id : row));
}

export async function loadInput(path) {
  const fullPath = resolve(path);
  const text = await readFile(fullPath, "utf8");
  const extension = extname(fullPath).toLowerCase();
  if (extension === ".csv") return idsFromCsv(text);
  if (extension === ".json") return jsonIds(JSON.parse(text));
  if (extension === ".jsonl") {
    return text.split(/\r?\n/).filter(Boolean).map((line) => {
      const row = JSON.parse(line);
      return assertCardId(row.card_id ?? row.id);
    });
  }
  return text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean).map(assertCardId);
}

export function cloudinarySettingsFromEnv(env = process.env) {
  let apiKey = env.CLOUDINARY_API_KEY || null;
  let apiSecret = env.CLOUDINARY_API_SECRET || null;
  let cloudName = env.CLOUDINARY_CLOUD_NAME || DEFAULT_CLOUD_NAME;

  // Compatibilidade com automações antigas que fornecem somente CLOUDINARY_URL.
  if (!apiKey && !apiSecret && env.CLOUDINARY_URL) {
    const parsed = new URL(env.CLOUDINARY_URL);
    if (parsed.protocol !== "cloudinary:" || !parsed.username || !parsed.password || !parsed.hostname) {
      throw new Error("CLOUDINARY_URL invalida");
    }
    apiKey = decodeURIComponent(parsed.username);
    apiSecret = decodeURIComponent(parsed.password);
    cloudName = parsed.hostname;
  }

  return { apiKey, apiSecret, cloudName };
}

function parseArgs(argv) {
  const cloudinary = cloudinarySettingsFromEnv();
  const args = {
    applyManifest: null,
    apiKey: cloudinary.apiKey,
    apiSecret: cloudinary.apiSecret,
    assetFolder: DEFAULT_ASSET_FOLDER,
    cardIds: [],
    cloudName: cloudinary.cloudName,
    concurrency: 4,
    delayMs: 500,
    databaseMethod: "auto",
    discoverMissing: false,
    input: null,
    inputKind: "local_operator_file",
    limit: null,
    offset: 0,
    output: DEFAULT_OUTPUT,
    retries: 3,
    supabaseApiKey: process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY || null,
    supabaseDbUrl: process.env.SUPABASE_DB_URL || null,
    supabaseUrl: process.env.SUPABASE_URL || null,
    timeoutMs: 30000,
    upload: false,
    uploadPreset: process.env.CLOUDINARY_UPLOAD_PRESET || DEFAULT_UPLOAD_PRESET
  };

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    const next = () => {
      const value = argv[++i];
      if (value == null) throw new Error(`valor ausente para ${token}`);
      return value;
    };
    if (token === "--apply") throw new Error("--apply foi removido: use --upload para criar manifesto ou --apply-manifest para aplicar um manifesto separadamente");
    else if (token === "--apply-manifest") args.applyManifest = resolve(next());
    else if (token === "--asset-folder") args.assetFolder = next();
    else if (token === "--card-id") args.cardIds.push(next());
    else if (token === "--cloud-name") args.cloudName = next();
    else if (token === "--concurrency") args.concurrency = Number(next());
    else if (token === "--delay-ms") args.delayMs = Number(next());
    else if (token === "--database-method") args.databaseMethod = next();
    else if (token === "--discover-missing") args.discoverMissing = true;
    else if (token === "--input") args.input = next();
    else if (token === "--input-kind") args.inputKind = next();
    else if (token === "--limit") args.limit = Number(next());
    else if (token === "--offset") args.offset = Number(next());
    else if (token === "--output") args.output = resolve(next());
    else if (token === "--retries") args.retries = Number(next());
    else if (token === "--timeout-ms") args.timeoutMs = Number(next());
    else if (token === "--upload") args.upload = true;
    else if (token === "--upload-preset") args.uploadPreset = next();
    else if (token === "--help" || token === "-h") args.help = true;
    else throw new Error(`argumento desconhecido: ${token}`);
  }

  if (!args.help) {
    const applyingManifest = Boolean(args.applyManifest);
    const discoveringMissing = args.discoverMissing;
    if (applyingManifest && discoveringMissing) throw new Error("--apply-manifest e --discover-missing sao operacoes separadas");
    if ((applyingManifest || discoveringMissing) && (args.input || args.cardIds.length || args.upload)) throw new Error("APPLY/descoberta nao aceitam input, card-id ou upload");
    if (!applyingManifest && !discoveringMissing && !args.input && !args.cardIds.length) throw new Error("informe --input ou ao menos um --card-id");
    if (!applyingManifest && !discoveringMissing && (!Number.isInteger(args.limit) || args.limit < 1 || args.limit > MAX_BATCH)) throw new Error(`--limit e obrigatorio e deve estar entre 1 e ${MAX_BATCH}`);
    if (!Number.isInteger(args.offset) || args.offset < 0) throw new Error("--offset deve ser inteiro >= 0");
    if (!Number.isInteger(args.concurrency) || args.concurrency < 1 || args.concurrency > MAX_CONCURRENCY) {
      throw new Error(`--concurrency deve estar entre 1 e ${MAX_CONCURRENCY}`);
    }
    if (!Number.isInteger(args.delayMs) || args.delayMs < 250) throw new Error("--delay-ms deve ser >= 250");
    if (!Number.isInteger(args.retries) || args.retries < 0 || args.retries > 8) throw new Error("--retries deve estar entre 0 e 8");
    if (Boolean(args.apiKey) !== Boolean(args.apiSecret)) throw new Error("CLOUDINARY_API_KEY e CLOUDINARY_API_SECRET devem ser definidos juntos");
    if (Boolean(args.supabaseUrl) !== Boolean(args.supabaseApiKey)) throw new Error("SUPABASE_URL e SUPABASE_SECRET_KEY/SUPABASE_SERVICE_ROLE_KEY devem ser definidos juntos");
    if (args.upload && !args.apiKey) {
      throw new Error("upload requer CLOUDINARY_API_KEY e CLOUDINARY_API_SECRET locais");
    }
    if (!new Set(["auto", "postgres", "data-api"]).has(args.databaseMethod)) throw new Error("--database-method deve ser auto, postgres ou data-api");
    const databaseOperation = applyingManifest || discoveringMissing;
    if (databaseOperation && args.databaseMethod === "postgres" && !args.supabaseDbUrl) throw new Error("operacao por Postgres requer SUPABASE_DB_URL no processo local");
    if (databaseOperation && args.databaseMethod === "data-api" && !args.supabaseUrl) throw new Error("operacao por Data API requer SUPABASE_URL e uma chave secreta no processo local");
    if (databaseOperation && args.databaseMethod === "auto" && !args.supabaseDbUrl && !args.supabaseUrl) throw new Error("operacao de banco requer SUPABASE_DB_URL ou SUPABASE_URL + chave secreta no processo local");
  }
  return args;
}

function usage() {
  return `Uso:
  node card-image-extractor.mjs --input cards.csv --limit 10
  node card-image-extractor.mjs --card-id 17592722922839 --limit 1 --upload
  node card-image-extractor.mjs --input cards.csv --offset 1 --limit 100 --concurrency 4 --upload
  node card-image-extractor.mjs --discover-missing --database-method auto
  node card-image-extractor.mjs --apply-manifest output/runs/<id>/manifest.json --database-method auto

Preparar/upload e APPLY MANIFEST sao operacoes distintas. Nenhuma preparacao altera o banco. --limit nunca pode exceder ${MAX_BATCH}.`;
}

const sleep = (ms) => new Promise((resolvePromise) => setTimeout(resolvePromise, ms));

function retryDelay(response, attempt) {
  const retryAfter = Number(response?.headers?.get("retry-after"));
  if (Number.isFinite(retryAfter) && retryAfter > 0) return retryAfter * 1000;
  return Math.min(30000, 1000 * (2 ** attempt));
}

async function fetchWithRetry(url, options, settings) {
  let lastError;
  for (let attempt = 0; attempt <= settings.retries; attempt += 1) {
    try {
      const response = await fetch(url, { ...options, signal: AbortSignal.timeout(settings.timeoutMs) });
      if (response.status !== 429 && response.status < 500) return response;
      lastError = new Error(`HTTP ${response.status}`);
      if (attempt < settings.retries) {
        await response.arrayBuffer().catch(() => {});
        await sleep(retryDelay(response, attempt));
      }
    } catch (error) {
      lastError = error;
      if (attempt < settings.retries) await sleep(Math.min(30000, 1000 * (2 ** attempt)));
    }
  }
  throw lastError ?? new Error("falha de rede sem resposta");
}

async function probeCloudinary(settings, cardId, cacheBust = false) {
  const base = deliveryUrl(settings.cloudName, cardId);
  const url = cacheBust ? `${base}?readback=${Date.now()}` : base;
  const response = await fetchWithRetry(url, { method: "HEAD", cache: "no-store" }, settings);
  return {
    status: response.status,
    contentType: response.headers.get("content-type"),
    contentLength: Number(response.headers.get("content-length")) || null,
    url: base
  };
}

async function waitForCloudinaryReadback(settings, cardId) {
  let result = null;
  for (let attempt = 0; attempt <= 6; attempt += 1) {
    result = await probeCloudinary(settings, cardId, true);
    if (result.status === 200 || result.status !== 404) return result;
    if (attempt < 6) await sleep(Math.min(10000, 1000 * (2 ** attempt)));
  }
  return result;
}

async function downloadSource(settings, cardId) {
  const url = sourceUrl(cardId);
  const response = await fetchWithRetry(url, { headers: { Accept: "image/png" } }, settings);
  if (!response.ok) throw new Error(`fonte eFHub respondeu HTTP ${response.status}`);
  const contentType = response.headers.get("content-type")?.split(";", 1)[0]?.trim().toLowerCase() || null;
  const buffer = Buffer.from(await response.arrayBuffer());
  const audit = auditImageContent(buffer);
  return {
    buffer,
    contentType,
    sourceUrl: url,
    ...audit
  };
}

function escapeContext(value) {
  return String(value).replaceAll("\\", "\\\\").replaceAll("=", "\\=").replaceAll("|", "\\|");
}

async function uploadCloudinary(settings, cardId, image) {
  const endpoint = `https://api.cloudinary.com/v1_1/${settings.cloudName}/image/upload`;
  const form = new FormData();
  form.set("file", new Blob([image.buffer], { type: image.contentType || "application/octet-stream" }), `${cardId}.png`);
  form.set("upload_preset", settings.uploadPreset);
  form.set("public_id", cardId);
  form.set("asset_folder", settings.assetFolder);
  form.set("tags", `efootballhub,card_id_${cardId}`);
  form.set("context", `card_id=${cardId}|source=efootballhub|source_url=${escapeContext(image.sourceUrl)}`);

  const request = { method: "POST", body: form };
  if (settings.apiKey) {
    form.set("overwrite", "false");
    request.headers = { Authorization: `Basic ${Buffer.from(`${settings.apiKey}:${settings.apiSecret}`).toString("base64")}` };
  }
  const response = await fetchWithRetry(endpoint, request, settings);
  const bodyText = await response.text();
  let body;
  try { body = JSON.parse(bodyText); } catch { body = { raw: bodyText.slice(0, 500) }; }
  if (!response.ok) {
    const error = new Error(`Cloudinary respondeu HTTP ${response.status}: ${body?.error?.message ?? "erro sem mensagem"}`);
    error.status = response.status;
    error.body = body;
    throw error;
  }
  if (String(body.public_id) !== cardId) throw new Error(`public_id divergente no upload: ${body.public_id}`);
  if (String(body.asset_folder) !== settings.assetFolder) throw new Error(`asset_folder divergente: ${body.asset_folder}`);
  return body;
}

function supabaseHeaders(settings, write = false) {
  const headers = {
    Accept: "application/json",
    apikey: settings.supabaseApiKey,
    "Accept-Profile": SUPABASE_SCHEMA
  };
  if (String(settings.supabaseApiKey).startsWith("eyJ")) headers.Authorization = `Bearer ${settings.supabaseApiKey}`;
  if (write) {
    headers["Content-Type"] = "application/json";
    headers["Content-Profile"] = SUPABASE_SCHEMA;
    headers.Prefer = "return=representation";
  }
  return headers;
}

function supabaseTableUrl(settings, parameters) {
  const base = String(settings.supabaseUrl).replace(/\/$/, "");
  const query = new URLSearchParams(parameters);
  return `${base}/rest/v1/${SUPABASE_TABLE}?${query}`;
}

function supabaseCardUrl(settings, cardId, select, onlyIfEmpty = false) {
  const parameters = {
    select,
    card_id: `eq.${assertCardId(cardId)}`,
    limit: "2"
  };
  if (onlyIfEmpty) parameters[SUPABASE_URL_COLUMN] = "is.null";
  return supabaseTableUrl(settings, parameters);
}

async function responseJson(response) {
  const text = await response.text();
  if (!text) return null;
  try { return JSON.parse(text); } catch { return null; }
}

export function supabaseFailureMessage(operation, status, body) {
  const code = typeof body?.code === "string" ? body.code : null;
  if (status === 406 && code === "PGRST106") {
    return `${operation} respondeu HTTP 406 (PGRST106): o schema ${SUPABASE_SCHEMA} nao esta exposto na Data API do projeto`;
  }
  if (status === 406 && code === "PGRST116") {
    return `${operation} respondeu HTTP 406 (PGRST116): a consulta singular retornou cardinalidade diferente de 1`;
  }
  const message = typeof body?.message === "string" ? body.message.slice(0, 300) : null;
  return `${operation} respondeu HTTP ${status}${code ? ` (${code})` : ""}${message ? `: ${message}` : ""}`;
}

async function readCanonicalCards(settings, cardIds) {
  const ids = uniqueCardIds(cardIds);
  if (!ids.length) return new Map();
  const response = await fetchWithRetry(
    supabaseTableUrl(settings, {
      select: `card_id,${SUPABASE_URL_COLUMN}`,
      card_id: `in.(${ids.join(",")})`,
      limit: String(ids.length)
    }),
    { method: "GET", headers: supabaseHeaders(settings) },
    settings
  );
  const rows = await responseJson(response);
  if (!response.ok) throw new Error(supabaseFailureMessage("Supabase read", response.status, rows));
  if (!Array.isArray(rows)) throw new Error("Supabase read nao retornou uma lista JSON");
  const requested = new Set(ids);
  const result = new Map();
  for (const row of rows) {
    const cardId = assertCardId(row?.card_id);
    if (!requested.has(cardId) || result.has(cardId)) {
      throw new Error(`Supabase read retornou card_id inesperado ou duplicado: ${cardId}`);
    }
    result.set(cardId, row);
  }
  return result;
}

async function readCanonicalCard(settings, cardId) {
  const rows = await readCanonicalCards(settings, [cardId]);
  const row = rows.get(cardId);
  if (!row) throw new Error(`card_id ${cardId} nao existe em ${SUPABASE_SCHEMA}.${SUPABASE_TABLE}`);
  return row;
}

async function readNextCanonicalCards(settings, limit, offset = 0) {
  const response = await fetchWithRetry(
    supabaseTableUrl(settings, {
      select: `card_id,${SUPABASE_URL_COLUMN}`,
      [SUPABASE_URL_COLUMN]: "is.null",
      order: "card_id.asc",
      limit: String(limit),
      offset: String(offset)
    }),
    { method: "GET", headers: supabaseHeaders(settings) },
    settings
  );
  const rows = await responseJson(response);
  if (!response.ok) throw new Error(supabaseFailureMessage("Supabase lote read", response.status, rows));
  if (!Array.isArray(rows)) throw new Error("Supabase lote read nao retornou uma lista JSON");
  const result = new Map();
  for (const row of rows) {
    const cardId = assertCardId(row?.card_id);
    if (result.has(cardId)) throw new Error(`Supabase lote read retornou card_id duplicado: ${cardId}`);
    result.set(cardId, row);
  }
  return result;
}

async function countCanonicalRowsDataApi(settings, onlyMissing) {
  const parameters = { select: "card_id", limit: "1" };
  if (onlyMissing) parameters[SUPABASE_URL_COLUMN] = "is.null";
  const response = await fetchWithRetry(
    supabaseTableUrl(settings, parameters),
    {
      method: "GET",
      headers: { ...supabaseHeaders(settings), Prefer: "count=exact", Range: "0-0", "Range-Unit": "items" }
    },
    settings
  );
  const body = await responseJson(response);
  if (!response.ok) throw new Error(supabaseFailureMessage("Supabase verificacao de coluna/contagem", response.status, body));
  const contentRange = response.headers.get("content-range") || "";
  const match = contentRange.match(/\/(\d+)$/);
  if (!match) throw new Error("Supabase nao retornou Content-Range com contagem exata");
  return Number(match[1]);
}

async function discoverMissingCardsDataApi(settings) {
  const totalCards = await countCanonicalRowsDataApi(settings, false);
  const missingCards = await countCanonicalRowsDataApi(settings, true);
  const pageSize = 1000;
  const rows = new Map();
  for (let offset = 0; offset < missingCards; offset += pageSize) {
    const page = await readNextCanonicalCards(settings, Math.min(pageSize, missingCards - offset), offset);
    for (const [cardId, row] of page) {
      if (rows.has(cardId)) throw new Error(`descoberta Supabase retornou card_id duplicado: ${cardId}`);
      rows.set(cardId, row);
    }
    if (page.size === 0) break;
  }
  if (rows.size !== missingCards) throw new Error(`contagem Supabase divergiu: esperado ${missingCards} sem link, recebido ${rows.size}`);
  return {
    column: { schema: SUPABASE_SCHEMA, table: SUPABASE_TABLE, name: SUPABASE_URL_COLUMN, exists: true, data_type: "confirmado_pela_data_api", is_nullable: null },
    total_cards: totalCards,
    already_linked: totalCards - missingCards,
    missing_cards: missingCards,
    rows
  };
}

async function syncCanonicalCardPhoto(settings, cardId, cloudinaryUrl) {
  const response = await fetchWithRetry(
    supabaseCardUrl(settings, cardId, `card_id,${SUPABASE_URL_COLUMN}`, true),
    {
      method: "PATCH",
      headers: supabaseHeaders(settings, true),
      body: JSON.stringify({ [SUPABASE_URL_COLUMN]: cloudinaryUrl })
    },
    settings
  );
  const rows = await responseJson(response);
  if (!response.ok) throw new Error(supabaseFailureMessage("Supabase update", response.status, rows));
  if (!Array.isArray(rows)) throw new Error("Supabase update nao retornou uma lista JSON");
  if (rows.length === 0) {
    const current = await readCanonicalCard(settings, cardId);
    if (current[SUPABASE_URL_COLUMN] === cloudinaryUrl) return current;
    throw new Error(`foto_url_cloudinary ja foi preenchida com outro valor para card_id ${cardId}; nada foi sobrescrito`);
  }
  if (rows.length !== 1 || String(rows[0].card_id) !== cardId) throw new Error(`readback Supabase nao retornou exatamente o card_id ${cardId}`);
  if (rows[0][SUPABASE_URL_COLUMN] !== cloudinaryUrl) {
    throw new Error(`readback Supabase divergiu para card_id ${cardId}`);
  }
  return rows[0];
}

export async function mapWithConcurrency(items, concurrency, worker) {
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > MAX_CONCURRENCY) {
    throw new Error(`concorrencia deve estar entre 1 e ${MAX_CONCURRENCY}`);
  }
  const results = new Array(items.length);
  let cursor = 0;
  const runners = Array.from({ length: Math.min(concurrency, items.length) }, async () => {
    while (true) {
      const index = cursor;
      cursor += 1;
      if (index >= items.length) return;
      results[index] = await worker(items[index], index);
    }
  });
  await Promise.all(runners);
  return results;
}

function createStartRateLimiter(delayMs) {
  let nextStart = 0;
  let queue = Promise.resolve();
  return () => {
    const turn = queue.then(async () => {
      const now = Date.now();
      const waitMs = Math.max(0, nextStart - now);
      nextStart = Math.max(nextStart, now) + delayMs;
      if (waitMs) await sleep(waitMs);
    });
    queue = turn.catch(() => {});
    return turn;
  };
}

function utcStamp() {
  return new Date().toISOString().replaceAll(":", "-").replaceAll(".", "-");
}

async function appendEvent(path, event) {
  await appendFile(path, `${JSON.stringify(event)}\n`, "utf8");
}

function countStatuses(events) {
  const counts = {};
  for (const event of events) counts[event.status] = (counts[event.status] ?? 0) + 1;
  return counts;
}

function provenanceFor(settings, cardId) {
  return {
    identity_key: "card_id",
    source: "efootballhub",
    source_url: sourceUrl(cardId),
    cloudinary_public_id: cardId,
    cloudinary_asset_folder: settings.assetFolder
  };
}

async function inputProvenance(settings, allIds) {
  if (!settings.input) return { kind: "explicit_card_id", path: null, sha256: null, total_unique: allIds.length };
  const path = resolve(settings.input);
  const bytes = await readFile(path);
  return {
    kind: settings.inputKind,
    path,
    sha256: createHash("sha256").update(bytes).digest("hex"),
    total_unique: allIds.length
  };
}

function createDataApiAdapter(settings) {
  return {
    method: "data_api_secret_key_server_side",
    discoverMissing() { return discoverMissingCardsDataApi(settings); },
    async applyConditional(items) {
      const initial = await readCanonicalCards(settings, items.map((item) => item.card_id));
      const decisions = new Map();
      for (const item of items) {
        const row = initial.get(item.card_id);
        if (!row) {
          decisions.set(item.card_id, { status: "missing_card", previous_url: null });
          continue;
        }
        const current = row[SUPABASE_URL_COLUMN] ?? null;
        if (current === item.candidate_url) {
          decisions.set(item.card_id, { status: "already_applied", previous_url: current });
          continue;
        }
        if (current) {
          decisions.set(item.card_id, { status: "conflict_preserved", previous_url: current, current_url: current });
          continue;
        }
        try {
          await syncCanonicalCardPhoto(settings, item.card_id, item.candidate_url);
          decisions.set(item.card_id, { status: "updated", previous_url: null });
        } catch (error) {
          const after = await readCanonicalCards(settings, [item.card_id]);
          const afterRow = after.get(item.card_id);
          const afterUrl = afterRow?.[SUPABASE_URL_COLUMN] ?? null;
          if (!afterRow) decisions.set(item.card_id, { status: "missing_card", previous_url: null });
          else if (afterUrl === item.candidate_url) decisions.set(item.card_id, { status: "already_applied", previous_url: afterUrl });
          else if (afterUrl) decisions.set(item.card_id, { status: "conflict_preserved", previous_url: afterUrl, current_url: afterUrl });
          else throw error;
        }
      }
      return decisions;
    },
    readMany(cardIds) { return readCanonicalCards(settings, cardIds); }
  };
}

async function createPostgresAdapter(settings) {
  let Client;
  try {
    const pg = await import("pg");
    Client = pg.Client ?? pg.default?.Client;
  } catch {
    throw new Error("acesso Postgres direto requer as dependencias verificadas por npm ci; execute novamente pelo iniciador");
  }
  if (!Client) throw new Error("pacote pg nao disponibilizou Client");
  // A URL operacional do painel usa o modo PostgreSQL `require`: a sessão é
  // criptografada, mas não depende de um arquivo CA instalado nesta máquina.
  // Se a URL pedir explicitamente `verify-ca` ou `verify-full`, a verificação
  // do certificado permanece habilitada no cliente Node.
  const requestedSslMode = (() => {
    try { return new URL(settings.supabaseDbUrl).searchParams.get("sslmode")?.toLowerCase() ?? "require"; }
    catch { return "require"; }
  })();
  const clientOptions = {
    connectionString: settings.supabaseDbUrl,
    ssl: { rejectUnauthorized: new Set(["verify-ca", "verify-full"]).has(requestedSslMode) },
    connectionTimeoutMillis: settings.timeoutMs
  };
  const connect = async () => {
    const client = new Client(clientOptions);
    await client.connect();
    return client;
  };
  return {
    method: "direct_postgres_transaction",
    async discoverMissing() {
      const client = await connect();
      try {
        // A descoberta conta e ordena dezenas de milhares de cartas. No
        // Session pooler ela pode ultrapassar 30 segundos sem estar travada.
        // Este limite maior vale somente para a sessão de leitura; o APPLY
        // mantém abaixo seu limite curto e independente de 30 segundos.
        await client.query("SELECT set_config('statement_timeout', $1, false)", [`${DISCOVERY_STATEMENT_TIMEOUT_MS}ms`]);
        const columnResult = await client.query(
          `SELECT data_type, is_nullable FROM information_schema.columns WHERE table_schema = $1 AND table_name = $2 AND column_name = $3`,
          [SUPABASE_SCHEMA, SUPABASE_TABLE, SUPABASE_URL_COLUMN]
        );
        if (columnResult.rowCount !== 1) throw new Error(`${DATABASE_TARGET} nao existe ou nao esta acessivel`);
        const countsResult = await client.query(
          `SELECT COUNT(*)::bigint AS total_cards, COUNT(*) FILTER (WHERE ${SUPABASE_URL_COLUMN} IS NULL)::bigint AS missing_cards FROM ${SUPABASE_SCHEMA}.${SUPABASE_TABLE}`
        );
        const result = await client.query(
          `SELECT card_id::text AS card_id, ${SUPABASE_URL_COLUMN} FROM ${SUPABASE_SCHEMA}.${SUPABASE_TABLE} WHERE ${SUPABASE_URL_COLUMN} IS NULL ORDER BY card_id`
        );
        const rows = new Map();
        for (const row of result.rows) {
          const cardId = assertCardId(row.card_id);
          if (rows.has(cardId)) throw new Error(`descoberta Postgres retornou card_id duplicado: ${cardId}`);
          rows.set(cardId, row);
        }
        const totalCards = Number(countsResult.rows[0].total_cards);
        const missingCards = Number(countsResult.rows[0].missing_cards);
        if (rows.size !== missingCards) throw new Error(`contagem Postgres divergiu: esperado ${missingCards} sem link, recebido ${rows.size}`);
        return {
          column: {
            schema: SUPABASE_SCHEMA,
            table: SUPABASE_TABLE,
            name: SUPABASE_URL_COLUMN,
            exists: true,
            data_type: columnResult.rows[0].data_type,
            is_nullable: columnResult.rows[0].is_nullable
          },
          total_cards: totalCards,
          already_linked: totalCards - missingCards,
          missing_cards: missingCards,
          rows
        };
      } finally {
        await client.end().catch(() => {});
      }
    },
    async applyConditional(items) {
      const client = await connect();
      const decisions = new Map();
      try {
        await client.query("BEGIN");
        await client.query("SET LOCAL statement_timeout = '30s'");
        for (const item of items) {
          const updated = await client.query(
            `UPDATE ${SUPABASE_SCHEMA}.${SUPABASE_TABLE} SET ${SUPABASE_URL_COLUMN} = $2 WHERE card_id = $1 AND ${SUPABASE_URL_COLUMN} IS NULL RETURNING card_id::text AS card_id, ${SUPABASE_URL_COLUMN}`,
            [item.card_id, item.candidate_url]
          );
          if (updated.rowCount === 1) {
            decisions.set(item.card_id, { status: "updated", previous_url: null });
            continue;
          }
          const current = await client.query(
            `SELECT card_id::text AS card_id, ${SUPABASE_URL_COLUMN} FROM ${SUPABASE_SCHEMA}.${SUPABASE_TABLE} WHERE card_id = $1 FOR UPDATE`,
            [item.card_id]
          );
          if (current.rowCount === 0) decisions.set(item.card_id, { status: "missing_card", previous_url: null });
          else if (current.rows[0][SUPABASE_URL_COLUMN] === item.candidate_url) decisions.set(item.card_id, { status: "already_applied", previous_url: item.candidate_url });
          else decisions.set(item.card_id, { status: "conflict_preserved", previous_url: current.rows[0][SUPABASE_URL_COLUMN], current_url: current.rows[0][SUPABASE_URL_COLUMN] });
        }
        await client.query("COMMIT");
        return decisions;
      } catch (error) {
        await client.query("ROLLBACK").catch(() => {});
        throw error;
      } finally {
        await client.end().catch(() => {});
      }
    },
    async readMany(cardIds) {
      if (!cardIds.length) return new Map();
      const client = await connect();
      try {
        const result = await client.query(
          `SELECT card_id::text AS card_id, ${SUPABASE_URL_COLUMN} FROM ${SUPABASE_SCHEMA}.${SUPABASE_TABLE} WHERE card_id = ANY($1::text[])`,
          [cardIds]
        );
        const rows = new Map();
        for (const row of result.rows) rows.set(assertCardId(row.card_id), row);
        return rows;
      } finally {
        await client.end().catch(() => {});
      }
    }
  };
}

async function databaseAdapterFor(settings) {
  if (settings.databaseMethod === "postgres" || (settings.databaseMethod === "auto" && settings.supabaseDbUrl)) return createPostgresAdapter(settings);
  return createDataApiAdapter(settings);
}

async function runDiscovery(settings) {
  const runId = utcStamp();
  const runDirectory = join(settings.output, "discoveries", runId);
  const eventsPath = join(runDirectory, "events.jsonl");
  const summaryPath = join(runDirectory, "summary.json");
  const snapshotPath = join(runDirectory, "card-ids-sem-link.txt");
  await mkdir(runDirectory, { recursive: true });
  let adapter;
  try {
    adapter = await databaseAdapterFor(settings);
    if (typeof adapter.discoverMissing !== "function") throw new Error("adaptador de banco nao suporta descoberta de cards sem link");
    const discovery = await adapter.discoverMissing();
    const cardIds = uniqueCardIds([...discovery.rows.keys()]);
    const snapshotContent = cardIds.length ? `${cardIds.join("\n")}\n` : "";
    const snapshotSha256 = createHash("sha256").update(snapshotContent).digest("hex");
    await writeFile(snapshotPath, snapshotContent, "utf8");
    const event = {
      run_id: runId,
      scope: "database_discovery",
      status: "database_universe_discovered",
      database_target: DATABASE_TARGET,
      database_access_method: adapter.method,
      column_verification: discovery.column,
      total_cards: discovery.total_cards,
      already_linked: discovery.already_linked,
      missing_cards: discovery.missing_cards,
      snapshot_file: snapshotPath,
      snapshot_sha256: snapshotSha256,
      database_modified: false
    };
    await appendEvent(eventsPath, event);
    const summary = {
      format: "clubefutebol-photo-database-discovery-v1",
      run_id: runId,
      mode: "discover_database_universe",
      database_target: DATABASE_TARGET,
      database_access_method: adapter.method,
      column_verified: discovery.column.exists === true,
      column_verification: discovery.column,
      total_cards: discovery.total_cards,
      already_linked: discovery.already_linked,
      missing_cards: discovery.missing_cards,
      selected: discovery.missing_cards,
      snapshot_file: snapshotPath,
      snapshot_sha256: snapshotSha256,
      counts: { database_universe_discovered: 1 },
      events_file: eventsPath,
      database_modified: false,
      completed_at_utc: new Date().toISOString()
    };
    await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
    console.log(JSON.stringify(event));
    console.log(JSON.stringify(summary));
    return { summary, events: [event], runDirectory };
  } catch (error) {
    const event = { run_id: runId, scope: "database_discovery", status: "failed_setup", database_target: DATABASE_TARGET, database_access_method: adapter?.method ?? null, database_modified: false, error: error.message };
    await appendEvent(eventsPath, event);
    const summary = {
      format: "clubefutebol-photo-database-discovery-v1",
      run_id: runId,
      mode: "discover_database_universe",
      database_target: DATABASE_TARGET,
      database_access_method: adapter?.method ?? null,
      column_verified: false,
      selected: 0,
      counts: { failed_setup: 1 },
      events_file: eventsPath,
      database_modified: false,
      completed_at_utc: new Date().toISOString()
    };
    await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
    console.log(JSON.stringify(event));
    console.log(JSON.stringify(summary));
    return { summary, events: [event], runDirectory };
  }
}

async function runPrepare(settings) {
  const runId = utcStamp();
  const runDirectory = join(settings.output, "runs", runId);
  const imageDirectory = join(runDirectory, "images");
  const eventsPath = join(runDirectory, "events.jsonl");
  const summaryPath = join(runDirectory, "summary.json");
  const manifestPath = join(runDirectory, "manifest.json");
  await mkdir(imageDirectory, { recursive: true });

  let allIds = [];
  let selectedIds = [];
  let provenance = null;
  try {
    const inputIds = settings.input ? await loadInput(settings.input) : [];
    allIds = uniqueCardIds([...settings.cardIds, ...inputIds]);
    selectedIds = allIds.slice(settings.offset, settings.offset + settings.limit);
    provenance = await inputProvenance(settings, allIds);
  } catch (error) {
    const event = { run_id: runId, scope: "run", status: "failed_setup", overwritten: false, error: error.message };
    await appendEvent(eventsPath, event);
    const summary = {
      format: "clubefutebol-photo-prepare-run-v1", run_id: runId, mode: settings.upload ? "prepare_and_upload" : "dry_run",
      selected: 0, counts: { failed_setup: 1 }, events_file: eventsPath, manifest_file: null, database_modified: false, completed_at_utc: new Date().toISOString()
    };
    await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
    console.log(JSON.stringify(event));
    console.log(JSON.stringify(summary));
    return { summary, events: [event], runDirectory };
  }

  if (!selectedIds.length) {
    const event = { run_id: runId, scope: "run", status: "selection_complete", overwritten: false, progress_completed: 0, progress_total: 0 };
    await appendEvent(eventsPath, event);
    const summary = {
      format: "clubefutebol-photo-prepare-run-v1", run_id: runId, mode: settings.upload ? "prepare_and_upload" : "dry_run",
      input_total: allIds.length, offset: settings.offset, selected: 0, counts: { selection_complete: 1 }, events_file: eventsPath,
      manifest_file: null, database_modified: false, completed_at_utc: new Date().toISOString()
    };
    await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
    console.log(JSON.stringify(event));
    console.log(JSON.stringify(summary));
    return { summary, events: [event], runDirectory };
  }

  const rateLimitStart = createStartRateLimiter(settings.delayMs);
  const prechecks = await mapWithConcurrency(selectedIds, settings.concurrency, async (cardId) => {
    await rateLimitStart();
    const candidateUrl = deliveryUrl(settings.cloudName, cardId);
    const base = {
      card_id: cardId,
      candidate_url: candidateUrl,
      provenance: provenanceFor(settings, cardId),
      overwrite_attempted: false
    };
    try {
      const before = await probeCloudinary(settings, cardId);
      if (before.status === 200) {
        return {
          base,
          item: {
            ...base,
            outcome: "cloudinary_existing",
            failure_or_skip_state: null,
            cloudinary_verification: { precheck_status: 200, final_status: 200, checked_at_utc: new Date().toISOString(), content_type: before.contentType, content_length: before.contentLength }
          }
        };
      }
      if (before.status !== 404) throw new Error(`precheck Cloudinary respondeu HTTP ${before.status}`);
      return { base, item: null };
    } catch (error) {
      return {
        base,
        item: {
          ...base,
          outcome: "failed",
          failure_or_skip_state: "cloudinary_precheck_failure",
          cloudinary_verification: { precheck_status: null, final_status: null, checked_at_utc: new Date().toISOString(), content_type: null, content_length: null },
          error: error.message
        }
      };
    }
  });

  let completed = 0;
  let ledgerQueue = Promise.resolve();
  const items = await mapWithConcurrency(prechecks, settings.concurrency, async ({ base, item: precheckedItem }) => {
    let item = precheckedItem;
    if (!item) {
      if (!settings.upload) {
        item = {
          ...base,
          outcome: "cloudinary_missing_dry_run",
          failure_or_skip_state: "upload_not_authorized_in_dry_run",
          cloudinary_verification: { precheck_status: 404, final_status: 404, checked_at_utc: new Date().toISOString(), content_type: null, content_length: null }
        };
      } else {
        try {
          await rateLimitStart();
          const image = await downloadSource(settings, base.card_id);
          if (image.contentAudit !== "png_valido") throw new Error("fonte nao retornou um PNG fisicamente valido; upload recusado");
          const localPath = join(imageDirectory, `${base.card_id}.png`);
          await writeFile(localPath, image.buffer);
          const uploaded = await uploadCloudinary(settings, base.card_id, image);
          // A resposta de upload pode chegar antes de o CDN disponibilizar a URL
          // pública sem versão. Aguarde a propagação antes de declarar falha.
          const after = await waitForCloudinaryReadback(settings, base.card_id);
          if (after.status !== 200 || after.url !== base.candidate_url) throw new Error(`readback Cloudinary respondeu HTTP ${after.status}`);
          item = {
            ...base,
            outcome: "cloudinary_uploaded",
            failure_or_skip_state: null,
            cloudinary_verification: { precheck_status: 404, final_status: 200, checked_at_utc: new Date().toISOString(), content_type: after.contentType, content_length: after.contentLength },
            upload_receipt: { public_id: uploaded.public_id, asset_folder: uploaded.asset_folder, asset_id: uploaded.asset_id, version: uploaded.version, secure_url: uploaded.secure_url },
            downloaded_artifact: { local_file: localPath, byte_size: image.byteSize, sha256: image.sha256, mime_type: image.contentType, width: image.width, height: image.height }
          };
        } catch (error) {
          item = {
            ...base,
            outcome: "failed",
            failure_or_skip_state: "network_or_validation_failure",
            cloudinary_verification: { precheck_status: 404, final_status: null, checked_at_utc: new Date().toISOString(), content_type: null, content_length: null },
            error: error.message
          };
        }
      }
    }
    completed += 1;
    const event = { run_id: runId, status: item.outcome, ...item, progress_completed: completed, progress_total: selectedIds.length, database_modified: false };
    ledgerQueue = ledgerQueue.then(async () => {
      await appendEvent(eventsPath, event);
      console.log(JSON.stringify(event));
    });
    await ledgerQueue;
    return item;
  });
  await ledgerQueue;

  const manifest = sealManifest({
    format: PHOTO_MANIFEST_FORMAT,
    manifest_id: runId,
    generated_at_utc: new Date().toISOString(),
    identity_key: "card_id",
    cloud_name: settings.cloudName,
    database_target: DATABASE_TARGET,
    overwrite_allowed: false,
    automatic_apply: false,
    input: { ...provenance, offset: settings.offset, selected: selectedIds.length },
    safeguards: { concurrency: settings.concurrency, delay_ms_between_card_starts: settings.delayMs, retries: settings.retries, timeout_ms: settings.timeoutMs },
    items
  });
  validateManifestDocument(manifest);
  await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  const eventViews = items.map((item) => ({ status: item.outcome }));
  const summary = {
    format: "clubefutebol-photo-prepare-run-v1",
    run_id: runId,
    mode: settings.upload ? "prepare_and_upload" : "dry_run",
    input_total: allIds.length,
    offset: settings.offset,
    selected: selectedIds.length,
    next_offset: settings.offset + selectedIds.length,
    counts: countStatuses(eventViews),
    events_file: eventsPath,
    manifest_file: manifestPath,
    manifest_sha256: manifest.integrity.sha256,
    database_modified: false,
    completed_at_utc: new Date().toISOString()
  };
  await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
  console.log(JSON.stringify(summary));
  return { summary, events: items, manifest, runDirectory };
}

async function runApply(settings) {
  const runId = utcStamp();
  const runDirectory = join(settings.output, "applies", runId);
  const eventsPath = join(runDirectory, "events.jsonl");
  const summaryPath = join(runDirectory, "summary.json");
  await mkdir(runDirectory, { recursive: true });
  let adapter;
  try {
    const manifest = JSON.parse(await readFile(settings.applyManifest, "utf8"));
    const validated = validateManifestDocument(manifest);
    adapter = await databaseAdapterFor(settings);
    const result = await applyManifestDocument(validated, {
      // O APPLY ocorre logo após o upload. Use a mesma espera de propagação do
      // CDN antes de decidir que a imagem deixou de existir.
      probeCloudinary: (cardId) => waitForCloudinaryReadback(settings, cardId),
      databaseAdapter: adapter
    });
    for (const event of result.events) {
      const persisted = { run_id: runId, manifest_id: validated.manifest_id, ...event };
      await appendEvent(eventsPath, persisted);
      console.log(JSON.stringify(persisted));
    }
    const summary = {
      format: APPLY_RUN_FORMAT,
      run_id: runId,
      mode: "apply_manifest",
      manifest_file: settings.applyManifest,
      manifest_id: validated.manifest_id,
      manifest_sha256: validated.integrity.sha256,
      database_target: DATABASE_TARGET,
      database_access_method: result.database_access_method,
      transaction_scope: result.database_access_method === "direct_postgres_transaction" ? "whole_manifest" : "one_atomic_http_patch_per_card",
      conditional_null_only: true,
      conflicts_preserved: true,
      independently_read_back: result.independently_read_back,
      selected: validated.items.length,
      counts: result.counts,
      events_file: eventsPath,
      completed_at_utc: new Date().toISOString()
    };
    await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
    console.log(JSON.stringify(summary));
    return { summary, events: result.events, runDirectory };
  } catch (error) {
    const event = { run_id: runId, scope: "run", status: "failed_setup", overwritten: false, error: error.message };
    await appendEvent(eventsPath, event);
    const summary = {
      format: APPLY_RUN_FORMAT, run_id: runId, mode: "apply_manifest", manifest_file: settings.applyManifest,
      database_target: DATABASE_TARGET, database_access_method: adapter?.method ?? null, conditional_null_only: true,
      conflicts_preserved: true, independently_read_back: false, selected: 0, counts: { failed_setup: 1 }, events_file: eventsPath,
      completed_at_utc: new Date().toISOString()
    };
    await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
    console.log(JSON.stringify(event));
    console.log(JSON.stringify(summary));
    return { summary, events: [event], runDirectory };
  }
}

export async function run(argv = process.argv.slice(2)) {
  const settings = parseArgs(argv);
  if (settings.help) {
    console.log(usage());
    return { help: true };
  }
  if (settings.discoverMissing) return runDiscovery(settings);
  return settings.applyManifest ? runApply(settings) : runPrepare(settings);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  run().catch((error) => {
    console.error(error.stack || error.message);
    process.exitCode = 1;
  });
}
