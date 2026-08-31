#!/usr/bin/env node

import { randomBytes, timingSafeEqual } from "node:crypto";
import { spawn } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { validateManifestDocument } from "./photo-manifest.mjs";

export const LOOPBACK_HOST = "127.0.0.1";
const TOOL_ROOT = dirname(fileURLToPath(import.meta.url));
const SAMPLE_SIZE = 1;
const BATCH_SIZE = 100;
const BATCH_CONCURRENCY = 4;
const BATCH_DELAY_MS = 500;
const CLOUDINARY_CLOUD_NAME = "demsusjwf";
const SUPABASE_PROJECT_URL = "https://trqqpsnafpbudtvvicch.supabase.co";
const MAX_BODY_BYTES = 16 * 1024 * 1024;
const IDLE_TIMEOUT_MS = 30 * 60 * 1000;
const SAVED_CREDENTIALS_PATH = join(TOOL_ROOT, "output", "state", "credentials.windows-dpapi.json");
const STATIC_FILES = new Map([
  ["/interface-local.css", { file: "interface-local.css", type: "text/css; charset=utf-8" }],
  ["/interface-local.js", { file: "interface-local.js", type: "text/javascript; charset=utf-8" }]
]);

export function runtimeCapabilities(env = process.env) {
  const cloudinaryConfigured = Boolean(env.CLOUDINARY_API_KEY && env.CLOUDINARY_API_SECRET);
  const directPostgresConfigured = Boolean(env.SUPABASE_DB_URL);
  const dataApiConfigured = Boolean(env.SUPABASE_URL && (env.SUPABASE_SECRET_KEY || env.SUPABASE_SERVICE_ROLE_KEY));
  return {
    cloudinaryConfigured,
    directPostgresConfigured,
    dataApiConfigured,
    databaseConfigured: directPostgresConfigured || dataApiConfigured,
    preferredDatabaseMethod: directPostgresConfigured ? "direct_postgres_transaction" : dataApiConfigured ? "data_api_secret_key_server_side" : null
  };
}

function cleanSecret(value) {
  const cleaned = String(value ?? "").trim();
  if (cleaned.length > 8192 || /[\r\n\0]/.test(cleaned)) throw new Error("Uma credencial tem formato inválido.");
  return cleaned;
}

function dpapiTransform(mode, input) {
  if (process.platform !== "win32") return Promise.reject(new Error("O cofre de credenciais desta interface exige Windows."));
  const protectScript = "Add-Type -AssemblyName System.Security;$plain=[Console]::In.ReadToEnd();$bytes=$null;$sealed=$null;try{$bytes=[Text.Encoding]::UTF8.GetBytes($plain);$sealed=[Security.Cryptography.ProtectedData]::Protect($bytes,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser);[Console]::Out.Write([Convert]::ToBase64String($sealed))}finally{if($bytes){[Array]::Clear($bytes,0,$bytes.Length)};if($sealed){[Array]::Clear($sealed,0,$sealed.Length)};$plain=$null}";
  const unprotectScript = "Add-Type -AssemblyName System.Security;$cipher=[Console]::In.ReadToEnd();$sealed=$null;$bytes=$null;try{$sealed=[Convert]::FromBase64String($cipher);$bytes=[Security.Cryptography.ProtectedData]::Unprotect($sealed,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser);[Console]::Out.Write([Text.Encoding]::UTF8.GetString($bytes))}finally{if($sealed){[Array]::Clear($sealed,0,$sealed.Length)};if($bytes){[Array]::Clear($bytes,0,$bytes.Length)};$cipher=$null}";
  const script = mode === "protect" ? protectScript : unprotectScript;
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", script], {
      cwd: TOOL_ROOT,
      stdio: ["pipe", "pipe", "pipe"],
      windowsHide: true
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { if (stdout.length < 65536) stdout += chunk.toString("utf8"); });
    child.stderr.on("data", (chunk) => { if (stderr.length < 4096) stderr += chunk.toString("utf8"); });
    child.once("error", rejectPromise);
    child.once("close", (code) => {
      if (code === 0 && stdout.trim()) resolvePromise(stdout.trim());
      else rejectPromise(new Error("O cofre de credenciais do Windows não pôde ser aberto. Feche e abra o aplicativo novamente; se persistir, consulte o log local."));
      stdout = "";
      stderr = "";
    });
    child.stdin.end(input, "utf8");
  });
}

