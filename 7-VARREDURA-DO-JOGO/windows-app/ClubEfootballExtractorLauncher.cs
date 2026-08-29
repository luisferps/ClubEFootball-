using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("Extrator eFootball")]
[assembly: AssemblyDescription("Busca e extração local de dados de futebol")]
[assembly: AssemblyProduct("Extrator eFootball")]
[assembly: AssemblyCompany("ClubEfootball")]
[assembly: AssemblyVersion("4.6.12.0")]
[assembly: AssemblyFileVersion("4.6.12.0")]

namespace ClubEfootballWindowsApp
{
    internal static class Program
    {
        private const int AppPort = 8776;
        private const string RuntimeVersion = "4.6.12";
        private const string AppUrl = "http://127.0.0.1:8776/Extrator-ClubEfootball.html?v=4.6.12";
        private const string StatusUrl = "http://127.0.0.1:8776/api/runtime-version";

        private static readonly object LogLock = new object();
        private static string LogPath = null;
        private static Process ServerProcess = null;

        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
            InitializeLog(root);
            Log("=== Extrator eFootball V" + RuntimeVersion + " iniciado ===");
            Log("Diretório raiz: " + root);
            Log("Porta exclusiva desta versão: " + AppPort);

            try
            {
                if (!ServerReady())
                {
                    Log("Runtime V" + RuntimeVersion + " ainda não está disponível; iniciando executor Python.");
                    StartHiddenExecutor(root);
                    WaitForServer();
                }
                else
                {
                    Log("Runtime V" + RuntimeVersion + " já estava disponível na porta " + AppPort + ".");
                }

                string edge = FindEdge();
                if (edge == null)
                {
                    throw new InvalidOperationException("Microsoft Edge não foi encontrado neste Windows.");
                }

                Log("Microsoft Edge: " + edge);
                ProcessStartInfo browser = new ProcessStartInfo();
                browser.FileName = edge;
                browser.Arguments = "--app=\"" + AppUrl + "\" --start-maximized --no-first-run --disable-http-cache --disable-features=msEdgeSidebarV2";
                browser.WorkingDirectory = root;
                browser.UseShellExecute = false;
                browser.CreateNoWindow = true;
                Process.Start(browser);
                Log("Interface V" + RuntimeVersion + " aberta em " + AppUrl);
            }
            catch (Exception error)
            {
                Log("FALHA NO LAUNCHER: " + error);
                MessageBox.Show(
                    "Não foi possível abrir o Extrator eFootball.\n\n" +
                    error.Message +
                    "\n\nLog de diagnóstico:\n" + LogPath,
                    "Extrator eFootball",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }

        private static void InitializeLog(string root)
        {
            try
            {
                string logs = Path.Combine(root, "logs");
                Directory.CreateDirectory(logs);
                LogPath = Path.Combine(logs, "extrator-v46.log");
            }
            catch
            {
                LogPath = Path.Combine(Path.GetTempPath(), "extrator-v46.log");
            }
        }

        private static void Log(string message)
        {
            if (String.IsNullOrEmpty(LogPath)) return;
            try
            {
                lock (LogLock)
                {
                    string line = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff") + " | LAUNCHER | " + message + Environment.NewLine;
                    File.AppendAllText(LogPath, line, new UTF8Encoding(false));
                }
            }
            catch
            {
                // O log nunca deve derrubar o aplicativo.
            }
        }

        private static bool ServerReady()
        {
            try
            {
                using (WebClient client = new WebClient())
                {
                    client.Proxy = null;
                    client.Headers[HttpRequestHeader.CacheControl] = "no-cache";
                    string status = client.DownloadString(StatusUrl + "?t=" + DateTime.UtcNow.Ticks);
                    bool online = status.Contains("\"online\": true") || status.Contains("\"online\":true");
                    bool version = status.Contains("\"version\": \"" + RuntimeVersion + "\"") ||
                                   status.Contains("\"version\":\"" + RuntimeVersion + "\"");
                    if (!online || !version)
                    {
                        Log("Resposta de runtime incompatível: " + status);
                    }
                    return online && version;
                }
            }
            catch (Exception error)
            {
                Log("Runtime V" + RuntimeVersion + " indisponível: " + error.Message);
                return false;
            }
        }

        private static void WaitForServer()
        {
            for (int attempt = 0; attempt < 200; attempt++)
            {
                if (ServerReady())
                {
                    Log("Runtime V" + RuntimeVersion + " respondeu após " + (attempt + 1) + " tentativa(s).");
                    return;
                }

                if (ServerProcess != null)
                {
                    try
                    {
                        if (ServerProcess.HasExited)
                        {
                            int code = ServerProcess.ExitCode;
                            Log("Executor Python encerrou antes do runtime responder. ExitCode=" + code);
                            throw new InvalidOperationException(
                                "O executor local encerrou antes de iniciar (código " + code + "). Veja o log para o erro real."
                            );
                        }
                    }
                    catch (InvalidOperationException)
                    {
                        throw;
                    }
                    catch (Exception error)
                    {
                        Log("Não foi possível consultar o estado do processo Python: " + error.Message);
                    }
                }

                Thread.Sleep(200);
            }

            throw new InvalidOperationException(
                "O executor local V" + RuntimeVersion + " não respondeu em 40 segundos. Veja o log para o erro real."
            );
        }

        private static void StartHiddenExecutor(string root)
        {
            string python = FindPythonExecutable();
            if (python == null)
            {
                throw new InvalidOperationException(
                    "Python não foi encontrado. O EXE procura python.exe e py.exe também no PATH."
                );
            }

            string script = Path.Combine(root, "executor", "servidor_v4612.py");
            string vendor = Path.Combine(root, "executor", "vendor");
            if (!File.Exists(script))
            {
                throw new InvalidOperationException("executor\\servidor_v4612.py não foi encontrado.");
            }

            bool isPyLauncher = String.Equals(Path.GetFileName(python), "py.exe", StringComparison.OrdinalIgnoreCase);
            string arguments = (isPyLauncher ? "-3 " : "") + "\"" + script + "\" --no-browser";

            Log("Python selecionado: " + python);
            Log("Comando do executor: " + Path.GetFileName(python) + " " + arguments);

            ProcessStartInfo server = new ProcessStartInfo();
            server.FileName = python;
            server.Arguments = arguments;
            server.WorkingDirectory = root;
            server.UseShellExecute = false;
            server.CreateNoWindow = true;
            server.WindowStyle = ProcessWindowStyle.Hidden;
            server.RedirectStandardOutput = true;
            server.RedirectStandardError = true;
            server.EnvironmentVariables["PYTHONPATH"] = vendor;
            server.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
            server.EnvironmentVariables["CLUBEF_EXTRACTOR_PORT"] = AppPort.ToString();
            server.EnvironmentVariables["CLUBEF_EXTRACTOR_RUNTIME_VERSION"] = RuntimeVersion;
            server.EnvironmentVariables["CLUBEF_EXTRACTOR_LOG"] = LogPath;
            server.EnvironmentVariables.Remove("CLUBEF_SOURCE_DT870_UPDATED");
            server.EnvironmentVariables.Remove("CLUBEF_SOURCE_DT200");
            server.EnvironmentVariables.Remove("CLUBEF_SOURCE_DT870_ORIGINAL");
            server.EnvironmentVariables.Remove("CLUBEF_SOURCE_DT261_BRA");
            server.EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE");

            Process process = new Process();
            process.StartInfo = server;
            process.EnableRaisingEvents = true;
            process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs args)
            {
                if (!String.IsNullOrEmpty(args.Data)) Log("PY-OUT | " + args.Data);
            };
            process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs args)
            {
                if (!String.IsNullOrEmpty(args.Data)) Log("PY-ERR | " + args.Data);
            };
            process.Exited += delegate
            {
                try { Log("Executor Python encerrado. ExitCode=" + process.ExitCode); }
                catch { Log("Executor Python encerrado."); }
            };

