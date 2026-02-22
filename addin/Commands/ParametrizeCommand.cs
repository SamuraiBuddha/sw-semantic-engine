// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Commands/ParametrizeCommand.cs
// WinForms dialog for the "Parametrize" toolbar button.
// ---------------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;
using SolidWorksSemanticEngine.Bridge;
using SolidWorksSemanticEngine.Models;
using SolidWorksSemanticEngine.Services;

namespace SolidWorksSemanticEngine.Commands
{
    /// <summary>
    /// A modeless WinForms dialog that lets the user pick a parameter space,
    /// edit parameter values, and resolve them to generated SolidWorks API
    /// code via the backend.
    /// </summary>
    public class ParametrizeCommand : Form
    {
        // ----- Controls ----------------------------------------------------

        private readonly Label _lblSpace;
        private readonly ComboBox _cboSpace;
        private readonly Button _btnPopulate;
        private readonly DataGridView _dgvParams;
        private readonly Button _btnResolve;
        private readonly Label _lblOutput;
        private readonly RichTextBox _rtbCode;
        private readonly Label _lblStatus;

        // ----- Dependencies ------------------------------------------------

        private readonly ApiClient _apiClient;
        private readonly SolidWorksContextService _contextService;

        // ----- Known Parameter Spaces (matches backend) --------------------

        private static readonly Dictionary<string, Dictionary<string, object>> KnownSpaces =
            new Dictionary<string, Dictionary<string, object>>
            {
                {
                    "extrusion_depth", new Dictionary<string, object>
                    {
                        { "depth_mm", 25.0 },
                        { "direction", "single" },
                        { "draft_angle_deg", 0.0 }
                    }
                },
                {
                    "circle_sketch", new Dictionary<string, object>
                    {
                        { "center_x_mm", 0.0 },
                        { "center_y_mm", 0.0 },
                        { "radius_mm", 10.0 }
                    }
                },
                {
                    "rectangle_sketch", new Dictionary<string, object>
                    {
                        { "x1_mm", -10.0 },
                        { "y1_mm", -10.0 },
                        { "x2_mm", 10.0 },
                        { "y2_mm", 10.0 }
                    }
                },
                {
                    "cut_extrude", new Dictionary<string, object>
                    {
                        { "depth_mm", 10.0 },
                        { "through_all", false }
                    }
                },
                {
                    "revolve_boss", new Dictionary<string, object>
                    {
                        { "angle_deg", 360.0 },
                        { "thin_wall", false },
                        { "thin_thickness_mm", 1.0 }
                    }
                },
                {
                    "fillet_feature", new Dictionary<string, object>
                    {
                        { "radius_mm", 2.0 }
                    }
                },
                {
                    "chamfer_feature", new Dictionary<string, object>
                    {
                        { "distance_mm", 1.0 },
                        { "angle_deg", 45.0 }
                    }
                }
            };

        // ----- Constructor -------------------------------------------------