async function saveCredentialsToWindowsVault(credentials) {
  let plainText = JSON.stringify({
    cloudinaryApiKey: credentials.cloudinaryApiKey,
    cloudinaryApiSecret: credentials.cloudinaryApiSecret,
    supabaseDbUrl: credentials.supabaseDbUrl
  });
  try {
    const ciphertext = await dpapiTransform("protect", plainText);
    await mkdir(dirname(SAVED_CREDENTIALS_PATH), { recursive: true });
    await writeFile(SAVED_CREDENTIALS_PATH, `${JSON.stringify({
      format: "clubefutebol-photo-credentials-windows-dpapi-v2",
      protection: "Windows DPAPI CurrentUser",
      ciphertext
    }, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });
  } finally {
    plainText = "";
  }
}

async function loadCredentialsFromWindowsVault() {
  let plainText = "";
  let document = null;
  let parsed = null;
  try {
    document = JSON.parse(await readFile(SAVED_CREDENTIALS_PATH, "utf8"));
    if (document?.format !== "clubefutebol-photo-credentials-windows-dpapi-v2" || !/^[A-Za-z0-9+/=]+$/.test(String(document.ciphertext ?? ""))) {
      throw new Error("O cofre de credenciais salvo é inválido.");
    }
    plainText = await dpapiTransform("unprotect", document.ciphertext);
    parsed = JSON.parse(plainText);
    const credentials = validateCredentialPayload(parsed, "direct", {});
    return credentials;
  } finally {
    plainText = "";
    if (document && typeof document === "object") document.ciphertext = "";
    if (parsed && typeof parsed === "object") for (const key of Object.keys(parsed)) parsed[key] = "";
  }
}

async function windowsVaultAvailable() {
  try {
    const credentials = await loadCredentialsFromWindowsVault();
    for (const key of Object.keys(credentials)) credentials[key] = "";
    return true;
  } catch {
    return false;
  }
}

export function validateCredentialPayload(payload, mode, env = process.env) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) throw new Error("Dados da operação ausentes.");
  const credentials = {
    cloudinaryApiKey: cleanSecret(payload.cloudinaryApiKey || env.CLOUDINARY_API_KEY),
    cloudinaryApiSecret: cleanSecret(payload.cloudinaryApiSecret || env.CLOUDINARY_API_SECRET),
    supabaseDbUrl: cleanSecret(payload.supabaseDbUrl || env.SUPABASE_DB_URL),
    supabaseServerKey: cleanSecret(payload.supabaseServerKey || env.SUPABASE_SECRET_KEY || env.SUPABASE_SERVICE_ROLE_KEY)
  };
  if (mode === "sample" || mode === "batch" || mode === "direct") {
    if (!credentials.cloudinaryApiKey || !credentials.cloudinaryApiSecret) throw new Error("Cole a API Key e a API Secret do Cloudinary na tela.");
  }
  if (mode === "apply" || mode === "discover" || mode === "direct") {
    if (!credentials.supabaseDbUrl && !credentials.supabaseServerKey) throw new Error("Cole a SUPABASE_DB_URL ou a chave secreta de servidor na tela.");
    if (mode === "direct" && !credentials.supabaseDbUrl) throw new Error("Cole a SUPABASE_DB_URL na tela.");
    if (credentials.supabaseDbUrl) {
      let parsed;
      try { parsed = new URL(credentials.supabaseDbUrl); } catch { throw new Error("SUPABASE_DB_URL inválida."); }
      if (!new Set(["postgres:", "postgresql:"]).has(parsed.protocol) || !parsed.hostname) throw new Error("SUPABASE_DB_URL precisa ser uma conexão PostgreSQL válida.");
    }
  }
  return credentials;
}

export function buildChildEnvironment(credentials, baseEnvironment = process.env) {
  const child = { ...baseEnvironment, CLOUDINARY_CLOUD_NAME, CLOUDINARY_UPLOAD_PRESET: "clubefutebol_cards_no_overwrite" };
  if (credentials.cloudinaryApiKey) child.CLOUDINARY_API_KEY = credentials.cloudinaryApiKey;
  if (credentials.cloudinaryApiSecret) child.CLOUDINARY_API_SECRET = credentials.cloudinaryApiSecret;
  if (credentials.supabaseDbUrl) child.SUPABASE_DB_URL = credentials.supabaseDbUrl;
  if (credentials.supabaseServerKey) {
    child.SUPABASE_URL = SUPABASE_PROJECT_URL;
    child.SUPABASE_SECRET_KEY = credentials.supabaseServerKey;
  }
  return child;
}

function secureHeaders(contentType = "application/json; charset=utf-8") {
  return {
    "Cache-Control": "no-store, max-age=0",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' https://res.cloudinary.com; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
    "Content-Type": contentType,
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    Pragma: "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY"
  };
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, secureHeaders());
  response.end(JSON.stringify(payload));
}

function tokenMatches(received, expected) {
  if (typeof received !== "string") return false;
  const left = Buffer.from(received);
  const right = Buffer.from(expected);
  return left.length === right.length && timingSafeEqual(left, right);
}

async function readJsonBody(request) {
  const chunks = [];
  let total = 0;
  try {
    for await (const chunk of request) {
      total += chunk.length;
      if (total > MAX_BODY_BYTES) throw new Error("Dados enviados excedem o limite local de 16 MiB.");
      chunks.push(Buffer.from(chunk));
    }
    const joined = Buffer.concat(chunks);
    try {
      return JSON.parse(joined.toString("utf8"));
    } finally {
      joined.fill(0);
    }
  } finally {
    for (const chunk of chunks) chunk.fill(0);
  }
}

function parseExtractorOutput(stdout) {
  let summary = null;
  let event = null;
  for (const line of stdout.split(/\r?\n/)) {
    if (!line.trim().startsWith("{")) continue;
    try {
      const value = JSON.parse(line);
      if (value.format && value.run_id) summary = value;
      else if (value.status && (value.card_id || value.scope === "run")) event = value;
    } catch {}
  }
  return { event, summary };
}

function extractorArguments(mode, universe, manifestPath) {
  if (mode === "sample" || mode === "batch") {
    const limit = mode === "sample" ? SAMPLE_SIZE : BATCH_SIZE;
    const concurrency = mode === "sample" ? 1 : BATCH_CONCURRENCY;
    return [
      "--input", universe.snapshotPath,
      "--input-kind", "database_null_snapshot",
      "--offset", String(universe.nextOffset),
      "--limit", String(limit),
      "--concurrency", String(concurrency),
      "--delay-ms", String(BATCH_DELAY_MS),
      "--upload"
    ];
  }
  if (mode === "discover") return ["--discover-missing", "--database-method", "auto"];
  if (mode === "apply") return ["--apply-manifest", manifestPath, "--database-method", "auto"];
  throw new Error("Modo de execução local inválido.");
}

function resultMessage(mode, event, summary, ok) {
  if (mode === "discover" && ok) return `Campo confirmado; ${summary?.missing_cards ?? 0} cards sem link foram colocados na fila local.`;
  if (mode === "apply" && ok) return "APPLY MANIFEST concluído; conflitos foram preservados e o banco foi relido.";
  if (!ok && typeof event?.error === "string" && event.error.length <= 600) {
    if (/password authentication failed/i.test(event.error)) return "A senha do banco na Supabase Database URL foi recusada.";
    if (/self-signed certificate/i.test(event.error)) return "A conexão segura com o Supabase foi recusada pelo certificado local.";
    return event.error;
  }
  if (ok && mode !== "apply" && summary?.selected === 0) return "O universo selecionado chegou ao fim.";
  if (mode === "sample" && ok) return "A amostra gerou um manifesto válido. Nenhuma linha do banco foi alterada.";
  if (mode === "batch" && ok) return "O lote gerou um manifesto durável. O banco continua inalterado até APPLY MANIFEST.";
  return "A operação terminou com falha. Consulte o resumo e o log local.";
}

async function executeExtractor(mode, credentials, universe = null, manifestPath = null, onProgress = () => {}) {
  const extractor = join(TOOL_ROOT, "card-image-extractor.mjs");
  const childEnvironment = buildChildEnvironment(credentials);
  let stdout = "";
  let stderr = "";
  try {
    const exitCode = await new Promise((resolvePromise, rejectPromise) => {
      const child = spawn(process.execPath, [extractor, ...extractorArguments(mode, universe, manifestPath)], {
        cwd: TOOL_ROOT,
        env: childEnvironment,
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true
      });
      let pendingLine = "";
      child.stdout.on("data", (chunk) => {
        const text = chunk.toString("utf8");
        if (stdout.length < 512000) stdout += text;
        pendingLine += text;
        const lines = pendingLine.split(/\r?\n/);
        pendingLine = lines.pop() ?? "";
        for (const line of lines) {
          const parsed = parseExtractorOutput(line);
          if (parsed.event) onProgress(parsed.event);
          if (parsed.summary) onProgress(parsed.summary);
        }
      });
      child.stderr.on("data", (chunk) => { if (stderr.length < 32000) stderr += chunk.toString("utf8"); });
      child.once("error", rejectPromise);
      child.once("close", resolvePromise);
    });
    const { event, summary } = parseExtractorOutput(stdout);
    const failedCount = (summary?.counts?.failed ?? 0) + (summary?.counts?.failed_setup ?? 0) + (summary?.counts?.cloudinary_reverification_failed ?? 0);
    const ok = exitCode === 0 && Boolean(summary) && failedCount === 0 && (mode === "discover" || summary.selected > 0 || summary.counts?.selection_complete === 1);
    const runKind = mode === "apply" ? "applies" : mode === "discover" ? "discoveries" : "runs";
    const runPath = summary?.run_id ? join(TOOL_ROOT, "output", runKind, summary.run_id) : null;
    return {
      ok,
      mode,
      status: event?.status ?? (ok ? "completed" : "failed"),
      message: resultMessage(mode, event, summary, ok),
      runPath,
      summaryPath: runPath ? join(runPath, "summary.json") : null,
      eventsPath: runPath ? join(runPath, "events.jsonl") : null,
      manifestPath: summary?.manifest_file ?? null,
      manifestSha256: summary?.manifest_sha256 ?? null,
      databaseAccessMethod: summary?.database_access_method ?? null,
      databaseModified: mode === "apply" ? (summary?.counts?.updated ?? 0) > 0 : false,
      columnVerified: summary?.column_verified ?? null,
      columnVerification: summary?.column_verification ?? null,
      totalCards: summary?.total_cards ?? null,
      alreadyLinked: summary?.already_linked ?? null,
      missingCards: summary?.missing_cards ?? null,
      snapshotPath: summary?.snapshot_file ?? null,
      snapshotSha256: summary?.snapshot_sha256 ?? null,
      selected: summary?.selected ?? 0,
      nextOffset: summary?.next_offset ?? universe?.nextOffset ?? 0,
      counts: summary?.counts ?? {}
    };
  } finally {
    stdout = "";
    stderr = "";
    for (const name of ["CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET", "SUPABASE_DB_URL", "SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY"]) {
      if (name in childEnvironment) childEnvironment[name] = "";
      delete childEnvironment[name];
    }
  }
}

async function universeFromDiscovery(result) {
  if (!result?.ok || !result.columnVerified || !result.snapshotPath || !Number.isInteger(result.missingCards) || result.missingCards < 0) {
    throw new Error("A descoberta não produziu uma fila Supabase válida.");
  }
  const sha256 = result.snapshotSha256;
  if (!/^[0-9a-f]{64}$/.test(String(sha256))) throw new Error("A fila descoberta não possui SHA-256 válido.");
  const stateDirectory = join(TOOL_ROOT, "output", "state");
  const statePath = join(stateDirectory, `${sha256}.json`);
  await mkdir(stateDirectory, { recursive: true });
  let nextOffset = 0;
  try {
    const saved = JSON.parse(await readFile(statePath, "utf8"));
    if (saved.input_sha256 === sha256 && Number.isInteger(saved.next_offset) && saved.next_offset >= 0 && saved.next_offset <= result.missingCards) nextOffset = saved.next_offset;
  } catch {}
  return {
    originalName: "Supabase · clube_novo.carta_jogo sem foto_url_cloudinary",
    sha256,
    snapshotPath: result.snapshotPath,
    statePath,
    total: result.missingCards,
    nextOffset,
    discoveryRunPath: result.runPath,
    totalCards: result.totalCards,
    alreadyLinked: result.alreadyLinked,
    columnVerification: result.columnVerification
  };
}

async function persistUniverseState(universe, lastManifestPath) {
  await writeFile(universe.statePath, `${JSON.stringify({
    format: "clubefutebol-photo-database-universe-state-v1",
    input_name: universe.originalName,
    input_sha256: universe.sha256,
    total: universe.total,
    next_offset: universe.nextOffset,
    last_manifest_file: lastManifestPath,
    updated_at_utc: new Date().toISOString()
  }, null, 2)}\n`, "utf8");
}

async function persistImportedManifest(payload) {
  const content = String(payload?.manifestContent ?? "");
  if (!content) throw new Error("Selecione um manifest.json ou use o último manifesto gerado.");
  const document = JSON.parse(content);
  const validated = validateManifestDocument(document);
  const directory = join(TOOL_ROOT, "output", "imported-manifests");
  await mkdir(directory, { recursive: true });
  const path = join(directory, `${validated.integrity.sha256}.json`);
  await writeFile(path, `${JSON.stringify(document, null, 2)}\n`, "utf8");
  return path;
}

function openDefaultBrowser(url) {
  if (process.platform === "win32") {
    const child = spawn("cmd.exe", ["/d", "/s", "/c", "start", "", url], { detached: true, stdio: "ignore", windowsHide: true });
    child.unref();
    return;
  }
  const command = process.platform === "darwin" ? "open" : "xdg-open";
  const child = spawn(command, [url], { detached: true, stdio: "ignore" });
  child.unref();
}

export async function startLocalInterface({ openBrowser = true } = {}) {
  const sessionToken = randomBytes(32).toString("hex");
  const htmlTemplate = await readFile(join(TOOL_ROOT, "interface-local.html"), "utf8");
  const capabilities = runtimeCapabilities();
  let savedCredentialsAvailable = await windowsVaultAvailable();
  let busy = false;
  let samplePassed = false;
  let universe = null;
  let discovery = null;
  let lastManifestPath = null;
  let runState = {
    running: false,
    mode: null,
    phase: "idle",
    completed: 0,
    total: 0,
    batches: 0,
    updated: 0,
    conflicts: 0,
    alreadyCurrent: 0,
    lastStatus: null,
    result: null
  };
  let idleTimer = null;
  let expectedOrigin = null;
  const protectedPosts = new Set(["/api/start-direct", "/api/discover-universe", "/api/run-sample", "/api/run-batch", "/api/apply-manifest", "/api/shutdown"]);

  async function runDirectPipeline(credentials, { rememberCredentials = false } = {}) {
    const totals = { batches: 0, updated: 0, conflicts: 0, alreadyCurrent: 0 };
    let lastBatch = null;
    let lastApply = null;
    try {
      universe = null;
      discovery = null;
      lastManifestPath = null;
      runState = {
        running: true,
        mode: "direct",
        phase: "discovering",
        completed: 0,
        total: 0,
        ...totals,
        lastStatus: "consulting_database",
        result: null
      };
      const discovered = await executeExtractor("discover", credentials, null, null, (progress) => {
        if (progress?.status) runState = { ...runState, lastStatus: progress.status };
      });
      if (!discovered.ok) throw new Error(discovered.message || "A consulta inicial ao Supabase falhou.");
      if (rememberCredentials) {
        await saveCredentialsToWindowsVault(credentials);
        savedCredentialsAvailable = true;
      }

      universe = await universeFromDiscovery(discovered);
      // A fila contém somente valores atualmente NULL. Cada nova execução começa
      // no primeiro item dessa fotografia atual do banco; assim um manifesto antigo
      // nunca faz o fluxo direto pular uma carta ainda pendente.
      universe.nextOffset = 0;
      discovery = discovered;
      samplePassed = false;
      lastManifestPath = null;
      runState = {
        ...runState,
        phase: universe.total === 0 ? "completed" : "preparing_batch",
        total: universe.total,
        lastStatus: universe.total === 0 ? "nothing_pending" : "database_queue_ready"
      };

      while (universe.nextOffset < universe.total) {
        const batchStart = universe.nextOffset;
        const batchNumber = totals.batches + 1;
        runState = {
          ...runState,
          phase: "extracting_batch",
          completed: batchStart,
          batches: totals.batches,
          lastStatus: `batch_${batchNumber}_starting`
        };
        lastBatch = await executeExtractor("batch", credentials, universe, null, (progress) => {
          if (progress?.status) {
            const withinBatch = Number.isInteger(progress.progress_completed) ? progress.progress_completed : 0;
            runState = {
              ...runState,
              completed: Math.min(universe.total, batchStart + withinBatch),
              lastStatus: progress.status
            };
          }
        });
        if (!lastBatch.ok || !lastBatch.manifestPath) {
          throw new Error(lastBatch.message || `O lote ${batchNumber} não produziu um manifesto válido.`);
        }
        if (!Number.isInteger(lastBatch.nextOffset) || lastBatch.nextOffset <= batchStart || lastBatch.nextOffset > universe.total) {
          throw new Error(`O lote ${batchNumber} retornou um ponto de continuação inválido.`);
        }

        lastManifestPath = lastBatch.manifestPath;
        runState = {
          ...runState,
          phase: "applying_batch",
          completed: batchStart,
          lastStatus: `batch_${batchNumber}_validating_and_applying`
        };
        lastApply = await executeExtractor("apply", credentials, universe, lastManifestPath, (progress) => {
          if (progress?.status) runState = { ...runState, lastStatus: progress.status };
        });
        if (!lastApply.ok) throw new Error(lastApply.message || `A gravação e releitura do lote ${batchNumber} falharam.`);

        totals.batches += 1;
        totals.updated += Number(lastApply.counts?.updated ?? 0);
        totals.conflicts += Number(lastApply.counts?.conflict_preserved ?? lastApply.counts?.conflict ?? 0);
        totals.alreadyCurrent += Number(lastApply.counts?.already_applied ?? 0);
        universe.nextOffset = lastBatch.nextOffset;
        await persistUniverseState(universe, lastManifestPath);
        runState = {
          ...runState,
          phase: universe.nextOffset < universe.total ? "preparing_batch" : "completed",
          completed: universe.nextOffset,
          ...totals,
          lastStatus: `batch_${batchNumber}_verified`
        };
      }

      const result = {
        ok: true,
        mode: "direct",
        status: "completed",
        message: universe.total === 0
          ? "Nenhuma carta sem link foi encontrada no Supabase."
          : `${totals.updated} links foram gravados e conferidos no Supabase.`,
        selected: universe.total,
        total: universe.total,
        ...totals,
        discoveryRunPath: discovery?.runPath ?? null,
        lastRunPath: lastBatch?.runPath ?? null,
        lastApplyPath: lastApply?.runPath ?? null,
        lastManifestPath,
        databaseAccessMethod: lastApply?.databaseAccessMethod ?? discovery?.databaseAccessMethod ?? null
      };
      runState = { ...runState, running: false, phase: "completed", completed: universe.total, lastStatus: "completed", result };
    } catch (error) {
      const result = {
        ok: false,
        mode: "direct",
        status: "failed",
        message: error.message?.slice(0, 600) || "A execução direta falhou.",
        selected: universe?.total ?? 0,
        total: universe?.total ?? 0,
        ...totals,
        discoveryRunPath: discovery?.runPath ?? null,
        lastRunPath: lastBatch?.runPath ?? null,
        lastApplyPath: lastApply?.runPath ?? null,
        lastManifestPath,
        databaseAccessMethod: lastApply?.databaseAccessMethod ?? discovery?.databaseAccessMethod ?? null
      };
      runState = { ...runState, running: false, phase: "failed", ...totals, lastStatus: "failed", result };
    } finally {
      busy = false;
      for (const key of Object.keys(credentials)) credentials[key] = "";
    }
  }

  const server = createServer(async (request, response) => {
    const url = new URL(request.url ?? "/", expectedOrigin ?? "http://127.0.0.1");
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => server.close(), IDLE_TIMEOUT_MS);
    try {
      if (request.method === "GET" && url.pathname === "/") {
        const html = htmlTemplate.replace("__LOCAL_SESSION_TOKEN__", sessionToken);
        response.writeHead(200, secureHeaders("text/html; charset=utf-8"));
        response.end(html);
        return;
      }
      if (request.method === "GET" && STATIC_FILES.has(url.pathname)) {
        const asset = STATIC_FILES.get(url.pathname);
        response.writeHead(200, secureHeaders(asset.type));
        response.end(await readFile(join(TOOL_ROOT, asset.file)));
        return;
      }
      if (request.method === "POST" && protectedPosts.has(url.pathname)) {
        if (request.headers.origin !== expectedOrigin || !tokenMatches(request.headers["x-local-session"], sessionToken)) {
          sendJson(response, 403, { ok: false, message: "Sessão local inválida." });
          return;
        }
      }
      if (request.method === "GET" && url.pathname === "/api/status") {
        if (!tokenMatches(request.headers["x-local-session"], sessionToken)) {
          sendJson(response, 403, { ok: false, message: "Sessão local inválida." });
          return;
        }
        sendJson(response, 200, {
          ok: true, samplePassed, universeLoaded: Boolean(universe), universeName: universe?.originalName ?? null,
          universeTotal: universe?.total ?? 0,
          nextOffset: universe?.nextOffset ?? 0,
          lastManifestPath,
          capabilities: { ...capabilities, credentialsSaved: savedCredentialsAvailable },
          ...runState
        });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/shutdown") {
        sendJson(response, 200, { ok: true });
        setImmediate(() => { if (server.listening) server.close(); });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/start-direct") {
        if (busy) { sendJson(response, 409, { ok: false, message: "Já existe uma execução em andamento." }); return; }
        let payload = null;
        let credentials = null;
        let rememberCredentials = false;
        try {
          payload = await readJsonBody(request);
          const enteredCredentials = [payload?.cloudinaryApiKey, payload?.cloudinaryApiSecret, payload?.supabaseDbUrl]
            .some((value) => Boolean(String(value ?? "").trim()));
          if (enteredCredentials) {
            credentials = validateCredentialPayload(payload, "direct");
            rememberCredentials = true;
          } else if (payload?.useSavedCredentials === true) {
            credentials = await loadCredentialsFromWindowsVault();
          } else {
            credentials = validateCredentialPayload(payload, "direct");
          }
          busy = true;
          runState = {
            running: true,
            mode: "direct",
            phase: "starting",
            completed: 0,
            total: 0,
            batches: 0,
            updated: 0,
            conflicts: 0,
            alreadyCurrent: 0,
            lastStatus: "starting",
            result: null
          };
          const taskCredentials = credentials;
          credentials = null;
          sendJson(response, 202, { ok: true, accepted: true, message: "Execução iniciada." });
          setImmediate(() => { void runDirectPipeline(taskCredentials, { rememberCredentials }); });
        } finally {
          if (payload && typeof payload === "object") for (const key of Object.keys(payload)) payload[key] = "";
          if (credentials) for (const key of Object.keys(credentials)) credentials[key] = "";
          payload = null;
          credentials = null;
        }
        return;
      }
      if (request.method === "POST" && ["/api/discover-universe", "/api/run-sample", "/api/run-batch", "/api/apply-manifest"].includes(url.pathname)) {
        const mode = url.pathname === "/api/discover-universe" ? "discover" : url.pathname === "/api/run-sample" ? "sample" : url.pathname === "/api/run-batch" ? "batch" : "apply";
        if (busy) { sendJson(response, 409, { ok: false, message: "Já existe uma execução em andamento." }); return; }
        if ((mode === "sample" || mode === "batch") && !universe) { sendJson(response, 412, { ok: false, message: "Consulte primeiro o Supabase para criar a fila de cards sem link." }); return; }
        if (mode === "batch" && !samplePassed) { sendJson(response, 412, { ok: false, message: "Execute e aprove primeiro a amostra de 1 card nesta sessão." }); return; }
        let payload = null;
        let credentials = null;
        try {
          payload = await readJsonBody(request);
          if (mode === "batch" && payload?.confirmBatch !== true) { sendJson(response, 412, { ok: false, message: "Confirme explicitamente o lote de até 100 cards." }); return; }
          if (mode === "apply" && payload?.confirmApply !== true) { sendJson(response, 412, { ok: false, message: "Confirme explicitamente APPLY MANIFEST." }); return; }
          credentials = validateCredentialPayload(payload, mode);
          let manifestPath = null;
          if (mode === "apply") manifestPath = payload?.manifestContent ? await persistImportedManifest(payload) : lastManifestPath;
          if (mode === "apply" && !manifestPath) { sendJson(response, 412, { ok: false, message: "Nenhum manifesto foi selecionado ou gerado nesta sessão." }); return; }

          busy = true;
          runState = { running: true, mode, completed: 0, total: mode === "sample" ? 1 : mode === "batch" ? 100 : 0, lastStatus: "starting" };
          try {
            const result = await executeExtractor(mode, credentials, universe, manifestPath, (progress) => {
              if (progress?.format) runState = { ...runState, completed: progress.selected ?? runState.completed, total: progress.selected ?? runState.total, lastStatus: "summary" };
              else if (progress?.status) runState = { ...runState, completed: progress.progress_completed ?? runState.completed, total: progress.progress_total ?? runState.total, lastStatus: progress.status };
            });
            if (mode === "discover" && result.ok) {
              universe = await universeFromDiscovery(result);
              discovery = result;
              samplePassed = false;
              lastManifestPath = null;
            }
            if (mode === "sample" && result.ok && result.selected === 1) samplePassed = true;
            if (mode !== "apply" && result.ok && result.selected > 0) {
              universe.nextOffset = result.nextOffset;
              lastManifestPath = result.manifestPath;
              await persistUniverseState(universe, lastManifestPath);
            }
            runState = { ...runState, running: false, lastStatus: result.status, result };
            sendJson(response, result.ok ? 200 : 422, result);
          } finally {
            busy = false;
            runState = { ...runState, running: false };
          }
        } finally {
          if (payload && typeof payload === "object") for (const key of Object.keys(payload)) payload[key] = "";
          if (credentials) for (const key of Object.keys(credentials)) credentials[key] = "";
          payload = null;
          credentials = null;
        }
        return;
      }
      sendJson(response, 404, { ok: false, message: "Rota local não encontrada." });
    } catch (error) {
      sendJson(response, 400, { ok: false, message: error.message?.slice(0, 600) || "A solicitação local não pôde ser processada." });
    }
  });
  server.on("close", () => clearTimeout(idleTimer));
  await new Promise((resolvePromise, rejectPromise) => {
    server.once("error", rejectPromise);
    server.listen(0, LOOPBACK_HOST, resolvePromise);
  });
  const address = server.address();
  expectedOrigin = `http://${LOOPBACK_HOST}:${address.port}`;
  console.log(`Interface local ativa somente em ${expectedOrigin}`);
  if (openBrowser) openDefaultBrowser(expectedOrigin);
  return { origin: expectedOrigin, server };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  startLocalInterface().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
