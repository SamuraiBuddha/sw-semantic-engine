// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Commands/SettingsCommand.cs
// WinForms dialog with TabControl for configuring the add-in.
// Tab 1: Model selector (installed + catalog, download/delete/test/import)
// Tab 2: General settings (ports, auto-launch toggles, paths)
// ---------------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using SolidWorksSemanticEngine.Models;
using SolidWorksSemanticEngine.Services;

namespace SolidWorksSemanticEngine.Commands
{
    /// <summary>
    /// Settings dialog with two tabs: Model selection and General configuration.
    /// </summary>
    public class SettingsCommand : Form
    {
        // ----- Catalog entry (matches swse-model-catalog.json) -----------------

        private class CatalogEntry
        {
            [JsonProperty("id")]          public string Id { get; set; }
            [JsonProperty("name")]        public string Name { get; set; }
            [JsonProperty("displayName")] public string DisplayName { get; set; }
            [JsonProperty("description")] public string Description { get; set; }
            [JsonProperty("size")]        public string Size { get; set; }
            [JsonProperty("sizeBytes")]   public long SizeBytes { get; set; }
            [JsonProperty("contextWindow")] public int ContextWindow { get; set; }
            [JsonProperty("recommended")] public bool Recommended { get; set; }
            [JsonProperty("cpuOptimized")] public bool CpuOptimized { get; set; }
            [JsonProperty("capabilities")] public List<string> Capabilities { get; set; }
        }

        /// <summary>
        /// Combined view of a model that may be in the catalog, installed, or both.
        /// </summary>
        private class ModelEntry
        {
            public string Name { get; set; }
            public string DisplayName { get; set; }
            public string Description { get; set; }
            public string SizeDisplay { get; set; }
            public bool IsInstalled { get; set; }
            public bool IsActive { get; set; }
            public bool Recommended { get; set; }
            public bool CpuOptimized { get; set; }
        }

        // ----- Fields ----------------------------------------------------------

        private readonly SwseConfig _config;
        private readonly Action<SwseConfig> _onSave;
        private OllamaService _ollamaService;
        private CancellationTokenSource _downloadCts;

        // Tab control
        private TabControl _tabControl;

        // Model tab controls
        private ListView _lstModels;
        private Button _btnSetActive;
        private Button _btnTest;
        private Button _btnDownload;
        private Button _btnDelete;
        private Button _btnImport;
        private Button _btnRefresh;
        private ProgressBar _progressBar;
        private Label _lblProgress;
        private Label _lblConnection;
        private RichTextBox _rtbTestOutput;

        // General tab controls
        private TextBox _txtOllamaUrl;
        private TextBox _txtBackendPort;
        private CheckBox _chkAutoOllama;
        private CheckBox _chkAutoBackend;
        private CheckBox _chkKillOnDisconnect;
        private TextBox _txtProjectRoot;
        private Button _btnOpenConfig;

        // Bottom buttons
        private Button _btnSave;
        private Button _btnCancel;

        // Data
        private List<CatalogEntry> _catalog = new List<CatalogEntry>();
        private List<ModelEntry> _modelEntries = new List<ModelEntry>();
        private string _activeModel;

        // ----- Constructor -----------------------------------------------------

        public SettingsCommand(SwseConfig config, Action<SwseConfig> onSave)
        {
            _config = config ?? new SwseConfig();
            _onSave = onSave;
            _activeModel = _config.ActiveModel ?? "sw-semantic-7b";

            string ollamaUrl = "http://localhost:" + _config.OllamaPort;
            _ollamaService = new OllamaService(ollamaUrl);

            Text = "Semantic Engine - Settings";
            Size = new Size(700, 620);
            StartPosition = FormStartPosition.CenterScreen;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;

            LoadCatalog();
            BuildUI();

            // Load models on first show
            Shown += async (s, e) => await RefreshModelList();
        }

        // ----- UI Construction -------------------------------------------------

