using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

[assembly: AssemblyTitle("Bonificador ClubEfootball")]
[assembly: AssemblyDescription("Fila, conferência e auditoria local do Bonificador")]
[assembly: AssemblyProduct("Bonificador ClubEfootball")]
[assembly: AssemblyCompany("ClubEfootball")]
[assembly: AssemblyVersion("2.0.24.0")]
[assembly: AssemblyFileVersion("2.0.24.0")]

namespace ClubEfootballBonificador
{
    internal static class Program
    {
        internal static int AppPort = 8766;
        internal static string BaseUrl { get { return "http://127.0.0.1:" + AppPort; } }
        private const string ExpectedApp = "\"aplicativo\": \"bonificador_clubefootball\"";
        private const string ExpectedVersion = "\"versao_interface\": \"20260831-v2-native\"";
        private static Process localComponent;
        private static string localComponentPath;

        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
            string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
            try
            {
                AppPort = EscolherPortaLivre(); ValidatePackage(root); StartHiddenServer(root); WaitForServer();
                Application.Run(new BonificadorForm());
            }
            catch (Exception error)
            {
                string message = "Não foi possível abrir o Bonificador ClubEfootball.\r\n\r\n" + error.Message;
                MessageBox.Show(message, "Bonificador ClubEfootball", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally { StopHiddenServer(); }
        }
        private const int LocalRequestTimeoutMs = 30000;
        private sealed class LocalWebClient : WebClient
        {
            protected override WebRequest GetWebRequest(Uri address)
            {
                WebRequest request = base.GetWebRequest(address);
                request.Timeout = LocalRequestTimeoutMs;
                return request;
            }
        }
        private static string Detail(WebException error)
        {
            try
            {
                if (error.Response == null) return error.Message;
                using (StreamReader reader = new StreamReader(error.Response.GetResponseStream()))
                {
                    string body = reader.ReadToEnd().Trim();
                    return String.IsNullOrEmpty(body) ? error.Message : body;
                }
            }
            catch { return error.Message; }
        }
        internal static string Get(string path)
        {
            try { using (LocalWebClient c = new LocalWebClient()) { c.Proxy = null; c.Encoding = Encoding.UTF8; return c.DownloadString(BaseUrl + path); } }
            catch (WebException error) { throw new InvalidOperationException(Detail(error), error); }
        }
        internal static string Post(string path)
        {
            try { using (LocalWebClient c = new LocalWebClient()) { c.Proxy = null; c.Encoding = Encoding.UTF8; c.Headers[HttpRequestHeader.ContentType] = "application/json"; return c.UploadString(BaseUrl + path, "POST", "{}"); } }
            catch (WebException error) { throw new InvalidOperationException(Detail(error), error); }
        }
        private static bool ServerReady() { try { string b = Get("/api/ping"); return b.Contains(ExpectedApp) && b.Contains(ExpectedVersion); } catch { return false; } }
        private static void WaitForServer() { for (int i = 0; i < 100; i++) { if (ServerReady()) return; Thread.Sleep(200); } throw new InvalidOperationException("O componente local do Bonificador não iniciou dentro do tempo esperado."); }
        private static int EscolherPortaLivre()
        {
            TcpListener probe = new TcpListener(IPAddress.Loopback, 0);
            probe.Start();
            int port = ((IPEndPoint)probe.LocalEndpoint).Port;
            probe.Stop();
            return port;
        }
        private static void ValidatePackage(string root)
        {
            if (Assembly.GetExecutingAssembly().GetManifestResourceStream("BonificadorComponente") == null) throw new InvalidOperationException("O componente local incorporado ao Bonificador está ausente.");
        }
        private static void StartHiddenServer(string root)
        {
            string component = PrepararComponenteIncorporado();
            ProcessStartInfo p = new ProcessStartInfo { FileName = component, Arguments = "--porta=" + AppPort, WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden, RedirectStandardOutput = false, RedirectStandardError = false };
            p.EnvironmentVariables["CLUBEF_BONIFICADOR_PORT"] = AppPort.ToString(); p.EnvironmentVariables["PYTHONUTF8"] = "1";
            p.EnvironmentVariables["CLUBEF_BONIFICADOR_CONFIG"] = Path.Combine(Directory.GetParent(root).FullName, "config.txt");
            Process child = Process.Start(p); if (child == null) throw new InvalidOperationException("Não foi possível iniciar o componente local."); localComponent = child;
        }
        private static void StopHiddenServer()
        {
            Process child = localComponent; localComponent = null;
            string component = localComponentPath; localComponentPath = null;
            if (child != null) try
            {
                if (!child.HasExited)
                {
                    ProcessStartInfo stop = new ProcessStartInfo { FileName = "taskkill.exe", Arguments = "/PID " + child.Id + " /T /F", UseShellExecute = false, CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden };
                    using (Process killer = Process.Start(stop)) { if (killer != null) killer.WaitForExit(5000); }
                }
            }
            catch { try { if (!child.HasExited) child.Kill(); } catch { } }
            if (child != null) try { child.WaitForExit(3000); } catch { }
            if (child != null) try { child.Dispose(); } catch { }
            try
            {
                for (int attempt = 0; attempt < 20 && !String.IsNullOrEmpty(component) && File.Exists(component); attempt++)
                {
                    try { File.Delete(component); } catch { Thread.Sleep(100); }
                }
                string folder = String.IsNullOrEmpty(component) ? null : Path.GetDirectoryName(component);
                if (!String.IsNullOrEmpty(folder) && Directory.Exists(folder) && Directory.GetFiles(folder).Length == 0 && Directory.GetDirectories(folder).Length == 0) Directory.Delete(folder);
            }
            catch { }
        }
        private static string PrepararComponenteIncorporado()
        {
            string folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ClubEfootball", "Bonificador", Assembly.GetExecutingAssembly().GetName().Version.ToString());
            string component = Path.Combine(folder, "Bonificador Componente Local.exe");
            localComponentPath = component;
            if (File.Exists(component) && new FileInfo(component).Length > 1000000) return component;
            Directory.CreateDirectory(folder);
            using (Stream source = Assembly.GetExecutingAssembly().GetManifestResourceStream("BonificadorComponente"))
            {
                if (source == null) throw new InvalidOperationException("O componente local incorporado não foi encontrado.");
                using (FileStream target = new FileStream(component, FileMode.Create, FileAccess.Write, FileShare.Read)) source.CopyTo(target);
            }
            return component;
        }
    }

