#!/usr/bin/env node

import { createHash } from "node:crypto";
import { appendFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { extname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const DEFAULT_CLOUD_NAME = "demsusjwf";
const DEFAULT_UPLOAD_PRESET = "clubefutebol_cards_no_overwrite";
const DEFAULT_ASSET_FOLDER = "clubefutebol/cards/efootballhub";
const DEFAULT_OUTPUT = resolve("output");
const SUPABASE_SCHEMA = "clube_novo";
const SUPABASE_TABLE = "carta_jogo";
const SUPABASE_URL_COLUMN = "foto_url_cloudinary";
const SOURCE_PREFIX = "https://efimg.com/efootballhub22/images/player_cards/";
const MAX_BATCH = 100;

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

function parseArgs(argv) {
  const args = {
    apply: false,
    apiKey: process.env.CLOUDINARY_API_KEY || null,
    apiSecret: process.env.CLOUDINARY_API_SECRET || null,
    assetFolder: DEFAULT_ASSET_FOLDER,
    cardIds: [],
    cloudName: process.env.CLOUDINARY_CLOUD_NAME || DEFAULT_CLOUD_NAME,
    delayMs: 1200,
    input: null,
    limit: null,
    output: DEFAULT_OUTPUT,
    retries: 3,
    supabaseServiceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY || null,
    supabaseUrl: process.env.SUPABASE_URL || null,
    timeoutMs: 30000,
    uploadPreset: process.env.CLOUDINARY_UPLOAD_PRESET || DEFAULT_UPLOAD_PRESET
  };

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    const next = () => {
      const value = argv[++i];
      if (value == null) throw new Error(`valor ausente para ${token}`);
      return value;
    };
    if (token === "--apply") args.apply = true;
    else if (token === "--asset-folder") args.assetFolder = next();
    else if (token === "--card-id") args.cardIds.push(next());
    else if (token === "--cloud-name") args.cloudName = next();
    else if (token === "--delay-ms") args.delayMs = Number(next());
    else if (token === "--input") args.input = next();
    else if (token === "--limit") args.limit = Number(next());
    else if (token === "--output") args.output = resolve(next());
    else if (token === "--retries") args.retries = Number(next());
    else if (token === "--timeout-ms") args.timeoutMs = Number(next());
    else if (token === "--upload-preset") args.uploadPreset = next();
    else if (token === "--help" || token === "-h") args.help = true;
    else throw new Error(`argumento desconhecido: ${token}`);
  }

  if (!args.help) {
    if (!args.input && !args.cardIds.length) throw new Error("informe --input ou ao menos um --card-id");
    if (!Number.isInteger(args.limit) || args.limit < 1 || args.limit > MAX_BATCH) {
      throw new Error(`--limit e obrigatorio e deve estar entre 1 e ${MAX_BATCH}`);
    }
    if (!Number.isInteger(args.delayMs) || args.delayMs < 250) throw new Error("--delay-ms deve ser >= 250");
    if (!Number.isInteger(args.retries) || args.retries < 0 || args.retries > 8) throw new Error("--retries deve estar entre 0 e 8");
    if (Boolean(args.apiKey) !== Boolean(args.apiSecret)) throw new Error("CLOUDINARY_API_KEY e CLOUDINARY_API_SECRET devem ser definidos juntos");
    if (Boolean(args.supabaseUrl) !== Boolean(args.supabaseServiceRoleKey)) {
      throw new Error("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem ser definidos juntos");
    }
    if (args.apply && !args.apiKey) {
      throw new Error("upload requer CLOUDINARY_API_KEY e CLOUDINARY_API_SECRET locais");
    }
    if (args.apply && !args.supabaseUrl) {
      throw new Error("upload requer SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY para vincular a foto em clube_novo.carta_jogo");
    }
  }
  return args;
}

function usage() {
  return `Uso:
  node card-image-extractor.mjs --input cards.csv --limit 10
  node card-image-extractor.mjs --card-id 17592722922839 --limit 1 --apply

Sem --apply, apenas inventaria. --limit e sempre obrigatorio e nunca pode exceder ${MAX_BATCH}.`;
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
    apikey: settings.supabaseServiceRoleKey,
    Authorization: `Bearer ${settings.supabaseServiceRoleKey}`,
    "Accept-Profile": SUPABASE_SCHEMA
  };
  if (write) {
    headers["Content-Type"] = "application/json";
    headers["Content-Profile"] = SUPABASE_SCHEMA;
    headers.Prefer = "return=representation";
  }
  return headers;
}

function supabaseCardUrl(settings, cardId, select) {
  const base = String(settings.supabaseUrl).replace(/\/$/, "");
  const query = new URLSearchParams({
    select,
    card_id: `eq.${assertCardId(cardId)}`,
    limit: "2"
  });
  return `${base}/rest/v1/${SUPABASE_TABLE}?${query}`;
}

async function readCanonicalCard(settings, cardId) {
  const response = await fetchWithRetry(
    supabaseCardUrl(settings, cardId, `card_id,${SUPABASE_URL_COLUMN}`),
    { method: "GET", headers: supabaseHeaders(settings) },
    settings
  );
  const rows = await response.json().catch(() => []);
  if (!response.ok) throw new Error(`Supabase read respondeu HTTP ${response.status}`);
  if (!Array.isArray(rows) || rows.length !== 1 || String(rows[0].card_id) !== cardId) {
    throw new Error(`card_id ${cardId} nao existe inequivocamente em ${SUPABASE_SCHEMA}.${SUPABASE_TABLE}`);
  }
  return rows[0];
}

