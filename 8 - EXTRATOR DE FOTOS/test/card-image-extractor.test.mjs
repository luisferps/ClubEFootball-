import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import {
  auditImageContent,
  assertCardId,
  cloudinarySettingsFromEnv,
  deliveryUrl,
  idsFromCsv,
  mapWithConcurrency,
  parseCsv,
  parsePng,
  run,
  sourceUrl,
  supabaseFailureMessage,
  uniqueCardIds
} from "../card-image-extractor.mjs";
import {
  buildChildEnvironment,
  LOOPBACK_HOST,
  runtimeCapabilities,
  startLocalInterface,
  validateCredentialPayload
} from "../interface-local-server.mjs";
import {
  applyManifestDocument,
  DATABASE_TARGET,
  PHOTO_MANIFEST_FORMAT,
  sealManifest,
  validateManifestDocument
} from "../photo-manifest.mjs";

test("interface local simples liga tres campos password ao fluxo direto sem armazenamento no navegador", async () => {
  assert.equal(LOOPBACK_HOST, "127.0.0.1");
  const credentials = validateCredentialPayload({
    cloudinaryApiKey: "key-ficticia",
    cloudinaryApiSecret: "secret-ficticia",
    supabaseDbUrl: "postgresql://usuario:senha@db.example.test:5432/postgres"
  }, "direct", {});
  const childEnvironment = buildChildEnvironment(credentials, {});
  assert.equal(childEnvironment.CLOUDINARY_API_KEY, "key-ficticia");
  assert.equal(childEnvironment.CLOUDINARY_API_SECRET, "secret-ficticia");
  assert.equal(childEnvironment.SUPABASE_DB_URL, "postgresql://usuario:senha@db.example.test:5432/postgres");
  assert.deepEqual(runtimeCapabilities({
    CLOUDINARY_API_KEY: "key-ficticia",
    CLOUDINARY_API_SECRET: "secret-ficticia",
    SUPABASE_DB_URL: "postgresql://ficticio"
  }), {
    cloudinaryConfigured: true,
    directPostgresConfigured: true,
    dataApiConfigured: false,
    databaseConfigured: true,
    preferredDatabaseMethod: "direct_postgres_transaction"
  });

  const html = await readFile(new URL("../interface-local.html", import.meta.url), "utf8");
  const browserCode = await readFile(new URL("../interface-local.js", import.meta.url), "utf8");
  assert.equal((html.match(/type="password"/g) ?? []).length, 3);
  assert.match(browserCode, /cloudinaryApiKey/);
  assert.match(browserCode, /supabaseDbUrl/);
  assert.doesNotMatch(browserCode, /localStorage|sessionStorage|document\.cookie/);
  assert.match(html, /id="start-button"[^>]*>INICIAR</);
  assert.match(browserCode, /\/api\/start-direct/);
  assert.doesNotMatch(html, /amostra|APPLY MANIFEST|confirm-batch|manifest-file/i);
  assert.throws(() => validateCredentialPayload({
    cloudinaryApiKey: "key-ficticia",
    cloudinaryApiSecret: "secret-ficticia"
  }, "direct", {}), /SUPABASE_DB_URL/);
  assert.throws(() => validateCredentialPayload({ supabaseDbUrl: "https://nao-e-postgres.test" }, "apply", {}), /PostgreSQL/);
  assert.throws(() => validateCredentialPayload({}, "discover", {}), /SUPABASE_DB_URL/);
});

test("servidor HTML escuta somente no loopback e exige sessão local", async () => {
  const { origin, server } = await startLocalInterface({ openBrowser: false });
  try {
    assert.equal(server.address().address, "127.0.0.1");
    const pageResponse = await fetch(origin);
    assert.equal(pageResponse.status, 200);
    assert.match(pageResponse.headers.get("content-security-policy"), /default-src 'self'/);
    const html = await pageResponse.text();
    const token = html.match(/name="local-session-token" content="([a-f0-9]+)"/)?.[1];
    assert.ok(token);

    const rejected = await fetch(`${origin}/api/shutdown`, { method: "POST", headers: { Origin: origin } });
    assert.equal(rejected.status, 403);

    const statusResponse = await fetch(`${origin}/api/status`, { headers: { "X-Local-Session": token } });
    assert.equal(statusResponse.status, 200);
    assert.equal((await statusResponse.json()).samplePassed, false);

    const batchBeforeSample = await fetch(`${origin}/api/run-batch`, {
      method: "POST",
      headers: { Origin: origin, "Content-Type": "application/json", "X-Local-Session": token },
      body: JSON.stringify({
        cloudinaryApiKey: "ficticia",
        cloudinaryApiSecret: "ficticia",
        supabaseServiceRole: "ficticia",
        confirmBatch: true
      })
    });
    assert.equal(batchBeforeSample.status, 412);

    const accepted = await fetch(`${origin}/api/shutdown`, {
      method: "POST",
      headers: { Origin: origin, "X-Local-Session": token }
    });
    assert.equal(accepted.status, 200);
  } finally {
    if (server.listening) await new Promise((resolve) => server.close(resolve));
  }
});