        private void BuildUI()
        {
            _tabControl = new TabControl
            {
                Location = new Point(8, 8),
                Size = new Size(668, 530)
            };

            BuildModelTab();
            BuildGeneralTab();

            // Bottom buttons
            _btnSave = new Button
            {
                Text = "Save",
                Location = new Point(500, 548),
                Size = new Size(80, 28)
            };
            _btnSave.Click += BtnSave_Click;

            _btnCancel = new Button
            {
                Text = "Cancel",
                Location = new Point(590, 548),
                Size = new Size(80, 28)
            };
            _btnCancel.Click += (s, e) => Close();

            Controls.AddRange(new Control[] { _tabControl, _btnSave, _btnCancel });
        }

        private void BuildModelTab()
        {
            var tabModel = new TabPage("Model");

            // Connection status
            _lblConnection = new Label
            {
                Text = "Checking Ollama connection...",
                Location = new Point(10, 10),
                AutoSize = true
            };

            // ListView for models
            _lstModels = new ListView
            {
                Location = new Point(10, 35),
                Size = new Size(640, 200),
                View = View.Details,
                FullRowSelect = true,
                GridLines = true,
                MultiSelect = false
            };
            _lstModels.Columns.Add("Model", 180);
            _lstModels.Columns.Add("Description", 230);
            _lstModels.Columns.Add("Size", 65);
            _lstModels.Columns.Add("Status", 80);
            _lstModels.Columns.Add("Tags", 80);
            _lstModels.SelectedIndexChanged += LstModels_SelectedIndexChanged;

            // Action buttons
            int btnY = 242;
            _btnSetActive = new Button { Text = "Set Active", Location = new Point(10, btnY), Size = new Size(85, 26), Enabled = false };
            _btnTest = new Button { Text = "Test", Location = new Point(100, btnY), Size = new Size(65, 26), Enabled = false };
            _btnDownload = new Button { Text = "Download", Location = new Point(170, btnY), Size = new Size(80, 26), Enabled = false };
            _btnDelete = new Button { Text = "Delete", Location = new Point(255, btnY), Size = new Size(65, 26), Enabled = false };
            _btnImport = new Button { Text = "Import from File...", Location = new Point(390, btnY), Size = new Size(130, 26) };
            _btnRefresh = new Button { Text = "Refresh", Location = new Point(580, btnY), Size = new Size(70, 26) };

            _btnSetActive.Click += BtnSetActive_Click;
            _btnTest.Click += BtnTest_Click;
            _btnDownload.Click += BtnDownload_Click;
            _btnDelete.Click += BtnDelete_Click;
            _btnImport.Click += BtnImport_Click;
            _btnRefresh.Click += async (s, e) => await RefreshModelList();

            // Progress bar
            _progressBar = new ProgressBar
            {
                Location = new Point(10, 275),
                Size = new Size(640, 20),
                Visible = false
            };
            _lblProgress = new Label
            {
                Text = "",
                Location = new Point(10, 298),
                Size = new Size(640, 18),
                Visible = false
            };

            // Test output
            var lblTestOutput = new Label
            {
                Text = "Test Output:",
                Location = new Point(10, 320),
                AutoSize = true
            };
            _rtbTestOutput = new RichTextBox
            {
                Location = new Point(10, 338),
                Size = new Size(640, 155),
                ReadOnly = true,
                Font = new Font("Consolas", 9f),
                WordWrap = true
            };

            tabModel.Controls.AddRange(new Control[]
            {
                _lblConnection, _lstModels,
                _btnSetActive, _btnTest, _btnDownload, _btnDelete, _btnImport, _btnRefresh,
                _progressBar, _lblProgress,
                lblTestOutput, _rtbTestOutput
            });

            _tabControl.TabPages.Add(tabModel);
        }

