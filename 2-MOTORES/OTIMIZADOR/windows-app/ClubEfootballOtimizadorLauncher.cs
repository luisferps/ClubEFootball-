using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("Otimizador ClubEfootball")]
[assembly: AssemblyDescription("Painel local de execução e acompanhamento do Otimizador")]
[assembly: AssemblyProduct("Otimizador ClubEfootball")]
[assembly: AssemblyCompany("ClubEfootball")]
[assembly: AssemblyVersion("1.4.0.0")]
[assembly: AssemblyFileVersion("1.4.0.0")]

namespace ClubEfootballOtimizador
{
    internal static class Program
    {
        private const int AppPort = 8769;
        private const string AppUrl = "http://127.0.0.1:8769/?v=20260831-v25";
        private const string StatusUrl = "http://127.0.0.1:8769/api/saude";
        private const string ExpectedApp = "\"aplicativo\": \"otimizador_clubefootball\"";
        private const string ExpectedVersion = "\"versao_interface\": \"20260831-v25\"";
        private static readonly object DiagnosticLock = new object();
        private static readonly StringBuilder StartupDiagnostic = new StringBuilder();

        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
            try
            {
                string health = ReadHealth();
                if (!ExpectedServer(health))
                {
                    if (health != null)
                        throw new InvalidOperationException("A porta interna do Otimizador está ocupada por outro aplicativo. Feche somente a outra janela do Otimizador e clique novamente neste ícone.");
                    ValidatePackage(root);
                    StartHiddenServer(root);
                    WaitForServer();
                }
                if (Environment.GetEnvironmentVariable("CLUBEF_OTIMIZADOR_NO_BROWSER") == "1") return;
                OpenBrowser(root);
            }
            catch (Exception error)
            {
                string message = "Não foi possível abrir o Otimizador ClubEfootball.\n\n" + error.Message;
                try { File.WriteAllText(Path.Combine(root, "ERRO-ABERTURA-OTIMIZADOR.txt"), message + Environment.NewLine); } catch { }
                MessageBox.Show(message + "\n\nO detalhe também foi salvo em ERRO-ABERTURA-OTIMIZADOR.txt.",
                    "Otimizador ClubEfootball", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private static string ReadHealth()
        {
            try
            {
                using (WebClient client = new WebClient())
                {
                    client.Proxy = null;
                    return client.DownloadString(StatusUrl);
                }
            }
            catch { return null; }
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
    }
}