            if (!process.Start())
            {
                throw new InvalidOperationException("O processo Python não pôde ser iniciado.");
            }

            ServerProcess = process;
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            Log("Executor Python V" + RuntimeVersion + " iniciado. PID=" + process.Id);
        }

        private static string FindPythonExecutable()
        {
            List<string> candidates = new List<string>();
            string user = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            candidates.Add(Path.Combine(user, ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "python.exe"));

            string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string programs = Path.Combine(local, "Programs", "Python");
            if (Directory.Exists(programs))
            {
                string[] folders = Directory.GetDirectories(programs, "Python*");
                Array.Sort(folders);
                Array.Reverse(folders);
                foreach (string folder in folders)
                {
                    candidates.Add(Path.Combine(folder, "python.exe"));
                }
            }

            string path = Environment.GetEnvironmentVariable("PATH") ?? "";
            foreach (string item in path.Split(Path.PathSeparator))
            {
                string folder = (item ?? "").Trim().Trim('"');
                if (String.IsNullOrEmpty(folder)) continue;
                candidates.Add(Path.Combine(folder, "python.exe"));
                candidates.Add(Path.Combine(folder, "py.exe"));
            }

            HashSet<string> seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (string candidate in candidates)
            {
                if (String.IsNullOrEmpty(candidate) || !seen.Add(candidate)) continue;
                try
                {
                    if (File.Exists(candidate)) return candidate;
                }
                catch
                {
                    // Continua procurando.
                }
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