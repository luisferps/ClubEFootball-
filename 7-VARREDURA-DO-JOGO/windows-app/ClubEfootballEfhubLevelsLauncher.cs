using System;
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

[assembly: System.Reflection.AssemblyTitle("Extrator de Níveis eFHUB")]
[assembly: System.Reflection.AssemblyDescription("Extração em lotes e atualização do clube_novo")]
[assembly: System.Reflection.AssemblyProduct("Extrator de Níveis eFHUB")]
[assembly: System.Reflection.AssemblyCompany("ClubEfootball")]
[assembly: System.Reflection.AssemblyVersion("1.0.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("1.0.0.0")]

namespace ClubEfootballEfhubLevels
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm(AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar)));
        }
    }

    internal sealed class MainForm : Form
    {
        private const string ProtocolVersion = "5.4.0";
        private const string CredentialSchema = "clubef-credencial-banco-windows-dpapi-v1";
        private static readonly byte[] CredentialEntropy = Encoding.UTF8.GetBytes("ClubEfootball Extrator V5.2 database credential");
        private readonly string root;
        private readonly JavaScriptSerializer json = new JavaScriptSerializer();
        private readonly ProgressBar progress = new ProgressBar();
        private readonly Label status = new Label();
        private readonly RichTextBox log = new RichTextBox();
        private readonly Button start = new Button(), cancel = new Button(), report = new Button(), configure = new Button(), openLog = new Button();
        private Process child;
        private string cancelPath, reportPath, logPath, currentRunDirectory;

        internal MainForm(string applicationRoot)
        {
            root = applicationRoot;
            json.MaxJsonLength = Int32.MaxValue;
            Directory.CreateDirectory(Path.Combine(root, "logs"));
            logPath = Path.Combine(root, "logs", "extrator-niveis-efhub-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".log");
            Text = "Extrator de Níveis eFHUB";
            StartPosition = FormStartPosition.CenterScreen;
            MinimumSize = new Size(820, 560);
            Size = new Size(980, 680);
            Font = new Font("Segoe UI", 10F);
            BuildLayout();
            SetStatus("Pronto para extrair todas as cartas necessárias ao Otimizador.");
            AppendLog("Aplicativo separado aberto. Nenhuma extração foi iniciada.");
            FormClosing += delegate { RequestCancel(); };
        }

        private void BuildLayout()
        {
            TableLayoutPanel layout = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(20), ColumnCount = 1, RowCount = 6 };
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            Controls.Add(layout);

            layout.Controls.Add(new Label { AutoSize = true, Font = new Font(Font.FontFamily, 18F, FontStyle.Bold), Text = "Extrator de níveis e orçamento do eFHUB" }, 0, 0);
            layout.Controls.Add(new Label { AutoSize = true, MaximumSize = new Size(900, 0), Padding = new Padding(0, 8, 0, 12),
                Text = "O programa percorre as cartas necessárias ao Otimizador na prioridade da fila. Coleta 1.000 cartas, grava níveis e orçamentos no clube_novo e confirma o lote antes de continuar." }, 0, 1);

            FlowLayoutPanel input = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill };
            input.Controls.Add(new Label { AutoSize = true, Padding = new Padding(0, 7, 0, 0), ForeColor = Color.DimGray,
                Text = "Unidade de gravação: 1.000 cartas. Esta etapa não reorganiza a fila e não altera publicações." });
            layout.Controls.Add(input, 0, 2);

            Panel progressPanel = new Panel { Height = 58, Dock = DockStyle.Fill };
            status.AutoSize = true; status.Dock = DockStyle.Top;
            progress.Dock = DockStyle.Bottom; progress.Height = 20; progress.Minimum = 0; progress.Maximum = 100;
            progressPanel.Controls.Add(status); progressPanel.Controls.Add(progress); layout.Controls.Add(progressPanel, 0, 3);

            log.Dock = DockStyle.Fill; log.ReadOnly = true; log.BackColor = Color.White; log.Font = new Font("Consolas", 9F); layout.Controls.Add(log, 0, 4);
            FlowLayoutPanel actions = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill };
            ConfigureButton(start, "EXTRAIR CARTAS DO OTIMIZADOR", delegate { StartExtraction(); });
            ConfigureButton(cancel, "CANCELAR", delegate { RequestCancel(); }); cancel.Enabled = false;
            ConfigureButton(report, "ABRIR RELATÓRIO", delegate { OpenReport(); }); report.Enabled = false;
            ConfigureButton(configure, "CONFIGURAR CONEXÃO", delegate { ConfigureConnection(); });
            ConfigureButton(openLog, "ABRIR LOG", delegate { OpenFile(logPath); });
            actions.Controls.Add(start); actions.Controls.Add(cancel); actions.Controls.Add(report); actions.Controls.Add(configure); actions.Controls.Add(openLog);
            layout.Controls.Add(actions, 0, 5);
        }

        private static void ConfigureButton(Button button, string text, EventHandler handler)
        {
            button.Text = text; button.AutoSize = true; button.Padding = new Padding(12, 6, 12, 6); button.Click += handler;
        }

        private string CredentialPath { get { return Path.Combine(root, "artefatos", "estado-operador", "credencial-banco.windows-dpapi.json"); } }

        private static string TextValue(Dictionary<string, object> source, string key)
        {
            object value; return source != null && source.TryGetValue(key, out value) && value != null ? Convert.ToString(value) : null;
        }

        private static void AssertOrdinaryFile(string path)
        {
            FileAttributes attributes = File.GetAttributes(path);
            FileInfo info = new FileInfo(path);
            if ((attributes & (FileAttributes.Directory | FileAttributes.ReparsePoint)) != 0 || info.Length <= 0 || info.Length > 131072)
                throw new InvalidOperationException("O arquivo protegido da conexão é inválido.");
        }

        private static string NormalizeConnectionString(string raw)
        {
            string value = (raw ?? "").Trim();
            Uri uri;
            if (value.Length == 0 || value.Length > 8192 || value.IndexOf('\0') >= 0 || value.IndexOf('\r') >= 0 || value.IndexOf('\n') >= 0 ||
                !Uri.TryCreate(value, UriKind.Absolute, out uri) ||
                !(String.Equals(uri.Scheme, "postgres", StringComparison.OrdinalIgnoreCase) || String.Equals(uri.Scheme, "postgresql", StringComparison.OrdinalIgnoreCase)))
                throw new InvalidOperationException("Cole uma connection string Postgres completa do botão Connect do Supabase.");
            string host = uri.Host ?? "";
            if (!(host.EndsWith(".supabase.co", StringComparison.OrdinalIgnoreCase) || host.EndsWith(".pooler.supabase.com", StringComparison.OrdinalIgnoreCase)))
                throw new InvalidOperationException("A conexão informada não pertence ao Postgres do Supabase.");
            if (String.IsNullOrEmpty(uri.UserInfo) || uri.UserInfo.IndexOf(':') < 1 || uri.UserInfo.EndsWith(":", StringComparison.Ordinal) ||
                value.IndexOf("[YOUR-PASSWORD]", StringComparison.OrdinalIgnoreCase) >= 0 || value.IndexOf("YOUR_PASSWORD", StringComparison.OrdinalIgnoreCase) >= 0)
                throw new InvalidOperationException("A connection string ainda não contém a senha atual.");
            if (uri.Port != -1 && uri.Port != 5432 && uri.Port != 6543)
                throw new InvalidOperationException("A porta não corresponde ao Postgres do Supabase.");
            Match ssl = Regex.Match(value, @"(?:\?|&)sslmode=([^&#]+)", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            if (ssl.Success)
            {
                string mode = Uri.UnescapeDataString(ssl.Groups[1].Value);
                if (!(String.Equals(mode, "require", StringComparison.OrdinalIgnoreCase) || String.Equals(mode, "verify-ca", StringComparison.OrdinalIgnoreCase) || String.Equals(mode, "verify-full", StringComparison.OrdinalIgnoreCase)))
                    throw new InvalidOperationException("A conexão precisa usar SSL seguro.");
            }
            else value += (value.IndexOf('?') >= 0 ? "&" : "?") + "sslmode=require";
            return value;
        }

        private string LoadCredential()
        {
            if (!File.Exists(CredentialPath)) throw new InvalidOperationException("A conexão ainda não foi configurada. Clique em CONFIGURAR CONEXÃO.");
            try
            {
                AssertOrdinaryFile(CredentialPath);
                Dictionary<string, object> envelope = json.DeserializeObject(File.ReadAllText(CredentialPath, Encoding.UTF8)) as Dictionary<string, object>;
                if (envelope == null || envelope.Count != 5 || TextValue(envelope, "schema") != CredentialSchema || TextValue(envelope, "protection") != "Windows DPAPI" || TextValue(envelope, "scope") != "CurrentUser")
                    throw new InvalidOperationException();
                byte[] encrypted = Convert.FromBase64String(TextValue(envelope, "ciphertext"));
                byte[] clear = ProtectedData.Unprotect(encrypted, CredentialEntropy, DataProtectionScope.CurrentUser);
                try { return NormalizeConnectionString(new UTF8Encoding(false, true).GetString(clear)); }
                finally { Array.Clear(clear, 0, clear.Length); Array.Clear(encrypted, 0, encrypted.Length); }
            }
            catch { throw new InvalidOperationException("A credencial protegida não pôde ser aberta. Configure novamente neste usuário do Windows."); }
        }

        private void SaveCredential(string dsn)
        {
            byte[] clear = Encoding.UTF8.GetBytes(NormalizeConnectionString(dsn));
            byte[] encrypted = null;
            try
            {
                encrypted = ProtectedData.Protect(clear, CredentialEntropy, DataProtectionScope.CurrentUser);
                Dictionary<string, object> envelope = new Dictionary<string, object>();
                envelope["schema"] = CredentialSchema; envelope["created_at"] = DateTime.UtcNow.ToString("o");
                envelope["protection"] = "Windows DPAPI"; envelope["scope"] = "CurrentUser"; envelope["ciphertext"] = Convert.ToBase64String(encrypted);
                string directory = Path.GetDirectoryName(CredentialPath); Directory.CreateDirectory(directory);
                string temporary = CredentialPath + ".novo-" + Guid.NewGuid().ToString("N");
                File.WriteAllText(temporary, json.Serialize(envelope), new UTF8Encoding(false));
                if (File.Exists(CredentialPath)) File.Replace(temporary, CredentialPath, null); else File.Move(temporary, CredentialPath);
            }
            finally { Array.Clear(clear, 0, clear.Length); if (encrypted != null) Array.Clear(encrypted, 0, encrypted.Length); }
        }

        private string FindPython(out bool launcher)
        {
            launcher = false;
            string cached = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "python.exe");
            if (File.Exists(cached)) return cached;
            foreach (string piece in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(Path.PathSeparator))
            {
                string folder = (piece ?? "").Trim().Trim('"'); if (folder.Length == 0) continue;
                string python = Path.Combine(folder, "python.exe"); if (File.Exists(python)) return python;
                string py = Path.Combine(folder, "py.exe"); if (File.Exists(py)) { launcher = true; return py; }
            }
            return null;
        }

        private ProcessStartInfo BuildCommand(string runDirectory, string arguments, string dsn, bool write)
        {
            bool launcher; string python = FindPython(out launcher);
            string script = Path.Combine(root, "executor", "desktop_worker.py");
            if (String.IsNullOrEmpty(python)) throw new InvalidOperationException("Python não foi encontrado neste Windows.");
            if (!File.Exists(script)) throw new InvalidOperationException("Não encontrei executor\\desktop_worker.py.");
            string common = (launcher ? "-3 " : "") + Quote(script) + " --root " + Quote(root) + " --run-dir " + Quote(runDirectory) +
                " --cancel " + Quote(Path.Combine(runDirectory, "CANCELAR.txt")) + " --protocol-version " + Quote(ProtocolVersion) + " " + arguments;
            ProcessStartInfo info = new ProcessStartInfo { FileName = python, Arguments = common, WorkingDirectory = root, UseShellExecute = false,
                CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            info.EnvironmentVariables["PYTHONPATH"] = Path.Combine(root, "executor", "vendor");
            info.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
            info.EnvironmentVariables["CLUBEF_SUPABASE_DB_URL"] = dsn;
            if (write) info.EnvironmentVariables["CLUBEF_ENABLE_REAL_WRITE"] = "1"; else info.EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE");
            return info;
        }

        private static string Quote(string value) { return "\"" + (value ?? "").Replace("\"", "\\\"") + "\""; }

        private void StartExtraction()
        {
            if (child != null && !child.HasExited) return;
            try
            {
                string dsn = LoadCredential();
                string runDirectory = Path.Combine(root, "artefatos", "efhub-niveis", "run-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N").Substring(0, 8));
                Directory.CreateDirectory(runDirectory); currentRunDirectory = runDirectory;
                cancelPath = Path.Combine(runDirectory, "CANCELAR.txt"); reportPath = Path.Combine(runDirectory, "resultado.html");
                progress.Value = 0; report.Enabled = false;
                SetRunning(true); SetStatus("Coletando cartas do Otimizador; gravação a cada lote de 1.000.");
                AppendLog("Extração do catálogo do Otimizador iniciada, em lotes transacionais de 1.000 cartas, sem preparar a fila.");
                StartChild(BuildCommand(runDirectory, "--extract-efhub-levels --efhub-all", dsn, true), true);
            }
            catch (Exception error) { AppendLog(error.Message); MessageBox.Show(error.Message, "Extrator de níveis eFHUB", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        private void ConfigureConnection()
        {
            if (child != null && !child.HasExited) return;
            string dsn;
            using (Form dialog = new Form())
            {
                dialog.Text = "Configurar conexão segura"; dialog.StartPosition = FormStartPosition.CenterParent; dialog.Size = new Size(800, 270); dialog.Font = Font;
                TableLayoutPanel panel = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(16), ColumnCount = 1, RowCount = 4 };
                panel.Controls.Add(new Label { AutoSize = true, MaximumSize = new Size(740, 0), Text = "No Supabase, copie a connection string Postgres pelo botão Connect. Ela será testada e protegida pelo Windows para este usuário." }, 0, 0);
                panel.Controls.Add(new Label { AutoSize = true, Padding = new Padding(0, 12, 0, 4), Text = "Connection string:" }, 0, 1);
                TextBox input = new TextBox { Dock = DockStyle.Top, UseSystemPasswordChar = true }; panel.Controls.Add(input, 0, 2);
                FlowLayoutPanel buttons = new FlowLayoutPanel { AutoSize = true, FlowDirection = FlowDirection.RightToLeft, Dock = DockStyle.Fill };
                Button ok = new Button { Text = "TESTAR E SALVAR", AutoSize = true, DialogResult = DialogResult.OK };
                Button close = new Button { Text = "CANCELAR", AutoSize = true, DialogResult = DialogResult.Cancel };
                buttons.Controls.Add(ok); buttons.Controls.Add(close); panel.Controls.Add(buttons, 0, 3); dialog.Controls.Add(panel); dialog.AcceptButton = ok; dialog.CancelButton = close;
                if (dialog.ShowDialog(this) != DialogResult.OK) return;
                try { dsn = NormalizeConnectionString(input.Text); } catch (Exception error) { MessageBox.Show(error.Message); return; }
                input.Clear();
            }
            try
            {
                string runDirectory = Path.Combine(root, "artefatos", "efhub-niveis", "teste-conexao-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N").Substring(0, 8));
                Directory.CreateDirectory(runDirectory);
                SetRunning(true); SetStatus("Testando a conexão em transação somente leitura.");
                StartChild(BuildCommand(runDirectory, "--test-database-connection", dsn, false), false, delegate(bool ok) {
                    if (!ok) return;
                    try { SaveCredential(dsn); SetStatus("Conexão confirmada e protegida pelo Windows."); AppendLog("Conexão testada e salva. Nenhum dado foi alterado."); }
                    catch (Exception error) { MessageBox.Show(error.Message, "Conexão", MessageBoxButtons.OK, MessageBoxIcon.Error); }
                });
            }
            catch (Exception error) { SetRunning(false); MessageBox.Show(error.Message, "Conexão", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        private void StartChild(ProcessStartInfo info, bool extraction, Action<bool> after = null)
        {
            ManualResetEvent outputClosed = new ManualResetEvent(false), errorClosed = new ManualResetEvent(false);
            Process process = new Process { StartInfo = info, EnableRaisingEvents = true }; child = process;
            process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data == null) outputClosed.Set(); else HandleLine(e.Data); };
            process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data == null) errorClosed.Set(); else AppendFromThread("ERRO | " + e.Data); };
            process.Exited += delegate {
                ThreadPool.QueueUserWorkItem(delegate {
                    process.WaitForExit(); outputClosed.WaitOne(10000); errorClosed.WaitOne(10000); int code = process.ExitCode;
                    try { BeginInvoke((MethodInvoker)delegate {
                        SetRunning(false); bool ok = code == 0;
                        if (extraction)
                        {
                            if (!File.Exists(reportPath) && Directory.Exists(currentRunDirectory))
                            {
                                string[] partialReports = Directory.GetFiles(currentRunDirectory, "resultado.html", SearchOption.AllDirectories);
                                Array.Sort(partialReports, StringComparer.OrdinalIgnoreCase);
                                if (partialReports.Length > 0) reportPath = partialReports[partialReports.Length - 1];
                            }
                            report.Enabled = File.Exists(reportPath);
                            if (ok) SetStatus("Extração concluída; todos os lotes foram gravados e conferidos.");
                            else if (File.Exists(cancelPath)) SetStatus("Cancelado. Os lotes anteriores já confirmados permanecem gravados.");
                            else SetStatus("Execução parcial ou recusada. Abra o relatório e o log.");
                        }
                        if (after != null) after(ok);
                        child = null; process.Dispose(); outputClosed.Close(); errorClosed.Close();
                    }); } catch { }
                });
            };
            try
            {
                process.Start();
                info.EnvironmentVariables.Remove("CLUBEF_SUPABASE_DB_URL");
                process.BeginOutputReadLine(); process.BeginErrorReadLine();
            }
            catch { child = null; process.Dispose(); SetRunning(false); throw; }
        }

        private void HandleLine(string line)
        {
            AppendFromThread(line);
            try
            {
                Dictionary<string, object> payload = json.DeserializeObject(line) as Dictionary<string, object>;
                if (payload == null) return;
                string type = TextValue(payload, "type");
                if (type == "progress")
                {
                    int current = Convert.ToInt32(payload.ContainsKey("current") ? payload["current"] : 0);
                    int total = Convert.ToInt32(payload.ContainsKey("total") ? payload["total"] : 0);
                    string message = TextValue(payload, "message") ?? "Coletando";
                    BeginInvoke((MethodInvoker)delegate { progress.Value = total > 0 ? Math.Max(0, Math.Min(100, (int)Math.Round(current * 100.0 / total))) : 0; SetStatus(message); });
                }
                else if (type == "batch_complete")
                {
                    BeginInvoke((MethodInvoker)delegate { SetStatus("Lote gravado e conferido; preparando o próximo."); });
                }
            }
            catch { }
        }

        private void SetRunning(bool running)
        {
            start.Enabled = !running; configure.Enabled = !running; cancel.Enabled = running;
        }

        private void RequestCancel()
        {
            try { if (child != null && !child.HasExited && !String.IsNullOrEmpty(cancelPath)) { File.WriteAllText(cancelPath, DateTime.UtcNow.ToString("o")); SetStatus("Cancelamento solicitado; aguardando o ponto seguro."); } } catch { }
        }

        private void OpenReport() { OpenFile(reportPath); }
        private static void OpenFile(string path) { if (!String.IsNullOrEmpty(path) && File.Exists(path)) Process.Start(new ProcessStartInfo { FileName = path, UseShellExecute = true }); }
        private void SetStatus(string text) { status.Text = "Estado: " + text; }

        private void AppendFromThread(string text)
        {
            try { if (IsHandleCreated) BeginInvoke((MethodInvoker)delegate { AppendLog(text); }); } catch { }
        }

        private void AppendLog(string text)
        {
            string line = DateTime.Now.ToString("HH:mm:ss") + " | " + text;
            log.AppendText(line + Environment.NewLine);
            try { File.AppendAllText(logPath, line + Environment.NewLine, new UTF8Encoding(false)); } catch { }
        }
    }
}
