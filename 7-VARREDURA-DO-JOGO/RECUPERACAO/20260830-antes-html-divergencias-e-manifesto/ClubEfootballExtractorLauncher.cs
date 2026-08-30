using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("Extrator eFootball")]
[assembly: System.Reflection.AssemblyDescription("Leitura física e conferência local em modo somente leitura")]
[assembly: System.Reflection.AssemblyProduct("Extrator eFootball")]
[assembly: System.Reflection.AssemblyCompany("ClubEfootball")]
[assembly: System.Reflection.AssemblyVersion("5.0.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("5.0.0.0")]

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
        private const string DesktopProtocolVersion = "5.0.0";
        private readonly string root;
        private readonly JavaScriptSerializer json = new JavaScriptSerializer();
        private readonly Dictionary<string, ListViewItem> families = new Dictionary<string, ListViewItem>(StringComparer.OrdinalIgnoreCase);
        private readonly Label database = new Label(), sources = new Label(), stage = new Label();
        private readonly ProgressBar progress = new ProgressBar();
        private readonly ListView familyList = new ListView();
        private readonly RichTextBox log = new RichTextBox();
        private readonly Button start = new Button(), cancel = new Button(), viewResult = new Button(), approve = new Button(), apply = new Button();
        private Process worker;
        private string cancelPath, resultPath;

        internal ExtractorForm(string applicationRoot)
        {
            root = applicationRoot;
            Text = "Extrator eFootball V" + DesktopProtocolVersion + " — conferência somente leitura";
            MinimumSize = new Size(900, 650); Size = new Size(1080, 760); StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 9F);
            BuildLayout();
            SetAvailability("Banco: aguardando", "Fontes: aguardando", "Pronto para iniciar uma varredura somente leitura.");
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
            viewResult.Text = "VER DIVERGÊNCIAS"; viewResult.AutoSize = true; viewResult.Padding = new Padding(12, 6, 12, 6); viewResult.Enabled = false; viewResult.Click += delegate { OpenResult(); };
            approve.Text = "APROVAR PACOTE"; approve.AutoSize = true; approve.Padding = new Padding(12, 6, 12, 6); approve.Enabled = false; approve.Click += delegate { ApprovePackage(); };
            apply.Text = "APLICAR PACOTE"; apply.AutoSize = true; apply.Padding = new Padding(12, 6, 12, 6); apply.Enabled = false; apply.Click += delegate { ApplyPackage(); };
            actions.Controls.Add(start); actions.Controls.Add(cancel); actions.Controls.Add(viewResult); actions.Controls.Add(approve); actions.Controls.Add(apply); layout.Controls.Add(actions, 0, 5);
        }

        private void SetAvailability(string databaseText, string sourceText, string stageText) { database.Text = databaseText; sources.Text = sourceText; stage.Text = "Etapa: " + stageText; }

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

        private void StartWorker()
        {
            if (worker != null && !worker.HasExited) return;
            string script = Path.Combine(root, "executor", "desktop_worker.py");
            if (!File.Exists(script)) { MessageBox.Show("Não encontrei executor\\desktop_worker.py.", "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error); return; }
            bool launcher; string python = FindPython(out launcher);
            if (String.IsNullOrEmpty(python)) { MessageBox.Show("Python não foi encontrado neste Windows.", "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error); return; }
            string runDirectory = Path.Combine(root, "artefatos", "desktop", "run-" + DateTime.Now.ToString("yyyyMMdd-HHmmss")); Directory.CreateDirectory(runDirectory);
            cancelPath = Path.Combine(runDirectory, "CANCELAR.txt"); resultPath = Path.Combine(runDirectory, "resultado.json");
            foreach (ListViewItem item in families.Values) { item.SubItems[1].Text = "aguardando"; item.SubItems[2].Text = "Ainda não iniciada."; }
            log.Clear(); progress.Value = 0; start.Enabled = false; cancel.Enabled = true; viewResult.Enabled = false; approve.Enabled = false; apply.Enabled = false; SetAvailability("Banco: conectando em leitura", "Fontes: verificando", "Preparando processo de extração separado."); AppendLog("Iniciando worker desktop V" + DesktopProtocolVersion + ". Nenhuma escrita no banco é permitida.");
            ProcessStartInfo info = new ProcessStartInfo(); info.FileName = python; info.Arguments = (launcher ? "-3 " : "") + Quote(script) + " --root " + Quote(root) + " --run-dir " + Quote(runDirectory) + " --cancel " + Quote(cancelPath) + " --protocol-version " + Quote(DesktopProtocolVersion); info.WorkingDirectory = root; info.UseShellExecute = false; info.CreateNoWindow = true; info.RedirectStandardOutput = true; info.RedirectStandardError = true; info.EnvironmentVariables["PYTHONPATH"] = Path.Combine(root, "executor", "vendor"); info.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"; info.EnvironmentVariables.Remove("CLUBEF_ENABLE_REAL_WRITE");
            worker = new Process { StartInfo = info, EnableRaisingEvents = true };
            worker.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (!String.IsNullOrEmpty(e.Data)) HandleWorkerLine(e.Data); };
            worker.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (!String.IsNullOrEmpty(e.Data)) AppendFromWorker("ERRO | " + e.Data); };
            worker.Exited += delegate { BeginInvoke((MethodInvoker)delegate { FinishWorker(worker.ExitCode); }); };
            try { worker.Start(); worker.BeginOutputReadLine(); worker.BeginErrorReadLine(); }
            catch (Exception error) { start.Enabled = true; cancel.Enabled = false; AppendLog("Falha ao iniciar worker: " + error.Message); MessageBox.Show(error.Message, "Extrator eFootball", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        private static string Quote(string value) { return "\"" + value.Replace("\"", "\\\"") + "\""; }
        private void HandleWorkerLine(string line)
        {
            if (IsDisposed) return;
            BeginInvoke((MethodInvoker)delegate {
                try
                {
                    Dictionary<string, object> message = json.DeserializeObject(line) as Dictionary<string, object>; if (message == null) { AppendLog(line); return; }
                    string type = TextValue(message, "type");
                    if (type == "status") { database.Text = "Banco: " + TextValue(message, "database"); sources.Text = "Fontes: " + TextValue(message, "sources"); stage.Text = "Etapa: " + TextValue(message, "message"); }
                    else if (type == "source") AppendLog("Fonte " + TextValue(message, "role") + ": " + TextValue(message, "message"));
                    else if (type == "progress") { int value; if (Int32.TryParse(TextValue(message, "percent"), out value)) progress.Value = Math.Max(progress.Minimum, Math.Min(progress.Maximum, value)); stage.Text = "Etapa: " + TextValue(message, "stage"); }
                    else if (type == "family") UpdateFamily(TextValue(message, "family"), TextValue(message, "state"), TextValue(message, "message"));
                    else if (type == "complete") { resultPath = TextValue(message, "result_path"); AppendLog("Resultado local: " + resultPath); }
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
        private void AppendFromWorker(string text) { if (!IsDisposed) BeginInvoke((MethodInvoker)delegate { AppendLog(text); }); }
        private void AppendLog(string text) { if (String.IsNullOrEmpty(text)) return; log.AppendText(DateTime.Now.ToString("HH:mm:ss") + " | " + text + Environment.NewLine); log.SelectionStart = log.TextLength; log.ScrollToCaret(); }
        private void RequestCancel()
        {
            if (String.IsNullOrEmpty(cancelPath) || worker == null || worker.HasExited) return;
            try { File.WriteAllText(cancelPath, "cancelled by user", new UTF8Encoding(false)); cancel.Enabled = false; AppendLog("Cancelamento solicitado. O worker salvará o estado seguro e encerrará."); }
            catch (Exception error) { AppendLog("Não foi possível solicitar cancelamento: " + error.Message); }
        }
        private void FinishWorker(int exitCode)
        {
            cancel.Enabled = false; start.Enabled = true; viewResult.Enabled = File.Exists(resultPath); approve.Enabled = File.Exists(Path.Combine(Path.GetDirectoryName(resultPath), "pacote-revisao.json")); apply.Enabled = false;
            if (exitCode == 0) { progress.Value = 100; stage.Text = "Etapa: conferência concluída — somente leitura."; AppendLog("Worker concluído. Nenhuma escrita automática foi executada."); }
            else { stage.Text = "Etapa: worker encerrado com código " + exitCode + ". Consulte o log e o resultado local."; AppendLog("Worker encerrado com código " + exitCode + ". A janela permaneceu disponível."); }
        }
        private void OpenResult() { if (File.Exists(resultPath)) Process.Start(new ProcessStartInfo("notepad.exe", Quote(resultPath)) { UseShellExecute = false }); }
        private void ApprovePackage()
        {
            string package = Path.Combine(Path.GetDirectoryName(resultPath), "pacote-revisao.json"); if (!File.Exists(package)) return;
            if (MessageBox.Show("Aprovar este pacote de revisão no contrato do Extrator? O aceite só vale se hash, fontes e contrato ainda coincidirem.", "Aprovação interna", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
            bool launcher; string python = FindPython(out launcher); string script = Path.Combine(root, "executor", "desktop_worker.py");
            ProcessStartInfo info = new ProcessStartInfo { FileName = python, Arguments = (launcher ? "-3 " : "") + Quote(script) + " --root " + Quote(root) + " --run-dir " + Quote(Path.GetDirectoryName(resultPath)) + " --cancel " + Quote(Path.Combine(Path.GetDirectoryName(resultPath), "CANCELAR.txt")) + " --protocol-version " + Quote(DesktopProtocolVersion) + " --approve-review " + Quote(package), WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            using (Process p = Process.Start(info)) { string output = p.StandardOutput.ReadToEnd() + p.StandardError.ReadToEnd(); p.WaitForExit(); AppendLog(output); apply.Enabled = p.ExitCode == 0; MessageBox.Show(p.ExitCode == 0 ? "Pacote aprovado no fluxo interno. A aplicação revalidará o mesmo hash, contrato, fontes e cobertura antes de qualquer escrita." : "Aprovação recusada: " + output, "Extrator eFootball", MessageBoxButtons.OK, p.ExitCode == 0 ? MessageBoxIcon.Information : MessageBoxIcon.Error); }
        }
        private void ApplyPackage()
        {
            string package = Path.Combine(Path.GetDirectoryName(resultPath), "pacote-revisao.json"); if (!File.Exists(package)) return;
            if (MessageBox.Show("Aplicar exclusivamente este pacote já aprovado? O worker recusará hash, fontes, contrato, cobertura ou envelopes divergentes.", "Aplicação transacional", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
            bool launcher; string python = FindPython(out launcher); string script = Path.Combine(root, "executor", "desktop_worker.py");
            ProcessStartInfo info = new ProcessStartInfo { FileName = python, Arguments = (launcher ? "-3 " : "") + Quote(script) + " --root " + Quote(root) + " --run-dir " + Quote(Path.GetDirectoryName(resultPath)) + " --cancel " + Quote(Path.Combine(Path.GetDirectoryName(resultPath), "CANCELAR.txt")) + " --protocol-version " + Quote(DesktopProtocolVersion) + " --apply-review " + Quote(package), WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            using (Process p = Process.Start(info)) { string output = p.StandardOutput.ReadToEnd() + p.StandardError.ReadToEnd(); p.WaitForExit(); AppendLog(output); MessageBox.Show(p.ExitCode == 0 ? "Pacote aplicado e confirmado." : "Aplicação recusada com segurança: " + output, "Extrator eFootball", MessageBoxButtons.OK, p.ExitCode == 0 ? MessageBoxIcon.Information : MessageBoxIcon.Error); }
        }
    }
}
