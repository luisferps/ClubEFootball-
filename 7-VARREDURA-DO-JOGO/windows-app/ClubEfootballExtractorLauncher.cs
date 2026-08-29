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
[assembly: AssemblyVersion("4.6.2.0")]
[assembly: AssemblyFileVersion("4.6.2.0")]

namespace ClubEfootballWindowsApp
{
    internal static class Program
    {
        private const int AppPort = 8767;
        private const string AppUrl = "http://127.0.0.1:8767/Extrator-ClubEfootball.html";
        private const string StatusUrl = "http://127.0.0.1:8767/api/status";

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
            throw new InvalidOperationException("O executor local V4.6.2 não respondeu. A instalação pode estar incompleta.");
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

            string programData = Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData);
            if (String.IsNullOrWhiteSpace(programData)) programData = @"C:\ProgramData";
            string programFilesX86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
            if (String.IsNullOrWhiteSpace(programFilesX86)) programFilesX86 = @"C:\Program Files (x86)";
            string programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
            if (String.IsNullOrWhiteSpace(programFiles)) programFiles = @"C:\Program Files";

            string downloadRoot = Path.Combine(programData, "KONAMI", "eFootball", "ST", "Download");
            string steamRootX86 = Path.Combine(programFilesX86, "Steam", "steamapps", "common", "eFootball");
            string steamRoot64 = Path.Combine(programFiles, "Steam", "steamapps", "common", "eFootball");

            string dt870Updated = FindSource(downloadRoot, "dt870_console_win.cpk");
            string dt200 = FindSourceInSteam(steamRootX86, steamRoot64, "dt200_console_all.cpk");
            string dt870Original = FindSourceInSteam(steamRootX86, steamRoot64, "dt870_console_win.cpk");
            string dt261Bra = FindSourceInSteam(steamRootX86, steamRoot64, "dt261_bra_console_win.cpk");

            ProcessStartInfo server = new ProcessStartInfo();
            server.FileName = pythonw;
            server.Arguments = "\"" + script + "\" --no-browser";
            server.WorkingDirectory = root;
            server.UseShellExecute = false;
            server.CreateNoWindow = true;
            server.WindowStyle = ProcessWindowStyle.Hidden;
            server.EnvironmentVariables["PYTHONPATH"] = vendor;
            server.EnvironmentVariables["CLUBEF_EXTRACTOR_PORT"] = AppPort.ToString();
            SetIfFound(server, "CLUBEF_SOURCE_DT870_UPDATED", dt870Updated);
            SetIfFound(server, "CLUBEF_SOURCE_DT200", dt200);
            SetIfFound(server, "CLUBEF_SOURCE_DT870_ORIGINAL", dt870Original);
            SetIfFound(server, "CLUBEF_SOURCE_DT261_BRA", dt261Bra);
            server.EnvironmentVariables.Remove("CLUBEF_SUPABASE_DB_URL");
            server.EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE");
            Process.Start(server);
        }

        private static void SetIfFound(ProcessStartInfo server, string variable, string value)
        {
            if (!String.IsNullOrWhiteSpace(value) && File.Exists(value))
                server.EnvironmentVariables[variable] = value;
            else
                server.EnvironmentVariables.Remove(variable);
        }

        private static string FindSourceInSteam(string rootX86, string root64, string filename)
        {
            string found = FindSource(rootX86, filename);
            if (!String.IsNullOrWhiteSpace(found)) return found;
            return FindSource(root64, filename);
        }

        private static string FindSource(string root, string filename)
        {
            try
            {
                if (String.IsNullOrWhiteSpace(root) || !Directory.Exists(root)) return null;

                string direct = Path.Combine(root, filename);
                if (File.Exists(direct)) return direct;

                string cpk = Path.Combine(root, "cpk", filename);
                if (File.Exists(cpk)) return cpk;

                string[] matches = Directory.GetFiles(root, filename, SearchOption.AllDirectories);
                if (matches != null && matches.Length > 0)
                {
                    Array.Sort(matches, delegate(string a, string b)
                    {
                        return File.GetLastWriteTimeUtc(b).CompareTo(File.GetLastWriteTimeUtc(a));
                    });
                    return matches[0];
                }
            }
            catch
            {
                // Se uma subpasta negar acesso, o servidor ainda possui seu fallback próprio.
            }
            return null;
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