test("aceita credenciais Cloudinary separadas e preserva CLOUDINARY_URL antiga", () => {
  assert.deepEqual(cloudinarySettingsFromEnv({
    CLOUDINARY_API_KEY: "api-key",
    CLOUDINARY_API_SECRET: "api-secret",
    CLOUDINARY_CLOUD_NAME: "demsusjwf"
  }), {
    apiKey: "api-key",
    apiSecret: "api-secret",
    cloudName: "demsusjwf"
  });

  assert.deepEqual(cloudinarySettingsFromEnv({
    CLOUDINARY_URL: "cloudinary://api-key:api-secret@demsusjwf"
  }), {
    apiKey: "api-key",
    apiSecret: "api-secret",
    cloudName: "demsusjwf"
  });
});

test("card_id permanece string numerica", () => {
  assert.equal(assertCardId("17592722922839"), "17592722922839");
  assert.throws(() => assertCardId("Lionel Messi"), /card_id invalido/);
});

test("URLs sao determinadas somente pelo card_id", () => {
  assert.equal(sourceUrl("17592722922839"), "https://efimg.com/efootballhub22/images/player_cards/17592722922839_l.png");
  assert.equal(deliveryUrl("demsusjwf", "17592722922839"), "https://res.cloudinary.com/demsusjwf/image/upload/17592722922839.png");
});

test("CSV RFC4180 preserva campos com virgula e aspas", () => {
  const rows = parseCsv('id,nome,meta\r\n"101334","Nome, Um","{\"\"a\"\":1}"\r\n');
  assert.deepEqual(rows, [["id", "nome", "meta"], ["101334", "Nome, Um", '{"a":1}']]);
  assert.deepEqual(idsFromCsv('card_id,nome\n17592722922839,Messi\n'), ["17592722922839"]);
});

test("deduplicacao usa somente card_id", () => {
  assert.deepEqual(uniqueCardIds(["2", "1", "2", "01", "1"]), ["2", "1", "01"]);
});

test("valida assinatura e dimensoes PNG", () => {
  const png = Buffer.alloc(24);
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).copy(png, 0);
  png.write("IHDR", 12, "ascii");
  png.writeUInt32BE(240, 16);
  png.writeUInt32BE(340, 20);
  assert.deepEqual(parsePng(png), { width: 240, height: 340 });
  assert.throws(() => parsePng(Buffer.from("not png")), /nao e PNG/);
});

test("auditoria de conteudo nao bloqueia arquivo nao PNG", () => {
  const audit = auditImageContent(Buffer.from("conteudo retornado pela fonte"));
  assert.equal(audit.contentAudit, "nao_png");
  assert.equal(audit.width, null);
  assert.equal(audit.height, null);
  assert.equal(audit.byteSize, 29);
  assert.match(audit.sha256, /^[0-9a-f]{64}$/);
});

test("HTTP 406 do schema Supabase produz diagnostico exato sem credencial", () => {
  const message = supabaseFailureMessage("Supabase read", 406, {
    code: "PGRST106",
    message: "Invalid schema: clube_novo",
    hint: "Only public is exposed"
  });
  assert.match(message, /PGRST106/);
  assert.match(message, /clube_novo/);
  assert.doesNotMatch(message, /service_role|apikey|Bearer/);
});

