using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("Otimizador ClubEfootball")]
[assembly: AssemblyDescription("Painel local de execução e acompanhamento do Otimizador")]
[assembly: AssemblyProduct("Otimizador ClubEfootball")]
[assembly: AssemblyCompany("ClubEfootball")]
[assembly: AssemblyVersion("1.7.4.0")]
[assembly: AssemblyFileVersion("1.7.4.0")]

namespace ClubEfootballOtimizador
{
    internal static class Program
    {
        private const int AppPort = 8769;
        private const string AppUrl = "http://127.0.0.1:8769/?v=20260901-v44";
        private const string StatusUrl = "http://127.0.0.1:8769/api/saude";
        private const string ExpectedApp = "\"aplicativo\": \"otimizador_clubefootball\"";
        private const string ExpectedVersion = "\"versao_interface\": \"20260901-v44\"";
        private static readonly object DiagnosticLock = new object();
        private static readonly StringBuilder StartupDiagnostic = new StringBuilder();
        private static Mutex LauncherMutex;

        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
            bool ownsMutex = false;
            StartupNotice startup = Environment.GetEnvironmentVariable("CLUBEF_OTIMIZADOR_NO_BROWSER") == "1"
                ? null : new StartupNotice();
            try
            {
                // V44 precisa poder substituir uma bandeja V43 ociosa. Se
                // compartilhassem o mesmo mutex, o novo ícone só esperaria a
                // versão antiga e nunca chegaria à verificação segura da porta.
                LauncherMutex = new Mutex(true, @"Local\ClubEfootballOtimizadorLauncherV44", out ownsMutex);
                if (!ownsMutex)
                {
                    // Outro clique durante a inicialização não cria segundo
                    // processo nem obriga o operador a clicar uma terceira vez:
                    // ele aguarda silenciosamente o primeiro abrir a porta e
                    // abre o painel por conta própria.
                    if (startup != null) startup.SetStatus("O Otimizador já está abrindo. Aguardando o painel local…");
                    if (!WaitForServer(75, startup))
                    {
                        MessageBox.Show(
                            "O Otimizador não terminou de iniciar em 15 segundos. Nenhuma fila foi iniciada. " +
                            "Confira ERRO-ABERTURA-OTIMIZADOR.txt se ele existir.",
                            "Otimizador ClubEfootball", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                        return;
                    }
                    if (Environment.GetEnvironmentVariable("CLUBEF_OTIMIZADOR_NO_BROWSER") != "1") OpenBrowser(root);
                    return;
                }
                string health = ReadHealth();
                if (!ExpectedServer(health))
                {
                    // Ao substituir o pacote, um serviço antigo e ocioso pode
                    // continuar na porta interna. O novo ícone o troca sozinho
                    // somente se ele se identifica como Otimizador e confirma
                    // que não há worker; um cálculo real nunca é interrompido.
                    if (CanReplaceIdlePreviousService(health))
                    {
                        StopPreviousIdleService();
                        Thread.Sleep(250);
                        health = ReadHealth();
                    }
                    // Uma porta aberta pode ser apenas o próprio serviço que
                    // acabou de ser lançado por um clique anterior. Esperamos
                    // alguns segundos antes de chamar isso de conflito.
                    if (!ExpectedServer(health) && PortaInternaOcupada())
                    {
                        if (startup != null) startup.SetStatus("Conferindo o serviço local já aberto…");
                        if (WaitForServer(25, startup)) health = ReadHealth();
                        else
                        {
                            health = ReadHealth();
                            if (CanReplaceIdlePreviousService(health))
                            {
                                StopPreviousIdleService();
                                Thread.Sleep(250);
                                health = ReadHealth();
                            }
                        }
                    }
                    if (!ExpectedServer(health))
                    {
                        if (health != null || PortaInternaOcupada())
                            throw new InvalidOperationException("A porta interna 8769 está em uso por outro aplicativo ou por um Otimizador com worker ativo. Nenhuma fila foi interrompida. Feche somente o outro aplicativo que usa essa porta; se o ícone do Otimizador estiver perto do relógio, dê duplo clique nele para reabrir o painel.");
                        EnsureConfiguration(root);
                        ValidatePackage(root);
                        if (startup != null) startup.SetStatus("Iniciando o componente local do Otimizador…");
                        StartHiddenServer(root);
                        if (startup != null) startup.SetStatus("Conectando o painel local…");
                        if (!WaitForServer(150, startup))
                        {
                            string diagnostic;
                            lock (DiagnosticLock) diagnostic = StartupDiagnostic.ToString().Trim();
                            throw new InvalidOperationException("O componente interno do Otimizador não respondeu." +
                                (String.IsNullOrEmpty(diagnostic) ? "" : "\n\nDetalhe técnico: " + diagnostic));
                        }
                    }
                }
                if (Environment.GetEnvironmentVariable("CLUBEF_OTIMIZADOR_NO_BROWSER") == "1") return;
                if (startup != null) startup.SetStatus("Abrindo o painel…");
                if (!ownsMutex)
                {
                    // Uma segunda abertura só traz a janela de volta. Ela nunca
                    // cria um segundo controlador nem interfere na fila ativa.
                    OpenBrowser(root);
                    return;
                }
                TrayController controller = new TrayController(root);
                controller.OpenPanel();
                // O aviso inicial só serve até o painel ser solicitado. A
                // bandeja fica viva por Application.Run, portanto deixá-lo
                // para o finally manteria "Abrindo o Otimizador" sobre uma
                // tela já aberta durante toda a sessão.
                if (startup != null)
                {
                    startup.Dispose();
                    startup = null;
                }
                Application.Run(controller);
            }
            catch (Exception error)
            {
                string message = "Não foi possível abrir o Otimizador ClubEfootball.\n\n" + error.Message;
                try { File.WriteAllText(Path.Combine(root, "ERRO-ABERTURA-OTIMIZADOR.txt"), message + Environment.NewLine); } catch { }
                MessageBox.Show(message + "\n\nO detalhe também foi salvo em ERRO-ABERTURA-OTIMIZADOR.txt.",
                    "Otimizador ClubEfootball", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                if (startup != null) startup.Dispose();
                if (ownsMutex && LauncherMutex != null)
                {
                    try { LauncherMutex.ReleaseMutex(); } catch { }
                }
            }
        }

        private static string ReadHealth()
        {
            try
            {
                HttpWebRequest request = (HttpWebRequest)WebRequest.Create(StatusUrl);
                request.Proxy = null;
                request.Timeout = 1500;
                request.ReadWriteTimeout = 1500;
                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                {
                    return reader.ReadToEnd();
                }
            }
            catch { return null; }
        }

        private static bool PortaInternaOcupada()
        {
            try
            {
                using (TcpClient client = new TcpClient())
                {
                    IAsyncResult tentativa = client.BeginConnect("127.0.0.1", AppPort, null, null);
                    if (!tentativa.AsyncWaitHandle.WaitOne(750)) return false;
                    client.EndConnect(tentativa);
                    return true;
                }
            }
            catch { return false; }
        }

        private static bool ExpectedServer(string status)
        {
            if (status == null) return false;
            bool ok = status.Contains("\"ok\": true") || status.Contains("\"ok\":true");
            return ok && status.Contains(ExpectedApp) && status.Contains(ExpectedVersion);
        }

        private static bool CanReplaceIdlePreviousService(string status)
        {
            if (String.IsNullOrEmpty(status) || !status.Contains(ExpectedApp)) return false;
            return status.Contains("\"worker_ativo\": false") || status.Contains("\"worker_ativo\":false");
        }

        private static void StopPreviousIdleService()
        {
            foreach (Process process in Process.GetProcessesByName("OtimizadorServico"))
            {
                try
                {
                    // Esta rotina só é chamada depois de a própria porta 8769
                    // se identificar como Otimizador e afirmar worker_ativo=false.
                    // Assim ela pode trocar uma cópia antiga em outra pasta,
                    // mas jamais toca um cálculo em curso.
                    process.Kill();
                    process.WaitForExit(3000);
                }
                catch { }
            }
            foreach (Process process in Process.GetProcessesByName("Otimizador ClubEfootball"))
            {
                try
                {
                    // A cópia anterior pode manter somente o ícone da bandeja
                    // depois da troca do pacote. A porta já confirmou que não
                    // existe worker, e jamais encerramos o próprio lançador.
                    if (process.Id == Process.GetCurrentProcess().Id) continue;
                    process.Kill();
                    process.WaitForExit(3000);
                }
                catch { }
            }
        }

        private static bool ServerReady()
        {
            return ExpectedServer(ReadHealth());
        }

        private static bool WaitForServer(int attempts, StartupNotice startup = null)
        {
            for (int attempt = 0; attempt < attempts; attempt++)
            {
                if (ServerReady()) return true;
                if (startup != null) startup.Pump();
                Thread.Sleep(200);
            }
            return false;
        }

        private static void StartHiddenServer(string root)
        {
            string service = Path.Combine(root, "runtime", "OtimizadorServico.exe");
            if (!File.Exists(service)) throw new InvalidOperationException("O componente interno portátil não foi encontrado. Reinstale a pasta completa do Otimizador.");
            ProcessStartInfo server = new ProcessStartInfo();
            server.FileName = service;
            server.WorkingDirectory = root;
            server.UseShellExecute = false;
            server.CreateNoWindow = true;
            server.WindowStyle = ProcessWindowStyle.Hidden;
            server.RedirectStandardOutput = true;
            server.RedirectStandardError = true;
            server.EnvironmentVariables["CLUBEF_OTIMIZADOR_ROOT"] = root;
            server.EnvironmentVariables["CLUBEF_OTIMIZADOR_PORT"] = AppPort.ToString();
            server.EnvironmentVariables["PYTHONUTF8"] = "1";
            lock (DiagnosticLock) StartupDiagnostic.Clear();
            Process process = new Process();
            process.StartInfo = server;
            process.OutputDataReceived += RecordServiceDiagnostic;
            process.ErrorDataReceived += RecordServiceDiagnostic;
            if (!process.Start()) throw new InvalidOperationException("Não foi possível iniciar o componente interno portátil.");
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
        }

        private static void RecordServiceDiagnostic(object sender, DataReceivedEventArgs eventArgs)
        {
            if (String.IsNullOrWhiteSpace(eventArgs.Data)) return;
            lock (DiagnosticLock)
            {
                if (StartupDiagnostic.Length < 1400) StartupDiagnostic.AppendLine(eventArgs.Data);
            }
        }

        private static string FindConfiguration(string root)
        {
            string parent = Directory.GetParent(root).FullName;
            string[] candidates = new string[] { Path.Combine(root, "config.txt"), Path.Combine(parent, "config.txt") };
            foreach (string candidate in candidates) if (File.Exists(candidate)) return candidate;
            return null;
        }

        private static bool IsConfigurationValid(string config)
        {
            if (String.IsNullOrEmpty(config) || !File.Exists(config)) return false;
            try
            {
                string text = File.ReadAllText(config);
                return text.IndexOf("SUPABASE_URL=", StringComparison.OrdinalIgnoreCase) >= 0 &&
                    text.IndexOf("SUPABASE_KEY=", StringComparison.OrdinalIgnoreCase) >= 0 &&
                    text.IndexOf("COLE_AQUI", StringComparison.OrdinalIgnoreCase) < 0;
            }
            catch { return false; }
        }

        private static string ConfigurationValue(string config, string name)
        {
            if (String.IsNullOrEmpty(config) || !File.Exists(config)) return "";
            try
            {
                foreach (string raw in File.ReadAllLines(config))
                {
                    string line = raw.Trim();
                    if (line.StartsWith(name + "=", StringComparison.OrdinalIgnoreCase))
                        return line.Substring(name.Length + 1).Trim();
                }
            }
            catch { }
            return "";
        }

        private static void EnsureConfiguration(string root)
        {
            string existing = FindConfiguration(root);
            if (IsConfigurationValid(existing)) return;

            string target = Path.Combine(root, "config.txt");
            string initialUrl = ConfigurationValue(existing, "SUPABASE_URL");
            using (Form dialog = new Form())
            {
                dialog.Text = "Configurar conexão do Otimizador";
                dialog.StartPosition = FormStartPosition.CenterScreen;
                dialog.FormBorderStyle = FormBorderStyle.FixedDialog;
                dialog.MaximizeBox = false;
                dialog.MinimizeBox = false;
                dialog.ClientSize = new Size(540, 270);

                Label title = new Label { Left = 22, Top = 18, Width = 495, Height = 42,
                    Text = "Esta cópia ainda não tem conexão local. Cole uma vez a URL e a chave do Supabase. Elas ficam somente neste computador e nunca vão para o navegador.",
                    AutoSize = false };
                Label urlLabel = new Label { Left = 22, Top = 78, Width = 150, Text = "URL do Supabase" };
                TextBox url = new TextBox { Left = 22, Top = 99, Width = 495, Text = initialUrl };
                Label keyLabel = new Label { Left = 22, Top = 135, Width = 240, Text = "Chave privada do aplicativo" };
                TextBox key = new TextBox { Left = 22, Top = 156, Width = 495, UseSystemPasswordChar = true };
                Label hint = new Label { Left = 22, Top = 188, Width = 495, Height = 28,
                    Text = "Depois de salvar, este mesmo ícone abre com um clique. O arquivo config.txt não é publicado no GitHub.",
                    AutoSize = false };
                Button cancel = new Button { Left = 328, Top = 228, Width = 88, Text = "Cancelar", DialogResult = DialogResult.Cancel };
                Button save = new Button { Left = 429, Top = 228, Width = 88, Text = "Salvar", DialogResult = DialogResult.None };
                save.Click += delegate
                {
                    string connectionUrl = url.Text.Trim().TrimEnd('/');
                    string connectionKey = key.Text.Trim();
                    if (!connectionUrl.StartsWith("https://", StringComparison.OrdinalIgnoreCase) || String.IsNullOrWhiteSpace(connectionKey) || connectionKey.IndexOf("COLE_AQUI", StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        MessageBox.Show("Informe uma URL https:// válida e uma chave não vazia.", "Configuração local", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                        return;
                    }
                    try
                    {
                        File.WriteAllText(target, "SUPABASE_URL=" + connectionUrl + Environment.NewLine + "SUPABASE_KEY=" + connectionKey + Environment.NewLine, new UTF8Encoding(false));
                        dialog.DialogResult = DialogResult.OK;
                    }
                    catch (Exception error)
                    {
                        MessageBox.Show("Não foi possível guardar a configuração local.\n\n" + error.Message, "Configuração local", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                };
                dialog.Controls.Add(title); dialog.Controls.Add(urlLabel); dialog.Controls.Add(url);
                dialog.Controls.Add(keyLabel); dialog.Controls.Add(key); dialog.Controls.Add(hint);
                dialog.Controls.Add(cancel); dialog.Controls.Add(save);
                dialog.AcceptButton = save;
                dialog.CancelButton = cancel;
                if (dialog.ShowDialog() != DialogResult.OK)
                    throw new InvalidOperationException("A conexão local não foi configurada. Nenhuma fila foi iniciada.");
            }
            if (!IsConfigurationValid(target))
                throw new InvalidOperationException("A configuração local não pôde ser validada. Nenhuma fila foi iniciada.");
        }

        private static void ValidatePackage(string root)
        {
            string[] required = new string[] {
                Path.Combine(root, "runtime", "OtimizadorServico.exe"),
                Path.Combine(root, "interface", "servidor.py"),
                Path.Combine(root, "interface", "index.html"),
                Path.Combine(root, "interface", "app.js"),
                Path.Combine(root, "interface", "style.css")
            };
            foreach (string file in required)
                if (!File.Exists(file)) throw new InvalidOperationException("O pacote está incompleto. Copie a pasta OTIMIZADOR inteira, inclusive runtime e interface.");
            if (!Directory.Exists(Path.Combine(root, "runtime", "_internal")))
                throw new InvalidOperationException("O runtime portátil está incompleto. Copie a pasta runtime inteira, inclusive a pasta _internal.");
            string config = FindConfiguration(root);
            if (!IsConfigurationValid(config))
                throw new InvalidOperationException("A conexão local do Otimizador está incompleta. Nenhuma fila foi iniciada.");
        }

        private static void OpenBrowser(string root)
        {
            string edge = FindEdge();
            if (edge != null)
            {
                ProcessStartInfo browser = new ProcessStartInfo();
                browser.FileName = edge;
                browser.Arguments = "--app=\"" + AppUrl + "\" --start-maximized --no-first-run --disable-features=msEdgeSidebarV2";
                browser.WorkingDirectory = root;
                browser.UseShellExecute = false;
                browser.CreateNoWindow = true;
                Process.Start(browser);
                return;
            }
            Process.Start(new ProcessStartInfo { FileName = AppUrl, UseShellExecute = true });
        }

        private static string FindEdge()
        {
            string x86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
            string x64 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
            string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string[] candidates = new string[] {
                Path.Combine(x86, "Microsoft", "Edge", "Application", "msedge.exe"),
                Path.Combine(x64, "Microsoft", "Edge", "Application", "msedge.exe"),
                Path.Combine(local, "Microsoft", "Edge", "Application", "msedge.exe")
            };
            foreach (string candidate in candidates) if (File.Exists(candidate)) return candidate;
            return null;
        }

        /// <summary>
        /// Retorno visual imediato no primeiro clique. Não tem controles de
        /// fila e não executa trabalho: só evita que a inicialização silenciosa
        /// seja confundida com um ícone que não funcionou.
        /// </summary>
        private sealed class StartupNotice : IDisposable
        {
            private readonly Form form;
            private readonly Label status;

            internal StartupNotice()
            {
                form = new Form();
                form.Text = "Otimizador ClubEfootball";
                form.StartPosition = FormStartPosition.CenterScreen;
                form.FormBorderStyle = FormBorderStyle.FixedDialog;
                form.ControlBox = false;
                form.MaximizeBox = false;
                form.MinimizeBox = false;
                form.ShowInTaskbar = true;
                form.ClientSize = new Size(420, 125);
                Label title = new Label { Left = 20, Top = 20, Width = 375, Height = 28,
                    Text = "Abrindo o Otimizador", Font = new Font(SystemFonts.MessageBoxFont, FontStyle.Bold) };
                status = new Label { Left = 20, Top = 60, Width = 375, Height = 42,
                    Text = "Preparando o painel local…", AutoSize = false };
                form.Controls.Add(title);
                form.Controls.Add(status);
                form.Show();
                Pump();
            }

            internal void SetStatus(string text)
            {
                status.Text = text;
                Pump();
            }

            internal void Pump()
            {
                if (form.IsDisposed) return;
                form.Refresh();
                Application.DoEvents();
            }

            public void Dispose()
            {
                if (form.IsDisposed) return;
                form.Close();
                form.Dispose();
            }
        }

        /// <summary>
        /// Controlador persistente na bandeja do Windows. Fechar o navegador
        /// apenas esconde o painel: este ícone continua mostrando se o worker
        /// deste computador está ativo e permite reabrir a mesma tela.
        /// </summary>
        private sealed class TrayController : ApplicationContext
        {
            private readonly string root;
            private readonly NotifyIcon tray;
            private readonly System.Windows.Forms.Timer refreshTimer;
            private readonly ToolStripMenuItem stateItem;
            private string lastSummary;

            internal TrayController(string applicationRoot)
            {
                root = applicationRoot;
                ContextMenuStrip menu = new ContextMenuStrip();
                ToolStripMenuItem openItem = new ToolStripMenuItem("Abrir painel do Otimizador");
                openItem.Click += delegate { OpenPanel(); };
                stateItem = new ToolStripMenuItem("Estado: verificando o serviço local");
                stateItem.Enabled = false;
                ToolStripMenuItem refreshItem = new ToolStripMenuItem("Atualizar estado");
                refreshItem.Click += delegate { RefreshStatus(); };
                ToolStripMenuItem hintItem = new ToolStripMenuItem("Fechar a janela não interrompe a fila");
                hintItem.Enabled = false;
                menu.Items.Add(openItem);
                menu.Items.Add(new ToolStripSeparator());
                menu.Items.Add(stateItem);
                menu.Items.Add(refreshItem);
                menu.Items.Add(new ToolStripSeparator());
                menu.Items.Add(hintItem);

                tray = new NotifyIcon();
                try { tray.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath) ?? SystemIcons.Application; }
                catch { tray.Icon = SystemIcons.Application; }
                tray.Visible = true;
                tray.ContextMenuStrip = menu;
                tray.Text = "Otimizador · verificando serviço local";
                tray.DoubleClick += delegate { OpenPanel(); };

                refreshTimer = new System.Windows.Forms.Timer();
                refreshTimer.Interval = 2000;
                refreshTimer.Tick += delegate { RefreshStatus(); };
                RefreshStatus();
                refreshTimer.Start();
                tray.ShowBalloonTip(
                    7000,
                    "Otimizador em segundo plano",
                    "Fechar a janela apenas esconde o painel. O ícone perto do relógio mostra o estado e reabre o Otimizador.",
                    ToolTipIcon.Info);
            }

            internal void OpenPanel()
            {
                OpenBrowser(root);
            }

            private void RefreshStatus()
            {
                string health = ReadHealth();
                if (!ExpectedServer(health))
                {
                    SetStatus("Servidor local indisponível", SystemIcons.Error);
                    return;
                }
                bool workerActive = ReadJsonBoolean(health, "worker_ativo");
                string summary = ReadJsonString(health, "worker_resumo");
                if (String.IsNullOrWhiteSpace(summary))
                    summary = workerActive ? "Worker local ativo" : "Servidor local ativo · nenhum worker local";
                SetStatus(summary, workerActive ? SystemIcons.Information : SystemIcons.Application);
            }

            private void SetStatus(string summary, Icon icon)
            {
                summary = String.IsNullOrWhiteSpace(summary) ? "Estado local não informado" : summary.Trim();
                tray.Icon = icon;
                tray.Text = CompactTooltip("Otimizador · " + summary);
                stateItem.Text = "Estado: " + summary;
                if (!String.Equals(lastSummary, summary, StringComparison.Ordinal))
                {
                    lastSummary = summary;
                    // O balão é informativo e não representa decisão de pausa,
                    // parada ou recuperação da fila.
                    if (summary.IndexOf("indisponível", StringComparison.OrdinalIgnoreCase) >= 0)
                        tray.ShowBalloonTip(5000, "Otimizador", summary, ToolTipIcon.Warning);
                }
            }

            private static string CompactTooltip(string value)
            {
                const int maximum = 63;
                return value.Length <= maximum ? value : value.Substring(0, maximum - 1) + "…";
            }

            private static bool ReadJsonBoolean(string json, string property)
            {
                if (String.IsNullOrEmpty(json)) return false;
                return Regex.IsMatch(
                    json,
                    "\"" + Regex.Escape(property) + "\"\\s*:\\s*true",
                    RegexOptions.IgnoreCase);
            }

            private static string ReadJsonString(string json, string property)
            {
                if (String.IsNullOrEmpty(json)) return null;
                Match match = Regex.Match(
                    json,
                    "\"" + Regex.Escape(property) + "\"\\s*:\\s*\"(?<value>(?:\\\\.|[^\"])*)\"");
                if (!match.Success) return null;
                try { return Regex.Unescape(match.Groups["value"].Value); }
                catch { return match.Groups["value"].Value; }
            }

            protected override void ExitThreadCore()
            {
                refreshTimer.Stop();
                refreshTimer.Dispose();
                tray.Visible = false;
                tray.Dispose();
                base.ExitThreadCore();
            }
        }
    }
}
