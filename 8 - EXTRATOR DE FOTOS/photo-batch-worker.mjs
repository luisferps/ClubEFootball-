#!/usr/bin/env node

import { spawn } from "node:child_process";
import { appendFile, mkdir, open, readFile, unlink, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const TOOL_ROOT = dirname(fileURLToPath(import.meta.url));
const OUTPUT_ROOT = join(TOOL_ROOT, "output");
const OPERATOR_ROOT = join(OUTPUT_ROOT, "operador");
const CONTROL_ROOT = join(OPERATOR_ROOT, "controle");
const STATE_PATH = join(OPERATOR_ROOT, "estado.json");
const LOCK_PATH = join(OPERATOR_ROOT, "execucao.lock.json");
const CREDENTIALS_PATH = join(OUTPUT_ROOT, "state", "credentials.windows-dpapi.json");
const EXTRACTOR_PATH = join(TOOL_ROOT, "card-image-extractor.mjs");
const BATCH_SIZE = 100;
const CONCURRENCY = 4;
const DELAY_MS = 500;
const CLOUDINARY_CLOUD_NAME = "demsusjwf";
const UPLOAD_PRESET = "clubefutebol_cards_no_overwrite";
const PAUSE_PATH = join(CONTROL_ROOT, "pausar.solicitado.json");
const STOP_PATH = join(CONTROL_ROOT, "parar.solicitado.json");

const sleep = (milliseconds) => new Promise((resolvePromise) => setTimeout(resolvePromise, milliseconds));

function parseArguments(argv) {
  const index = argv.indexOf("--run-id");
  const runId = index >= 0 ? argv[index + 1] : null;
  if (!runId || !/^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z$/.test(runId)) throw new Error("Identificador de execução inválido.");
  return { runId };
}

function sanitize(text) {
  return String(text ?? "")
    .replace(/postgres(?:ql)?:\/\/\S+/gi, "[SUPABASE_DATABASE_URL_OCULTA]")
    .replace(/cloudinary:\/\/\S+/gi, "[CLOUDINARY_URL_OCULTA]")
    .slice(0, 4000);
}

function failureCount(counts = {}) {
  return Number(counts.failed ?? 0)
    + Number(counts.failed_setup ?? 0)
    + Number(counts.cloudinary_reverification_failed ?? 0)
    + Number(counts.manifest_item_not_eligible ?? 0)
    + Number(counts.missing_card ?? 0);
}

export function validateApplySummary(summary) {
  if (!summary || summary.format !== "clubefutebol-photo-manifest-apply-v1") throw new Error("O APPLY não produziu um resumo reconhecido.");
  if (summary.conditional_null_only !== true) throw new Error("O APPLY não confirmou atualização somente em campo NULL.");
  if (summary.conflicts_preserved !== true) throw new Error("O APPLY não confirmou preservação de conflitos.");
  if (summary.independently_read_back !== true) throw new Error("O APPLY não confirmou a releitura independente.");
  if (failureCount(summary.counts) > 0) throw new Error("O APPLY terminou com falha ou item não verificável.");
  const conflicts = Number(summary.counts?.conflict_preserved ?? summary.counts?.conflict ?? 0);
  if (conflicts !== 0) throw new Error(`${conflicts} conflito(s) foram preservados; a execução parou para conferência.`);
  return {
    updated: Number(summary.counts?.updated ?? 0),
    alreadyCurrent: Number(summary.counts?.already_applied ?? 0),
    conflicts
  };
}

async function pathExists(path) {
  try {
    await readFile(path);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw error;
  }
}

async function dpapiUnprotect(ciphertext) {
  if (process.platform !== "win32") throw new Error("O cofre local exige Windows.");
  const script = "Add-Type -AssemblyName System.Security;$cipher=[Console]::In.ReadToEnd();$sealed=$null;$bytes=$null;try{$sealed=[Convert]::FromBase64String($cipher);$bytes=[Security.Cryptography.ProtectedData]::Unprotect($sealed,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser);[Console]::Out.Write([Text.Encoding]::UTF8.GetString($bytes))}finally{if($sealed){[Array]::Clear($sealed,0,$sealed.Length)};if($bytes){[Array]::Clear($bytes,0,$bytes.Length)};$cipher=$null}";
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
      if (code === 0 && stdout.trim()) resolvePromise(stdout);
      else rejectPromise(new Error("O cofre local não pôde ser aberto nesta conta do Windows."));
      stdout = "";
      stderr = "";
    });
    child.stdin.end(ciphertext, "utf8");
  });
}