test("descoberta Data API confirma campo e cria fila somente com cards NULL", async () => {
  const temp = await mkdtemp(join(tmpdir(), "cards-discovery-"));
  const originalFetch = globalThis.fetch;
  const previousUrl = process.env.SUPABASE_URL;
  const previousSecret = process.env.SUPABASE_SECRET_KEY;
  const calls = [];
  process.env.SUPABASE_URL = "https://project-ref.supabase.co";
  process.env.SUPABASE_SECRET_KEY = "sb_secret_ficticia";
  globalThis.fetch = async (url, options = {}) => {
    const requestUrl = String(url);
    const headers = options.headers ?? {};
    const exactCount = headers.Prefer === "count=exact";
    const onlyMissing = requestUrl.includes("foto_url_cloudinary=is.null");
    calls.push({ url: requestUrl, method: options.method ?? "GET", exactCount });
    if (exactCount && !onlyMissing) {
      return new Response(JSON.stringify([{ card_id: "10001" }]), { status: 200, headers: { "Content-Type": "application/json", "Content-Range": "0-0/3" } });
    }
    if (exactCount && onlyMissing) {
      return new Response(JSON.stringify([{ card_id: "10002" }]), { status: 200, headers: { "Content-Type": "application/json", "Content-Range": "0-0/2" } });
    }
    if (onlyMissing) {
      return new Response(JSON.stringify([
        { card_id: "10002", foto_url_cloudinary: null },
        { card_id: "10003", foto_url_cloudinary: null }
      ]), { status: 200, headers: { "Content-Type": "application/json" } });
    }
    throw new Error(`chamada inesperada: ${requestUrl}`);
  };
  try {
    const result = await run(["--discover-missing", "--database-method", "data-api", "--output", temp]);
    assert.equal(result.summary.column_verified, true);
    assert.equal(result.summary.total_cards, 3);
    assert.equal(result.summary.already_linked, 1);
    assert.equal(result.summary.missing_cards, 2);
    assert.equal(result.summary.database_modified, false);
    assert.equal(await readFile(result.summary.snapshot_file, "utf8"), "10002\n10003\n");
    assert.ok(calls.every((call) => call.method === "GET"));
  } finally {
    globalThis.fetch = originalFetch;
    if (previousUrl == null) delete process.env.SUPABASE_URL;
    else process.env.SUPABASE_URL = previousUrl;
    if (previousSecret == null) delete process.env.SUPABASE_SECRET_KEY;
    else process.env.SUPABASE_SECRET_KEY = previousSecret;
    await rm(temp, { recursive: true, force: true });
  }
});

function sampleManifest(items) {
  return sealManifest({
    format: PHOTO_MANIFEST_FORMAT,
    manifest_id: "test-run",
    generated_at_utc: "2026-08-30T00:00:00.000Z",
    identity_key: "card_id",
    cloud_name: "demsusjwf",
    database_target: DATABASE_TARGET,
    overwrite_allowed: false,
    automatic_apply: false,
    input: { kind: "test", path: null, sha256: null, total_unique: items.length, offset: 0, selected: items.length },
    safeguards: { concurrency: 1, delay_ms_between_card_starts: 250, retries: 3, timeout_ms: 30000 },
    items
  });
}

function eligibleManifestItem(cardId = "17592722922839") {
  return {
    card_id: cardId,
    candidate_url: `https://res.cloudinary.com/demsusjwf/image/upload/${cardId}.png`,
    provenance: {
      identity_key: "card_id",
      source: "efootballhub",
      source_url: `https://efimg.com/efootballhub22/images/player_cards/${cardId}_l.png`,
      cloudinary_public_id: cardId,
      cloudinary_asset_folder: "clubefutebol/cards/efootballhub"
    },
    overwrite_attempted: false,
    outcome: "cloudinary_existing",
    failure_or_skip_state: null,
    cloudinary_verification: { precheck_status: 200, final_status: 200, checked_at_utc: "2026-08-30T00:00:00.000Z", content_type: "image/png", content_length: 100 }
  };
}

test("manifesto selado falha fechado se for adulterado", () => {
  const manifest = sampleManifest([eligibleManifestItem()]);
  assert.equal(validateManifestDocument(manifest).items.length, 1);
  manifest.items[0].candidate_url = "https://example.invalid/outro.png";
  assert.throws(() => validateManifestDocument(manifest), /SHA-256|candidate_url/);
});

