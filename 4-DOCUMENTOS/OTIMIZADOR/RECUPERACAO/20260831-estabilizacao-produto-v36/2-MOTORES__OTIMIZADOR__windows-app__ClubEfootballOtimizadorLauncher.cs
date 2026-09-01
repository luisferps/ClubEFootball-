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
[assembly: AssemblyVersion("1.6.4.0")]
[assembly: AssemblyFileVersion("1.6.4.0")]

namespace ClubEfootballOtimizador
{
    internal static class Program
    {
        private const int AppPort = 8769;
        private const string AppUrl = "http://127.0.0.1:8769/?v=20260831-v35";
        private const string StatusUrl = "http://127.0.0.1:8769/api/saude";
        private const string ExpectedApp = "\"aplicativo\": \"otimizador_clubefootball\"";
        private const string ExpectedVersion = "\"versao_interface\": \"20260831-v35\"";
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
            try
            {
                LauncherMutex = new Mutex(true, @"Local\ClubEfootballOtimizadorLauncherV30", out ownsMutex);
                if (!ownsMutex)
                {
                    // Outro clique durante a inicialização não pode criar um
                    // segundo serviço nem esperar em paralelo pela mesma porta.
                    if (!ExpectedServer(ReadHealth()))
                    {
                        MessageBox.Show(
                            "O Otimizador já está iniciando em segundo plano. Aguarde alguns segundos e clique novamente no mesmo ícone.",
                            "Otimizador ClubEfootball", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        return;
                    }
                    if (Environment.GetEnvironmentVariable("CLUBEF_OTIMIZADOR_NO_BROWSER") != "1") OpenBrowser(root);
                    return;
                }
                string health = ReadHealth();
                if (!ExpectedServer(health))
                {
                    if (health != null || PortaInternaOcupada())
                        throw new InvalidOperationException("A porta interna do Otimizador está ocupada por outro aplicativo. Se o ícone do Otimizador estiver perto do relógio, dê duplo clique nele para reabrir o painel. Caso contrário, a porta 8769 pertence a outro aplicativo.");
                    ValidatePackage(root);
                    StartHiddenServer(root);
                    WaitForServer();
                }
                if (Environment.GetEnvironmentVariable("CLUBEF_OTIMIZADOR_NO_BROWSER") == "1") return;
                if (!ownsMutex)
                {
                    // Uma segunda abertura só traz a janela de volta. Ela nunca
                    // cria um segundo controlador nem interfere na fila ativa.
                    OpenBrowser(root);
                    return;
                }
                TrayController controller = new TrayController(root);
                controller.OpenPanel();
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

        private static bool ServerReady()
        {
            return ExpectedServer(ReadHealth());
        }

        private static void WaitForServer()
        {
            for (int attempt = 0; attempt < 150; attempt++)
            {
                if (ServerReady()) return;
                Thread.Sleep(200);
            }
            string diagnostic;
            lock (DiagnosticLock) diagnostic = StartupDiagnostic.ToString().Trim();
            throw new InvalidOperationException("O componente interno do Otimizador não respondeu." +
                (String.IsNullOrEmpty(diagnostic) ? "" : "\n\nDetalhe técnico: " + diagnostic));
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
            string[] candidates = new string[] { Path.Combine(parent, "config.txt"), Path.Combine(root, "config.txt") };
            foreach (string candidate in candidates) if (File.Exists(candidate)) return candidate;
            return null;
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
            string config = FindConfiguration(root);
            if (String.IsNullOrEmpty(config)) throw new InvalidOperationException("A conexão local ainda não foi configurada nesta cópia. Instale config.txt uma única vez na pasta 2-MOTORES ou OTIMIZADOR.");
            string text = File.ReadAllText(config);
            if (text.IndexOf("SUPABASE_URL=", StringComparison.OrdinalIgnoreCase) < 0 ||
                text.IndexOf("SUPABASE_KEY=", StringComparison.OrdinalIgnoreCase) < 0 ||
                text.IndexOf("COLE_AQUI", StringComparison.OrdinalIgnoreCase) >= 0)
                throw new InvalidOperationException("A configuração local do Otimizador está incompleta. Atualize config.txt uma única vez.");
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
