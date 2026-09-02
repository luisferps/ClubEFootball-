import { createHash } from "node:crypto";

export const PHOTO_MANIFEST_FORMAT = "clubefutebol-photo-manifest-v1";
export const APPLY_RUN_FORMAT = "clubefutebol-photo-manifest-apply-v1";
export const DATABASE_TARGET = "clube_novo.carta_jogo.foto_url_cloudinary";
const ELIGIBLE_OUTCOMES = new Set(["cloudinary_existing", "cloudinary_uploaded"]);

function assertCardId(value) {
  const cardId = String(value ?? "").trim();
  if (!/^\d+$/.test(cardId)) throw new Error(`manifesto contem card_id invalido: ${JSON.stringify(value)}`);
  return cardId;
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

export function manifestSha256(document) {
  const { integrity: _ignored, ...payload } = document ?? {};
  return createHash("sha256").update(canonicalJson(payload)).digest("hex");
}

export function sealManifest(document) {
  const sealed = { ...document };
  sealed.integrity = { algorithm: "sha256", canonicalization: "recursive-key-sort-v1", sha256: manifestSha256(sealed) };
  return sealed;
}

export function expectedCandidateUrl(cloudName, cardId) {
  return `https://res.cloudinary.com/${cloudName}/image/upload/${assertCardId(cardId)}.png`;
}

export function expectedSourceUrl(cardId) {
  return `https://efimg.com/efootballhub22/images/player_cards/${assertCardId(cardId)}_l.png`;
}

export function validateManifestDocument(document, { maxItems = 100 } = {}) {
  if (!document || typeof document !== "object" || Array.isArray(document)) throw new Error("manifesto precisa ser um objeto JSON");
  if (document.format !== PHOTO_MANIFEST_FORMAT) throw new Error(`formato de manifesto nao suportado: ${document.format ?? "ausente"}`);
  if (document.identity_key !== "card_id") throw new Error("manifesto nao declara card_id como identidade unica");
  if (document.database_target !== DATABASE_TARGET) throw new Error(`destino do manifesto deve ser exatamente ${DATABASE_TARGET}`);
  if (document.overwrite_allowed !== false) throw new Error("manifesto nao proibe sobrescrita");
  if (!/^[a-z0-9_-]+$/i.test(String(document.cloud_name ?? ""))) throw new Error("cloud_name invalido no manifesto");
  if (!Array.isArray(document.items) || document.items.length < 1 || document.items.length > maxItems) {
    throw new Error(`manifesto precisa conter entre 1 e ${maxItems} itens`);
  }
  if (document.integrity?.algorithm !== "sha256" || !/^[0-9a-f]{64}$/.test(String(document.integrity?.sha256 ?? ""))) {
    throw new Error("manifesto nao contem integridade SHA-256 valida");
  }
  const computedHash = manifestSha256(document);
  if (computedHash !== document.integrity.sha256) throw new Error("SHA-256 do manifesto divergiu; APPLY recusado");

  const seen = new Set();
  const items = document.items.map((item, index) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) throw new Error(`item ${index + 1} do manifesto e invalido`);
    const cardId = assertCardId(item.card_id);
    if (seen.has(cardId)) throw new Error(`manifesto contem card_id duplicado: ${cardId}`);
    seen.add(cardId);
    const candidateUrl = expectedCandidateUrl(document.cloud_name, cardId);
    if (item.candidate_url !== candidateUrl) throw new Error(`candidate_url divergente para card_id ${cardId}`);
    if (item.provenance?.identity_key !== "card_id" || item.provenance?.source !== "efootballhub") {
      throw new Error(`proveniencia incompleta para card_id ${cardId}`);
    }
    if (item.provenance?.source_url !== expectedSourceUrl(cardId)) throw new Error(`source_url divergente para card_id ${cardId}`);
    if (item.provenance?.cloudinary_public_id !== cardId) throw new Error(`public_id divergente para card_id ${cardId}`);
    if (typeof item.outcome !== "string" || !item.outcome) throw new Error(`outcome ausente para card_id ${cardId}`);
    if (!(item.failure_or_skip_state === null || typeof item.failure_or_skip_state === "string")) {
      throw new Error(`failure_or_skip_state invalido para card_id ${cardId}`);
    }
    if (item.overwrite_attempted !== false) throw new Error(`item ${cardId} nao comprova overwrite=false`);
    if (ELIGIBLE_OUTCOMES.has(item.outcome)) {
      if (item.cloudinary_verification?.final_status !== 200) throw new Error(`item elegivel ${cardId} nao tem verificacao Cloudinary HTTP 200`);
      if (item.failure_or_skip_state !== null) throw new Error(`item elegivel ${cardId} contem estado de falha/skip`);
    }
    return { ...item, card_id: cardId };
  });

  return { ...document, items };
}