test("APPLY validado atualiza somente NULL e faz readback independente com mocks", async () => {
  const item = eligibleManifestItem();
  const manifest = sampleManifest([item]);
  let applyCalls = 0;
  let readbackCalls = 0;
  const adapter = {
    method: "mock_transaction",
    async applyConditional(items) {
      applyCalls += 1;
      assert.equal(items.length, 1);
      return new Map([[item.card_id, { status: "updated", previous_url: null }]]);
    },
    async readMany(cardIds) {
      readbackCalls += 1;
      assert.deepEqual(cardIds, [item.card_id]);
      return new Map([[item.card_id, { card_id: item.card_id, foto_url_cloudinary: item.candidate_url }]]);
    }
  };
  const result = await applyManifestDocument(manifest, {
    probeCloudinary: async () => ({ status: 200, url: item.candidate_url }),
    databaseAdapter: adapter
  });
  assert.equal(result.counts.updated, 1);
  assert.equal(result.events[0].database_readback_ok, true);
  assert.equal(applyCalls, 1);
  assert.equal(readbackCalls, 1);
});

test("pool processa 100 itens com concorrencia limitada", async () => {
  const items = Array.from({ length: 100 }, (_, index) => index);
  let active = 0;
  let peak = 0;
  const result = await mapWithConcurrency(items, 4, async (value) => {
    active += 1;
    peak = Math.max(peak, active);
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 1));
    active -= 1;
    return value * 2;
  });
  assert.equal(result.length, 100);
  assert.equal(peak, 4);
  assert.equal(result[99], 198);
});

test("dry-run paralelo cria manifesto duravel e nunca chama upload ou banco", async () => {
  const temp = await mkdtemp(join(tmpdir(), "cards-dry-run-"));
  const input = join(temp, "cards.txt");
  await writeFile(input, "10001\n10002\n10003\n", "utf8");
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url: String(url), method: options.method ?? "GET" });
    return new Response(null, { status: 404 });
  };
  try {
    const result = await run(["--input", input, "--limit", "3", "--concurrency", "3", "--delay-ms", "250", "--output", temp]);
    assert.equal(result.summary.mode, "dry_run");
    assert.equal(result.summary.selected, 3);
    assert.equal(result.summary.counts.cloudinary_missing_dry_run, 3);
    assert.equal(result.summary.database_modified, false);
    const manifest = JSON.parse(await readFile(result.summary.manifest_file, "utf8"));
    assert.equal(validateManifestDocument(manifest).items.length, 3);
    assert.ok(manifest.items.every((item) => item.failure_or_skip_state === "upload_not_authorized_in_dry_run"));
    assert.equal(calls.length, 3);
    assert.ok(calls.every((call) => call.method === "HEAD" && call.url.startsWith("https://res.cloudinary.com/")));
  } finally {
    globalThis.fetch = originalFetch;
    await rm(temp, { recursive: true, force: true });
  }
});

test("upload mockado cria manifesto elegivel sem qualquer chamada de banco", async () => {
  const temp = await mkdtemp(join(tmpdir(), "cards-upload-mock-"));
  const originalFetch = globalThis.fetch;
  const previousKey = process.env.CLOUDINARY_API_KEY;
  const previousSecret = process.env.CLOUDINARY_API_SECRET;
  const calls = [];
  let readbackCalls = 0;
  const png = Buffer.alloc(24);
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).copy(png, 0);
  png.write("IHDR", 12, "ascii");
  png.writeUInt32BE(240, 16);
  png.writeUInt32BE(340, 20);
  process.env.CLOUDINARY_API_KEY = "cloud-key-ficticia";
  process.env.CLOUDINARY_API_SECRET = "cloud-secret-ficticio";
  globalThis.fetch = async (url, options = {}) => {
    const call = { url: String(url), method: options.method ?? "GET" };
    calls.push(call);
    if (call.method === "HEAD" && !call.url.includes("readback=")) return new Response(null, { status: 404 });
    if (call.url.startsWith("https://efimg.com/")) return new Response(png, { status: 200, headers: { "Content-Type": "image/png" } });
    if (call.method === "POST" && call.url.includes("api.cloudinary.com")) {
      return new Response(JSON.stringify({
        public_id: "17592722922839",
        asset_folder: "clubefutebol/cards/efootballhub",
        asset_id: "asset-ficticio",
        version: 1,
        secure_url: "https://res.cloudinary.com/demsusjwf/image/upload/17592722922839.png"
      }), { status: 200, headers: { "Content-Type": "application/json" } });
    }
    if (call.method === "HEAD" && call.url.includes("readback=")) {
      readbackCalls += 1;
      return new Response(null, {
        status: readbackCalls === 1 ? 404 : 200,
        headers: readbackCalls === 1 ? {} : { "Content-Type": "image/png", "Content-Length": "24" }
      });
    }
    throw new Error(`chamada inesperada no mock: ${call.method} ${call.url}`);
  };
  try {
    const result = await run(["--card-id", "17592722922839", "--limit", "1", "--delay-ms", "250", "--upload", "--output", temp]);
    assert.equal(result.summary.counts.cloudinary_uploaded, 1);
    assert.equal(result.summary.database_modified, false);
    const manifest = validateManifestDocument(JSON.parse(await readFile(result.summary.manifest_file, "utf8")));
    assert.equal(manifest.items[0].outcome, "cloudinary_uploaded");
    assert.equal(manifest.items[0].cloudinary_verification.final_status, 200);
    assert.equal(readbackCalls, 2);
    assert.ok(calls.every((call) => !call.url.includes("supabase")));
  } finally {
    globalThis.fetch = originalFetch;
    if (previousKey == null) delete process.env.CLOUDINARY_API_KEY;
    else process.env.CLOUDINARY_API_KEY = previousKey;
    if (previousSecret == null) delete process.env.CLOUDINARY_API_SECRET;
    else process.env.CLOUDINARY_API_SECRET = previousSecret;
    await rm(temp, { recursive: true, force: true });
  }
});