    internal sealed class FuncaoChoice { internal string Id, Nome; public override string ToString() { return Nome + " (#" + Id + ")"; } }

    internal sealed class BonificadorForm : Form
    {
        private readonly JavaScriptSerializer json = new JavaScriptSerializer { MaxJsonLength = Int32.MaxValue };
        private readonly Label status = new Label(), andamento = new Label(), totais = new Label(), linhaAtual = new Label();
        private readonly ProgressBar progresso = new ProgressBar(); private readonly DataGridView fila = new DataGridView(), resultadosFila = new DataGridView();
        private readonly Label resumoResultados = new Label();
        private readonly RichTextBox log = new RichTextBox(), resultado = new RichTextBox(); private readonly TextBox cardId = new TextBox(); private readonly ComboBox funcao = new ComboBox();
        private readonly Button iniciar = new Button(), parar = new Button(), atualizar = new Button(), simular = new Button(), auditoria = new Button();
        private readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer(); private bool consultando;

        internal BonificadorForm()
        {
            Text = "Bonificador ClubEfootball V2.0.24 — filas e resultados"; MinimumSize = new Size(980, 680); Size = new Size(1320, 820); StartPosition = FormStartPosition.CenterScreen; Font = new Font("Segoe UI", 9F);
            BuildLayout(); timer.Interval = 2000; timer.Tick += delegate { RefreshQueue(false); }; Shown += delegate { status.Text = "Contrato: consultando em segundo plano"; andamento.Text = "Estado: carregando fila sem bloquear a tela"; RefreshQueue(true); timer.Start(); }; FormClosing += delegate { timer.Stop(); };
        }
        private void BuildLayout()
        {
            TableLayoutPanel page = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(18), ColumnCount = 1, RowCount = 3 }; page.RowStyles.Add(new RowStyle(SizeType.AutoSize)); page.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); page.RowStyles.Add(new RowStyle(SizeType.AutoSize)); Controls.Add(page);
            FlowLayoutPanel header = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill }; Label title = new Label { Text = "BONIFICADOR", AutoSize = true, Font = new Font(Font.FontFamily, 17F, FontStyle.Bold), Padding = new Padding(0, 0, 28, 8) }; status.AutoSize = true; status.Padding = new Padding(0, 7, 28, 8); status.Text = "Contrato: verificando"; header.Controls.Add(title); header.Controls.Add(status); page.Controls.Add(header, 0, 0);
            TabControl tabs = new TabControl { Dock = DockStyle.Fill }; tabs.TabPages.Add(FilaTab()); tabs.TabPages.Add(ResultadosTab()); tabs.TabPages.Add(ConferenciaTab()); tabs.TabPages.Add(AuditoriaTab()); tabs.SelectedIndexChanged += delegate { if (tabs.SelectedIndex == 2 && funcao.Items.Count == 0) LoadFunctions(); }; page.Controls.Add(tabs, 0, 1);
            page.Controls.Add(new Label { AutoSize = true, Text = "Aplicativo local. O navegador não acessa o banco. A fila vem apenas do contrato canônico; nenhum fallback legado é usado.", ForeColor = Color.DimGray, Padding = new Padding(0, 10, 0, 0) }, 0, 2);
        }
        private TabPage FilaTab()
        {
            TabPage tab = new TabPage("Fila do Bonificador"); TableLayoutPanel box = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(12), ColumnCount = 1, RowCount = 6 }; box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); box.RowStyles.Add(new RowStyle(SizeType.Absolute, 135F)); tab.Controls.Add(box);
            box.Controls.Add(new Label { AutoSize = true, Text = "Mostra automaticamente as linhas canônicas marcadas como 'Bonificador não executado'. A tela não cria nem inventa entradas." }, 0, 0);
            FlowLayoutPanel actions = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill }; iniciar.Text = "INICIAR BONIFICADOR"; parar.Text = "PARAR NORMALMENTE"; atualizar.Text = "ATUALIZAR"; parar.Enabled = false; iniciar.AutoSize = parar.AutoSize = atualizar.AutoSize = true; iniciar.Click += delegate { ActionPipeline("/api/pipeline/iniciar"); }; parar.Click += delegate { ActionPipeline("/api/pipeline/parar"); }; atualizar.Click += delegate { RefreshQueue(true); }; actions.Controls.Add(iniciar); actions.Controls.Add(parar); actions.Controls.Add(atualizar); box.Controls.Add(actions, 0, 1);
            andamento.AutoSize = true; andamento.Text = "Estado: consultando"; box.Controls.Add(andamento, 0, 2); FlowLayoutPanel summary = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill }; totais.AutoSize = true; totais.Padding = new Padding(0, 4, 30, 4); linhaAtual.AutoSize = true; linhaAtual.Padding = new Padding(0, 4, 0, 4); summary.Controls.Add(totais); summary.Controls.Add(linhaAtual); box.Controls.Add(summary, 0, 3);
            TableLayoutPanel gridBox = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 2 }; gridBox.RowStyles.Add(new RowStyle(SizeType.AutoSize)); gridBox.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); progresso.Minimum = 0; progresso.Maximum = 100; progresso.Dock = DockStyle.Top; progresso.Height = 14; gridBox.Controls.Add(progresso, 0, 0); ConfigureGrid(fila, false); gridBox.Controls.Add(fila, 0, 1); box.Controls.Add(gridBox, 0, 4); log.Dock = DockStyle.Fill; log.ReadOnly = true; log.Font = new Font("Consolas", 8.5F); log.BackColor = Color.White; box.Controls.Add(log, 0, 5); return tab;
        }
        private TabPage ResultadosTab()
        {
            TabPage tab = new TabPage("Fila de resultados"); TableLayoutPanel box = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(12), ColumnCount = 1, RowCount = 3 }; box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); tab.Controls.Add(box);
            box.Controls.Add(new Label { AutoSize = true, Text = "Mostra somente as linhas efetivamente calculadas nesta rodada. Pendentes continuam na aba Fila do Bonificador." }, 0, 0);
            resumoResultados.AutoSize = true; resumoResultados.Padding = new Padding(0, 6, 0, 6); resumoResultados.Text = "Resultados desta rodada: 0"; box.Controls.Add(resumoResultados, 0, 1);
            ConfigureGrid(resultadosFila, true); box.Controls.Add(resultadosFila, 0, 2); tab.Enter += delegate { CarregarResultadosPersistidos(); }; return tab;
        }
        private TabPage ConferenciaTab()
        {
            TabPage tab = new TabPage("Testar uma carta"); TableLayoutPanel box = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(14), ColumnCount = 1, RowCount = 3 }; box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); tab.Controls.Add(box); FlowLayoutPanel form = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill }; cardId.Width = 260; funcao.Width = 300; funcao.DropDownStyle = ComboBoxStyle.DropDownList; simular.Text = "SIMULAR SOMENTE LEITURA"; simular.AutoSize = true; simular.Click += delegate { Simular(); }; form.Controls.Add(new Label { Text = "Carta (card_id):", AutoSize = true, Padding = new Padding(0, 9, 4, 0) }); form.Controls.Add(cardId); form.Controls.Add(new Label { Text = "Função:", AutoSize = true, Padding = new Padding(12, 9, 4, 0) }); form.Controls.Add(funcao); form.Controls.Add(simular); box.Controls.Add(form, 0, 0); box.Controls.Add(new Label { AutoSize = true, Text = "Mostra corpo, pé ruim, posição principal, dois playstyles, IA, molde, régua e gates. Não grava resultados." }, 0, 1); resultado.Dock = DockStyle.Fill; resultado.ReadOnly = true; resultado.Font = new Font("Consolas", 9F); box.Controls.Add(resultado, 0, 2); return tab;
        }
        private TabPage AuditoriaTab()
        {
            TabPage tab = new TabPage("Auditoria e paridade"); TableLayoutPanel box = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(14), ColumnCount = 1, RowCount = 2 }; box.RowStyles.Add(new RowStyle(SizeType.AutoSize)); box.RowStyles.Add(new RowStyle(SizeType.Percent, 100F)); tab.Controls.Add(box); auditoria.Text = "ATUALIZAR AUDITORIA"; auditoria.AutoSize = true; auditoria.Click += delegate { Audit(); }; box.Controls.Add(auditoria, 0, 0); RichTextBox outBox = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, Font = new Font("Consolas", 9F) }; auditoria.Tag = outBox; box.Controls.Add(outBox, 0, 1); return tab;
        }
        private void ConfigureGrid(DataGridView grade, bool resultados)
        {
            grade.Dock = DockStyle.Fill; grade.ReadOnly = true; grade.AllowUserToAddRows = false; grade.AllowUserToDeleteRows = false; grade.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.DisplayedCells; grade.SelectionMode = DataGridViewSelectionMode.FullRowSelect; grade.Columns.Add("Carta", "Carta"); grade.Columns.Add("Função", "Função"); grade.Columns.Add("Posição", "Posição"); grade.Columns.Add("Estado", resultados ? "Resultado" : "Estado");
            if (resultados) { grade.Columns.Add("Corpo", "Corpo"); grade.Columns.Add("Pe", "Pé ruim"); grade.Columns.Add("Estilo", "Playstyle"); grade.Columns.Add("IA", "IA"); grade.Columns.Add("Total", "Bônus total"); }
            grade.Columns.Add("Gate", "Gate / motivo");
        }
        private void OnUi(Action action)
        {
            if (IsDisposed || Disposing || !IsHandleCreated) return;
            try { BeginInvoke(action); } catch (InvalidOperationException) { }
        }
        private void LoadFunctions()
        {
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    string body = Program.Get("/api/funcoes");
                    OnUi(delegate
                    {
                        try
                        {
                            Dictionary<string, object> root = Map(body); funcao.Items.Clear();
                            foreach (object item in List(root, "funcoes")) { Dictionary<string, object> row = item as Dictionary<string, object>; if (row != null) funcao.Items.Add(new FuncaoChoice { Id = Value(row, "id"), Nome = Value(row, "nome") }); }
                            if (funcao.Items.Count > 0) funcao.SelectedIndex = 0;
                        }
                        catch (Exception error) { log.Text = "Catálogo de funções indisponível: " + error.Message; }
                    });
                }
                catch (Exception error) { OnUi(delegate { log.Text = "Catálogo de funções indisponível: " + error.Message; }); }
            });
        }
        private void ActionPipeline(string route)
        {
            iniciar.Enabled = false; parar.Enabled = false; andamento.Text = "Estado: enviando comando sem bloquear a tela";
            ThreadPool.QueueUserWorkItem(delegate
            {
                try { Program.Post(route); OnUi(delegate { RefreshQueue(true); }); }
                catch (Exception error) { OnUi(delegate { andamento.Text = "Comando recusado: " + error.Message; RefreshQueue(true); }); }
            });
        }
        private void RefreshQueue(bool force)
        {
            if (consultando) return; consultando = true; andamento.Text = "Estado: consultando fila em segundo plano";
            ThreadPool.QueueUserWorkItem(delegate
            {
                string queueBody;
                try
                {
                    queueBody = Program.Get("/api/fila/status");
                    OnUi(delegate
                    {
                        try
                        {
                            Dictionary<string, object> root = Map(queueBody), data = Map(root["fila"]), pipe = Map(data["pipeline"]); status.Text = "Fila disponível; verificando régua"; string state = Value(pipe, "estado"), message = Value(pipe, "mensagem"); andamento.Text = "Estado: " + state + " — " + message; bool active = Bool(pipe, "ativo"); iniciar.Enabled = false; parar.Enabled = active;
                            int pending = Number(data, "total"), total = Number(pipe, "total_rodada"), calculated = Number(pipe, "calculados"), confirmed = Number(pipe, "confirmados"); totais.Text = "Pendentes agora: " + pending + "  |  Rodada: " + total + "  |  Calculados: " + calculated + "  |  Confirmados: " + confirmed; Dictionary<string, object> current = pipe.ContainsKey("linha_atual") && pipe["linha_atual"] is Dictionary<string, object> ? (Dictionary<string, object>)pipe["linha_atual"] : new Dictionary<string, object>(); linhaAtual.Text = current.Count == 0 ? "Linha atual: nenhuma" : "Linha atual: " + Value(current, "linha_id") + " · carta " + Value(current, "card_id") + " · função " + Value(current, "funcao_id"); int denominator = Math.Max(total, calculated + pending); progresso.Value = denominator == 0 ? 0 : Math.Min(100, Math.Max(0, (int)Math.Round(100.0 * calculated / denominator)));
                            Dictionary<string, object> apresentacaoPorLinha = new Dictionary<string, object>(); fila.Rows.Clear(); foreach (object item in List(data, "itens")) { Dictionary<string, object> row = item as Dictionary<string, object>; if (row != null) { apresentacaoPorLinha[Value(row, "linha_id")] = row; fila.Rows.Add(CartaExibicao(row), FuncaoExibicao(row), PosicaoExibicao(row), Value(row, "estado"), ListaTexto(row, "faltou")); } }
                            resultadosFila.Rows.Clear(); Dictionary<string, object> resultados = pipe.ContainsKey("resultados") && pipe["resultados"] is Dictionary<string, object> ? Map(pipe["resultados"]) : new Dictionary<string, object>(); List<Dictionary<string, object>> linhasResultado = new List<Dictionary<string, object>>(); foreach (object valor in resultados.Values) { Dictionary<string, object> linha = valor as Dictionary<string, object>; if (linha != null) linhasResultado.Add(linha); } linhasResultado.Sort(delegate(Dictionary<string, object> a, Dictionary<string, object> b) { return Number(a, "linha_id").CompareTo(Number(b, "linha_id")); }); foreach (Dictionary<string, object> row in linhasResultado) { Dictionary<string, object> origem = apresentacaoPorLinha.ContainsKey(Value(row, "linha_id")) ? apresentacaoPorLinha[Value(row, "linha_id")] as Dictionary<string, object> : null; resultadosFila.Rows.Add(CartaExibicao(origem), FuncaoExibicao(origem), PosicaoExibicao(origem), Value(row, "estado"), Bonus(row, "b_corpo"), Bonus(row, "b_pe_ruim"), Bonus(row, "b_estilo"), Bonus(row, "b_ia"), Bonus(row, "b_total"), ListaTexto(row, "faltou")); } resumoResultados.Text = "Resultados desta rodada: " + linhasResultado.Count + " | Confirmados: " + confirmed + " | Bloqueados: " + linhasResultado.FindAll(delegate(Dictionary<string, object> row) { return Value(row, "estado") == "bloqueada"; }).Count; log.Text = String.Join(Environment.NewLine, List(pipe, "eventos").ConvertAll(delegate(object x) { return Convert.ToString(x); }));
                        }
                        catch (Exception error) { status.Text = "Fila indisponível"; andamento.Text = error.Message; consultando = false; }
                    });
                }
                catch (Exception error) { OnUi(delegate { status.Text = "Fila indisponível"; andamento.Text = error.Message; consultando = false; }); return; }
                try
                {
                    string healthBody = Program.Get("/api/saude");
                    OnUi(delegate
                    {
                        try
                        {
                            Dictionary<string, object> health = Map(healthBody); bool apt = Bool(health, "pode_rodar"); status.Text = apt ? "Fila disponível; contrato canônico apto" : "Fila disponível; contrato bloqueado"; iniciar.Enabled = apt && !parar.Enabled;
                        }
                        catch (Exception error) { status.Text = "Fila disponível; régua indisponível"; log.Text = "Consulta da régua: " + error.Message + Environment.NewLine + log.Text; }
                        finally { consultando = false; }
                    });
                }
                catch (Exception error) { OnUi(delegate { status.Text = "Fila disponível; régua indisponível"; log.Text = "Consulta da régua: " + error.Message + Environment.NewLine + log.Text; consultando = false; }); }
            });
        }
        private void CarregarResultadosPersistidos()
        {
            resumoResultados.Text = "Consultando resultados confirmados...";
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    string body = Program.Get("/api/resultados");
                    OnUi(delegate
                    {
                        try
                        {
                            Dictionary<string, object> root = Map(body), dados = Map(root["resultados"]); List<object> itens = List(dados, "itens"); resultadosFila.Rows.Clear(); foreach (object item in itens) { Dictionary<string, object> row = item as Dictionary<string, object>; if (row != null) resultadosFila.Rows.Add(CartaExibicao(row), FuncaoExibicao(row), PosicaoExibicao(row), Value(row, "estado"), Bonus(row, "b_corpo"), Bonus(row, "b_pe_ruim"), Bonus(row, "b_estilo"), Bonus(row, "b_ia"), Bonus(row, "b_total"), ListaTexto(row, "faltou")); } resumoResultados.Text = "Resultados confirmados: " + itens.Count;
                        }
                        catch (Exception error) { resumoResultados.Text = "Resultados indisponíveis: " + error.Message; }
                    });
                }
                catch (Exception error) { OnUi(delegate { resumoResultados.Text = "Resultados indisponíveis: " + error.Message; }); }
            });
        }
        private void Simular()
        {
            FuncaoChoice selected = funcao.SelectedItem as FuncaoChoice; if (selected == null || String.IsNullOrWhiteSpace(cardId.Text)) { resultado.Text = "Informe card_id e função."; return; } string id = cardId.Text.Trim(), functionId = selected.Id; resultado.Text = "Consultando simulação em segundo plano...";
            ThreadPool.QueueUserWorkItem(delegate { try { string body = Program.Get("/api/simular?card_id=" + Uri.EscapeDataString(id) + "&funcao_id=" + Uri.EscapeDataString(functionId)); OnUi(delegate { try { resultado.Text = json.Serialize(Map(body)); } catch (Exception error) { resultado.Text = "Simulação recusada: " + error.Message; } }); } catch (Exception error) { OnUi(delegate { resultado.Text = "Simulação recusada: " + error.Message; }); } });
        }
        private void Audit() { RichTextBox target = auditoria.Tag as RichTextBox; target.Text = "Consultando auditoria em segundo plano..."; ThreadPool.QueueUserWorkItem(delegate { try { string body = Program.Get("/api/auditoria"); OnUi(delegate { try { target.Text = json.Serialize(Map(body)); } catch (Exception error) { target.Text = "Auditoria indisponível: " + error.Message; } }); } catch (Exception error) { OnUi(delegate { target.Text = "Auditoria indisponível: " + error.Message; }); } }); }
        private Dictionary<string, object> Map(object value) { Dictionary<string, object> map = value as Dictionary<string, object>; if (map == null) throw new InvalidOperationException("Resposta local inválida."); return map; }
        private Dictionary<string, object> Map(string body) { return Map(json.DeserializeObject(body)); }
        private List<object> List(Dictionary<string, object> map, string key) { if (!map.ContainsKey(key) || map[key] == null || map[key] is string) return new List<object>(); IEnumerable sequence = map[key] as IEnumerable; if (sequence == null) return new List<object>(); List<object> result = new List<object>(); foreach (object item in sequence) result.Add(item); return result; }
        private string Value(Dictionary<string, object> map, string key) { return map.ContainsKey(key) && map[key] != null ? Convert.ToString(map[key]) : "—"; }
        private string CartaExibicao(Dictionary<string, object> map) { if (map == null) return "Carta sem referência humana"; string nome = Value(map, "carta_nome"), tipo = Value(map, "carta_tipo"), overall = Value(map, "carta_overall"); return nome + (tipo == "—" ? "" : " · " + tipo) + (overall == "—" ? "" : " · OVR " + overall); }
        private string FuncaoExibicao(Dictionary<string, object> map) { if (map == null) return "Função sem referência humana"; string nome = Value(map, "funcao_nome"), codigo = Value(map, "funcao_codigo"); return codigo == "—" || String.IsNullOrWhiteSpace(codigo) ? nome : nome + " · " + codigo; }
        private string PosicaoExibicao(Dictionary<string, object> map) { if (map == null) return "Posição sem referência humana"; string nome = Value(map, "posicao_nome"), codigo = Value(map, "posicao_codigo"); return codigo == "—" || String.IsNullOrWhiteSpace(codigo) ? nome : nome + " · " + codigo; }
        private string Bonus(Dictionary<string, object> map, string key) { if (!map.ContainsKey(key) || map[key] == null) return "—"; try { return Convert.ToDouble(map[key]).ToString("0.0000"); } catch { return "—"; } }
        private string ListaTexto(Dictionary<string, object> map, string key) { List<object> valores = List(map, key); return valores.Count == 0 ? "apto" : String.Join("; ", valores.ConvertAll(delegate(object valor) { return Convert.ToString(valor); })); }
        private int Number(Dictionary<string, object> map, string key) { try { return map.ContainsKey(key) && map[key] != null ? Convert.ToInt32(map[key]) : 0; } catch { return 0; } }
        private bool Bool(Dictionary<string, object> map, string key) { try { return map.ContainsKey(key) && map[key] != null && Convert.ToBoolean(map[key]); } catch { return false; } }
    }
}
