using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Reflection;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

[assembly: AssemblyTitle("Bonificador ClubEfootball")]
[assembly: AssemblyDescription("Fila, conferência e auditoria local do Bonificador")]
[assembly: AssemblyProduct("Bonificador ClubEfootball")]
[assembly: AssemblyCompany("ClubEfootball")]
[assembly: AssemblyVersion("2.0.0.0")]
[assembly: AssemblyFileVersion("2.0.0.0")]

namespace ClubEfootballBonificador
{
    internal static class Program
    {
        internal const int AppPort = 8766;
        internal const string BaseUrl = "http://127.0.0.1:8766";
        private const string ExpectedApp = "\"aplicativo\": \"bonificador_clubefootball\"";
        private const string ExpectedVersion = "\"versao_interface\": \"20260831-v2-native\"";

        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
            string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
            try
            {
                if (!ServerReady()) { ValidatePackage(root); StartHiddenServer(root); WaitForServer(); }
                Application.Run(new BonificadorForm());
            }
            catch (Exception error)
            {
                string message = "Não foi possível abrir o Bonificador ClubEfootball.\r\n\r\n" + error.Message;
                try { File.WriteAllText(Path.Combine(root, "ERRO-ABERTURA-BONIFICADOR.txt"), message); } catch { }
                MessageBox.Show(message, "Bonificador ClubEfootball", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
        internal static string Get(string path) { using (WebClient c = new WebClient()) { c.Proxy = null; return c.DownloadString(BaseUrl + path); } }
        internal static string Post(string path) { using (WebClient c = new WebClient()) { c.Proxy = null; c.Headers[HttpRequestHeader.ContentType] = "application/json"; return c.UploadString(BaseUrl + path, "POST", "{}"); } }
        private static bool ServerReady() { try { string b = Get("/api/saude"); return b.Contains(ExpectedApp) && b.Contains(ExpectedVersion); } catch { return false; } }
        private static void WaitForServer() { for (int i = 0; i < 100; i++) { if (ServerReady()) return; Thread.Sleep(200); } throw new InvalidOperationException("O componente local do Bonificador não respondeu. Confira ERRO-ABERTURA-BONIFICADOR.txt e a configuração desta cópia."); }
        private static void ValidatePackage(string root)
        {
            foreach (string file in new[] { Path.Combine(root, "interface", "servidor.py"), Path.Combine(root, "motor_bonus.py") }) if (!File.Exists(file)) throw new InvalidOperationException("O pacote do Bonificador está incompleto: " + file);
            if (!File.Exists(Path.Combine(Directory.GetParent(root).FullName, "config.txt"))) throw new InvalidOperationException("A configuração compartilhada não foi encontrada em 2-MOTORES\\config.txt.");
        }
        private static void StartHiddenServer(string root)
        {
            string python = FindPython(); if (python == null) throw new InvalidOperationException("O runtime do Bonificador não foi encontrado. Mantenha a pasta runtime junto do executável.");
            string log = Path.Combine(root, "COMPONENTE-LOCAL-BONIFICADOR.log");
            ProcessStartInfo p = new ProcessStartInfo { FileName = python, Arguments = "-u \"" + Path.Combine(root, "interface", "servidor.py") + "\"", WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden, RedirectStandardOutput = true, RedirectStandardError = true };
            p.EnvironmentVariables["CLUBEF_BONIFICADOR_PORT"] = AppPort.ToString(); p.EnvironmentVariables["PYTHONUTF8"] = "1";
            Process child = Process.Start(p); if (child == null) throw new InvalidOperationException("Não foi possível iniciar o componente local.");
            ThreadPool.QueueUserWorkItem(delegate { try { File.AppendAllText(log, child.StandardOutput.ReadToEnd() + child.StandardError.ReadToEnd()); } catch { } });
        }
        private static string FindPython()
        {
            string user = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile); List<string> paths = new List<string> { Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "runtime", "python.exe"), Path.Combine(user, ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "python.exe") };
            string programs = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python");
            if (Directory.Exists(programs)) { string[] folders = Directory.GetDirectories(programs, "Python*"); Array.Sort(folders); Array.Reverse(folders); foreach (string f in folders) paths.Add(Path.Combine(f, "python.exe")); }
            foreach (string p in paths) if (File.Exists(p)) return p; return null;
        }
    }