        public ParametrizeCommand(ApiClient apiClient, SolidWorksContextService contextService)
        {
            _apiClient = apiClient ?? throw new ArgumentNullException(nameof(apiClient));
            _contextService = contextService;

            // -- Form properties --
            Text = "Semantic Engine - Parametrize";
            Size = new Size(640, 580);
            StartPosition = FormStartPosition.CenterScreen;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;

            // -- Parameter space combo --
            _lblSpace = new Label
            {
                Text = "Parameter Space:",
                Location = new Point(12, 15),
                AutoSize = true
            };

            _cboSpace = new ComboBox
            {
                Location = new Point(130, 12),
                Size = new Size(200, 24),
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            foreach (string spaceName in KnownSpaces.Keys)
            {
                _cboSpace.Items.Add(spaceName);
            }
            _cboSpace.SelectedIndex = 0;

            _btnPopulate = new Button
            {
                Text = "Load Defaults",
                Location = new Point(340, 10),
                Size = new Size(100, 28)
            };
            _btnPopulate.Click += BtnPopulate_Click;

            // -- Parameter grid --
            _dgvParams = new DataGridView
            {
                Location = new Point(12, 48),
                Size = new Size(600, 160),
                AllowUserToAddRows = false,
                AllowUserToDeleteRows = false,
                RowHeadersVisible = false,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                EditMode = DataGridViewEditMode.EditOnEnter
            };
            _dgvParams.Columns.Add("ParamName", "Parameter");
            _dgvParams.Columns.Add("ParamValue", "Value");
            _dgvParams.Columns["ParamName"].ReadOnly = true;

            // -- Resolve button --
            _btnResolve = new Button
            {
                Text = "Resolve",
                Location = new Point(520, 215),
                Size = new Size(92, 28)
            };
            _btnResolve.Click += BtnResolve_Click;

            // -- Output --
            _lblOutput = new Label
            {
                Text = "Generated Code:",
                Location = new Point(12, 250),
                AutoSize = true
            };

            _rtbCode = new RichTextBox
            {
                Location = new Point(12, 270),
                Size = new Size(600, 230),
                ReadOnly = true,
                Font = new Font("Consolas", 9.5f),
                WordWrap = false
            };

            // -- Status --
            _lblStatus = new Label
            {
                Text = "Ready. Select a parameter space and click Load Defaults.",
                Location = new Point(12, 510),
                AutoSize = true
            };

            // -- Add controls --
            Controls.AddRange(new Control[]
            {
                _lblSpace, _cboSpace, _btnPopulate,
                _dgvParams,
                _btnResolve,
                _lblOutput, _rtbCode,
                _lblStatus
            });

            // Load defaults for the initially selected space
            PopulateGrid();
        }

        // ----- Event Handlers ----------------------------------------------

        private void BtnPopulate_Click(object sender, EventArgs e)
        {
            PopulateGrid();
        }

        private async void BtnResolve_Click(object sender, EventArgs e)
        {
            string spaceName = _cboSpace.SelectedItem?.ToString();
            if (string.IsNullOrEmpty(spaceName))
            {
                MessageBox.Show("Please select a parameter space.", "Validation",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            _btnResolve.Enabled = false;
            _lblStatus.Text = "Resolving parameters...";
            _rtbCode.Clear();

            // Gather assignments from the grid
            var assignments = new Dictionary<string, object>();
            for (int i = 0; i < _dgvParams.Rows.Count; i++)
            {
                string name = _dgvParams.Rows[i].Cells["ParamName"].Value?.ToString();
                string rawVal = _dgvParams.Rows[i].Cells["ParamValue"].Value?.ToString();

                if (string.IsNullOrEmpty(name)) continue;

                // Attempt to parse as number, bool, or leave as string
                assignments[name] = ParseValue(rawVal);
            }

            var request = new ParameterResolveRequest
            {
                ParameterSpaceName = spaceName,
                Assignments = assignments
            };

            ParameterResolveResponse response = await _apiClient.ResolveParametersAsync(request);

            if (response != null)
            {
                _rtbCode.Text = response.GeneratedCode ?? "(no code returned)";

                if (response.ValidationErrors != null && response.ValidationErrors.Count > 0)
                {
                    _rtbCode.AppendText("\n\n// --- Validation Errors ---\n");
                    foreach (string err in response.ValidationErrors)
                    {
                        _rtbCode.AppendText("// [WARN] " + err + "\n");
                    }
                    _lblStatus.Text = string.Format("Done with {0} warning(s).",
                        response.ValidationErrors.Count);
                }
                else
                {
                    _lblStatus.Text = "Done  [->]  Parameters resolved.";
                }
            }
            else
            {
                _rtbCode.Text = "[FAIL] Unable to reach the backend API.\n"
                              + "Make sure the server is running at http://localhost:8000";
                _lblStatus.Text = "Error - backend unreachable.";
            }

            _btnResolve.Enabled = true;
        }

        // ----- Private Helpers ---------------------------------------------

        /// <summary>
        /// Populates the DataGridView with default values from the selected
        /// parameter space. If the context service is available, it also
        /// attempts to pre-populate with current dimension values.
        /// </summary>
        private void PopulateGrid()
        {
            _dgvParams.Rows.Clear();

            string spaceName = _cboSpace.SelectedItem?.ToString();
            if (string.IsNullOrEmpty(spaceName)) return;

            if (!KnownSpaces.ContainsKey(spaceName)) return;

            Dictionary<string, object> defaults = KnownSpaces[spaceName];
            foreach (var kvp in defaults)
            {
                _dgvParams.Rows.Add(kvp.Key, kvp.Value?.ToString() ?? "");
            }

            _lblStatus.Text = string.Format("Loaded {0} parameters for '{1}'.",
                defaults.Count, spaceName);
        }

        /// <summary>
        /// Attempts to parse a string value as double, bool, or leaves it
        /// as a string.
        /// </summary>
        private static object ParseValue(string rawVal)
        {
            if (string.IsNullOrEmpty(rawVal))
                return rawVal;

            // Try bool
            if (bool.TryParse(rawVal, out bool boolVal))
                return boolVal;

            // Try double
            if (double.TryParse(rawVal, System.Globalization.NumberStyles.Float,
                System.Globalization.CultureInfo.InvariantCulture, out double numVal))
                return numVal;

            // Fall back to string
            return rawVal;
        }
    }
}