async function syncCanonicalCardPhoto(settings, cardId, cloudinaryUrl) {
  const response = await fetchWithRetry(
    supabaseCardUrl(settings, cardId, `card_id,${SUPABASE_URL_COLUMN}`),
    {
      method: "PATCH",
      headers: supabaseHeaders(settings, true),
      body: JSON.stringify({ [SUPABASE_URL_COLUMN]: cloudinaryUrl })
    },
    settings
  );
  const rows = await response.json().catch(() => []);
  if (!response.ok) throw new Error(`Supabase update respondeu HTTP ${response.status}`);
  if (!Array.isArray(rows) || rows.length !== 1 || String(rows[0].card_id) !== cardId) {
    throw new Error(`readback Supabase nao retornou exatamente o card_id ${cardId}`);
  }
  if (rows[0][SUPABASE_URL_COLUMN] !== cloudinaryUrl) {
    throw new Error(`readback Supabase divergiu para card_id ${cardId}`);
  }
  return rows[0];
}

function utcStamp() {
  return new Date().toISOString().replaceAll(":", "-").replaceAll(".", "-");
}

async function appendEvent(path, event) {
  await appendFile(path, `${JSON.stringify(event)}\n`, "utf8");
}

export async function run(argv = process.argv.slice(2)) {
  const settings = parseArgs(argv);
  if (settings.help) {
    console.log(usage());
    return { help: true };
  }

  const inputIds = settings.input ? await loadInput(settings.input) : [];
  const allIds = uniqueCardIds([...settings.cardIds, ...inputIds]);
  const selectedIds = allIds.slice(0, settings.limit);
  const runId = utcStamp();
  const runDirectory = join(settings.output, "runs", runId);
  const imageDirectory = join(runDirectory, "images");
  const eventsPath = join(runDirectory, "events.jsonl");
  const summaryPath = join(runDirectory, "summary.json");
  await mkdir(imageDirectory, { recursive: true });

  const events = [];
  for (let index = 0; index < selectedIds.length; index += 1) {
    const cardId = selectedIds[index];
    const baseEvent = { run_id: runId, card_id: cardId, source_url: sourceUrl(cardId), cloudinary_url: deliveryUrl(settings.cloudName, cardId) };
    let event;
    try {
      if (settings.apply) await readCanonicalCard(settings, cardId);
      const before = await probeCloudinary(settings, cardId);
      if (before.status === 200) {
        if (settings.apply) {
          await syncCanonicalCardPhoto(settings, cardId, before.url);
          event = {
            ...baseEvent,
            status: "existing_synced",
            precheck_status: 200,
            overwritten: false,
            database_synced: true,
            database_target: `${SUPABASE_SCHEMA}.${SUPABASE_TABLE}.${SUPABASE_URL_COLUMN}`,
            content_type: before.contentType,
            byte_size: before.contentLength
          };
        } else {
          event = { ...baseEvent, status: "existing", precheck_status: 200, overwritten: false, content_type: before.contentType, byte_size: before.contentLength };
        }
      } else if (before.status !== 404) {
        throw new Error(`precheck Cloudinary respondeu HTTP ${before.status}`);
      } else if (!settings.apply) {
        event = { ...baseEvent, status: "missing_dry_run", precheck_status: 404, overwritten: false };
      } else {
        const image = await downloadSource(settings, cardId);
        const localPath = join(imageDirectory, `${cardId}.png`);
        await writeFile(localPath, image.buffer);
        const uploaded = await uploadCloudinary(settings, cardId, image);
        const after = await probeCloudinary(settings, cardId, true);
        if (after.status !== 200) throw new Error(`readback Cloudinary respondeu HTTP ${after.status}`);
        await syncCanonicalCardPhoto(settings, cardId, after.url);
        event = {
          ...baseEvent,
          status: "uploaded",
          precheck_status: 404,
          readback_status: 200,
          overwritten: false,
          database_synced: true,
          database_target: `${SUPABASE_SCHEMA}.${SUPABASE_TABLE}.${SUPABASE_URL_COLUMN}`,
          public_id: uploaded.public_id,
          asset_folder: uploaded.asset_folder,
          asset_id: uploaded.asset_id,
          version: uploaded.version,
          secure_url: uploaded.secure_url,
          local_file: localPath,
          byte_size: image.byteSize,
          sha256: image.sha256,
          mime_type: image.contentType,
          content_audit: image.contentAudit,
          width: image.width,
          height: image.height
        };
      }
    } catch (error) {
      event = { ...baseEvent, status: "failed", overwritten: false, error: error.message };
    }
    events.push(event);
    await appendEvent(eventsPath, event);
    console.log(JSON.stringify(event));
    if (index + 1 < selectedIds.length) await sleep(settings.delayMs + Math.floor(Math.random() * 251));
  }

  const counts = {};
  for (const event of events) counts[event.status] = (counts[event.status] ?? 0) + 1;
  const summary = {
    format: "clubefutebol-card-image-extractor-run-v1",
    run_id: runId,
    mode: settings.apply ? "apply" : "inventory",
    cloud_name: settings.cloudName,
    upload_preset: settings.uploadPreset,
    upload_mode: settings.apiKey ? "authenticated_basic" : "none",
    asset_folder: settings.assetFolder,
    overwrite_allowed: false,
    database_sync_required_on_apply: true,
    database_target: `${SUPABASE_SCHEMA}.${SUPABASE_TABLE}.${SUPABASE_URL_COLUMN}`,
    input_total: allIds.length,
    selected: selectedIds.length,
    limit: settings.limit,
    counts,
    events_file: eventsPath,
    completed_at_utc: new Date().toISOString()
  };
  await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
  console.log(JSON.stringify(summary));
  return { summary, events, runDirectory };
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  run().catch((error) => {
    console.error(error.stack || error.message);
    process.exitCode = 1;
  });
}