        private void BuildGeneralTab()
        {
            var tabGeneral = new TabPage("General");
            int y = 20;
            int labelX = 15;
            int inputX = 170;
            int inputW = 350;

            // Ollama URL
            tabGeneral.Controls.Add(new Label { Text = "Ollama URL:", Location = new Point(labelX, y + 3), AutoSize = true });
            _txtOllamaUrl = new TextBox
            {
                Text = "http://localhost:" + _config.OllamaPort,
                Location = new Point(inputX, y),
                Size = new Size(inputW, 22)
            };
            tabGeneral.Controls.Add(_txtOllamaUrl);
            y += 35;

            // Backend port
            tabGeneral.Controls.Add(new Label { Text = "Backend Port:", Location = new Point(labelX, y + 3), AutoSize = true });
            _txtBackendPort = new TextBox
            {
                Text = _config.BackendPort.ToString(),
                Location = new Point(inputX, y),
                Size = new Size(80, 22)
            };
            tabGeneral.Controls.Add(_txtBackendPort);
            y += 40;

            // Auto-launch Ollama
            _chkAutoOllama = new CheckBox
            {
                Text = "Auto-launch Ollama on add-in startup",
                Location = new Point(labelX, y),
                AutoSize = true,
                Checked = _config.AutoLaunchOllama
            };
            tabGeneral.Controls.Add(_chkAutoOllama);
            y += 28;

            // Auto-launch Backend
            _chkAutoBackend = new CheckBox
            {
                Text = "Auto-launch Backend on add-in startup",
                Location = new Point(labelX, y),
                AutoSize = true,
                Checked = _config.AutoLaunchBackend
            };
            tabGeneral.Controls.Add(_chkAutoBackend);
            y += 28;

            // Kill on disconnect
            _chkKillOnDisconnect = new CheckBox
            {
                Text = "Kill managed processes when add-in unloads",
                Location = new Point(labelX, y),
                AutoSize = true,
                Checked = _config.KillOnDisconnect
            };
            tabGeneral.Controls.Add(_chkKillOnDisconnect);
            y += 40;

            // Project root (read-only)
            tabGeneral.Controls.Add(new Label { Text = "Project Root:", Location = new Point(labelX, y + 3), AutoSize = true });
            _txtProjectRoot = new TextBox
            {
                Text = _config.ProjectRoot ?? "",
                Location = new Point(inputX, y),
                Size = new Size(inputW, 22),
                ReadOnly = true,
                BackColor = SystemColors.Control
            };
            tabGeneral.Controls.Add(_txtProjectRoot);
            y += 40;

            // Open config file button
            _btnOpenConfig = new Button
            {
                Text = "Open config file in Notepad",
                Location = new Point(labelX, y),
                Size = new Size(200, 28)
            };
            _btnOpenConfig.Click += BtnOpenConfig_Click;
            tabGeneral.Controls.Add(_btnOpenConfig);

            _tabControl.TabPages.Add(tabGeneral);
        }

        // ----- Catalog Loading -------------------------------------------------

