// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Commands/GenerateCodeCommand.cs
// WinForms dialog for the "Generate Code" toolbar button.
// ---------------------------------------------------------------------------

using System;
using System.Drawing;
using System.Windows.Forms;
using SolidWorksSemanticEngine.Bridge;
using SolidWorksSemanticEngine.Models;
using SolidWorksSemanticEngine.Services;

namespace SolidWorksSemanticEngine.Commands
{
    /// <summary>
    /// A modeless WinForms dialog that lets the user type a natural-language
    /// prompt, pick a domain, and receive generated SolidWorks API code from
    /// the backend.
    /// </summary>
    public class GenerateCodeCommand : Form
    {
        // ----- Controls ----------------------------------------------------

        private readonly Label _lblPrompt;
        private readonly TextBox _txtPrompt;
        private readonly Label _lblDomain;
        private readonly ComboBox _cboDomain;
        private readonly CheckBox _chkComments;
        private readonly Button _btnGenerate;
        private readonly Label _lblOutput;
        private readonly RichTextBox _rtbCode;
        private readonly Label _lblStatus;

        // ----- Dependencies ------------------------------------------------

        private readonly ApiClient _apiClient;
        private readonly SolidWorksContextService _contextService;

        // ----- Domain helper class -----------------------------------------

        /// <summary>
        /// Maps display name (shown in combo) to wire value (sent to backend).
        /// </summary>
        private class DomainItem
        {
            public string DisplayName { get; }
            public string WireValue { get; }

            public DomainItem(string displayName, string wireValue)
            {
                DisplayName = displayName;
                WireValue = wireValue;
            }

            public override string ToString()
            {
                return DisplayName;
            }
        }

        private static readonly DomainItem[] Domains = new DomainItem[]
        {
            new DomainItem("API (General)", "api"),
            new DomainItem("Sketch", "sketch"),
            new DomainItem("Feature", "feature"),
            new DomainItem("GD&T", "gdt")
        };

        // ----- Constructor -------------------------------------------------

        public GenerateCodeCommand(ApiClient apiClient, SolidWorksContextService contextService)
        {
            _apiClient = apiClient ?? throw new ArgumentNullException(nameof(apiClient));
            _contextService = contextService;

            // -- Form properties --
            Text = "Semantic Engine - Generate Code";
            Size = new Size(620, 520);
            StartPosition = FormStartPosition.CenterScreen;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;

            // -- Prompt label + textbox --
            _lblPrompt = new Label { Text = "Prompt:", Location = new Point(12, 15), AutoSize = true };
            _txtPrompt = new TextBox
            {
                Location = new Point(12, 35),
                Size = new Size(580, 60),
                Multiline = true,
                ScrollBars = ScrollBars.Vertical
            };

            // -- Domain combo --
            _lblDomain = new Label { Text = "Domain:", Location = new Point(12, 105), AutoSize = true };
            _cboDomain = new ComboBox
            {
                Location = new Point(70, 102),
                Size = new Size(160, 24),
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            _cboDomain.Items.AddRange(Domains);
            _cboDomain.SelectedIndex = 0;

            // -- Include comments checkbox --
            _chkComments = new CheckBox
            {
                Text = "Include comments",
                Location = new Point(250, 104),
                AutoSize = true,
                Checked = true
            };

            // -- Generate button --
            _btnGenerate = new Button
            {
                Text = "Generate",
                Location = new Point(500, 100),
                Size = new Size(92, 28)
            };
            _btnGenerate.Click += BtnGenerate_Click;

            // -- Output label + rich text box --
            _lblOutput = new Label { Text = "Generated Code:", Location = new Point(12, 140), AutoSize = true };
            _rtbCode = new RichTextBox
            {
                Location = new Point(12, 160),
                Size = new Size(580, 280),
                ReadOnly = true,
                Font = new Font("Consolas", 9.5f),
                WordWrap = false
            };

            // -- Status label --
            _lblStatus = new Label
            {
                Text = "Ready.",
                Location = new Point(12, 450),
                AutoSize = true
            };

            // -- Add controls --
            Controls.AddRange(new Control[]
            {
                _lblPrompt, _txtPrompt,
                _lblDomain, _cboDomain, _chkComments,
                _btnGenerate,
                _lblOutput, _rtbCode,
                _lblStatus
            });
        }

        // ----- Event Handlers ----------------------------------------------

        private async void BtnGenerate_Click(object sender, EventArgs e)
        {
            string prompt = _txtPrompt.Text.Trim();
            if (string.IsNullOrEmpty(prompt))
            {
                MessageBox.Show("Please enter a prompt.", "Validation",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            _btnGenerate.Enabled = false;
            _lblStatus.Text = "Generating...";
            _rtbCode.Clear();

            // Gather full context from the active SolidWorks document
            string context = string.Empty;
            if (_contextService != null)
            {
                context = _contextService.BuildFullContext();
            }

            // Get the wire value from the selected domain item
            DomainItem selectedDomain = _cboDomain.SelectedItem as DomainItem;
            string wireValue = selectedDomain != null ? selectedDomain.WireValue : "api";

            var request = new CodeGenerationRequest
            {
                Prompt = prompt,
                Context = context,
                Domain = wireValue,
                IncludeComments = _chkComments.Checked
            };

            CodeGenerationResponse response = await _apiClient.GenerateCodeAsync(request);

            if (response != null)
            {
                // Display the generated code
                _rtbCode.Text = response.Code ?? "(no code returned)";

                // Append explanation as comments
                if (!string.IsNullOrEmpty(response.Explanation))
                {
                    _rtbCode.AppendText("\n\n// --- Explanation ---\n");
                    foreach (string line in response.Explanation.Split('\n'))
                    {
                        _rtbCode.AppendText("// " + line.TrimEnd() + "\n");
                    }
                }

                // Append warnings with [WARN] markers
                if (response.Warnings != null && response.Warnings.Count > 0)
                {
                    _rtbCode.AppendText("\n// --- Warnings ---\n");
                    foreach (string warning in response.Warnings)
                    {
                        _rtbCode.AppendText("// [WARN] " + warning + "\n");
                    }
                }

                // Show confidence in status
                _lblStatus.Text = string.Format(
                    "Done  [->]  Confidence: {0:P0}",
                    response.Confidence);
            }
            else
            {
                _rtbCode.Text = "[FAIL] Unable to reach the backend API.\n"
                              + "The add-in auto-launches the backend on startup.\n"
                              + "If this persists, check that swse-config.json is correct\n"
                              + "and that port 8000+ is not blocked by another service.";
                _lblStatus.Text = "Error - backend unreachable.";
            }

            _btnGenerate.Enabled = true;
        }
    }
}
