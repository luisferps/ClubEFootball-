const form = document.querySelector("#start-form");
const cloudinaryApiKeyInput = document.querySelector("#cloudinary-api-key");
const cloudinaryApiSecretInput = document.querySelector("#cloudinary-api-secret");
const supabaseDbUrlInput = document.querySelector("#supabase-db-url");
const startButton = document.querySelector("#start-button");
const runProgress = document.querySelector("#run-progress");
const statusText = document.querySelector("#status-text");
const sessionToken = document.querySelector('meta[name="local-session-token"]').content;

const credentialInputs = [cloudinaryApiKeyInput, cloudinaryApiSecretInput, supabaseDbUrlInput];
let running = false;
let progressTimer = null;
let savedCredentials = false;

function credentialsReady() {
  const filled = credentialInputs.filter((input) => Boolean(input.value.trim())).length;
  return filled === credentialInputs.length || (filled === 0 && savedCredentials);
}

function updateButton() {
  startButton.disabled = running || !credentialsReady();
}

function clearCredentials() {
  for (const input of credentialInputs) input.value = "";
}

function updateCredentialPlaceholders() {
  cloudinaryApiKeyInput.placeholder = savedCredentials ? "Salva nesta máquina" : "";
  cloudinaryApiSecretInput.placeholder = savedCredentials ? "Salva nesta máquina" : "";
  supabaseDbUrlInput.placeholder = savedCredentials ? "Salva nesta máquina" : "postgresql://...";
}

function setStatus(message, state = "neutral") {
  statusText.textContent = message;
  statusText.dataset.state = state;
}

function phaseMessage(status) {
  if (status.phase === "starting" || status.phase === "discovering") return "Consultando o Supabase e montando a fila de cartas sem foto…";
  if (status.phase === "extracting_batch") {
    return `Buscando e enviando fotos: ${status.completed ?? 0} de ${status.total ?? 0} · lote ${(status.batches ?? 0) + 1}.`;
  }
  if (status.phase === "applying_batch") {
    return `Gravando e conferindo o lote ${(status.batches ?? 0) + 1} no Supabase…`;
  }
  if (status.phase === "preparing_batch") {
    return `Lote ${status.batches ?? 0} conferido · ${status.completed ?? 0} de ${status.total ?? 0} cartas processadas.`;
  }
  if (status.phase === "completed") {
    const updated = status.result?.updated ?? status.updated ?? 0;
    return status.total === 0
      ? "Concluído: nenhuma carta sem link foi encontrada."
      : `Concluído: ${updated} links gravados e conferidos no Supabase.`;
  }
  if (status.phase === "failed") return `Execução interrompida: ${status.result?.message || "consulte os logs locais."}`;
  return status.running ? "Execução em andamento…" : "Aguardando as credenciais.";
}

function renderStatus(status) {
  const total = Number(status.total ?? 0);
  const completed = Math.min(Number(status.completed ?? 0), total || 1);
  runProgress.hidden = !(status.running || status.phase === "completed" || status.phase === "failed");
  runProgress.max = total > 0 ? total : 1;
  runProgress.value = completed;
  setStatus(phaseMessage(status), status.phase === "failed" ? "failure" : status.phase === "completed" ? "success" : status.running ? "running" : "neutral");
  running = Boolean(status.running);
  updateButton();
}

function ensureStatusPolling() {
  if (!progressTimer) progressTimer = setInterval(readStatus, 1000);
}

async function readStatus() {
  try {
    const response = await fetch("/api/status", {
      method: "GET",
      cache: "no-store",
      credentials: "omit",
      headers: { "X-Local-Session": sessionToken }
    });
    if (!response.ok) throw new Error();
    const status = await response.json();
    savedCredentials = Boolean(status.capabilities?.credentialsSaved);
    updateCredentialPlaceholders();
    renderStatus(status);
    if (!status.running && status.phase === "idle" && savedCredentials) {
      setStatus("Credenciais lembradas nesta máquina. Clique em INICIAR.");
    }
  } catch {
    if (running) setStatus("Não foi possível ler o estado do aplicativo local.", "failure");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (running || !credentialsReady()) return;

  const replacingSavedCredentials = credentialInputs.every((input) => Boolean(input.value.trim()));
  const body = replacingSavedCredentials
    ? {
        cloudinaryApiKey: cloudinaryApiKeyInput.value,
        cloudinaryApiSecret: cloudinaryApiSecretInput.value,
        supabaseDbUrl: supabaseDbUrlInput.value
      }
    : { useSavedCredentials: true };
  running = true;
  updateButton();
  runProgress.hidden = false;
  runProgress.max = 1;
  runProgress.value = 0;
  setStatus("Iniciando…", "running");

  try {
    const response = await fetch("/api/start-direct", {
      method: "POST",
      cache: "no-store",
      credentials: "omit",
      headers: { "Content-Type": "application/json", "X-Local-Session": sessionToken },
      body: JSON.stringify(body)
    });
    const result = await response.json().catch(() => ({ ok: false, message: "Resposta local inválida." }));
    if (!response.ok || !result.ok) throw new Error(result.message || "Não foi possível iniciar.");
    clearCredentials();
    for (const key of Object.keys(body)) body[key] = "";
    ensureStatusPolling();
    await readStatus();
  } catch (error) {
    running = false;
    setStatus(error.message || "Não foi possível iniciar o aplicativo.", "failure");
    updateButton();
    for (const key of Object.keys(body)) body[key] = "";
  }
});

for (const input of credentialInputs) input.addEventListener("input", updateButton);

window.addEventListener("pagehide", () => {
  clearCredentials();
  if (progressTimer) clearInterval(progressTimer);
});

updateButton();
readStatus();
ensureStatusPolling();