function validateCredentials(value) {
  const credentials = {
    cloudinaryApiKey: String(value?.cloudinaryApiKey ?? "").trim(),
    cloudinaryApiSecret: String(value?.cloudinaryApiSecret ?? "").trim(),
    supabaseDbUrl: String(value?.supabaseDbUrl ?? "").trim()
  };
  for (const secret of Object.values(credentials)) {
    if (!secret || secret.length > 8192 || /[\r\n\0]/.test(secret)) throw new Error("O cofre local contém credencial ausente ou inválida.");
  }
  let databaseUrl;
  try { databaseUrl = new URL(credentials.supabaseDbUrl); } catch { throw new Error("A Supabase Database URL salva é inválida."); }
  if (!new Set(["postgres:", "postgresql:"]).has(databaseUrl.protocol) || !databaseUrl.hostname) throw new Error("A Supabase Database URL precisa ser uma conexão PostgreSQL.");
  if (databaseUrl.port === "6543") throw new Error("A URL usa Transaction pooler 6543. Configure Session pooler na porta 5432.");
  return credentials;
}

async function loadCredentials() {
  let document = null;
  let plaintext = "";
  let parsed = null;
  try {
    document = JSON.parse(await readFile(CREDENTIALS_PATH, "utf8"));
    if (document?.format !== "clubefutebol-photo-credentials-windows-dpapi-v2" || !/^[A-Za-z0-9+/=]+$/.test(String(document.ciphertext ?? ""))) throw new Error("O arquivo do cofre local é inválido.");
    plaintext = await dpapiUnprotect(document.ciphertext);
    parsed = JSON.parse(plaintext);
    return validateCredentials(parsed);
  } finally {
    plaintext = "";
    if (document && typeof document === "object") document.ciphertext = "";
    if (parsed && typeof parsed === "object") for (const key of Object.keys(parsed)) parsed[key] = "";
  }
}

function childEnvironment(credentials) {
  return {
    ...process.env,
    CLOUDINARY_API_KEY: credentials.cloudinaryApiKey,
    CLOUDINARY_API_SECRET: credentials.cloudinaryApiSecret,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_UPLOAD_PRESET: UPLOAD_PRESET,
    SUPABASE_DB_URL: credentials.supabaseDbUrl
  };
}

async function acquireLock(runId) {
  await mkdir(OPERATOR_ROOT, { recursive: true });
  const payload = `${JSON.stringify({ run_id: runId, pid: process.pid, created_at_utc: new Date().toISOString() }, null, 2)}\n`;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const handle = await open(LOCK_PATH, "wx");
      try { await handle.writeFile(payload, "utf8"); } finally { await handle.close(); }
      return;
    } catch (error) {
      if (error?.code !== "EEXIST") throw error;
      let stale = true;
      try {
        const prior = JSON.parse(await readFile(LOCK_PATH, "utf8"));
        if (Number.isInteger(prior?.pid)) {
          try { process.kill(prior.pid, 0); stale = false; } catch {}
        }
      } catch {}
      if (!stale) throw new Error("Já existe um Extrator de Fotos em execução.");
      await unlink(LOCK_PATH).catch(() => {});
    }
  }
  throw new Error("Não foi possível reservar a execução exclusiva.");
}

async function releaseLock(runId) {
  try {
    const lock = JSON.parse(await readFile(LOCK_PATH, "utf8"));
    if (lock?.run_id === runId && lock?.pid === process.pid) await unlink(LOCK_PATH);
  } catch {}
}

