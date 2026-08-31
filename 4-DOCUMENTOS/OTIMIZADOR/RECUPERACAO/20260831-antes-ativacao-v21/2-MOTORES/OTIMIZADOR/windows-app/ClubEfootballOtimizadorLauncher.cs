using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("Otimizador ClubEfootball")]
[assembly: AssemblyDescription("Painel local de execução e acompanhamento do Otimizador")]
[assembly: AssemblyProduct("Otimizador ClubEfootball")]
[assembly: AssemblyCompany("ClubEfootball")]
[assembly: AssemblyVersion("1.1.0.0")]
[assembly: AssemblyFileVersion("1.1.0.0")]

namespace ClubEfootballOtimizador
{
    internal static class Program
    {
        private const string AppUrl = "http://127.0.0.1:8767/?v=20260831-v20";
        private const string StatusUrl = "http://127.0.0.1:8767/api/saude";
        private const string ExpectedApp = "\"aplicativo\": \"otimizador_clubefootball\"";
        private const string ExpectedVersion = "\"versao_interface\": \"20260831-v20\"";

        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            try
            {
                string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
                string health = ReadHealth();
                if (!ExpectedServer(health))
                {
                    if (health != null)
                        throw new InvalidOperationException("Já existe outra versão usando a porta do Otimizador. Feche a janela antiga e abra novamente.");
                    StartHiddenServer(root);
                    WaitForServer();
                }
                if (Environment.GetEnvironmentVariable("CLUBEF_OTIMIZADOR_NO_BROWSER") == "1") return;
                string edge = FindEdge();
                if (edge == null) throw new InvalidOperationException("Microsoft Edge não foi encontrado neste Windows.");
                ProcessStartInfo browser = new ProcessStartInfo();
                browser.FileName = edge;
                browser.Arguments = "--app=\"" + AppUrl + "\" --start-maximized --no-first-run --disable-features=msEdgeSidebarV2";
                browser.WorkingDirectory = root;
                browser.UseShellExecute = false;
                browser.CreateNoWindow = true;
                Process.Start(browser);
            }
            catch (Exception error)
            {
                MessageBox.Show("Não foi possível abrir o Otimizador ClubEfootball.\n\n" + error.Message,
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
            for (int attempt = 0; attempt < 80; attempt++)
            {
                if (ServerReady()) return;
                Thread.Sleep(200);
            }
            throw new InvalidOperationException("O servidor local do Otimizador não respondeu.");
        }

        private static void StartHiddenServer(string root)
        {
            string pythonw = FindPythonW();
            if (pythonw == null) throw new InvalidOperationException("O componente interno Python não foi encontrado.");
            string script = Path.Combine(root, "interface", "servidor.py");
            if (!File.Exists(script)) throw new InvalidOperationException("interface\\servidor.py não foi encontrado.");
            ProcessStartInfo server = new ProcessStartInfo();
            server.FileName = pythonw;
            server.Arguments = "\"" + script + "\"";
            server.WorkingDirectory = root;
            server.UseShellExecute = false;
            server.CreateNoWindow = true;
            server.WindowStyle = ProcessWindowStyle.Hidden;
            server.EnvironmentVariables["CLUBEF_OTIMIZADOR_PORT"] = "8767";
            server.EnvironmentVariables["PYTHONUTF8"] = "1";
            Process.Start(server);
        }

        private static string FindPythonW()
        {
            string user = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            List<string> candidates = new List<string>();
            candidates.Add(Path.Combine(user, ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "pythonw.exe"));
            string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string programs = Path.Combine(local, "Programs", "Python");
            candidates.Add(Path.Combine(local, "Microsoft", "WindowsApps", "pythonw.exe"));
            if (Directory.Exists(programs))
            {
                string[] folders = Directory.GetDirectories(programs, "Python*");
                Array.Sort(folders); Array.Reverse(folders);
                foreach (string folder in folders) candidates.Add(Path.Combine(folder, "pythonw.exe"));
            }
            string path = Environment.GetEnvironmentVariable("PATH") ?? "";
            foreach (string folder in path.Split(Path.PathSeparator))
            {
                if (!String.IsNullOrWhiteSpace(folder)) candidates.Add(Path.Combine(folder.Trim(), "pythonw.exe"));
            }
            foreach (string candidate in candidates) if (File.Exists(candidate)) return candidate;
            return null;
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