test("lote verifica todo o Cloudinary antes da primeira busca no EFHub", async () => {
  const temp = await mkdtemp(join(tmpdir(), "cards-cloudinary-first-"));
  const input = join(temp, "cards.txt");
  await writeFile(input, "20001\n20002\n20003\n", "utf8");
  const originalFetch = globalThis.fetch;
  const previousKey = process.env.CLOUDINARY_API_KEY;
  const previousSecret = process.env.CLOUDINARY_API_SECRET;
  const calls = [];
  const png = Buffer.alloc(24);
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).copy(png, 0);
  png.write("IHDR", 12, "ascii");
  png.writeUInt32BE(240, 16);
  png.writeUInt32BE(340, 20);
  process.env.CLOUDINARY_API_KEY = "cloud-key-ficticia";
  process.env.CLOUDINARY_API_SECRET = "cloud-secret-ficticio";
  globalThis.fetch = async (url, options = {}) => {
    const requestUrl = String(url);
    const method = options.method ?? "GET";
    calls.push({ url: requestUrl, method });
    if (method === "HEAD" && !requestUrl.includes("readback=")) {
      return new Response(null, { status: requestUrl.includes("20002.png") ? 200 : 404, headers: { "Content-Type": "image/png" } });
    }
    if (requestUrl.startsWith("https://efimg.com/")) return new Response(png, { status: 200, headers: { "Content-Type": "image/png" } });
    if (method === "POST" && requestUrl.includes("api.cloudinary.com")) {
      const cardId = String(options.body.get("public_id"));
      return new Response(JSON.stringify({
        public_id: cardId,
        asset_folder: "clubefutebol/cards/efootballhub",
        asset_id: `asset-${cardId}`,
        version: 1,
        secure_url: `https://res.cloudinary.com/demsusjwf/image/upload/${cardId}.png`
      }), { status: 200, headers: { "Content-Type": "application/json" } });
    }
    if (method === "HEAD" && requestUrl.includes("readback=")) return new Response(null, { status: 200, headers: { "Content-Type": "image/png" } });
    throw new Error(`chamada inesperada no mock: ${method} ${requestUrl}`);
  };
  try {
    const result = await run(["--input", input, "--limit", "3", "--concurrency", "3", "--delay-ms", "250", "--upload", "--output", temp]);
    assert.equal(result.summary.counts.cloudinary_existing, 1);
    assert.equal(result.summary.counts.cloudinary_uploaded, 2);
    const precheckIndexes = calls
      .map((call, index) => ({ ...call, index }))
      .filter((call) => call.method === "HEAD" && !call.url.includes("readback="))
      .map((call) => call.index);
    const firstEfHubIndex = calls.findIndex((call) => call.url.startsWith("https://efimg.com/"));
    assert.equal(precheckIndexes.length, 3);
    assert.ok(Math.max(...precheckIndexes) < firstEfHubIndex);
    assert.ok(calls.every((call) => !call.url.includes("supabase")));
  } finally {
    globalThis.fetch = originalFetch;
    if (previousKey == null) delete process.env.CLOUDINARY_API_KEY;
    else process.env.CLOUDINARY_API_KEY = previousKey;
    if (previousSecret == null) delete process.env.CLOUDINARY_API_SECRET;
    else process.env.CLOUDINARY_API_SECRET = previousSecret;
    await rm(temp, { recursive: true, force: true });
  }
});
