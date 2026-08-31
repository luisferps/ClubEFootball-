using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("Extrator eFootball")]
[assembly: System.Reflection.AssemblyDescription("Varredura somente leitura e ações separadas confirmadas")]
[assembly: System.Reflection.AssemblyProduct("Extrator eFootball")]
[assembly: System.Reflection.AssemblyCompany("ClubEfootball")]
[assembly: System.Reflection.AssemblyVersion("5.3.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("5.3.0.0")]

namespace ClubEfootballWindowsApp
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new ExtractorForm(AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar)));
        }
    }

    internal sealed class ExtractorForm : Form
    {
        private const string DesktopProtocolVersion = "5.3.0";
        private const string CredentialSchema = "clubef-credencial-banco-windows-dpapi-v1";
        // O valor V1 é estável de propósito: trocá-lo invalidaria a credencial
        // DPAPI que o operador já salvou na versão anterior.
        private static readonly byte[] CredentialEntropyV1 = Encoding.UTF8.GetBytes("ClubEfootball Extrator V5.2 database credential");
        private readonly string root;
        private readonly JavaScriptSerializer json = new JavaScriptSerializer();
        private readonly Dictionary<string, ListViewItem> families = new Dictionary<string, ListViewItem>(StringComparer.OrdinalIgnoreCase);
        private readonly Label database = new Label(), sources = new Label(), stage = new Label();
        private readonly ProgressBar progress = new ProgressBar();
        private readonly ListView familyList = new ListView();
        private readonly RichTextBox log = new RichTextBox();
        private readonly Button start = new Button(), cancel = new Button(), viewResult = new Button(), reviewMotors = new Button(), selectItems = new Button(), approve = new Button(), apply = new Button(), installMotorProtection = new Button(), configureConnection = new Button(), openLog = new Button();
        private readonly object logLock = new object();
        private Process worker;
        private WorkerRunState currentWorkerRun;
        private string cancelPath, resultPath, sessionLogPath, selectedPackagePath, motorProtectionManifestPath;
        private bool applicationReady, selectionAvailable, motorProtectionSeedReady, auxiliaryCommandRunning;

        private sealed class WorkerRunState
        {
            internal readonly object Sync = new object();
            internal readonly ManualResetEvent StandardOutputClosed = new ManualResetEvent(false);
            internal readonly ManualResetEvent StandardErrorClosed = new ManualResetEvent(false);
            internal Process Process;
            internal string InitialResultPath, FinalResultPath;
            internal bool CompleteSeen, ApplicationReady, SelectionAvailable, MotorProtectionSeedReady;
            internal string MotorProtectionManifestPath;
            internal int CompletionScheduled;
        }

        private sealed class CommandRunState
        {
            internal readonly object Sync = new object();
            internal readonly StringBuilder StandardOutput = new StringBuilder();
            internal readonly StringBuilder StandardError = new StringBuilder();
            internal readonly ManualResetEvent StandardOutputClosed = new ManualResetEvent(false);
            internal readonly ManualResetEvent StandardErrorClosed = new ManualResetEvent(false);
            internal Process Process;
            internal int CompletionScheduled;
        }

        private sealed class CommandResult
        {
            internal int ExitCode;
            internal string StandardOutput, StandardError, InfrastructureError;
            internal bool StreamsDrained;
            internal bool Succeeded { get { return ExitCode == 0 && StreamsDrained && String.IsNullOrEmpty(InfrastructureError); } }
        }

        private sealed class AuxiliaryUiState
        {
            internal bool Start, ViewResult, ReviewMotors, SelectItems, Approve, Apply, InstallMotorProtection, ConfigureConnection;
        }

        private sealed class SelectionChoice
        {
            internal string Id, Description;
            public override string ToString() { return Description; }
        }

        private sealed class MotorCardChoice
        {
            internal string Id, Name, State, Fingerprint, ExistingReason, Pending;
            public override string ToString() { return Name + " | card " + Id + " | " + State; }
        }

        private sealed class MotorProtectionPreviewInfo
        {
            internal long ResultsToInvalidate, DatabaseCards, CardsToRegister;
            internal string OperationMode, ConfirmationSha256;
        }

        internal ExtractorForm(string applicationRoot)
        {
            root = applicationRoot;
            json.MaxJsonLength = Int32.MaxValue;
            string logsDirectory = Path.Combine(root, "logs");
            Directory.CreateDirectory(logsDirectory);
            sessionLogPath = Path.Combine(logsDirectory, "extrator-desktop-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".log");
            Text = "Extrator eFootball V" + DesktopProtocolVersion + " — varredura somente leitura; envios separados";
            MinimumSize = new Size(900, 650); Size = new Size(1080, 760); StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 9F);
            BuildLayout();
            SetAvailability("Banco: aguardando", "Fontes: aguardando", "Pronto para iniciar uma varredura somente leitura.");
            AppendLog("Aplicativo aberto. Log persistente: " + sessionLogPath);
            FormClosing += delegate { RequestCancel(); };
        }

        private void BuildLayout()
        {
            TableLayoutPanel layout = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(18), ColumnCount = 1, RowCount = 6 };
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize)); layout.RowStyles.Add(new RowStyle(SizeType.AutoSize)); layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 48F)); layout.RowStyles.Add(new RowStyle(SizeType.Percent, 52F)); layout.RowStyles.Add(new RowStyle(SizeType.AutoSize)); Controls.Add(layout);
            Label title = new Label { AutoSize = true, Font = new Font(Font.FontFamily, 16F, FontStyle.Bold), Text = "Extrator eFootball" }; layout.Controls.Add(title, 0, 0);
            FlowLayoutPanel status = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill };
            database.AutoSize = true; database.Padding = new Padding(0, 8, 28, 6); sources.AutoSize = true; sources.Padding = new Padding(0, 8, 28, 6); status.Controls.Add(database); status.Controls.Add(sources); layout.Controls.Add(status, 0, 1);
            Panel progressPanel = new Panel { Height = 54, Dock = DockStyle.Fill }; stage.AutoSize = true; stage.Dock = DockStyle.Top; progress.Dock = DockStyle.Bottom; progress.Height = 17; progress.Minimum = 0; progress.Maximum = 100; progressPanel.Controls.Add(stage); progressPanel.Controls.Add(progress); layout.Controls.Add(progressPanel, 0, 2);
            familyList.Dock = DockStyle.Fill; familyList.View = View.Details; familyList.FullRowSelect = true; familyList.GridLines = true; familyList.Columns.Add("Família", 155); familyList.Columns.Add("Estado", 150); familyList.Columns.Add("Detalhe", 660);
            foreach (string family in new[] { "Cartas", "Relações", "Dimensões", "Ímpetos", "Técnicos", "Textos", "Metadados" }) UpdateFamily(family, "aguardando", "Ainda não iniciada."); layout.Controls.Add(familyList, 0, 3);
            log.Dock = DockStyle.Fill; log.ReadOnly = true; log.BackColor = Color.White; log.Font = new Font("Consolas", 9F); layout.Controls.Add(log, 0, 4);
            FlowLayoutPanel actions = new FlowLayoutPanel { AutoSize = true };
            start.Text = "INICIAR VARREDURA"; start.AutoSize = true; start.Padding = new Padding(12, 6, 12, 6); start.Click += delegate { StartWorker(); };
            cancel.Text = "CANCELAR"; cancel.AutoSize = true; cancel.Padding = new Padding(12, 6, 12, 6); cancel.Enabled = false; cancel.Click += delegate { RequestCancel(); };
            viewResult.Text = "VER RESULTADO"; viewResult.AutoSize = true; viewResult.Padding = new Padding(12, 6, 12, 6); viewResult.Enabled = false; viewResult.Click += delegate { OpenResult(); };
            reviewMotors.Text = "REVISAR USO NOS MOTORES"; reviewMotors.AutoSize = true; reviewMotors.Padding = new Padding(12, 6, 12, 6); reviewMotors.Enabled = false; reviewMotors.Click += delegate { ReviewMotorCards(); };
            selectItems.Text = "ESCOLHER O QUE ENVIAR"; selectItems.AutoSize = true; selectItems.Padding = new Padding(12, 6, 12, 6); selectItems.Enabled = false; selectItems.Click += delegate { SelectApplicationItems(); };
            approve.Text = "APROVAR PACOTE"; approve.AutoSize = true; approve.Padding = new Padding(12, 6, 12, 6); approve.Enabled = false; approve.Click += delegate { ApprovePackage(); };
            apply.Text = "APLICAR PACOTE"; apply.AutoSize = true; apply.Padding = new Padding(12, 6, 12, 6); apply.Enabled = false; apply.Click += delegate { ApplyPackage(); };
            installMotorProtection.Text = "INSTALAR/ATUALIZAR PROTEÇÃO DOS MOTORES"; installMotorProtection.AutoSize = true; installMotorProtection.Padding = new Padding(12, 6, 12, 6); installMotorProtection.Enabled = false; installMotorProtection.Click += delegate { InstallProtectionForMotors(); };
            configureConnection.Text = "CONFIGURAR CONEXÃO"; configureConnection.AutoSize = true; configureConnection.Padding = new Padding(12, 6, 12, 6); configureConnection.Click += delegate { ConfigureDatabaseConnection(); };
            openLog.Text = "ABRIR LOG"; openLog.AutoSize = true; openLog.Padding = new Padding(12, 6, 12, 6); openLog.Click += delegate { OpenPersistentLog(); };
            actions.Controls.Add(start); actions.Controls.Add(cancel); actions.Controls.Add(viewResult); actions.Controls.Add(reviewMotors); actions.Controls.Add(selectItems); actions.Controls.Add(approve); actions.Controls.Add(apply); actions.Controls.Add(installMotorProtection); actions.Controls.Add(configureConnection); actions.Controls.Add(openLog); layout.Controls.Add(actions, 0, 5);
        }

        private void SetAvailability(string databaseText, string sourceText, string stageText) { database.Text = databaseText; sources.Text = sourceText; stage.Text = "Etapa: " + stageText; }

        private string CredentialPath { get { return Path.Combine(root, "artefatos", "estado-operador", "credencial-banco.windows-dpapi.json"); } }

        private static void AssertOrdinaryFile(string path)
        {
            FileAttributes attributes = File.GetAttributes(path);
            if ((attributes & FileAttributes.Directory) != 0 || (attributes & FileAttributes.ReparsePoint) != 0)
                throw new InvalidOperationException("O arquivo protegido da conexão não é um arquivo local comum. A conexão foi bloqueada por segurança.");
            FileInfo info = new FileInfo(path);
            if (info.Length <= 0 || info.Length > 131072)
                throw new InvalidOperationException("O arquivo protegido da conexão tem tamanho inválido. A conexão foi bloqueada por segurança.");
        }

        private static string NormalizeConnectionString(string raw)
        {
            string value = (raw ?? "").Trim();
            if (value.Length == 0 || value.Length > 8192 || value.IndexOf('\0') >= 0 || value.IndexOf('\r') >= 0 || value.IndexOf('\n') >= 0)
                throw new InvalidOperationException("Cole uma connection string completa e válida do botão Connect do Supabase.");
            Uri uri;
            if (!Uri.TryCreate(value, UriKind.Absolute, out uri) ||
                !(String.Equals(uri.Scheme, "postgres", StringComparison.OrdinalIgnoreCase) || String.Equals(uri.Scheme, "postgresql", StringComparison.OrdinalIgnoreCase)))
                throw new InvalidOperationException("A connection string precisa começar com postgres:// ou postgresql://.");
            string host = uri.Host ?? "";
            if (!(host.EndsWith(".supabase.co", StringComparison.OrdinalIgnoreCase) || host.EndsWith(".pooler.supabase.com", StringComparison.OrdinalIgnoreCase)))
                throw new InvalidOperationException("O endereço não pertence a uma conexão Postgres do Supabase. Copie a string diretamente pelo botão Connect.");
            if (String.IsNullOrEmpty(uri.UserInfo) || uri.UserInfo.IndexOf(':') < 1 || uri.UserInfo.EndsWith(":", StringComparison.Ordinal) ||
                value.IndexOf("[YOUR-PASSWORD]", StringComparison.OrdinalIgnoreCase) >= 0 || value.IndexOf("YOUR_PASSWORD", StringComparison.OrdinalIgnoreCase) >= 0)
                throw new InvalidOperationException("A connection string ainda não contém a senha atual do banco.");
            if (uri.Port != -1 && uri.Port != 5432 && uri.Port != 6543)
                throw new InvalidOperationException("A porta da connection string não corresponde ao Postgres do Supabase.");
            Match ssl = Regex.Match(value, @"(?:\?|&)sslmode=([^&#]+)", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            if (ssl.Success)
            {
                string mode = Uri.UnescapeDataString(ssl.Groups[1].Value);
                if (!(String.Equals(mode, "require", StringComparison.OrdinalIgnoreCase) || String.Equals(mode, "verify-ca", StringComparison.OrdinalIgnoreCase) || String.Equals(mode, "verify-full", StringComparison.OrdinalIgnoreCase)))
                    throw new InvalidOperationException("A conexão precisa usar SSL seguro (sslmode=require ou mais forte).");
            }
            else value += (value.IndexOf('?') >= 0 ? "&" : "?") + "sslmode=require";
            return value;
        }

        private string LoadProtectedCredential(bool required)
        {
            string path = CredentialPath;
            if (!File.Exists(path))
            {
                if (required) throw new InvalidOperationException("A conexão ainda não foi configurada. Clique em CONFIGURAR CONEXÃO antes de iniciar a varredura.");
                return null;
            }
            try
            {
                AssertOrdinaryFile(path);
                Dictionary<string, object> envelope = json.DeserializeObject(File.ReadAllText(path, Encoding.UTF8)) as Dictionary<string, object>;
                if (envelope == null || envelope.Count != 5 || TextValue(envelope, "schema") != CredentialSchema ||
                    TextValue(envelope, "protection") != "Windows DPAPI" || TextValue(envelope, "scope") != "CurrentUser" ||
                    String.IsNullOrEmpty(TextValue(envelope, "created_at")) || String.IsNullOrEmpty(TextValue(envelope, "ciphertext")))
                    throw new InvalidOperationException();
                byte[] encrypted = Convert.FromBase64String(TextValue(envelope, "ciphertext"));
                if (encrypted.Length < 32 || encrypted.Length > 65536) throw new InvalidOperationException();
                byte[] clear = ProtectedData.Unprotect(encrypted, CredentialEntropyV1, DataProtectionScope.CurrentUser);
                try { return NormalizeConnectionString(new UTF8Encoding(false, true).GetString(clear)); }
                finally { Array.Clear(clear, 0, clear.Length); Array.Clear(encrypted, 0, encrypted.Length); }
            }
            catch (InvalidOperationException error)
            {
                if (!String.IsNullOrEmpty(error.Message)) throw;
                throw new InvalidOperationException("O arquivo protegido da conexão é inválido. Configure novamente; nenhuma credencial foi utilizada.");
            }
            catch
            {
                throw new InvalidOperationException("A credencial protegida não pôde ser aberta por este usuário do Windows. Configure novamente.");
            }
        }

        private void SaveProtectedCredential(string dsn)
        {
            string normalized = NormalizeConnectionString(dsn);
            byte[] clear = Encoding.UTF8.GetBytes(normalized);
            byte[] encrypted = null;
            string temporary = null;
            try
            {
                encrypted = ProtectedData.Protect(clear, CredentialEntropyV1, DataProtectionScope.CurrentUser);
                Dictionary<string, object> envelope = new Dictionary<string, object>();
                envelope["schema"] = CredentialSchema; envelope["created_at"] = DateTime.UtcNow.ToString("o");
                envelope["protection"] = "Windows DPAPI"; envelope["scope"] = "CurrentUser";
                envelope["ciphertext"] = Convert.ToBase64String(encrypted);
                string path = CredentialPath; string directory = Path.GetDirectoryName(path); Directory.CreateDirectory(directory);
                if ((File.GetAttributes(directory) & FileAttributes.ReparsePoint) != 0)
                    throw new InvalidOperationException("A pasta de estado da conexão não é uma pasta local comum.");
                if (File.Exists(path)) AssertOrdinaryFile(path);
                temporary = path + ".novo-" + Guid.NewGuid().ToString("N");
                byte[] document = new UTF8Encoding(false).GetBytes(json.Serialize(envelope));
                using (FileStream stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                {
                    stream.Write(document, 0, document.Length); stream.Flush(true);
                }
                AssertOrdinaryFile(temporary);
                if (File.Exists(path)) File.Replace(temporary, path, null); else File.Move(temporary, path);
                temporary = null;
            }
            finally
            {
                Array.Clear(clear, 0, clear.Length);
                if (encrypted != null) Array.Clear(encrypted, 0, encrypted.Length);
                if (!String.IsNullOrEmpty(temporary)) try { File.Delete(temporary); } catch { }
            }
        }

        private void InjectDatabaseCredential(ProcessStartInfo info, string dsn)
        {
            info.EnvironmentVariables.Remove("CLUBEF_SUPABASE_DB_URL");
            info.EnvironmentVariables.Remove("SUPABASE_DB_PASSWORD");
            info.EnvironmentVariables.Remove("PGPASSWORD");
            if (!String.IsNullOrEmpty(dsn)) info.EnvironmentVariables["CLUBEF_SUPABASE_DB_URL"] = dsn;
        }

        private void InjectStoredDatabaseCredential(ProcessStartInfo info, bool required)
        {
            InjectDatabaseCredential(info, LoadProtectedCredential(required));
        }

        private static void ForgetProcessCredential(ProcessStartInfo info)
        {
            try { info.EnvironmentVariables.Remove("CLUBEF_SUPABASE_DB_URL"); } catch { }
        }

        private string CreateMotorProtectionAuthorization(string runDirectory, string manifestPath, string confirmationSha256)
        {
            string expectedRun = Path.GetFullPath(runDirectory);
            string expectedManifest = Path.GetFullPath(manifestPath);
            if (!File.Exists(expectedManifest) || !String.Equals(Path.GetDirectoryName(Path.GetDirectoryName(expectedManifest)), expectedRun, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("O seed da proteção não pertence à execução atual.");
            byte[] nonce = new byte[32];
            using (RandomNumberGenerator generator = RandomNumberGenerator.Create()) { generator.GetBytes(nonce); }
            try
            {
                Dictionary<string, object> envelope = new Dictionary<string, object>();
                DateTime issued = DateTime.UtcNow;
                envelope["schema"] = "clubef-autorizacao-escrita-ui-v1";
                envelope["action"] = "install_motor_protection";
                envelope["protocol_version"] = DesktopProtocolVersion;
                envelope["manifest_path"] = expectedManifest;
                envelope["confirmation_sha256"] = confirmationSha256;
                envelope["launcher_pid"] = Process.GetCurrentProcess().Id;
                envelope["launcher_executable"] = Path.GetFullPath(Application.ExecutablePath);
                envelope["issued_at"] = issued.ToString("o");
                envelope["expires_at"] = issued.AddMinutes(5).ToString("o");
                envelope["nonce"] = BitConverter.ToString(nonce).Replace("-", "").ToLowerInvariant();
                envelope["database_write_authorized"] = true;
                string path = Path.Combine(expectedRun, "autorizacao-protecao-motores-" + Guid.NewGuid().ToString("N") + ".json");
                string temporary = path + ".novo";
                byte[] document = new UTF8Encoding(false).GetBytes(json.Serialize(envelope));
                try
                {
                    using (FileStream stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                    {
                        stream.Write(document, 0, document.Length); stream.Flush(true);
                    }
                    File.Move(temporary, path);
                }
                catch
                {
                    try { if (File.Exists(temporary)) File.Delete(temporary); } catch { }
                    throw;
                }
                return path;
            }
            finally { Array.Clear(nonce, 0, nonce.Length); }
        }

        private string FindPython(out bool isLauncher)
        {
            isLauncher = false;
            string cached = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "python.exe");
            if (File.Exists(cached)) return cached;
            foreach (string piece in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(Path.PathSeparator))
            {
                string folder = (piece ?? "").Trim().Trim('"'); if (folder.Length == 0) continue;
                string python = Path.Combine(folder, "python.exe"); if (File.Exists(python)) return python;
                string launcher = Path.Combine(folder, "py.exe"); if (File.Exists(launcher)) { isLauncher = true; return launcher; }
            }
            return null;
        }

        private ProcessStartInfo BuildDatabaseTestCommand(string dsn)
        {
            bool launcher; string python = FindPython(out launcher); string script = Path.Combine(root, "executor", "desktop_worker.py");
            if (String.IsNullOrEmpty(python)) throw new InvalidOperationException("Python não foi encontrado neste Windows.");
            string runDirectory = Path.Combine(root, "artefatos", "desktop", "teste-conexao-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N").Substring(0, 8));
            Directory.CreateDirectory(runDirectory);
            string arguments = (launcher ? "-3 " : "") + Quote(script) + " --root " + Quote(root) + " --run-dir " + Quote(runDirectory) + " --cancel " + Quote(Path.Combine(runDirectory, "CANCELAR.txt")) + " --protocol-version " + Quote(DesktopProtocolVersion) + " --test-database-connection";
            ProcessStartInfo info = new ProcessStartInfo { FileName = python, Arguments = arguments, WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            info.EnvironmentVariables["PYTHONPATH"] = Path.Combine(root, "executor", "vendor");
            info.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
            info.EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE");
            InjectDatabaseCredential(info, dsn);
            return info;
        }

        private void ConfigureDatabaseConnection()
        {
            if (auxiliaryCommandRunning || (worker != null && !worker.HasExited)) return;
            string dsn;
            using (Form dialog = new Form())
            {
                dialog.Text = "Configurar conexão segura"; dialog.StartPosition = FormStartPosition.CenterParent; dialog.MinimumSize = new Size(720, 300); dialog.Size = new Size(820, 330); dialog.Font = Font;
                TableLayoutPanel panel = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(16), ColumnCount = 1, RowCount = 4 };
                panel.RowStyles.Add(new RowStyle(SizeType.AutoSize)); panel.RowStyles.Add(new RowStyle(SizeType.AutoSize)); panel.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); panel.RowStyles.Add(new RowStyle(SizeType.AutoSize)); dialog.Controls.Add(panel);
                Label explanation = new Label { AutoSize = true, MaximumSize = new Size(760, 0), Text = "No Supabase, abra o projeto, clique em Connect e copie a connection string completa. Se a conexão direta não funcionar nesta rede, escolha Session pooler. Confirme que a senha atual substituiu [YOUR-PASSWORD]." };
                panel.Controls.Add(explanation, 0, 0);
                Label fieldLabel = new Label { AutoSize = true, Padding = new Padding(0, 12, 0, 4), Text = "Connection string (fica mascarada):" }; panel.Controls.Add(fieldLabel, 0, 1);
                TextBox input = new TextBox { Dock = DockStyle.Top, UseSystemPasswordChar = true }; panel.Controls.Add(input, 0, 2);
                FlowLayoutPanel buttons = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill, FlowDirection = FlowDirection.RightToLeft };
                Button testAndSave = new Button { Text = "TESTAR E SALVAR", AutoSize = true, DialogResult = DialogResult.OK };
                Button close = new Button { Text = "CANCELAR", AutoSize = true, DialogResult = DialogResult.Cancel };
                buttons.Controls.Add(testAndSave); buttons.Controls.Add(close); panel.Controls.Add(buttons, 0, 3); dialog.AcceptButton = testAndSave; dialog.CancelButton = close;
                if (dialog.ShowDialog(this) != DialogResult.OK) return;
                try { dsn = NormalizeConnectionString(input.Text); }
                catch (Exception error) { MessageBox.Show(error.Message, "Configurar conexão", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
                input.Clear();
            }
            AuxiliaryUiState uiState = null;
            try
            {
                uiState = BeginAuxiliaryOperation();
                database.Text = "Banco: testando em somente leitura"; stage.Text = "Etapa: testando a conexão sem alterar dados.";
                AppendLog("Teste de conexão iniciado em transação somente leitura. A credencial não será registrada no log.");
                RunCommandAsync(BuildDatabaseTestCommand(dsn), delegate(CommandResult commandResult) {
                    RestoreAuxiliaryOperation(uiState);
                    if (!commandResult.Succeeded)
                    {
                        database.Text = "Banco: conexão recusada";
                        string failure = CommandFailureText(commandResult, "A conexão foi recusada. A credencial não foi salva.");
                        AppendLog(failure); MessageBox.Show(failure, "Configurar conexão", MessageBoxButtons.OK, MessageBoxIcon.Error); return;
                    }
                    try
                    {
                        SaveProtectedCredential(dsn);
                        database.Text = "Banco: conexão protegida confirmada"; stage.Text = "Etapa: conexão testada e salva somente para este usuário do Windows.";
                        AppendLog("Conexão confirmada em modo somente leitura e salva com Windows DPAPI. Nenhum dado do banco foi alterado.");
                        MessageBox.Show("Conexão confirmada e salva com a proteção do Windows. Nenhum dado do banco foi alterado. Agora você pode iniciar uma nova varredura.", "Conexão pronta", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    catch (Exception error)
                    {
                        database.Text = "Banco: conexão não salva";
                        AppendLog("A conexão passou no teste, mas não pôde ser salva com a proteção do Windows: " + error.Message);
                        MessageBox.Show("A conexão passou no teste, mas não pôde ser salva com a proteção do Windows. " + error.Message, "Configurar conexão", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                });
            }
            catch (Exception error)
            {
                if (uiState != null) RestoreAuxiliaryOperation(uiState);
                AppendLog("Não foi possível iniciar o teste seguro da conexão: " + error.Message);
                MessageBox.Show(error.Message, "Configurar conexão", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void StartWorker()
        {
            if (auxiliaryCommandRunning) return;
            if (worker != null && !worker.HasExited) return;
            string script = Path.Combine(root, "executor", "desktop_worker.py");
            if (!File.Exists(script)) { MessageBox.Show("Não encontrei executor\\desktop_worker.py.", "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error); return; }
            bool launcher; string python = FindPython(out launcher);
            if (String.IsNullOrEmpty(python)) { MessageBox.Show("Python não foi encontrado neste Windows.", "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error); return; }
            string protectedDsn;
            try { protectedDsn = LoadProtectedCredential(true); }
            catch (Exception error) { AppendLog(error.Message); MessageBox.Show(error.Message, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
            string runDirectory = Path.Combine(root, "artefatos", "desktop", "run-" + DateTime.Now.ToString("yyyyMMdd-HHmmss")); Directory.CreateDirectory(runDirectory);
            cancelPath = Path.Combine(runDirectory, "CANCELAR.txt"); resultPath = Path.Combine(runDirectory, "resultado.json");
            foreach (ListViewItem item in families.Values) { item.SubItems[1].Text = "aguardando"; item.SubItems[2].Text = "Ainda não iniciada."; }
            applicationReady = false; selectionAvailable = false; motorProtectionSeedReady = false; selectedPackagePath = null; motorProtectionManifestPath = null; log.Clear(); progress.Value = 0; start.Enabled = false; cancel.Enabled = true; viewResult.Enabled = false; reviewMotors.Enabled = false; selectItems.Enabled = false; approve.Enabled = false; apply.Enabled = false; installMotorProtection.Enabled = false; configureConnection.Enabled = false; SetAvailability("Banco: conectando em leitura", "Fontes: verificando", "Preparando processo de extração separado."); AppendLog("Iniciando worker desktop V" + DesktopProtocolVersion + ". Nenhuma escrita no banco é permitida.");
            ProcessStartInfo info = new ProcessStartInfo(); info.FileName = python; info.Arguments = (launcher ? "-3 " : "") + Quote(script) + " --root " + Quote(root) + " --run-dir " + Quote(runDirectory) + " --cancel " + Quote(cancelPath) + " --protocol-version " + Quote(DesktopProtocolVersion); info.WorkingDirectory = root; info.UseShellExecute = false; info.CreateNoWindow = true; info.RedirectStandardOutput = true; info.RedirectStandardError = true; info.EnvironmentVariables["PYTHONPATH"] = Path.Combine(root, "executor", "vendor"); info.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"; info.EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE");
            InjectDatabaseCredential(info, protectedDsn);
            WorkerRunState run = new WorkerRunState();
            Process process = new Process { StartInfo = info, EnableRaisingEvents = true };
            run.Process = process; run.InitialResultPath = resultPath;
            currentWorkerRun = run; worker = process;
            process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) {
                if (e.Data == null) { run.StandardOutputClosed.Set(); return; }
                CaptureWorkerComplete(run, e.Data);
                HandleWorkerLine(run, e.Data);
            };
            process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) {
                if (e.Data == null) { run.StandardErrorClosed.Set(); return; }
                AppendFromWorker("ERRO | " + e.Data);
            };
            process.Exited += delegate { CompleteWorkerAfterExit(run); };
            try { process.Start(); ForgetProcessCredential(info); process.BeginOutputReadLine(); process.BeginErrorReadLine(); }
            catch (Exception error)
            {
                try { if (!process.HasExited) process.Kill(); } catch { }
                currentWorkerRun = null; worker = null;
                run.StandardOutputClosed.Close(); run.StandardErrorClosed.Close(); process.Dispose();
                start.Enabled = true; cancel.Enabled = false; configureConnection.Enabled = true; AppendLog("Falha ao iniciar worker: " + error.Message); MessageBox.Show(error.Message, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private static string Quote(string value) { return "\"" + value.Replace("\"", "\\\"") + "\""; }
        private void CaptureWorkerComplete(WorkerRunState run, string line)
        {
            try
            {
                JavaScriptSerializer parser = new JavaScriptSerializer(); parser.MaxJsonLength = Int32.MaxValue;
                Dictionary<string, object> message = parser.DeserializeObject(line) as Dictionary<string, object>;
                if (message == null || TextValue(message, "type") != "complete") return;
                bool ready, canSelect, protectionReady;
                string completedPath = TextValue(message, "result_path");
                lock (run.Sync)
                {
                    run.CompleteSeen = true;
                    run.FinalResultPath = String.IsNullOrEmpty(completedPath) ? run.InitialResultPath : completedPath;
                    run.ApplicationReady = Boolean.TryParse(TextValue(message, "application_ready"), out ready) && ready;
                    run.SelectionAvailable = Boolean.TryParse(TextValue(message, "selection_available"), out canSelect) && canSelect;
                    run.MotorProtectionSeedReady = Boolean.TryParse(TextValue(message, "motor_protection_seed_ready"), out protectionReady) && protectionReady;
                    run.MotorProtectionManifestPath = TextValue(message, "motor_protection_manifest_path");
                }
            }
            catch { /* A mensagem será exibida como evento inválido pela interface. */ }
        }

        private void CompleteWorkerAfterExit(WorkerRunState run)
        {
            if (Interlocked.Exchange(ref run.CompletionScheduled, 1) != 0) return;
            ThreadPool.QueueUserWorkItem(delegate {
                int exitCode = -1; string drainError = null;
                try
                {
                    run.Process.WaitForExit();
                    bool outputClosed = run.StandardOutputClosed.WaitOne(10000);
                    bool errorClosed = run.StandardErrorClosed.WaitOne(10000);
                    if (!outputClosed || !errorClosed) drainError = "O worker terminou, mas a interface não recebeu o fim dos dois canais de saída. As ações de envio foram bloqueadas por segurança.";
                    exitCode = run.Process.ExitCode;
                }
                catch (Exception error) { drainError = "Não foi possível confirmar o encerramento completo do worker: " + error.Message; }
                if (IsDisposed || !IsHandleCreated) return;
                try { BeginInvoke((MethodInvoker)delegate { FinishWorker(run, exitCode, drainError); }); }
                catch (InvalidOperationException) { }
            });
        }

        private void HandleWorkerLine(WorkerRunState run, string line)
        {
            if (IsDisposed) return;
            BeginInvoke((MethodInvoker)delegate {
                if (!Object.ReferenceEquals(currentWorkerRun, run)) return;
                try
                {
                    Dictionary<string, object> message = json.DeserializeObject(line) as Dictionary<string, object>; if (message == null) { AppendLog(line); return; }
                    string type = TextValue(message, "type");
                    if (type == "status") { database.Text = "Banco: " + TextValue(message, "database"); sources.Text = "Fontes: " + TextValue(message, "sources"); stage.Text = "Etapa: " + TextValue(message, "message"); }
                    else if (type == "source") AppendLog("Fonte " + TextValue(message, "role") + ": " + TextValue(message, "message"));
                    else if (type == "progress") { int value; if (Int32.TryParse(TextValue(message, "percent"), out value)) progress.Value = Math.Max(progress.Minimum, Math.Min(progress.Maximum, value)); stage.Text = "Etapa: " + TextValue(message, "stage"); }
                    else if (type == "family") UpdateFamily(TextValue(message, "family"), TextValue(message, "state"), TextValue(message, "message"));
                    else if (type == "complete")
                    {
                        string completedPath = TextValue(message, "result_path");
                        if (!String.IsNullOrEmpty(completedPath)) AppendLog("Resultado local: " + completedPath);
                        string applicationState = TextValue(message, "application_state");
                        if (!String.IsNullOrEmpty(applicationState)) AppendLog("Plano de aplicação: " + applicationState + "; itens que podem ser marcados=" + TextValue(message, "selectable_count") + "; itens somente para observação=" + TextValue(message, "not_selectable_count") + "; pendências conhecidas=" + TextValue(message, "unresolved_pending_count") + "; avisos históricos=" + TextValue(message, "historical_warning_count") + ".");
                    }
                    else AppendLog(TextValue(message, "message"));
                }
                catch (Exception error) { AppendLog("Evento inválido do worker: " + error.Message); }
            });
        }
        private static string TextValue(Dictionary<string, object> message, string key) { object value; return message.TryGetValue(key, out value) && value != null ? Convert.ToString(value) : ""; }
        private void UpdateFamily(string family, string state, string detail)
        {
            if (String.IsNullOrEmpty(family)) return; ListViewItem item;
            if (!families.TryGetValue(family, out item)) { item = new ListViewItem(family); item.SubItems.Add(""); item.SubItems.Add(""); families[family] = item; familyList.Items.Add(item); }
            item.SubItems[1].Text = state; item.SubItems[2].Text = detail;
        }
        private void AppendFromWorker(string text)
        {
            if (IsDisposed || !IsHandleCreated) return;
            try { BeginInvoke((MethodInvoker)delegate { if (!IsDisposed) AppendLog(text); }); }
            catch (InvalidOperationException) { }
        }
        private void AppendLog(string text)
        {
            if (String.IsNullOrEmpty(text)) return;
            string line = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " | " + text + Environment.NewLine;
            log.AppendText(line); log.SelectionStart = log.TextLength; log.ScrollToCaret();
            try { lock (logLock) { File.AppendAllText(sessionLogPath, line, new UTF8Encoding(false)); } }
            catch { /* A interface continua viva mesmo se o disco ficar indisponível. */ }
        }
        private void RequestCancel()
        {
            if (String.IsNullOrEmpty(cancelPath) || worker == null || worker.HasExited) return;
            try { File.WriteAllText(cancelPath, "cancelled by user", new UTF8Encoding(false)); cancel.Enabled = false; AppendLog("Cancelamento solicitado. O worker salvará o estado seguro e encerrará."); }
            catch (Exception error) { AppendLog("Não foi possível solicitar cancelamento: " + error.Message); }
        }
        private void FinishWorker(WorkerRunState run, int exitCode, string drainError)
        {
            if (!Object.ReferenceEquals(currentWorkerRun, run)) return;
            bool completeSeen, finalApplicationReady, finalSelectionAvailable, finalMotorProtectionSeedReady;
            string finalResultPath, finalMotorProtectionManifestPath;
            lock (run.Sync)
            {
                completeSeen = run.CompleteSeen;
                finalResultPath = String.IsNullOrEmpty(run.FinalResultPath) ? run.InitialResultPath : run.FinalResultPath;
                finalApplicationReady = run.ApplicationReady;
                finalSelectionAvailable = run.SelectionAvailable;
                finalMotorProtectionSeedReady = run.MotorProtectionSeedReady;
                finalMotorProtectionManifestPath = run.MotorProtectionManifestPath;
            }
            resultPath = finalResultPath;
            applicationReady = exitCode == 0 && completeSeen && String.IsNullOrEmpty(drainError) && finalApplicationReady;
            selectionAvailable = exitCode == 0 && completeSeen && String.IsNullOrEmpty(drainError) && finalSelectionAvailable;
            motorProtectionManifestPath = finalMotorProtectionManifestPath;
            motorProtectionSeedReady = exitCode == 0 && completeSeen && String.IsNullOrEmpty(drainError) && finalMotorProtectionSeedReady && !String.IsNullOrEmpty(motorProtectionManifestPath) && File.Exists(motorProtectionManifestPath);
            if (!String.IsNullOrEmpty(drainError)) AppendLog(drainError);
            if (!completeSeen)
            {
                applicationReady = false; selectionAvailable = false;
                AppendLog("O worker não entregou a confirmação final em JSON. Seleção, aprovação e aplicação permanecem bloqueadas por segurança.");
            }
            cancel.Enabled = false; start.Enabled = true; configureConnection.Enabled = true; viewResult.Enabled = File.Exists(resultPath); reviewMotors.Enabled = File.Exists(Path.Combine(Path.GetDirectoryName(resultPath), "revisao-prontidao-motores.json")); selectItems.Enabled = selectionAvailable && File.Exists(Path.Combine(Path.GetDirectoryName(resultPath), "pacote-revisao.json")); approve.Enabled = applicationReady && !String.IsNullOrEmpty(selectedPackagePath) && File.Exists(selectedPackagePath); apply.Enabled = false; installMotorProtection.Enabled = motorProtectionSeedReady;
            if (exitCode == 0 && completeSeen && String.IsNullOrEmpty(drainError)) { progress.Value = 100; stage.Text = "Etapa: conferência concluída — somente leitura."; AppendLog("Worker concluído. Nenhuma escrita automática foi executada."); }
            else if (exitCode == 0) { stage.Text = "Etapa: worker encerrado sem confirmação final completa. Envio bloqueado; consulte o log."; }
            else { stage.Text = "Etapa: worker encerrado com código " + exitCode + ". Consulte o log e o resultado local."; AppendLog("Worker encerrado com código " + exitCode + ". A janela permaneceu disponível."); }
            run.StandardOutputClosed.Close(); run.StandardErrorClosed.Close();
        }

        private void OpenPersistentLog()
        {
            try
            {
                if (!File.Exists(sessionLogPath)) File.WriteAllText(sessionLogPath, "Log ainda sem eventos." + Environment.NewLine, new UTF8Encoding(false));
                Process.Start(new ProcessStartInfo { FileName = sessionLogPath, UseShellExecute = true });
            }
            catch (Exception error)
            {
                AppendLog("Não foi possível abrir o log persistente: " + error.Message);
                MessageBox.Show("Não foi possível abrir o log persistente: " + error.Message, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
        private void OpenResult()
        {
            if (!File.Exists(resultPath)) return;
            string reviewHtml = Path.Combine(Path.GetDirectoryName(resultPath), "resultado.html");
            if (!File.Exists(reviewHtml))
            {
                MessageBox.Show("O resumo HTML desta execução ainda não existe. O JSON técnico foi preservado e não será aberto no Bloco de Notas.", "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            try
            {
                Process.Start(new ProcessStartInfo { FileName = reviewHtml, UseShellExecute = true });
                AppendLog("Resultado, divergências e pendências abertos no navegador: " + reviewHtml);
            }
            catch (Exception error)
            {
                AppendLog("Não foi possível abrir o resultado HTML: " + error.Message);
                MessageBox.Show("Não foi possível abrir o resultado HTML: " + error.Message, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private Dictionary<string, Dictionary<string, object>> ReadMotorOverrides(string overridePath)
        {
            Dictionary<string, Dictionary<string, object>> rows = new Dictionary<string, Dictionary<string, object>>(StringComparer.OrdinalIgnoreCase);
            if (!File.Exists(overridePath)) return rows;
            Dictionary<string, object> envelope = json.DeserializeObject(File.ReadAllText(overridePath, Encoding.UTF8)) as Dictionary<string, object>;
            object cardsObject;
            IEnumerable sequence;
            if (envelope == null || TextValue(envelope, "schema") != "clubef-prontidao-motores-operador-v1" || !envelope.TryGetValue("cards", out cardsObject) || (sequence = cardsObject as IEnumerable) == null)
                throw new InvalidOperationException("O arquivo de marcações dos motores é inválido.");
            foreach (object raw in sequence)
            {
                Dictionary<string, object> row = raw as Dictionary<string, object>;
                if (row == null) throw new InvalidOperationException("O arquivo de marcações contém uma linha que não é um card válido. Nada foi carregado.");
                string id = TextValue(row, "card_id");
                if (String.IsNullOrEmpty(id) || rows.ContainsKey(id)) throw new InvalidOperationException("Há uma marcação de motor sem identidade ou repetida.");
                string state = TextValue(row, "estado");
                if (!String.Equals(state, "incompleto_confirmado", StringComparison.Ordinal))
                    throw new InvalidOperationException("A marcação do card " + id + " tem o estado inesperado '" + state + "'. Somente 'incompleto_confirmado' pode bloquear motores; o arquivo inteiro foi recusado por segurança.");
                rows[id] = row;
            }
            return rows;
        }

        private List<MotorCardChoice> ReadMotorChoices(string reviewPath)
        {
            Dictionary<string, object> envelope = json.DeserializeObject(File.ReadAllText(reviewPath, Encoding.UTF8)) as Dictionary<string, object>;
            object cardsObject;
            IEnumerable sequence;
            if (envelope == null || TextValue(envelope, "schema") != "clubef-prontidao-motores-revisao-operador-v1" || !envelope.TryGetValue("cards", out cardsObject) || (sequence = cardsObject as IEnumerable) == null)
                throw new InvalidOperationException("A revisão de cartas para os motores é inválida.");
            List<MotorCardChoice> result = new List<MotorCardChoice>();
            foreach (object raw in sequence)
            {
                Dictionary<string, object> row = raw as Dictionary<string, object>;
                if (row == null) continue;
                string id = TextValue(row, "card_id"), name = TextValue(row, "nome"), state = TextValue(row, "estado");
                if (String.IsNullOrEmpty(id)) continue;
                string stateLabel = state == "pronto_para_motores" ? "pronto" : state == "aguardando_insumos" ? "aguarda dado realmente não conferido" : state == "aguardando_decisao_de_vinculo" ? "aguarda decisão" : state;
                List<string> pendingLabels = new List<string>();
                object pendingObject;
                IEnumerable pendingSequence;
                if (row.TryGetValue("pendencias_conhecidas", out pendingObject) && (pendingSequence = pendingObject as IEnumerable) != null)
                {
                    foreach (object pendingRaw in pendingSequence)
                    {
                        Dictionary<string, object> pending = pendingRaw as Dictionary<string, object>;
                        if (pending != null) pendingLabels.Add(TextValue(pending, "significado"));
                    }
                }
                string existingReason = null;
                object markerObject;
                Dictionary<string, object> marker;
                if (row.TryGetValue("marcacao_operador", out markerObject) && (marker = markerObject as Dictionary<string, object>) != null) existingReason = TextValue(marker, "motivo");
                result.Add(new MotorCardChoice {
                    Id = id,
                    Name = String.IsNullOrEmpty(name) ? "Card sem nome" : name,
                    State = stateLabel,
                    Fingerprint = TextValue(row, "input_fingerprint"),
                    ExistingReason = existingReason,
                    Pending = String.Join("; ", pendingLabels.ToArray())
                });
            }
            return result;
        }

        private ProcessStartInfo BuildMotorRefreshCommand()
        {
            bool launcher; string python = FindPython(out launcher); string script = Path.Combine(root, "executor", "desktop_worker.py");
            if (String.IsNullOrEmpty(python)) throw new InvalidOperationException("Python não foi encontrado neste Windows.");
            string runDirectory = Path.GetDirectoryName(resultPath);
            string arguments = (launcher ? "-3 " : "") + Quote(script) + " --root " + Quote(root) + " --run-dir " + Quote(runDirectory) + " --cancel " + Quote(Path.Combine(runDirectory, "CANCELAR.txt")) + " --protocol-version " + Quote(DesktopProtocolVersion) + " --refresh-motor-readiness";
            ProcessStartInfo info = new ProcessStartInfo { FileName = python, Arguments = arguments, WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            info.EnvironmentVariables["PYTHONPATH"] = Path.Combine(root, "executor", "vendor");
            info.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
            info.EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE");
            InjectStoredDatabaseCredential(info, false);
            return info;
        }

        private AuxiliaryUiState BeginAuxiliaryOperation()
        {
            if (auxiliaryCommandRunning) throw new InvalidOperationException("Já existe uma ação em andamento. Aguarde a conclusão mostrada na própria janela.");
            AuxiliaryUiState state = new AuxiliaryUiState {
                Start = start.Enabled,
                ViewResult = viewResult.Enabled,
                ReviewMotors = reviewMotors.Enabled,
                SelectItems = selectItems.Enabled,
                Approve = approve.Enabled,
                Apply = apply.Enabled,
                InstallMotorProtection = installMotorProtection.Enabled,
                ConfigureConnection = configureConnection.Enabled
            };
            auxiliaryCommandRunning = true; UseWaitCursor = true;
            start.Enabled = false; viewResult.Enabled = false; reviewMotors.Enabled = false; selectItems.Enabled = false; approve.Enabled = false; apply.Enabled = false; installMotorProtection.Enabled = false; configureConnection.Enabled = false;
            return state;
        }

        private void RestoreAuxiliaryOperation(AuxiliaryUiState state)
        {
            auxiliaryCommandRunning = false; UseWaitCursor = false;
            start.Enabled = state.Start; viewResult.Enabled = state.ViewResult; reviewMotors.Enabled = state.ReviewMotors; selectItems.Enabled = state.SelectItems; approve.Enabled = state.Approve; apply.Enabled = state.Apply; installMotorProtection.Enabled = state.InstallMotorProtection; configureConnection.Enabled = state.ConfigureConnection;
        }

        private void RunCommandAsync(ProcessStartInfo info, Action<CommandResult> completed)
        {
            CommandRunState run = new CommandRunState();
            Process process = new Process { StartInfo = info, EnableRaisingEvents = true }; run.Process = process;
            process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) {
                if (e.Data == null) { run.StandardOutputClosed.Set(); return; }
                lock (run.Sync) run.StandardOutput.AppendLine(e.Data);
                AppendFromWorker(e.Data);
            };
            process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) {
                if (e.Data == null) { run.StandardErrorClosed.Set(); return; }
                lock (run.Sync) run.StandardError.AppendLine(e.Data);
                AppendFromWorker("ERRO | " + e.Data);
            };
            process.Exited += delegate { CompleteCommandAfterExit(run, completed); };
            try { process.Start(); ForgetProcessCredential(info); process.BeginOutputReadLine(); process.BeginErrorReadLine(); }
            catch
            {
                try { if (!process.HasExited) process.Kill(); } catch { }
                try { process.Dispose(); } catch { }
                throw;
            }
        }

        private void CompleteCommandAfterExit(CommandRunState run, Action<CommandResult> completed)
        {
            if (Interlocked.Exchange(ref run.CompletionScheduled, 1) != 0) return;
            ThreadPool.QueueUserWorkItem(delegate {
                CommandResult result = new CommandResult { ExitCode = -1 };
                try
                {
                    run.Process.WaitForExit();
                    bool outputClosed = run.StandardOutputClosed.WaitOne(10000);
                    bool errorClosed = run.StandardErrorClosed.WaitOne(10000);
                    result.StreamsDrained = outputClosed && errorClosed;
                    if (!result.StreamsDrained) result.InfrastructureError = "A ação terminou, mas a interface não recebeu o fim dos dois canais de saída.";
                    result.ExitCode = run.Process.ExitCode;
                }
                catch (Exception error) { result.InfrastructureError = "Não foi possível confirmar o encerramento da ação: " + error.Message; }
                lock (run.Sync)
                {
                    result.StandardOutput = run.StandardOutput.ToString();
                    result.StandardError = run.StandardError.ToString();
                }
                run.StandardOutputClosed.Close(); run.StandardErrorClosed.Close(); run.Process.Dispose();
                if (IsDisposed || !IsHandleCreated) return;
                try { BeginInvoke((MethodInvoker)delegate { completed(result); }); }
                catch (InvalidOperationException) { }
            });
        }

        private static string CommandFailureText(CommandResult result, string fallback)
        {
            StringBuilder detail = new StringBuilder();
            if (!String.IsNullOrEmpty(result.InfrastructureError)) detail.AppendLine(result.InfrastructureError);
            if (!String.IsNullOrWhiteSpace(result.StandardError)) detail.AppendLine(result.StandardError.Trim());
            if (!String.IsNullOrWhiteSpace(result.StandardOutput)) detail.AppendLine(result.StandardOutput.Trim());
            string text = detail.ToString().Trim();
            if (text.Length > 3500) text = text.Substring(text.Length - 3500);
            return String.IsNullOrEmpty(text) ? fallback : fallback + Environment.NewLine + Environment.NewLine + text;
        }

        private void ReviewMotorCards()
        {
            if (auxiliaryCommandRunning) return;
            if (String.IsNullOrEmpty(resultPath)) return;
            string runDirectory = Path.GetDirectoryName(resultPath);
            string reviewPath = Path.Combine(runDirectory, "revisao-prontidao-motores.json");
            string stateDirectory = Path.Combine(root, "artefatos", "estado-operador");
            string overridePath = Path.Combine(stateDirectory, "prontidao-motores-operador.json");
            if (!File.Exists(reviewPath)) { MessageBox.Show("Esta execução não possui a revisão de uso nos motores.", "Uso nos motores", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
            try
            {
                List<MotorCardChoice> choices = ReadMotorChoices(reviewPath);
                Dictionary<string, Dictionary<string, object>> existing = ReadMotorOverrides(overridePath);
                Dictionary<string, MotorCardChoice> byId = new Dictionary<string, MotorCardChoice>(StringComparer.OrdinalIgnoreCase);
                HashSet<string> marked = new HashSet<string>(existing.Keys, StringComparer.OrdinalIgnoreCase);
                foreach (MotorCardChoice choice in choices) byId[choice.Id] = choice;
                using (Form dialog = new Form())
                {
                    dialog.Text = "Revisar quais cartas não podem entrar nos motores"; dialog.StartPosition = FormStartPosition.CenterParent; dialog.MinimumSize = new Size(900, 600); dialog.Size = new Size(1080, 740); dialog.Font = Font;
                    TableLayoutPanel panel = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(14), RowCount = 5, ColumnCount = 1 };
                    panel.RowStyles.Add(new RowStyle(SizeType.AutoSize)); panel.RowStyles.Add(new RowStyle(SizeType.AutoSize)); panel.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); panel.RowStyles.Add(new RowStyle(SizeType.AutoSize)); panel.RowStyles.Add(new RowStyle(SizeType.AutoSize)); dialog.Controls.Add(panel);
                    Label explanation = new Label { AutoSize = true, MaximumSize = new Size(1020, 0), Text = "Marque somente um card que você sabe que chegou parcialmente carregado pela Konami. Um espaço conferido e vazio significa que o card não possui aquele item e continua completo. Esta tela nunca declara um card completo por decisão manual: a liberação depende da leitura automática. A marcação bloqueia apenas Otimizador e Bonificador; publicação e envio ao banco continuam separados." }; panel.Controls.Add(explanation, 0, 0);
                    FlowLayoutPanel searchPanel = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill };
                    searchPanel.Controls.Add(new Label { AutoSize = true, Padding = new Padding(0, 6, 4, 0), Text = "Buscar por nome ou card ID:" });
                    TextBox search = new TextBox { Width = 420 }; searchPanel.Controls.Add(search); panel.Controls.Add(searchPanel, 0, 1);
                    ListView list = new ListView { Dock = DockStyle.Fill, View = View.Details, CheckBoxes = true, FullRowSelect = true, GridLines = true };
                    list.Columns.Add("Bloquear", 70); list.Columns.Add("Card", 330); list.Columns.Add("Card ID", 180); list.Columns.Add("Situação automática", 220); list.Columns.Add("Observação conhecida", 360); panel.Controls.Add(list, 0, 2);
                    bool loading = false;
                    list.ItemChecked += delegate(object sender, ItemCheckedEventArgs eventArgs) { if (loading) return; MotorCardChoice choice = eventArgs.Item.Tag as MotorCardChoice; if (choice == null) return; if (eventArgs.Item.Checked) marked.Add(choice.Id); else marked.Remove(choice.Id); };
                    Action populate = delegate {
                        string query = search.Text.Trim(); loading = true; list.BeginUpdate(); list.Items.Clear();
                        foreach (MotorCardChoice choice in choices)
                        {
                            if (query.Length > 0 && choice.Name.IndexOf(query, StringComparison.OrdinalIgnoreCase) < 0 && choice.Id.IndexOf(query, StringComparison.OrdinalIgnoreCase) < 0) continue;
                            ListViewItem item = new ListViewItem(""); item.SubItems.Add(choice.Name); item.SubItems.Add(choice.Id); item.SubItems.Add(choice.State); item.SubItems.Add(choice.Pending); item.Tag = choice; item.Checked = marked.Contains(choice.Id); list.Items.Add(item);
                        }
                        list.EndUpdate(); loading = false;
                    };
                    search.TextChanged += delegate { populate(); }; populate();
                    TableLayoutPanel reasonPanel = new TableLayoutPanel { AutoSize = true, Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 2 };
                    reasonPanel.Controls.Add(new Label { AutoSize = true, Text = "Motivo obrigatório para as novas marcações:" }, 0, 0);
                    TextBox reason = new TextBox { Dock = DockStyle.Fill, Multiline = true, Height = 52 }; reasonPanel.Controls.Add(reason, 0, 1); panel.Controls.Add(reasonPanel, 0, 3);
                    FlowLayoutPanel buttons = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill, FlowDirection = FlowDirection.RightToLeft };
                    Button save = new Button { Text = "SALVAR E ATUALIZAR RELATÓRIO", AutoSize = true, DialogResult = DialogResult.OK };
                    Button close = new Button { Text = "CANCELAR", AutoSize = true, DialogResult = DialogResult.Cancel };
                    buttons.Controls.Add(save); buttons.Controls.Add(close); panel.Controls.Add(buttons, 0, 4); dialog.AcceptButton = save; dialog.CancelButton = close;
                    save.Click += delegate {
                        List<string> newMarks = new List<string>(); foreach (string id in marked) if (!existing.ContainsKey(id)) newMarks.Add(id);
                        if (newMarks.Count > 0 && String.IsNullOrWhiteSpace(reason.Text)) { MessageBox.Show("Explique por que esses cards estão incompletos.", "Motivo obrigatório", MessageBoxButtons.OK, MessageBoxIcon.Information); dialog.DialogResult = DialogResult.None; }
                    };
                    if (dialog.ShowDialog(this) != DialogResult.OK) return;
                    List<object> savedRows = new List<object>();
                    foreach (string id in marked)
                    {
                        Dictionary<string, object> old;
                        if (existing.TryGetValue(id, out old)) { savedRows.Add(old); continue; }
                        MotorCardChoice choice;
                        if (!byId.TryGetValue(id, out choice)) continue;
                        Dictionary<string, object> row = new Dictionary<string, object>();
                        row["card_id"] = id; row["estado"] = "incompleto_confirmado"; row["motivo"] = reason.Text.Trim(); row["componentes"] = new string[0]; row["evidencia"] = "marcado manualmente na janela do Extrator"; row["input_fingerprint"] = choice.Fingerprint; row["marcado_em"] = DateTime.UtcNow.ToString("o"); savedRows.Add(row);
                    }
                    // Marcações antigas sem card na fotografia atual não são apagadas por acidente.
                    foreach (KeyValuePair<string, Dictionary<string, object>> pair in existing) if (!byId.ContainsKey(pair.Key)) savedRows.Add(pair.Value);
                    Directory.CreateDirectory(stateDirectory);
                    Dictionary<string, object> envelope = new Dictionary<string, object>(); envelope["schema"] = "clubef-prontidao-motores-operador-v1"; envelope["atualizado_em"] = DateTime.UtcNow.ToString("o"); envelope["database_write"] = false; envelope["cards"] = savedRows.ToArray();
                    File.WriteAllText(overridePath, json.Serialize(envelope), new UTF8Encoding(false));
                    AppendLog("Marcações locais dos motores salvas: " + marked.Count + ". Nenhuma escrita no banco foi feita.");
                    AuxiliaryUiState uiState = BeginAuxiliaryOperation();
                    try
                    {
                        RunCommandAsync(BuildMotorRefreshCommand(), delegate(CommandResult commandResult) {
                            RestoreAuxiliaryOperation(uiState);
                            reviewMotors.Enabled = File.Exists(reviewPath);
                            if (!commandResult.Succeeded)
                            {
                                string failure = CommandFailureText(commandResult, "As marcações foram salvas, mas o relatório não pôde ser atualizado. Consulte o log.");
                                AppendLog(failure); MessageBox.Show(failure, "Uso nos motores", MessageBoxButtons.OK, MessageBoxIcon.Error); return;
                            }
                            motorProtectionManifestPath = Path.Combine(runDirectory, "protecao-motores", "manifest-seed-completude-motores.json");
                            motorProtectionSeedReady = File.Exists(motorProtectionManifestPath);
                            installMotorProtection.Enabled = motorProtectionSeedReady;
                            MessageBox.Show("Revisão atualizada. Cards marcados ficam fora do Otimizador e do Bonificador, mas continuam disponíveis para publicação. O banco não foi alterado.", "Revisão concluída", MessageBoxButtons.OK, MessageBoxIcon.Information);
                            OpenResult();
                        });
                    }
                    catch { RestoreAuxiliaryOperation(uiState); throw; }
                }
            }
            catch (Exception error) { AppendLog("Falha na revisão dos motores: " + error.Message); MessageBox.Show(error.Message, "Uso nos motores", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        private List<SelectionChoice> ReadSelectionChoices(string packagePath)
        {
            Dictionary<string, object> package = json.DeserializeObject(File.ReadAllText(packagePath, Encoding.UTF8)) as Dictionary<string, object>;
            object reviewObject, statusObject, choicesObject;
            Dictionary<string, object> review, status;
            if (package == null || !package.TryGetValue("pacote_revisao", out reviewObject) || (review = reviewObject as Dictionary<string, object>) == null ||
                !review.TryGetValue("application_status", out statusObject) || (status = statusObject as Dictionary<string, object>) == null ||
                !status.TryGetValue("selectable_items", out choicesObject)) throw new InvalidOperationException("O pacote não contém a lista de mudanças selecionáveis.");
            IEnumerable sequence = choicesObject as IEnumerable;
            if (sequence == null) throw new InvalidOperationException("A lista de mudanças selecionáveis é inválida.");
            List<SelectionChoice> result = new List<SelectionChoice>();
            foreach (object raw in sequence)
            {
                Dictionary<string, object> item = raw as Dictionary<string, object>;
                if (item == null) continue;
                string id = TextValue(item, "selecao_id"), description = TextValue(item, "descricao");
                if (!String.IsNullOrEmpty(id) && !String.IsNullOrEmpty(description)) result.Add(new SelectionChoice { Id = id, Description = description });
            }
            return result;
        }

        private void SelectApplicationItems()
        {
            if (auxiliaryCommandRunning) return;
            string basePackage = Path.Combine(Path.GetDirectoryName(resultPath), "pacote-revisao.json");
            if (!File.Exists(basePackage)) return;
            try
            {
                List<SelectionChoice> choices = ReadSelectionChoices(basePackage);
                if (choices.Count == 0) { MessageBox.Show("Não há dados novos ou alterados que possam ser enviados nesta execução.", "Seleção de envio", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
                using (Form dialog = new Form())
                {
                    dialog.Text = "Escolha exatamente o que será enviado"; dialog.StartPosition = FormStartPosition.CenterParent; dialog.MinimumSize = new Size(760, 520); dialog.Size = new Size(920, 650); dialog.Font = Font;
                    TableLayoutPanel panel = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(14), RowCount = 3, ColumnCount = 1 };
                    panel.RowStyles.Add(new RowStyle(SizeType.AutoSize)); panel.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); panel.RowStyles.Add(new RowStyle(SizeType.AutoSize)); dialog.Controls.Add(panel);
                    Label explanation = new Label { AutoSize = true, MaximumSize = new Size(850, 0), Text = "Nada vem marcado. Marque somente os dados novos ou alterados que você quer enviar. Pendências conhecidas e registros antigos continuam no relatório, mas não aparecem como dados enviáveis." }; panel.Controls.Add(explanation, 0, 0);
                    CheckedListBox list = new CheckedListBox { Dock = DockStyle.Fill, CheckOnClick = true, HorizontalScrollbar = true };
                    foreach (SelectionChoice choice in choices) list.Items.Add(choice, false); panel.Controls.Add(list, 0, 1);
                    FlowLayoutPanel buttons = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill, FlowDirection = FlowDirection.RightToLeft };
                    Button confirm = new Button { Text = "CRIAR PACOTE COM OS MARCADOS", AutoSize = true, DialogResult = DialogResult.OK };
                    Button close = new Button { Text = "CANCELAR", AutoSize = true, DialogResult = DialogResult.Cancel };
                    Button markAll = new Button { Text = "MARCAR TODOS", AutoSize = true };
                    Button clear = new Button { Text = "DESMARCAR TODOS", AutoSize = true };
                    markAll.Click += delegate { for (int i = 0; i < list.Items.Count; i++) list.SetItemChecked(i, true); };
                    clear.Click += delegate { for (int i = 0; i < list.Items.Count; i++) list.SetItemChecked(i, false); };
                    confirm.Click += delegate { if (list.CheckedItems.Count == 0) { MessageBox.Show("Marque pelo menos um item ou cancele.", "Seleção de envio", MessageBoxButtons.OK, MessageBoxIcon.Information); dialog.DialogResult = DialogResult.None; } };
                    buttons.Controls.Add(confirm); buttons.Controls.Add(close); buttons.Controls.Add(clear); buttons.Controls.Add(markAll); panel.Controls.Add(buttons, 0, 2); dialog.AcceptButton = confirm; dialog.CancelButton = close;
                    if (dialog.ShowDialog(this) != DialogResult.OK) return;
                    List<string> selectedIds = new List<string>(); foreach (object raw in list.CheckedItems) selectedIds.Add(((SelectionChoice)raw).Id);
                    string selectionPath = Path.Combine(Path.GetDirectoryName(resultPath), "selecao-operador.json");
                    Dictionary<string, object> selection = new Dictionary<string, object>(); selection["schema"] = "clubef-selecao-operador-v1"; selection["selected_ids"] = selectedIds.ToArray(); selection["database_write"] = false;
                    File.WriteAllText(selectionPath, json.Serialize(selection), new UTF8Encoding(false));
                    string expectedSelectedPackage = Path.Combine(Path.GetDirectoryName(resultPath), "pacote-selecionado.json");
                    AuxiliaryUiState uiState = BeginAuxiliaryOperation();
                    try
                    {
                        RunCommandAsync(BuildWorkerCommand("--select-review", basePackage, false, "--selection-file " + Quote(selectionPath)), delegate(CommandResult commandResult) {
                            RestoreAuxiliaryOperation(uiState);
                            if (!commandResult.Succeeded || !File.Exists(expectedSelectedPackage))
                            {
                                selectedPackagePath = null; approve.Enabled = false; apply.Enabled = false; selectItems.Enabled = selectionAvailable && File.Exists(basePackage);
                                string failure = CommandFailureText(commandResult, "Não foi possível criar o pacote selecionado. Consulte o log.");
                                AppendLog(failure); MessageBox.Show(failure, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error); return;
                            }
                            selectedPackagePath = expectedSelectedPackage; applicationReady = true; approve.Enabled = true; apply.Enabled = false;
                            stage.Text = "Etapa: " + selectedIds.Count + " item(ns) marcado(s); aguardando aprovação separada.";
                            AppendLog("Seleção salva. Itens marcados para o pacote: " + selectedIds.Count + ". Nenhuma escrita no banco foi feita.");
                            MessageBox.Show("Pacote criado somente com os " + selectedIds.Count + " item(ns) marcados. Agora revise e use APROVAR PACOTE se estiver correto.", "Seleção concluída", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        });
                    }
                    catch { RestoreAuxiliaryOperation(uiState); throw; }
                }
            }
            catch (Exception error) { AppendLog("Falha ao selecionar itens: " + error.Message); MessageBox.Show(error.Message, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        private MotorProtectionPreviewInfo ReadMotorProtectionImpact(string previewPath)
        {
            Dictionary<string, object> report = json.DeserializeObject(File.ReadAllText(previewPath, Encoding.UTF8)) as Dictionary<string, object>;
            object previewObject;
            Dictionary<string, object> preview;
            bool readOnly, wroteDatabase;
            if (report == null || TextValue(report, "schema") != "clubef-previa-instalacao-protecao-motores-v1" ||
                !(TextValue(report, "state") == "ready_for_explicit_install_or_update" || TextValue(report, "state") == "already_up_to_date") ||
                !Boolean.TryParse(TextValue(report, "transaction_read_only"), out readOnly) || !readOnly ||
                !Boolean.TryParse(TextValue(report, "database_write"), out wroteDatabase) || wroteDatabase ||
                !report.TryGetValue("preview", out previewObject) || (preview = previewObject as Dictionary<string, object>) == null)
                throw new InvalidOperationException("A prévia da proteção não contém a confirmação de somente leitura.");
            MotorProtectionPreviewInfo info = new MotorProtectionPreviewInfo();
            info.OperationMode = TextValue(preview, "operation_mode");
            info.ConfirmationSha256 = TextValue(report, "confirmation_sha256");
            if (!Regex.IsMatch(info.ConfirmationSha256, "^[0-9a-f]{64}$", RegexOptions.CultureInvariant) ||
                !(info.OperationMode == "initial_install" || info.OperationMode == "incremental_update" || info.OperationMode == "already_up_to_date"))
                throw new InvalidOperationException("A prévia não está vinculada ao estado atual do banco e do seed.");
            if (!Int64.TryParse(TextValue(preview, "results_to_invalidate"), out info.ResultsToInvalidate) || info.ResultsToInvalidate < 0)
                throw new InvalidOperationException("A prévia não informou quantos resultados atuais seriam invalidados.");
            if (!Int64.TryParse(TextValue(preview, "database_card_count"), out info.DatabaseCards) || info.DatabaseCards < 1 ||
                !Int64.TryParse(TextValue(preview, "cards_to_register"), out info.CardsToRegister) || info.CardsToRegister < 0 || info.CardsToRegister > info.DatabaseCards)
                throw new InvalidOperationException("A prévia não informou quantas cartas seriam protegidas agora.");
            if ((info.OperationMode == "already_up_to_date") != (TextValue(report, "state") == "already_up_to_date"))
                throw new InvalidOperationException("O resultado da prévia está internamente divergente.");
            return info;
        }

        private string MotorProtectionFailureText(string runDirectory, string confirmationSha256, CommandResult result)
        {
            string diagnostic = (result.StandardOutput ?? "") + "\n" + (result.StandardError ?? "");
            if (Regex.IsMatch(diagnostic, "\\\"commit_status\\\"\\s*:\\s*\\\"(?:commit_status_unknown|committed_readback_failed)\\\"", RegexOptions.CultureInvariant))
                return "O banco pode ter confirmado a proteção, mas a conferência final não terminou. NÃO tente novamente. Abra o log para auditoria; o aviso continua válido mesmo se o arquivo local de resultado não pôde ser gravado.";
            if (Regex.IsMatch(diagnostic, "\\\"commit_status\\\"\\s*:\\s*\\\"rolled_back_confirmed\\\"", RegexOptions.CultureInvariant))
                return "Uma nova conexão comprovou que toda a tentativa foi desfeita. Faça outra prévia antes de tentar novamente.";
            string reportPath = Path.Combine(runDirectory, "instalacao-protecao-motores.json");
            try
            {
                if (File.Exists(reportPath))
                {
                    Dictionary<string, object> report = json.DeserializeObject(File.ReadAllText(reportPath, Encoding.UTF8)) as Dictionary<string, object>;
                    if (report != null && TextValue(report, "confirmation_sha256") == confirmationSha256)
                    {
                        string stateValue = TextValue(report, "state");
                        if (stateValue == "commit_status_unknown" || stateValue == "committed_readback_failed")
                            return "O banco pode ter confirmado a proteção, mas a conferência final não terminou. NÃO tente novamente. Abra o log e o arquivo instalacao-protecao-motores.json para auditoria.";
                        if (stateValue == "rolled_back_confirmed_after_commit_error")
                            return "Uma nova conexão comprovou que toda a tentativa foi desfeita. Faça outra prévia antes de tentar novamente.";
                    }
                }
            }
            catch { }
            return CommandFailureText(result, "A instalação/atualização foi recusada antes do COMMIT. Consulte o log persistente.");
        }

        private void InstallProtectionForMotors()
        {
            if (auxiliaryCommandRunning || !motorProtectionSeedReady || String.IsNullOrEmpty(motorProtectionManifestPath) || !File.Exists(motorProtectionManifestPath)) return;
            string runDirectory = Path.GetDirectoryName(resultPath);
            string previewPath = Path.Combine(runDirectory, "previa-protecao-motores.json");
            AuxiliaryUiState previewUi = null;
            try
            {
                previewUi = BeginAuxiliaryOperation();
                stage.Text = "Etapa: conferindo em somente leitura o impacto atual da proteção dos motores.";
                AppendLog("Prévia da proteção dos motores iniciada em somente leitura. Nenhum dado será alterado.");
                RunCommandAsync(BuildWorkerCommand("--preview-motor-protection", motorProtectionManifestPath, false), delegate(CommandResult previewResult) {
                    RestoreAuxiliaryOperation(previewUi);
                    if (!previewResult.Succeeded || !File.Exists(previewPath))
                    {
                        string failure = CommandFailureText(previewResult, "A prévia segura da proteção foi recusada. Nada foi instalado.");
                        AppendLog(failure); MessageBox.Show(failure, "Proteção dos motores", MessageBoxButtons.OK, MessageBoxIcon.Error); return;
                    }
                    MotorProtectionPreviewInfo preview;
                    try { preview = ReadMotorProtectionImpact(previewPath); }
                    catch (Exception error) { AppendLog(error.Message); MessageBox.Show(error.Message, "Proteção dos motores", MessageBoxButtons.OK, MessageBoxIcon.Error); return; }
                    if (preview.OperationMode == "already_up_to_date")
                    {
                        motorProtectionSeedReady = false; installMotorProtection.Enabled = false;
                        stage.Text = "Etapa: proteção dos motores já corresponde às cartas conferidas.";
                        AppendLog("Prévia concluída: nenhuma carta mudou e nenhuma escrita é necessária.");
                        MessageBox.Show("A proteção já está atualizada para as " + preview.DatabaseCards + " cartas conferidas. Nada foi gravado. Publicar cartas continua independente.", "Proteção dos motores", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        return;
                    }
                    string operation = preview.OperationMode == "initial_install"
                        ? "A instalação inicial criará as travas e registrará as " + preview.CardsToRegister + " cartas conferidas."
                        : "A atualização registrará somente as " + preview.CardsToRegister + " carta(s) nova(s) ou alterada(s); a migração não será repetida.";
                    string confirmation =
                        "A prévia somente leitura confirmou o estado atual do banco.\r\n\r\n" +
                        operation + "\r\n\r\n" +
                        preview.ResultsToInvalidate + " resultado(s) atual(is) de teste serão marcados como inválidos e precisarão ser refeitos com a carta conferida. Esse número veio do banco agora; não está fixo no programa.\r\n\r\n" +
                        "A instalação protege somente o Otimizador e o Bonificador. Ela NÃO impede inserir, exibir ou publicar cartas.\r\n\r\n" +
                        "A ação, a auditoria e as cartas indicadas serão tratadas em uma única transação. Uma nova conexão fará a conferência integral. Se a resposta do COMMIT ficar incerta, o programa não permitirá uma repetição cega.\r\n\r\n" +
                        "Esta ação é separada de APLICAR PACOTE e nunca acontece automaticamente. Deseja instalar/atualizar agora?";
                    if (MessageBox.Show(confirmation, "Instalar/atualizar proteção dos motores", MessageBoxButtons.YesNo, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button2) != DialogResult.Yes)
                    {
                        AppendLog("Instalação da proteção cancelada pelo operador depois da prévia. Nenhuma escrita foi feita.");
                        return;
                    }
                    AuxiliaryUiState installUi = null;
                    try
                    {
                        installUi = BeginAuxiliaryOperation();
                        stage.Text = "Etapa: instalando/atualizando a proteção dos motores em transação única.";
                        AppendLog("Instalação/atualização explícita confirmada e vinculada à prévia " + preview.ConfirmationSha256 + ". Publicação permanece independente.");
                        string authorizationPath = CreateMotorProtectionAuthorization(runDirectory, motorProtectionManifestPath, preview.ConfirmationSha256);
                        RunCommandAsync(BuildWorkerCommand("--install-motor-protection", motorProtectionManifestPath, true, "--confirmation-sha256 " + Quote(preview.ConfirmationSha256) + " --operator-write-authorization " + Quote(authorizationPath)), delegate(CommandResult installResult) {
                            RestoreAuxiliaryOperation(installUi);
                            if (!installResult.Succeeded)
                            {
                                string failure = MotorProtectionFailureText(runDirectory, preview.ConfirmationSha256, installResult);
                                AppendLog(failure); MessageBox.Show(failure, "Proteção dos motores", MessageBoxButtons.OK, MessageBoxIcon.Error); return;
                            }
                            motorProtectionSeedReady = false; installMotorProtection.Enabled = false;
                            stage.Text = "Etapa: proteção dos motores instalada/atualizada e conferida por nova conexão.";
                            AppendLog("Proteção dos motores instalada/atualizada por ação explícita e confirmada por readback independente.");
                            MessageBox.Show("Proteção instalada/atualizada e conferida. Otimizador e Bonificador usam apenas cartas com coleta confirmada. A publicação de cartas continua independente.", "Proteção dos motores", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        });
                    }
                    catch (Exception error)
                    {
                        if (installUi != null) RestoreAuxiliaryOperation(installUi);
                        AppendLog("Não foi possível iniciar a instalação: " + error.Message);
                        MessageBox.Show(error.Message, "Proteção dos motores", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                });
            }
            catch (Exception error)
            {
                if (previewUi != null) RestoreAuxiliaryOperation(previewUi);
                AppendLog("Não foi possível iniciar a prévia da proteção: " + error.Message);
                MessageBox.Show(error.Message, "Proteção dos motores", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private ProcessStartInfo BuildWorkerCommand(string action, string package, bool enableProductiveWrite)
        {
            return BuildWorkerCommand(action, package, enableProductiveWrite, null);
        }
        private ProcessStartInfo BuildWorkerCommand(string action, string package, bool enableProductiveWrite, string extraArguments)
        {
            bool launcher; string python = FindPython(out launcher); string script = Path.Combine(root, "executor", "desktop_worker.py");
            if (String.IsNullOrEmpty(python)) throw new InvalidOperationException("Python não foi encontrado neste Windows.");
            string arguments = (launcher ? "-3 " : "") + Quote(script) + " --root " + Quote(root) + " --run-dir " + Quote(Path.GetDirectoryName(resultPath)) + " --cancel " + Quote(Path.Combine(Path.GetDirectoryName(resultPath), "CANCELAR.txt")) + " --protocol-version " + Quote(DesktopProtocolVersion) + " " + action + " " + Quote(package);
            if (!String.IsNullOrEmpty(extraArguments)) arguments += " " + extraArguments;
            ProcessStartInfo info = new ProcessStartInfo { FileName = python, Arguments = arguments, WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            info.EnvironmentVariables["PYTHONPATH"] = Path.Combine(root, "executor", "vendor");
            info.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
            if (enableProductiveWrite) info.EnvironmentVariables["CLUBEF_ENABLE_REAL_WRITE"] = "1";
            else info.EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE");
            InjectStoredDatabaseCredential(info, action != "--select-review");
            return info;
        }

        private void ApprovePackage()
        {
            if (auxiliaryCommandRunning) return;
            string package = selectedPackagePath; if (String.IsNullOrEmpty(package) || !File.Exists(package)) { MessageBox.Show("Primeiro use ESCOLHER O QUE ENVIAR e marque os itens desejados.", "Aprovação interna", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
            if (MessageBox.Show("Aprovar somente os itens marcados neste pacote? O aceite só vale se hash, fontes, contrato e seleção ainda coincidirem.", "Aprovação interna", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
            AuxiliaryUiState uiState = null;
            try
            {
                uiState = BeginAuxiliaryOperation();
                RunCommandAsync(BuildWorkerCommand("--approve-review", package, false), delegate(CommandResult commandResult) {
                    RestoreAuxiliaryOperation(uiState);
                    apply.Enabled = commandResult.Succeeded; approve.Enabled = !commandResult.Succeeded; selectItems.Enabled = !commandResult.Succeeded && selectionAvailable;
                    if (commandResult.Succeeded)
                    {
                        MessageBox.Show("Pacote selecionado aprovado. A aplicação revalidará o mesmo hash, contrato, fontes e itens marcados antes de qualquer escrita.", "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    else
                    {
                        string failure = CommandFailureText(commandResult, "Aprovação recusada com segurança.");
                        AppendLog(failure); MessageBox.Show(failure, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                });
            }
            catch (Exception error) { if (uiState != null) RestoreAuxiliaryOperation(uiState); AppendLog("Falha ao aprovar pacote: " + error.Message); MessageBox.Show(error.Message, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }
        private void ApplyPackage()
        {
            if (auxiliaryCommandRunning) return;
            string package = selectedPackagePath; if (String.IsNullOrEmpty(package) || !File.Exists(package)) return;
            if (MessageBox.Show("Aplicar exclusivamente os itens marcados e já aprovados? O worker recusará qualquer diferença de hash, fontes, contrato, seleção ou leitura de volta.", "Aplicação transacional", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
            AuxiliaryUiState uiState = null;
            try
            {
                uiState = BeginAuxiliaryOperation();
                RunCommandAsync(BuildWorkerCommand("--apply-review", package, true), delegate(CommandResult commandResult) {
                    RestoreAuxiliaryOperation(uiState);
                    if (commandResult.Succeeded)
                    {
                        apply.Enabled = false; approve.Enabled = false; selectItems.Enabled = false; stage.Text = "Etapa: pacote aplicado e confirmado por readback independente.";
                        MessageBox.Show("Pacote aplicado e confirmado por readback independente.", "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    else
                    {
                        apply.Enabled = true;
                        string failure = CommandFailureText(commandResult, "Aplicação recusada com segurança.");
                        AppendLog(failure); MessageBox.Show(failure, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                });
            }
            catch (Exception error) { if (uiState != null) RestoreAuxiliaryOperation(uiState); AppendLog("Falha ao aplicar pacote: " + error.Message); MessageBox.Show(error.Message, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }
    }
}