    internal sealed class FuncaoChoice { internal string Id, Nome; public override string ToString() { return Nome + " (#" + Id + ")"; } }

    internal sealed class BonificadorForm : Form
    {
        private readonly JavaScriptSerializer json = new JavaScriptSerializer { MaxJsonLength = Int32.MaxValue };
        private readonly Label status = new Label(), andamento = new Label(), totais = new Label(), linhaAtual = new Label();
        private readonly ProgressBar progresso = new ProgressBar(); private readonly DataGridView fila = new DataGridView();
        private readonly RichTextBox log = new RichTextBox(), resultado = new RichTextBox(); private readonly TextBox cardId = new TextBox(); private readonly ComboBox funcao = new ComboBox();
        private readonly Button iniciar = new Button(), parar = new Button(), atualizar = new Button(), simular = new Button(), auditoria = new Button();
        private readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer(); private bool consultando;

        internal BonificadorForm()
        {
            Text = "Bonificador ClubEfootball V2 — fila e conferência"; MinimumSize = new Size(980, 680); Size = new Size(1220, 820); StartPosition = FormStartPosition.CenterScreen; Font = new Font("Segoe UI", 9F);
            BuildLayout(); timer.Interval = 2000; timer.Tick += delegate { RefreshQueue(false); }; Shown += delegate { LoadFunctions(); RefreshQueue(true); timer.Start(); }; FormClosing += delegate { timer.Stop(); };
        }
        private void BuildLayout()
        {
            TableLayoutPanel page = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(18), ColumnCount = 1, RowCount = 3 }; page.RowStyles.Add(new RowStyle(SizeType.AutoSize)); page.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); page.RowStyles.Add(new RowStyle(SizeType.AutoSize)); Controls.Add(page);
            FlowLayoutPanel header = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill }; Label title = new Label { Text = "BONIFICADOR", AutoSize = true, Font = new Font(Font.FontFamily, 17F, FontStyle.Bold), Padding = new Padding(0, 0, 28, 8) }; status.AutoSize = true; status.Padding = new Padding(0, 7, 28, 8); status.Text = "Contrato: verificando"; header.Controls.Add(title); header.Controls.Add(status); page.Controls.Add(header, 0, 0);
            TabControl tabs = new TabControl { Dock = DockStyle.Fill }; tabs.TabPages.Add(FilaTab()); tabs.TabPages.Add(ConferenciaTab()); tabs.TabPages.Add(AuditoriaTab()); page.Controls.Add(tabs, 0, 1);
            page.Controls.Add(new Label { AutoSize = true, Text = "Aplicativo local. O navegador não acessa o banco. A fila vem apenas do contrato canônico; nenhum fallback legado é usado.", ForeColor = Color.DimGray, Padding = new Padding(0, 10, 0, 0) }, 0, 2);
        }
        private TabPage FilaTab()
        {
            TabPage tab = new TabPage("Fila do Bonificador"); TableLayoutPanel box = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(12), ColumnCount = 1, RowCount = 6 }; box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); box.RowStyles.Add(new RowStyle(SizeType.Absolute, 135F)); tab.Controls.Add(box);
            box.Controls.Add(new Label { AutoSize = true, Text = "Acompanha somente pares pendentes que o Otimizador já confirmou. A tela não cria fila nem inventa entradas." }, 0, 0);
            FlowLayoutPanel actions = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill }; iniciar.Text = "INICIAR BONIFICADOR"; parar.Text = "PARAR NORMALMENTE"; atualizar.Text = "ATUALIZAR"; parar.Enabled = false; iniciar.AutoSize = parar.AutoSize = atualizar.AutoSize = true; iniciar.Click += delegate { ActionPipeline("/api/pipeline/iniciar"); }; parar.Click += delegate { ActionPipeline("/api/pipeline/parar"); }; atualizar.Click += delegate { RefreshQueue(true); }; actions.Controls.Add(iniciar); actions.Controls.Add(parar); actions.Controls.Add(atualizar); box.Controls.Add(actions, 0, 1);
            andamento.AutoSize = true; andamento.Text = "Estado: consultando"; box.Controls.Add(andamento, 0, 2); FlowLayoutPanel summary = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill }; totais.AutoSize = true; totais.Padding = new Padding(0, 4, 30, 4); linhaAtual.AutoSize = true; linhaAtual.Padding = new Padding(0, 4, 0, 4); summary.Controls.Add(totais); summary.Controls.Add(linhaAtual); box.Controls.Add(summary, 0, 3);
            TableLayoutPanel gridBox = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 2 }; gridBox.RowStyles.Add(new RowStyle(SizeType.AutoSize)); gridBox.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); progresso.Minimum = 0; progresso.Maximum = 100; progresso.Dock = DockStyle.Top; progresso.Height = 14; gridBox.Controls.Add(progresso, 0, 0); ConfigureGrid(); gridBox.Controls.Add(fila, 0, 1); box.Controls.Add(gridBox, 0, 4); log.Dock = DockStyle.Fill; log.ReadOnly = true; log.Font = new Font("Consolas", 8.5F); log.BackColor = Color.White; box.Controls.Add(log, 0, 5); return tab;
        }
        private TabPage ConferenciaTab()
        {
            TabPage tab = new TabPage("Testar uma carta"); TableLayoutPanel box = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(14), ColumnCount = 1, RowCount = 3 }; box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); tab.Controls.Add(box); FlowLayoutPanel form = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill }; cardId.Width = 260; funcao.Width = 300; funcao.DropDownStyle = ComboBoxStyle.DropDownList; simular.Text = "SIMULAR SOMENTE LEITURA"; simular.AutoSize = true; simular.Click += delegate { Simular(); }; form.Controls.Add(new Label { Text = "Carta (card_id):", AutoSize = true, Padding = new Padding(0, 9, 4, 0) }); form.Controls.Add(cardId); form.Controls.Add(new Label { Text = "Função:", AutoSize = true, Padding = new Padding(12, 9, 4, 0) }); form.Controls.Add(funcao); form.Controls.Add(simular); box.Controls.Add(form, 0, 0); box.Controls.Add(new Label { AutoSize = true, Text = "Mostra corpo, pé ruim, posição principal, dois playstyles, IA, molde, régua e gates. Não grava resultados." }, 0, 1); resultado.Dock = DockStyle.Fill; resultado.ReadOnly = true; resultado.Font = new Font("Consolas", 9F); box.Controls.Add(resultado, 0, 2); return tab;
        }
        private TabPage AuditoriaTab()
        {
            TabPage tab = new TabPage("Auditoria e paridade"); TableLayoutPanel box = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(14), ColumnCount = 1, RowCount = 2 }; box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); tab.Controls.Add(box); auditoria.Text = "ATUALIZAR AUDITORIA"; auditoria.AutoSize = true; auditoria.Click += delegate { Audit(); }; box.Controls.Add(auditoria, 0, 0); RichTextBox outBox = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, Font = new Font("Consolas", 9F) }; auditoria.Tag = outBox; box.Controls.Add(outBox, 0, 1); return tab;
        }
        private void ConfigureGrid()
        {
            fila.Dock = DockStyle.Fill; fila.ReadOnly = true; fila.AllowUserToAddRows = false; fila.AllowUserToDeleteRows = false; fila.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill; fila.SelectionMode = DataGridViewSelectionMode.FullRowSelect; fila.Columns.Add("Linha", "Linha"); fila.Columns.Add("Carta", "Carta / card_id"); fila.Columns.Add("Função", "Função"); fila.Columns.Add("Posição", "Posição ID"); fila.Columns.Add("Estado", "Estado"); fila.Columns.Add("Versão", "Versão da carta"); fila.Columns.Add("Fingerprint", "Fingerprint");
        }
        private void LoadFunctions()
        {
            try { Dictionary<string, object> root = Map(Program.Get("/api/funcoes")); foreach (object item in List(root, "funcoes")) { Dictionary<string, object> row = item as Dictionary<string, object>; if (row != null) funcao.Items.Add(new FuncaoChoice { Id = Value(row, "id"), Nome = Value(row, "nome") }); } if (funcao.Items.Count > 0) funcao.SelectedIndex = 0; } catch (Exception error) { status.Text = "Contrato indisponível: " + error.Message; }
        }
        private void ActionPipeline(string route) { try { Program.Post(route); RefreshQueue(true); } catch (Exception error) { andamento.Text = "Comando recusado: " + error.Message; } }
        private void RefreshQueue(bool force)
        {
            if (consultando && !force) return; consultando = true;
            try
            {
                Dictionary<string, object> health = Map(Program.Get("/api/saude")), root = Map(Program.Get("/api/fila/status")), data = Map(root["fila"]), pipe = Map(data["pipeline"]); status.Text = Bool(health, "pode_rodar") ? "Contrato canônico apto" : "Contrato bloqueado"; string state = Value(pipe, "estado"), message = Value(pipe, "mensagem"); andamento.Text = "Estado: " + state + " — " + message; bool active = Bool(pipe, "ativo"); iniciar.Enabled = !active; parar.Enabled = active;
                int pending = Number(data, "total"), total = Number(pipe, "total_rodada"), calculated = Number(pipe, "calculados"), confirmed = Number(pipe, "confirmados"); totais.Text = "Pendentes agora: " + pending + "  |  Rodada: " + total + "  |  Calculados: " + calculated + "  |  Confirmados: " + confirmed; Dictionary<string, object> current = pipe.ContainsKey("linha_atual") && pipe["linha_atual"] is Dictionary<string, object> ? (Dictionary<string, object>)pipe["linha_atual"] : new Dictionary<string, object>(); linhaAtual.Text = current.Count == 0 ? "Linha atual: nenhuma" : "Linha atual: " + Value(current, "linha_id") + " · carta " + Value(current, "card_id") + " · função " + Value(current, "funcao_id"); int denominator = Math.Max(total, calculated + pending); progresso.Value = denominator == 0 ? 0 : Math.Min(100, Math.Max(0, (int)Math.Round(100.0 * calculated / denominator)));
                fila.Rows.Clear(); foreach (object item in List(data, "itens")) { Dictionary<string, object> row = item as Dictionary<string, object>; if (row != null) fila.Rows.Add(Value(row, "linha_id"), Value(row, "card_id"), Value(row, "funcao_nome") + " (" + Value(row, "funcao_codigo") + ")", Value(row, "posicao_id"), Value(row, "estado"), Value(row, "carta_versao"), Value(row, "carta_fingerprint")); } log.Text = String.Join(Environment.NewLine, List(pipe, "eventos").ConvertAll(delegate(object x) { return Convert.ToString(x); }));
            }
            catch (Exception error) { status.Text = "Fila indisponível"; andamento.Text = error.Message; }
            finally { consultando = false; }
        }
        private void Simular()
        {
            FuncaoChoice selected = funcao.SelectedItem as FuncaoChoice; if (selected == null || String.IsNullOrWhiteSpace(cardId.Text)) { resultado.Text = "Informe card_id e função."; return; } try { resultado.Text = json.Serialize(Map(Program.Get("/api/simular?card_id=" + Uri.EscapeDataString(cardId.Text.Trim()) + "&funcao_id=" + Uri.EscapeDataString(selected.Id)))); } catch (Exception error) { resultado.Text = "Simulação recusada: " + error.Message; }
        }
        private void Audit() { RichTextBox target = auditoria.Tag as RichTextBox; try { target.Text = json.Serialize(Map(Program.Get("/api/auditoria"))); } catch (Exception error) { target.Text = "Auditoria indisponível: " + error.Message; } }
        private Dictionary<string, object> Map(object value) { Dictionary<string, object> map = value as Dictionary<string, object>; if (map == null) throw new InvalidOperationException("Resposta local inválida."); return map; }
        private Dictionary<string, object> Map(string body) { return Map(json.DeserializeObject(body)); }
        private List<object> List(Dictionary<string, object> map, string key) { ArrayList list = map.ContainsKey(key) ? map[key] as ArrayList : null; return list == null ? new List<object>() : new List<object>(list.ToArray()); }
        private string Value(Dictionary<string, object> map, string key) { return map.ContainsKey(key) && map[key] != null ? Convert.ToString(map[key]) : "—"; }
        private int Number(Dictionary<string, object> map, string key) { try { return map.ContainsKey(key) && map[key] != null ? Convert.ToInt32(map[key]) : 0; } catch { return 0; } }
        private bool Bool(Dictionary<string, object> map, string key) { try { return map.ContainsKey(key) && map[key] != null && Convert.ToBoolean(map[key]); } catch { return false; } }
    }
}
