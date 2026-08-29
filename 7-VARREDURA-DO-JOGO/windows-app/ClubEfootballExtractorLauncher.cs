using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("Extrator eFootball")]
[assembly: AssemblyDescription("Busca e extração local de dados de futebol")]
[assembly: AssemblyProduct("Extrator eFootball")]
[assembly: AssemblyCompany("ClubEfootball")]
[assembly: AssemblyVersion("4.6.3.0")]
[assembly: AssemblyFileVersion("4.6.3.0")]

namespace ClubEfootballWindowsApp
{
    internal static class Program
    {
        // Porta própria desta compilação para impedir que um processo antigo
        // ainda vivo seja reutilizado. O launcher NÃO decide fontes físicas:
        // a descoberta automática pertence ao núcleo do Extrator.
        private const int AppPort = 8768;
        private const string AppUrl = "http://127.0.0.1:8768/Extrator-ClubEfootball.html";
        private const string StatusUrl = "http://127.0.0.1:8768/api/status";

        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            try
            {
                string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
                if (!ServerReady())
                {
                    StartHiddenExecutor(root);
                    WaitForServer();
                }

                string edge = FindEdge();
                if (edge == null)
                {
                    throw new InvalidOperationException("Microsoft Edge não foi encontrado neste Windows.");
                }

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
                MessageBox.Show(
                    "Não foi possível abrir o Extrator eFootball.\n\n" + error.Message,
                    "Extrator eFootball",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }

        private static bool ServerReady()
        {
            try
            {
                using (WebClient client = new WebClient())
                {
                    client.Proxy = null;
                    string status = client.DownloadString(StatusUrl);
                    return status.Contains("\"online\": true") || status.Contains("\"online\":true");
                }
            }
            catch
            {
                return false;
            }
        }

        private static void WaitForServer()
        {
            for (int attempt = 0; attempt < 80; attempt++)
            {
                if (ServerReady()) return;
                Thread.Sleep(200);
            }
            throw new InvalidOperationException("O executor local V4.6.3 não respondeu. A instalação pode estar incompleta.");
        }

        private static void StartHiddenExecutor(string root)
        {
            string pythonw = FindPythonW();
            if (pythonw == null)
            {
                throw new InvalidOperationException("O componente interno Python não foi encontrado.");
            }

            string script = Path.Combine(root, "executor", "servidor_v46.py");
            string vendor = Path.Combine(root, "executor", "vendor");
            if (!File.Exists(script))
            {
                throw new InvalidOperationException("executor\\servidor_v46.py não foi encontrado.");
            }

            ProcessStartInfo server = new ProcessStartInfo();
            server.FileName = pythonw;
            server.Arguments = "\"" + script + "\" --no-browser";
            server.WorkingDirectory = root;
            server.UseShellExecute = false;
            server.CreateNoWindow = true;
            server.WindowStyle = ProcessWindowStyle.Hidden;
            server.EnvironmentVariables["PYTHONPATH"] = vendor;
            server.EnvironmentVariables["CLUBEF_EXTRACTOR_PORT"] = AppPort.ToString();
            // O launcher não aponta DT870/DT200/textos. O executor original
            // usa ProgramData/Steam e só cai no seletor manual se a fonte não existir.
            server.EnvironmentVariables.Remove("CLUBEF_SOURCE_DT870_UPDATED");
            server.EnvironmentVariables.Remove("CLUBEF_SOURCE_DT200");
            server.EnvironmentVariables.Remove("CLUBEF_SOURCE_DT870_ORIGINAL");
            server.EnvironmentVariables.Remove("CLUBEF_SOURCE_DT261_BRA");
            server.EnvironmentVariables.Remove("CLUBEF_SUPABASE_DB_URL");
            server.EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE");
            Process.Start(server);
        }

        private static string FindPythonW()
        {
            string user = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            List<string> candidates = new List<string>();
            candidates.Add(Path.Combine(user, ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "pythonw.exe"));

            string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string programs = Path.Combine(local, "Programs", "Python");
            if (Directory.Exists(programs))
            {
                string[] folders = Directory.GetDirectories(programs, "Python*");
                Array.Sort(folders);
                Array.Reverse(folders);
                foreach (string folder in folders) candidates.Add(Path.Combine(folder, "pythonw.exe"));
            }

            foreach (string candidate in candidates)
            {
                if (File.Exists(candidate)) return candidate;
            }
            return null;
        }

        private static string FindEdge()
        {
            string programFilesX86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
            string programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
            string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string[] candidates = new string[]
            {
                Path.Combine(programFilesX86, "Microsoft", "Edge", "Application", "msedge.exe"),
                Path.Combine(programFiles, "Microsoft", "Edge", "Application", "msedge.exe"),
                Path.Combine(local, "Microsoft", "Edge", "Application", "msedge.exe")
            };
            foreach (string candidate in candidates)
            {
                if (File.Exists(candidate)) return candidate;
            }
            return null;
        }
    }
}
