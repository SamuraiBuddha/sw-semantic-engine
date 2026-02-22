// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Commands/ExplainApiCommand.cs
// WinForms dialog for the "Explain API" toolbar button.
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
    /// A modeless WinForms dialog that lets the user look up SolidWorks API
    /// method documentation from the backend reference database.
    /// </summary>
    public class ExplainApiCommand : Form
    {
        // ----- Controls ----------------------------------------------------

        private readonly Label _lblMethod;
        private readonly ComboBox _cboMethod;
        private readonly Button _btnLookUp;
        private readonly Label _lblResult;
        private readonly RichTextBox _rtbResult;
        private readonly Label _lblStatus;

        // ----- Dependencies ------------------------------------------------

        private readonly ApiClient _apiClient;
        private readonly SolidWorksContextService _contextService;

        // ----- Known methods for autocomplete ------------------------------

        private static readonly string[] KnownMethods = new string[]
        {
            "GetActiveDoc",
            "CreateSketch",
            "InsertSketch",
            "FeatureExtrusion3",
            "CreateCircle",
            "CreateLine",
            "AddConstraint",
            "CreateDimension",
            "CreateToleranceFeature",
            "ClearSelection2",
            "FeatureCut4",
            "FeatureRevolve2"
        };

        // ----- Constructor -------------------------------------------------

        public ExplainApiCommand(ApiClient apiClient, SolidWorksContextService contextService)
        {
            _apiClient = apiClient ?? throw new ArgumentNullException(nameof(apiClient));
            _contextService = contextService;

            // -- Form properties --
            Text = "Semantic Engine - Explain API";
            Size = new Size(640, 520);
            StartPosition = FormStartPosition.CenterScreen;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;

            // -- Method combo with autocomplete --
            _lblMethod = new Label
            {
                Text = "Method Name:",
                Location = new Point(12, 15),
                AutoSize = true
            };

            _cboMethod = new ComboBox
            {
                Location = new Point(110, 12),
                Size = new Size(320, 24),
                DropDownStyle = ComboBoxStyle.DropDown,
                AutoCompleteMode = AutoCompleteMode.SuggestAppend,
                AutoCompleteSource = AutoCompleteSource.ListItems
            };
            _cboMethod.Items.AddRange(KnownMethods);

            // Pre-select a method based on current selection type (if available)
            SuggestMethodFromSelection();

            // -- Look up button --
            _btnLookUp = new Button
            {
                Text = "Look Up",
                Location = new Point(440, 10),
                Size = new Size(92, 28)
            };
            _btnLookUp.Click += BtnLookUp_Click;

            // Pressing Enter in the combo triggers lookup
            _cboMethod.KeyDown += (s, e) =>
            {
                if (e.KeyCode == Keys.Enter)
                {
                    e.SuppressKeyPress = true;
                    BtnLookUp_Click(s, e);
                }
            };

            // -- Result display --
            _lblResult = new Label
            {
                Text = "Reference:",
                Location = new Point(12, 50),
                AutoSize = true
            };

            _rtbResult = new RichTextBox
            {
                Location = new Point(12, 70),
                Size = new Size(600, 370),
                ReadOnly = true,
                Font = new Font("Consolas", 9.5f),
                WordWrap = true
            };

            // -- Status --
            _lblStatus = new Label
            {
                Text = "Ready. Type a method name or select from the dropdown.",
                Location = new Point(12, 450),
                AutoSize = true
            };

            // -- Add controls --
            Controls.AddRange(new Control[]
            {
                _lblMethod, _cboMethod, _btnLookUp,
                _lblResult, _rtbResult,
                _lblStatus
            });
        }

        // ----- Event Handlers ----------------------------------------------

        private async void BtnLookUp_Click(object sender, EventArgs e)
        {
            string methodName = _cboMethod.Text.Trim();
            if (string.IsNullOrEmpty(methodName))
            {
                MessageBox.Show("Please enter a method name.", "Validation",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            _btnLookUp.Enabled = false;
            _lblStatus.Text = "Looking up...";
            _rtbResult.Clear();

            APIReferenceResponse response = await _apiClient.GetReferenceAsync(methodName);

            if (response != null)
            {
                _rtbResult.Text = FormatReference(response);
                _lblStatus.Text = string.Format("Found: {0}.{1}",
                    response.Interface ?? "?", response.MethodName ?? methodName);
            }
            else
            {
                _rtbResult.Text = "[FAIL] Method not found or backend unreachable.\n"
                                + "Make sure the server is running at http://localhost:8000\n"
                                + "and the method name is correct (case-sensitive).";
                _lblStatus.Text = "Error - method not found or backend unreachable.";
            }

            _btnLookUp.Enabled = true;
        }

        // ----- Private Helpers ---------------------------------------------

        /// <summary>
        /// Formats the API reference response into a readable text block.
        /// </summary>
        private static string FormatReference(APIReferenceResponse r)
        {
            var sb = new System.Text.StringBuilder();

            sb.AppendLine("========================================");
            sb.AppendFormat("  {0}.{1}", r.Interface ?? "?", r.MethodName ?? "?").AppendLine();
            sb.AppendLine("========================================");
            sb.AppendLine();

            // Signature
            if (!string.IsNullOrEmpty(r.Signature))
            {
                sb.AppendLine("SIGNATURE:");
                sb.AppendLine("  " + r.Signature);
                sb.AppendLine();
            }

            // Return type
            if (!string.IsNullOrEmpty(r.ReturnType))
            {
                sb.AppendLine("RETURNS:");
                sb.AppendLine("  " + r.ReturnType);
                sb.AppendLine();
            }

            // Description
            if (!string.IsNullOrEmpty(r.Description))
            {
                sb.AppendLine("DESCRIPTION:");
                sb.AppendLine("  " + r.Description);
                sb.AppendLine();
            }

            // Parameters
            if (r.Parameters != null && r.Parameters.Count > 0)
            {
                sb.AppendLine("PARAMETERS:");
                foreach (var p in r.Parameters)
                {
                    sb.AppendFormat("  {0} ({1})", p.Name ?? "?", p.Type ?? "?").AppendLine();
                    if (!string.IsNullOrEmpty(p.Description))
                    {
                        sb.AppendLine("      " + p.Description);
                    }
                }
                sb.AppendLine();
            }

            // Example code
            if (!string.IsNullOrEmpty(r.ExampleCode))
            {
                sb.AppendLine("EXAMPLE:");
                sb.AppendLine("----------------------------------------");
                sb.AppendLine(r.ExampleCode);
                sb.AppendLine("----------------------------------------");
            }

            return sb.ToString();
        }

        /// <summary>
        /// Suggests a method name based on the currently selected entity type.
        /// </summary>
        private void SuggestMethodFromSelection()
        {
            if (_contextService == null) return;

            try
            {
                string selInfo = _contextService.GetSelectedEntityInfo();
                if (string.IsNullOrEmpty(selInfo)) return;

                // Simple heuristic: suggest a method based on selection type keywords
                if (selInfo.Contains("Face"))
                {
                    _cboMethod.Text = "FeatureExtrusion3";
                }
                else if (selInfo.Contains("Edge"))
                {
                    _cboMethod.Text = "FeatureCut4";
                }
                else if (selInfo.Contains("Sketch"))
                {
                    _cboMethod.Text = "InsertSketch";
                }
                else if (selInfo.Contains("Component"))
                {
                    _cboMethod.Text = "GetActiveDoc";
                }
            }
            catch
            {
                // Not critical -- leave combo empty
            }
        }
    }
}