export function eligibleManifestItems(document) {
  const validated = validateManifestDocument(document);
  return validated.items.filter((item) => ELIGIBLE_OUTCOMES.has(item.outcome));
}

function makeBaseApplyEvent(item) {
  return {
    card_id: item.card_id,
    candidate_url: item.candidate_url,
    database_target: DATABASE_TARGET,
    manifest_outcome: item.outcome,
    overwritten: false
  };
}

export async function applyManifestDocument(document, { probeCloudinary, databaseAdapter }) {
  if (typeof probeCloudinary !== "function") throw new Error("adaptador de verificacao Cloudinary ausente");
  if (!databaseAdapter || typeof databaseAdapter.applyConditional !== "function" || typeof databaseAdapter.readMany !== "function") {
    throw new Error("adaptador de banco invalido");
  }
  const manifest = validateManifestDocument(document);
  const eventsByCard = new Map();
  const verified = [];

  for (const item of manifest.items) {
    const base = makeBaseApplyEvent(item);
    if (!ELIGIBLE_OUTCOMES.has(item.outcome)) {
      eventsByCard.set(item.card_id, { ...base, status: "manifest_item_not_eligible", failure_or_skip_state: item.failure_or_skip_state ?? item.outcome });
      continue;
    }
    try {
      const probe = await probeCloudinary(item.card_id, true);
      if (probe.status !== 200 || probe.url !== item.candidate_url) {
        eventsByCard.set(item.card_id, {
          ...base,
          status: "cloudinary_reverification_failed",
          failure_or_skip_state: `cloudinary_http_${probe.status}`,
          cloudinary_readback_status: probe.status
        });
        continue;
      }
      verified.push(item);
    } catch (error) {
      eventsByCard.set(item.card_id, {
        ...base,
        status: "cloudinary_reverification_failed",
        failure_or_skip_state: "cloudinary_request_failed",
        error: error.message
      });
    }
  }

  if (verified.length) {
    const decisions = await databaseAdapter.applyConditional(verified);
    if (!(decisions instanceof Map)) throw new Error("adaptador de banco nao retornou decisoes por card_id");
    const readback = await databaseAdapter.readMany(verified.map((item) => item.card_id));
    if (!(readback instanceof Map)) throw new Error("readback do banco nao retornou mapa por card_id");

    for (const item of verified) {
      const decision = decisions.get(item.card_id);
      if (!decision) throw new Error(`banco nao retornou decisao para card_id ${item.card_id}`);
      const row = readback.get(item.card_id);
      const actualUrl = row?.foto_url_cloudinary ?? null;
      let readbackOk = false;
      if (["updated", "already_applied"].includes(decision.status)) readbackOk = actualUrl === item.candidate_url;
      else if (decision.status === "conflict_preserved") readbackOk = Boolean(actualUrl) && actualUrl === decision.current_url && actualUrl !== item.candidate_url;
      else if (decision.status === "missing_card") readbackOk = !row;
      if (!readbackOk) throw new Error(`readback independente divergiu para card_id ${item.card_id}`);
      eventsByCard.set(item.card_id, {
        ...makeBaseApplyEvent(item),
        status: decision.status,
        database_access_method: databaseAdapter.method,
        database_previous_url: decision.previous_url ?? null,
        database_readback_url: actualUrl,
        database_readback_ok: true,
        cloudinary_readback_status: 200,
        failure_or_skip_state: decision.status === "conflict_preserved" ? "existing_value_preserved" : decision.status === "missing_card" ? "card_not_found" : null
      });
    }
  }

  const events = manifest.items.map((item) => eventsByCard.get(item.card_id));
  const counts = {};
  for (const event of events) counts[event.status] = (counts[event.status] ?? 0) + 1;
  return {
    manifest,
    events,
    counts,
    database_access_method: databaseAdapter.method,
    independently_read_back: verified.length > 0
  };
}