async function runWorker({ runId }) {
  const runDirectory = join(OPERATOR_ROOT, "runs", runId);
  const logPath = join(runDirectory, "execucao.log");
  const eventsPath = join(runDirectory, "eventos.jsonl");
  const summaryPath = join(runDirectory, "resumo.json");
  await mkdir(runDirectory, { recursive: true });
  await mkdir(CONTROL_ROOT, { recursive: true });
  await acquireLock(runId);

  let credentials = null;
  let environment = null;
  let currentState = {
    format: "clubefutebol-photo-operator-state-v1",
    run_id: runId,
    pid: process.pid,
    status: "starting",
    phase: "starting",
    queue_total: 0,
    queue_completed: 0,
    safe_batches: 0,
    updated: 0,
    already_current: 0,
    conflicts: 0,
    last_manifest_file: null,
    last_prepare_run: null,
    last_apply_run: null,
    final_missing: null,
    log_file: logPath,
    events_file: eventsPath,
    summary_file: summaryPath,
    started_at_utc: new Date().toISOString(),
    updated_at_utc: new Date().toISOString()
  };
  let stateWriteQueue = Promise.resolve();

  const writeState = (patch = {}) => {
    currentState = { ...currentState, ...patch, updated_at_utc: new Date().toISOString() };
    const snapshot = `${JSON.stringify(currentState, null, 2)}\n`;
    stateWriteQueue = stateWriteQueue.then(() => writeFile(STATE_PATH, snapshot, "utf8"));
    return stateWriteQueue;
  };
  const log = async (message) => appendFile(logPath, `[${new Date().toISOString()}] ${sanitize(message)}\n`, "utf8");
  const event = async (status, details = {}) => {
    const safeDetails = { ...details };
    if (safeDetails.error) safeDetails.error = sanitize(safeDetails.error);
    await appendFile(eventsPath, `${JSON.stringify({ run_id: runId, status, at_utc: new Date().toISOString(), ...safeDetails })}\n`, "utf8");
  };

  const execute = async (mode, argumentsList) => {
    await log(`Iniciando etapa ${mode}.`);
    return new Promise((resolvePromise, rejectPromise) => {
      const child = spawn(process.execPath, [EXTRACTOR_PATH, ...argumentsList], {
        cwd: TOOL_ROOT,
        env: environment,
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true
      });
      let pending = "";
      let summary = null;
      let stderr = "";
      child.stdout.on("data", (chunk) => {
        pending += chunk.toString("utf8");
        const lines = pending.split(/\r?\n/);
        pending = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.trim()) continue;
          void appendFile(logPath, `[extrator:${mode}] ${sanitize(line)}\n`, "utf8");
          if (!line.trim().startsWith("{")) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed?.format && parsed?.run_id) summary = parsed;
            if (Number.isInteger(parsed?.progress_completed)) void writeState({ current_card_progress: parsed.progress_completed, current_card_total: parsed.progress_total ?? null });
          } catch {}
        }
      });
      child.stderr.on("data", (chunk) => { if (stderr.length < 32000) stderr += chunk.toString("utf8"); });
      child.once("error", rejectPromise);
      child.once("close", async (code) => {
        if (pending.trim()) await appendFile(logPath, `[extrator:${mode}] ${sanitize(pending)}\n`, "utf8");
        if (stderr.trim()) await appendFile(logPath, `[extrator:${mode}:erro] ${sanitize(stderr)}\n`, "utf8");
        if (code !== 0 || !summary) {
          rejectPromise(new Error(`A etapa ${mode} terminou sem resumo válido (código ${code}).`));
          return;
        }
        resolvePromise(summary);
      });
    });
  };

  const controlCheckpoint = async (position) => {
    if (await pathExists(STOP_PATH)) {
      await writeState({ status: "stopped_safe", phase: "stopped_safe", control_position: position });
      await event("stopped_safe", { position });
      await log(`Parada segura atendida em ${position}.`);
      return "stop";
    }
    if (!(await pathExists(PAUSE_PATH))) return "continue";
    await writeState({ status: "paused", phase: "paused", control_position: position });
    await event("paused", { position });
    await log(`Pausa atendida em ${position}.`);
    while (await pathExists(PAUSE_PATH)) {
      if (await pathExists(STOP_PATH)) {
        await writeState({ status: "stopped_safe", phase: "stopped_safe", control_position: position });
        await event("stopped_safe", { position });
        await log(`Parada segura atendida durante a pausa em ${position}.`);
        return "stop";
      }
      await sleep(1000);
    }
    await writeState({ status: "running", phase: position, control_position: null });
    await event("resumed", { position });
    await log(`Execução retomada em ${position}.`);
    return "continue";
  };

  let finalStatus = "failed";
  let finalMessage = "A execução não foi concluída.";
  try {
    await writeState();
    await event("worker_started", { pid: process.pid });
    await log("Executor operacional iniciado. Credenciais permanecem no cofre DPAPI desta conta do Windows.");
    credentials = await loadCredentials();
    environment = childEnvironment(credentials);
    await writeState({ status: "running", phase: "discovering" });

    let cycle = 0;
    for (;;) {
      if (await controlCheckpoint("before_discovery") === "stop") {
        finalStatus = "stopped_safe";
        finalMessage = "Parada segura concluída antes de uma nova consulta.";
        break;
      }
      cycle += 1;
      await writeState({ status: "running", phase: "discovering", discovery_cycle: cycle, current_card_progress: null, current_card_total: null });
      const discovery = await execute("discover", ["--discover-missing", "--database-method", "postgres"]);
      if (failureCount(discovery.counts) > 0 || discovery.column_verified !== true || !discovery.snapshot_file) throw new Error("A consulta ao Supabase não produziu uma fila válida.");
      const total = Number(discovery.missing_cards ?? discovery.selected ?? 0);
      if (!Number.isInteger(total) || total < 0) throw new Error("A fila retornou uma contagem inválida.");
      await event("queue_discovered", { cycle, total, snapshot_sha256: discovery.snapshot_sha256 ?? null });
      await writeState({
        phase: total === 0 ? "final_readback_complete" : "queue_ready",
        queue_total: total,
        queue_completed: 0,
        final_missing: total,
        queue_snapshot_file: discovery.snapshot_file,
        queue_snapshot_sha256: discovery.snapshot_sha256 ?? null,
        discovery_run: discovery.run_id
      });
      if (total === 0) {
        finalStatus = "completed";
        finalMessage = "Fila concluída e releitura final confirmou zero cartas elegíveis pendentes.";
        break;
      }

      let offset = 0;
      while (offset < total) {
        if (await controlCheckpoint("before_batch") === "stop") {
          finalStatus = "stopped_safe";
          finalMessage = "Parada segura concluída antes de iniciar um novo lote.";
          break;
        }
        const batchNumber = currentState.safe_batches + 1;
        await writeState({ status: "running", phase: "preparing_batch", queue_completed: offset, current_batch: batchNumber });
        await event("batch_started", { batch: batchNumber, offset, limit: BATCH_SIZE });
        const prepared = await execute("prepare", [
          "--input", discovery.snapshot_file,
          "--input-kind", "database_null_snapshot",
          "--offset", String(offset),
          "--limit", String(BATCH_SIZE),
          "--concurrency", String(CONCURRENCY),
          "--delay-ms", String(DELAY_MS),
          "--upload"
        ]);
        const nextOffset = Number(prepared.next_offset);
        if (failureCount(prepared.counts) > 0 || !prepared.manifest_file || !Number.isInteger(nextOffset) || nextOffset <= offset || nextOffset > total) throw new Error(`O lote ${batchNumber} não produziu um manifesto integral; nenhum APPLY desse lote foi executado.`);
        await writeState({
          phase: "manifest_ready",
          last_manifest_file: prepared.manifest_file,
          last_prepare_run: prepared.run_id,
          pending_apply_batch: batchNumber,
          current_card_progress: null,
          current_card_total: null
        });
        await event("manifest_ready", { batch: batchNumber, manifest_file: prepared.manifest_file, manifest_sha256: prepared.manifest_sha256 ?? null });

        if (await controlCheckpoint("before_apply") === "stop") {
          finalStatus = "stopped_safe";
          finalMessage = "Parada segura concluída antes do APPLY; o manifesto ficou preservado e o banco desse lote não foi alterado.";
          break;
        }
        await writeState({ status: "running", phase: "applying_batch" });
        const applied = await execute("apply", ["--apply-manifest", prepared.manifest_file, "--database-method", "postgres"]);
        let appliedCounts;
        try {
          appliedCounts = validateApplySummary(applied);
        } catch (error) {
          await writeState({
            updated: currentState.updated + Number(applied.counts?.updated ?? 0),
            already_current: currentState.already_current + Number(applied.counts?.already_applied ?? 0),
            conflicts: currentState.conflicts + Number(applied.counts?.conflict_preserved ?? applied.counts?.conflict ?? 0),
            last_apply_run: applied.run_id ?? null
          });
          throw error;
        }
        offset = nextOffset;
        await writeState({
          status: "running",
          phase: "batch_verified",
          queue_completed: offset,
          safe_batches: currentState.safe_batches + 1,
          updated: currentState.updated + appliedCounts.updated,
          already_current: currentState.already_current + appliedCounts.alreadyCurrent,
          conflicts: currentState.conflicts + appliedCounts.conflicts,
          last_apply_run: applied.run_id,
          pending_apply_batch: null,
          last_safe_batch: batchNumber
        });
        await event("batch_verified", {
          batch: batchNumber,
          queue_completed: offset,
          updated: appliedCounts.updated,
          already_current: appliedCounts.alreadyCurrent,
          conflicts: appliedCounts.conflicts,
          conditional_null_only: applied.conditional_null_only,
          independently_read_back: applied.independently_read_back
        });
        await log(`Lote seguro ${batchNumber} concluído: ${appliedCounts.updated} atualizado(s), ${appliedCounts.alreadyCurrent} já atual(is), 0 conflitos.`);
      }
      if (finalStatus === "stopped_safe") break;
      await writeState({ phase: "final_readback", final_missing: null });
      await event("queue_snapshot_completed", { cycle, total });
    }
  } catch (error) {
    finalStatus = "failed";
    finalMessage = sanitize(error?.message || "Falha operacional sem mensagem.");
    await writeState({ status: "failed", phase: "failed", error: finalMessage });
    await event("failed", { error: finalMessage });
    await log(`FALHA: ${finalMessage}`);
  } finally {
    if (credentials) for (const key of Object.keys(credentials)) credentials[key] = "";
    if (environment) {
      for (const name of ["CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET", "SUPABASE_DB_URL"]) {
        if (name in environment) environment[name] = "";
        delete environment[name];
      }
    }
    const completedAt = new Date().toISOString();
    if (finalStatus !== "failed") await writeState({ status: finalStatus, phase: finalStatus, message: finalMessage, completed_at_utc: completedAt });
    const summary = {
      format: "clubefutebol-photo-operator-run-v1",
      run_id: runId,
      status: finalStatus,
      message: finalMessage,
      database_target: "clube_novo.carta_jogo.foto_url_cloudinary",
      database_access_method: "direct_postgres_transaction",
      batch_size: BATCH_SIZE,
      safe_batches: currentState.safe_batches,
      updated: currentState.updated,
      already_current: currentState.already_current,
      conflicts: currentState.conflicts,
      conditional_null_only: true,
      conflicts_preserved: true,
      independently_read_back: currentState.safe_batches > 0 || currentState.final_missing === 0,
      final_missing: currentState.final_missing,
      last_manifest_file: currentState.last_manifest_file,
      last_prepare_run: currentState.last_prepare_run,
      last_apply_run: currentState.last_apply_run,
      log_file: logPath,
      events_file: eventsPath,
      started_at_utc: currentState.started_at_utc,
      completed_at_utc: completedAt
    };
    await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
    await log(`Executor encerrado com status ${finalStatus}.`);
    await releaseLock(runId);
  }
  if (finalStatus === "failed") process.exitCode = 1;
}

export async function main(argv = process.argv.slice(2)) {
  await runWorker(parseArguments(argv));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(sanitize(error?.stack || error?.message));
    process.exitCode = 1;
  });
}