        private void LoadCatalog()
        {
            try
            {
                // Try embedded resource first, then file next to DLL
                string dllDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? "";
                string catalogPath = Path.Combine(dllDir, "Config", "swse-model-catalog.json");

                if (!File.Exists(catalogPath))
                {
                    // Also check one level up in case of build output structure
                    catalogPath = Path.Combine(dllDir, "swse-model-catalog.json");
                }

                if (File.Exists(catalogPath))
                {
                    string json = File.ReadAllText(catalogPath);
                    _catalog = JsonConvert.DeserializeObject<List<CatalogEntry>>(json)
                               ?? new List<CatalogEntry>();
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine("[SWSE] Model catalog not found.");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine("[SWSE] Failed to load catalog: " + ex.Message);
            }
        }

        // ----- Model List Refresh -----------------------------------------------

        private async Task RefreshModelList()
        {
            _lstModels.Items.Clear();
            _modelEntries.Clear();

            bool connected = await _ollamaService.CheckHealthAsync();
            _lblConnection.Text = connected
                ? "[OK] Ollama connected at " + "http://localhost:" + _config.OllamaPort
                : "[X] Ollama not reachable at port " + _config.OllamaPort;
            _lblConnection.ForeColor = connected ? Color.DarkGreen : Color.DarkRed;

            // Get installed models
            var installed = new Dictionary<string, OllamaModel>(StringComparer.OrdinalIgnoreCase);
            if (connected)
            {
                try
                {
                    var models = await _ollamaService.ListModelsAsync();
                    foreach (var m in models)
                    {
                        installed[m.Name] = m;
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine("[SWSE] Failed to list models: " + ex.Message);
                }
            }

            // Merge catalog + installed into unified list
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            // Add catalog entries first
            foreach (var cat in _catalog)
            {
                bool isInstalled = installed.ContainsKey(cat.Name);
                OllamaModel inst = isInstalled ? installed[cat.Name] : null;

                var entry = new ModelEntry
                {
                    Name = cat.Name,
                    DisplayName = cat.DisplayName,
                    Description = cat.Description,
                    SizeDisplay = isInstalled ? inst.SizeDisplay : cat.Size,
                    IsInstalled = isInstalled,
                    IsActive = string.Equals(cat.Name, _activeModel, StringComparison.OrdinalIgnoreCase),
                    Recommended = cat.Recommended,
                    CpuOptimized = cat.CpuOptimized
                };

                _modelEntries.Add(entry);
                seen.Add(cat.Name);
            }

            // Add installed models not in catalog
            foreach (var kvp in installed)
            {
                if (!seen.Contains(kvp.Key))
                {
                    var m = kvp.Value;
                    var entry = new ModelEntry
                    {
                        Name = m.Name,
                        DisplayName = m.Name,
                        Description = m.Details?.Family ?? "Installed model",
                        SizeDisplay = m.SizeDisplay,
                        IsInstalled = true,
                        IsActive = string.Equals(m.Name, _activeModel, StringComparison.OrdinalIgnoreCase),
                        Recommended = false,
                        CpuOptimized = false
                    };
                    _modelEntries.Add(entry);
                }
            }

            // Populate ListView
            foreach (var entry in _modelEntries)
            {
                string status = "";
                if (entry.IsActive) status = "[ACTIVE]";
                else if (entry.IsInstalled) status = "Installed";
                else status = "Not installed";

                var tags = new List<string>();
                if (entry.Recommended) tags.Add("Rec");
                if (entry.CpuOptimized) tags.Add("CPU");
                if (entry.IsActive) tags.Add("Active");

                var item = new ListViewItem(new string[]
                {
                    entry.DisplayName,
                    entry.Description,
                    entry.SizeDisplay,
                    status,
                    string.Join(", ", tags)
                });

                if (entry.IsActive)
                    item.BackColor = Color.FromArgb(0xE8, 0xF5, 0xE9); // light green
                else if (!entry.IsInstalled)
                    item.ForeColor = Color.Gray;

                _lstModels.Items.Add(item);
            }

            UpdateButtonStates();
        }

        // ----- Button state management ------------------------------------------

        private void UpdateButtonStates()
        {
            var entry = GetSelectedEntry();
            bool hasSelection = entry != null;
            bool installed = entry?.IsInstalled ?? false;
            bool isActive = entry?.IsActive ?? false;

            _btnSetActive.Enabled = hasSelection && installed && !isActive;
            _btnTest.Enabled = hasSelection && installed;
            _btnDownload.Enabled = hasSelection && !installed;
            _btnDelete.Enabled = hasSelection && installed && !isActive;
        }

        private ModelEntry GetSelectedEntry()
        {
            if (_lstModels.SelectedIndices.Count == 0) return null;
            int idx = _lstModels.SelectedIndices[0];
            if (idx < 0 || idx >= _modelEntries.Count) return null;
            return _modelEntries[idx];
        }

        private void LstModels_SelectedIndexChanged(object sender, EventArgs e)
        {
            UpdateButtonStates();
        }

        // ----- Set Active -------------------------------------------------------

        private void BtnSetActive_Click(object sender, EventArgs e)
        {
            var entry = GetSelectedEntry();
            if (entry == null || !entry.IsInstalled) return;

            _activeModel = entry.Name;

            // Update all entries
            foreach (var m in _modelEntries)
                m.IsActive = string.Equals(m.Name, _activeModel, StringComparison.OrdinalIgnoreCase);

            // Refresh display
            RefreshListViewColors();
            UpdateButtonStates();

            _rtbTestOutput.AppendText("[OK] Active model set to: " + _activeModel + "\n");
        }

        private void RefreshListViewColors()
        {
            for (int i = 0; i < _lstModels.Items.Count && i < _modelEntries.Count; i++)
            {
                var entry = _modelEntries[i];
                var item = _lstModels.Items[i];

                string status = "";
                if (entry.IsActive) status = "[ACTIVE]";
                else if (entry.IsInstalled) status = "Installed";
                else status = "Not installed";

                item.SubItems[3].Text = status;

                var tags = new List<string>();
                if (entry.Recommended) tags.Add("Rec");
                if (entry.CpuOptimized) tags.Add("CPU");
                if (entry.IsActive) tags.Add("Active");
                item.SubItems[4].Text = string.Join(", ", tags);

                if (entry.IsActive)
                {
                    item.BackColor = Color.FromArgb(0xE8, 0xF5, 0xE9);
                    item.ForeColor = Color.Black;
                }
                else if (!entry.IsInstalled)
                {
                    item.BackColor = Color.White;
                    item.ForeColor = Color.Gray;
                }
                else
                {
                    item.BackColor = Color.White;
                    item.ForeColor = Color.Black;
                }
            }
        }

        // ----- Test Model -------------------------------------------------------

        private async void BtnTest_Click(object sender, EventArgs e)
        {
            var entry = GetSelectedEntry();
            if (entry == null || !entry.IsInstalled) return;

            _btnTest.Enabled = false;
            _rtbTestOutput.Clear();
            _rtbTestOutput.AppendText("[->] Testing model: " + entry.Name + "...\n");

            var result = await _ollamaService.TestModelAsync(entry.Name);

            if (result.Success)
            {
                _rtbTestOutput.AppendText("[OK] Response from " + result.Model + ":\n");
                _rtbTestOutput.AppendText(result.Response.Trim() + "\n\n");
                _rtbTestOutput.AppendText(string.Format(
                    "Duration: {0:F1}s  |  Tokens evaluated: {1}\n",
                    result.TotalDurationSeconds, result.EvalCount));
            }
            else
            {
                _rtbTestOutput.AppendText("[FAIL] Test failed: " + result.Error + "\n");
            }

            _btnTest.Enabled = true;
        }

        // ----- Download Model ---------------------------------------------------

        private async void BtnDownload_Click(object sender, EventArgs e)
        {
            var entry = GetSelectedEntry();
            if (entry == null || entry.IsInstalled) return;

            var confirmResult = MessageBox.Show(
                "Download model '" + entry.Name + "' (" + entry.SizeDisplay + ")?\n\n"
                + "This may take several minutes depending on your connection.",
                "Confirm Download",
                MessageBoxButtons.OKCancel,
                MessageBoxIcon.Question);

            if (confirmResult != DialogResult.OK) return;

            SetDownloadUIState(true);
            _rtbTestOutput.Clear();
            _rtbTestOutput.AppendText("[->] Downloading " + entry.Name + "...\n");

            _downloadCts = new CancellationTokenSource();

            var progress = new Progress<DownloadProgress>(dp =>
            {
                if (dp.Total > 0)
                {
                    _progressBar.Value = Math.Min(100, (int)dp.Percent);
                    _lblProgress.Text = string.Format(
                        "{0}: {1:F0}%  ({2:F0} MB / {3:F0} MB)",
                        dp.Status, dp.Percent,
                        dp.Completed / 1_000_000.0,
                        dp.Total / 1_000_000.0);
                }
                else
                {
                    _lblProgress.Text = dp.Status;
                }
            });

            try
            {
                await _ollamaService.DownloadModelAsync(entry.Name, progress, _downloadCts.Token);
                _rtbTestOutput.AppendText("[OK] Download complete: " + entry.Name + "\n");
            }
            catch (OperationCanceledException)
            {
                _rtbTestOutput.AppendText("[X] Download cancelled.\n");
            }
            catch (Exception ex)
            {
                _rtbTestOutput.AppendText("[FAIL] Download failed: " + ex.Message + "\n");
            }
            finally
            {
                SetDownloadUIState(false);
                _downloadCts?.Dispose();
                _downloadCts = null;
            }

            await RefreshModelList();
        }

        private void SetDownloadUIState(bool downloading)
        {
            _progressBar.Visible = downloading;
            _lblProgress.Visible = downloading;
            _progressBar.Value = 0;
            _btnDownload.Enabled = !downloading;
            _btnDelete.Enabled = !downloading;
            _btnImport.Enabled = !downloading;
        }

        // ----- Delete Model -----------------------------------------------------

        private async void BtnDelete_Click(object sender, EventArgs e)
        {
            var entry = GetSelectedEntry();
            if (entry == null || !entry.IsInstalled || entry.IsActive) return;

            var confirmResult = MessageBox.Show(
                "Delete model '" + entry.Name + "' from Ollama?\n\n"
                + "You can re-download it later.",
                "Confirm Delete",
                MessageBoxButtons.OKCancel,
                MessageBoxIcon.Warning);

            if (confirmResult != DialogResult.OK) return;

            try
            {
                await _ollamaService.DeleteModelAsync(entry.Name);
                _rtbTestOutput.AppendText("[OK] Deleted: " + entry.Name + "\n");
            }
            catch (Exception ex)
            {
                _rtbTestOutput.AppendText("[FAIL] Delete failed: " + ex.Message + "\n");
            }

            await RefreshModelList();
        }

        // ----- Import from File -------------------------------------------------

        private async void BtnImport_Click(object sender, EventArgs e)
        {
            using (var ofd = new OpenFileDialog())
            {
                ofd.Title = "Select GGUF Model File";
                ofd.Filter = "GGUF Models (*.gguf)|*.gguf|All Files (*.*)|*.*";
                ofd.CheckFileExists = true;

                if (ofd.ShowDialog() != DialogResult.OK) return;

                string ggufPath = ofd.FileName;

                // Ask for model name
                string suggestedName = Path.GetFileNameWithoutExtension(ggufPath)
                    .ToLowerInvariant()
                    .Replace(" ", "-")
                    .Replace("_", "-");

                string modelName = PromptForText(
                    "Import Model",
                    "Enter a name for this model in Ollama:",
                    suggestedName);

                if (string.IsNullOrWhiteSpace(modelName)) return;

                SetDownloadUIState(true);
                _rtbTestOutput.Clear();
                _rtbTestOutput.AppendText("[->] Importing " + ggufPath + "\n");
                _rtbTestOutput.AppendText("     as '" + modelName + "'...\n");

                _downloadCts = new CancellationTokenSource();
                var progress = new Progress<DownloadProgress>(dp =>
                {
                    _lblProgress.Text = dp.Status;
                });

                try
                {
                    await _ollamaService.CreateModelFromFileAsync(
                        modelName, ggufPath, progress, _downloadCts.Token);
                    _rtbTestOutput.AppendText("[OK] Model created: " + modelName + "\n");
                    _rtbTestOutput.AppendText("     Source: " + ggufPath + "\n");
                }
                catch (OperationCanceledException)
                {
                    _rtbTestOutput.AppendText("[X] Import cancelled.\n");
                }
                catch (Exception ex)
                {
                    _rtbTestOutput.AppendText("[FAIL] Import failed: " + ex.Message + "\n");
                }
                finally
                {
                    SetDownloadUIState(false);
                    _downloadCts?.Dispose();
                    _downloadCts = null;
                }

                await RefreshModelList();
            }
        }

        /// <summary>Simple input dialog to prompt for a text value.</summary>
        private static string PromptForText(string title, string label, string defaultValue)
        {
            var dlg = new Form
            {
                Text = title,
                Size = new Size(400, 160),
                StartPosition = FormStartPosition.CenterParent,
                FormBorderStyle = FormBorderStyle.FixedDialog,
                MaximizeBox = false,
                MinimizeBox = false
            };

            var lbl = new Label { Text = label, Location = new Point(12, 15), AutoSize = true };
            var txt = new TextBox { Text = defaultValue, Location = new Point(12, 38), Size = new Size(360, 22) };
            var btnOk = new Button { Text = "OK", DialogResult = DialogResult.OK, Location = new Point(212, 75), Size = new Size(75, 26) };
            var btnCx = new Button { Text = "Cancel", DialogResult = DialogResult.Cancel, Location = new Point(297, 75), Size = new Size(75, 26) };

            dlg.AcceptButton = btnOk;
            dlg.CancelButton = btnCx;
            dlg.Controls.AddRange(new Control[] { lbl, txt, btnOk, btnCx });

            return dlg.ShowDialog() == DialogResult.OK ? txt.Text.Trim() : null;
        }

        // ----- Open Config File -------------------------------------------------

        private void BtnOpenConfig_Click(object sender, EventArgs e)
        {
            try
            {
                string dllDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? "";
                string configPath = Path.Combine(dllDir, "swse-config.json");

                if (File.Exists(configPath))
                {
                    System.Diagnostics.Process.Start("notepad.exe", configPath);
                }
                else
                {
                    MessageBox.Show(
                        "Config file not found at:\n" + configPath,
                        "File Not Found",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Failed to open config: " + ex.Message);
            }
        }

        // ----- Save Settings ----------------------------------------------------

        private void BtnSave_Click(object sender, EventArgs e)
        {
            // Parse Ollama port from URL
            try
            {
                var uri = new Uri(_txtOllamaUrl.Text.Trim());
                _config.OllamaPort = uri.Port > 0 ? uri.Port : 11434;
            }
            catch
            {
                _config.OllamaPort = 11434;
            }

            // Parse backend port
            int backendPort;
            if (int.TryParse(_txtBackendPort.Text.Trim(), out backendPort) && backendPort > 0 && backendPort < 65536)
            {
                _config.BackendPort = backendPort;
            }

            _config.AutoLaunchOllama = _chkAutoOllama.Checked;
            _config.AutoLaunchBackend = _chkAutoBackend.Checked;
            _config.KillOnDisconnect = _chkKillOnDisconnect.Checked;
            _config.ActiveModel = _activeModel;

            // Write config to disk
            SaveConfigToDisk();

            // Notify parent
            _onSave?.Invoke(_config);

            Close();
        }

        private void SaveConfigToDisk()
        {
            try
            {
                string dllDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? "";
                string configPath = Path.Combine(dllDir, "swse-config.json");

                string json = JsonConvert.SerializeObject(_config, Formatting.Indented);
                File.WriteAllText(configPath, json);

                System.Diagnostics.Debug.WriteLine("[SWSE] Config saved to " + configPath);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Failed to save config: " + ex.Message,
                    "Save Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
            }
        }

        // ----- Cleanup ----------------------------------------------------------

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            _downloadCts?.Cancel();
            _downloadCts?.Dispose();
            _ollamaService?.Dispose();
            base.OnFormClosed(e);
        }
    }
}
