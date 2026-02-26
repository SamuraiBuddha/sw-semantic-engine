// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Application.cs
// ISwAddin implementation: entry point for the SolidWorks add-in.
// ---------------------------------------------------------------------------

using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Win32;
using Newtonsoft.Json;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
using SolidWorks.Interop.swpublished;
using SolidWorksSemanticEngine.Bridge;
using SolidWorksSemanticEngine.Commands;
using SolidWorksSemanticEngine.Models;
using SolidWorksSemanticEngine.Services;

namespace SolidWorksSemanticEngine
{
    /// <summary>
    /// Main SolidWorks add-in class. Implements <see cref="ISwAddin"/> to
    /// integrate with the SolidWorks host application.
    /// </summary>
    [Guid("A1B2C3D4-E5F6-7890-ABCD-EF1234567890")]
    [ComVisible(true)]
    public class Application : ISwAddin
    {
        // ----- Constants ---------------------------------------------------

        /// <summary>Unique identifier for the command group.</summary>
        private const int CommandGroupId = 10100;

        /// <summary>Command IDs for each button in the toolbar.</summary>
        private const int CmdIdGenerateCode = 0;
        private const int CmdIdParametrize  = 1;
        private const int CmdIdExplainApi   = 2;
        private const int CmdIdSettings     = 3;

        // ----- Fields ------------------------------------------------------

        private ISldWorks _swApp;
        private ICommandManager _cmdMgr;
        private int _addinCookie;

        private SwseConfig _config;
        private BackendLauncher _launcher;

        /// <summary>HTTP bridge to the backend API.</summary>
        public ApiClient ApiClient { get; private set; }

        /// <summary>Service for extracting SolidWorks model context.</summary>
        public SolidWorksContextService ContextService { get; private set; }

        // ----- ISwAddin Implementation -------------------------------------

        /// <summary>
        /// Called by SolidWorks when the add-in is loaded.
        /// </summary>
        /// <param name="thisSW">The SolidWorks application object.</param>
        /// <param name="cookie">Registration cookie assigned to this add-in.</param>
        /// <returns>True if initialization succeeds.</returns>
        public bool ConnectToSW(object thisSW, int cookie)
        {
            _swApp = (ISldWorks)thisSW;
            _addinCookie = cookie;
            _swApp.SetAddinCallbackInfo2(0, this, _addinCookie);

            // Load configuration from swse-config.json next to the DLL
            _config = LoadConfig();

            // Initialize services with configured port (may be updated after discovery)
            int port = _config?.BackendPort ?? 8000;
            ApiClient = new ApiClient("http://localhost:" + port);
            ContextService = new SolidWorksContextService(_swApp);

            // Auto-launch backend services in the background.
            // After port discovery completes, re-create ApiClient if the
            // backend ended up on a different port.
            if (_config != null)
            {
                _launcher = new BackendLauncher(_config);
                Task.Run(async () =>
                {
                    await _launcher.EnsureServicesRunningAsync();

                    int actualPort = _launcher.ActualBackendPort;
                    if (actualPort != port)
                    {
                        System.Diagnostics.Debug.WriteLine(
                            "[SWSE] Backend port resolved to " + actualPort +
                            " (configured: " + port + "). Updating ApiClient.");
                        var old = ApiClient;
                        ApiClient = new ApiClient("http://localhost:" + actualPort);
                        old?.Dispose();
                    }
                });
            }

            // Build the command group UI
            CreateCommandGroup();

            return true;
        }

        /// <summary>
        /// Called by SolidWorks when the add-in is unloaded.
        /// </summary>
        /// <returns>True if cleanup succeeds.</returns>
        public bool DisconnectFromSW()
        {
            RemoveCommandGroup();

            // Stop managed processes if configured
            if (_config != null && _config.KillOnDisconnect && _launcher != null)
            {
                _launcher.StopServices();
            }
            _launcher?.Dispose();
            _launcher = null;
            _config = null;

            ApiClient?.Dispose();
            ApiClient = null;
            ContextService = null;
            _swApp = null;

            // Force garbage collection so COM refs are released promptly
            GC.Collect();
            GC.WaitForPendingFinalizers();

            return true;
        }

        // ----- Command Group Setup -----------------------------------------

        /// <summary>
        /// Creates the "Semantic Engine" command group with three toolbar
        /// buttons: Generate Code, Parametrize, and Explain API.
        /// Also registers a CommandTab so buttons appear on the ribbon.
        /// </summary>
        private void CreateCommandGroup()
        {
            _cmdMgr = _swApp.GetCommandManager(_addinCookie);

            // Check whether our command group already exists and whether
            // its command list has changed since the last registration.
            int[] registeredIds = new int[] { CmdIdGenerateCode, CmdIdParametrize, CmdIdExplainApi, CmdIdSettings };
            bool ignorePrevious = false;

            object registryIDs;
            bool getDataResult = _cmdMgr.GetGroupDataFromRegistry(CommandGroupId, out registryIDs);
            if (getDataResult)
            {
                int[] knownIDs = (int[])registryIDs;
                if (!CompareIDs(knownIDs, registeredIds))
                    ignorePrevious = true;
            }

            // Generate icon bitmap strips (placed next to the DLL)
            string iconDir = Path.GetDirectoryName(
                Assembly.GetExecutingAssembly().Location) ?? "";
            string smallIconPath = Path.Combine(iconDir, "swse_icons_20.bmp");
            string largeIconPath = Path.Combine(iconDir, "swse_icons_32.bmp");
            string smallMainPath = Path.Combine(iconDir, "swse_main_20.bmp");
            string largeMainPath = Path.Combine(iconDir, "swse_main_32.bmp");
            EnsureIconFiles(smallIconPath, 20, 4);
            EnsureIconFiles(largeIconPath, 32, 4);
            EnsureIconFiles(smallMainPath, 20, 1);
            EnsureIconFiles(largeMainPath, 32, 1);

            int errors = 0;
            ICommandGroup cmdGroup = _cmdMgr.CreateCommandGroup2(
                CommandGroupId,
                "Semantic Engine",
                "SolidWorks Semantic Engine - AI-powered code generation",
                "SolidWorks Semantic Engine",
                -1,
                ignorePrevious,
                ref errors);

            cmdGroup.LargeIconList = largeIconPath;
            cmdGroup.SmallIconList = smallIconPath;
            cmdGroup.LargeMainIcon = largeMainPath;
            cmdGroup.SmallMainIcon = smallMainPath;

            int cmdIndex0 = cmdGroup.AddCommandItem2(
                "Generate Code", -1, "Generate SolidWorks API code from a natural-language prompt",
                "Generate Code", 0, nameof(OnGenerateCode), nameof(EnableMethod),
                CmdIdGenerateCode, (int)swCommandItemType_e.swMenuItem | (int)swCommandItemType_e.swToolbarItem);

            int cmdIndex1 = cmdGroup.AddCommandItem2(
                "Parametrize", -1, "Resolve model parameters and generate parametric code",
                "Parametrize", 1, nameof(OnParametrize), nameof(EnableMethod),
                CmdIdParametrize, (int)swCommandItemType_e.swMenuItem | (int)swCommandItemType_e.swToolbarItem);

            int cmdIndex2 = cmdGroup.AddCommandItem2(
                "Explain API", -1, "Look up SolidWorks API reference documentation",
                "Explain API", 2, nameof(OnExplainApi), nameof(EnableMethod),
                CmdIdExplainApi, (int)swCommandItemType_e.swMenuItem | (int)swCommandItemType_e.swToolbarItem);

            int cmdIndex3 = cmdGroup.AddCommandItem2(
                "Settings", -1, "Configure the Semantic Engine (model, ports, etc.)",
                "Settings", 3, nameof(OnSettings), nameof(EnableMethod),
                CmdIdSettings, (int)swCommandItemType_e.swMenuItem | (int)swCommandItemType_e.swToolbarItem);

            cmdGroup.HasToolbar = true;
            cmdGroup.HasMenu = true;
            cmdGroup.Activate();

            // Add a CommandTab for each document type so buttons appear
            // on the ribbon even when no document is open (swDocNONE = 0)
            int[] docTypes = new int[]
            {
                (int)swDocumentTypes_e.swDocNONE,
                (int)swDocumentTypes_e.swDocPART,
                (int)swDocumentTypes_e.swDocASSEMBLY,
                (int)swDocumentTypes_e.swDocDRAWING
            };

            foreach (int docType in docTypes)
            {
                CommandTab cmdTab = _cmdMgr.GetCommandTab(docType, "Semantic Engine");
                if (cmdTab != null)
                {
                    // Remove stale tab so we can recreate it cleanly
                    _cmdMgr.RemoveCommandTab(cmdTab);
                }

                cmdTab = _cmdMgr.AddCommandTab(docType, "Semantic Engine");
                if (cmdTab == null)
                    continue;

                CommandTabBox cmdBox = cmdTab.AddCommandTabBox();
                if (cmdBox == null)
                    continue;

                // Each command needs its ID from the group and a text display style
                int[] cmdIDs = new int[]
                {
                    cmdGroup.CommandID[cmdIndex0],
                    cmdGroup.CommandID[cmdIndex1],
                    cmdGroup.CommandID[cmdIndex2],
                    cmdGroup.CommandID[cmdIndex3]
                };
                int[] textTypes = new int[]
                {
                    (int)swCommandTabButtonTextDisplay_e.swCommandTabButton_TextBelow,
                    (int)swCommandTabButtonTextDisplay_e.swCommandTabButton_TextBelow,
                    (int)swCommandTabButtonTextDisplay_e.swCommandTabButton_TextBelow,
                    (int)swCommandTabButtonTextDisplay_e.swCommandTabButton_TextBelow
                };

                cmdBox.AddCommands(cmdIDs, textTypes);
            }
        }

        /// <summary>Removes the command group during teardown.</summary>
        private void RemoveCommandGroup()
        {
            _cmdMgr?.RemoveCommandGroup2(CommandGroupId, false);
        }

        /// <summary>Compares two integer arrays for equality.</summary>
        private static bool CompareIDs(int[] a, int[] b)
        {
            if (a == null || b == null) return false;
            if (a.Length != b.Length) return false;
            for (int i = 0; i < a.Length; i++)
            {
                if (a[i] != b[i]) return false;
            }
            return true;
        }

        /// <summary>
        /// Generates a simple colored-square BMP icon strip if the file
        /// does not already exist. Each icon in the strip is
        /// <paramref name="size"/> x <paramref name="size"/> pixels.
        /// </summary>
        private static void EnsureIconFiles(string path, int size, int count)
        {
            if (File.Exists(path))
                return;

            try
            {
                int width = size * count;
                using (var bmp = new Bitmap(width, size, PixelFormat.Format24bppRgb))
                using (var g = Graphics.FromImage(bmp))
                {
                    // Distinct colors per command slot
                    Color[] colors = new Color[]
                    {
                        Color.FromArgb(0x33, 0x99, 0xFF),   // blue   - Generate
                        Color.FromArgb(0xFF, 0x99, 0x33),   // orange - Parametrize
                        Color.FromArgb(0x33, 0xCC, 0x66),   // green  - Explain
                        Color.FromArgb(0x88, 0x88, 0x88)    // gray   - Settings
                    };

                    g.Clear(Color.White);

                    for (int i = 0; i < count && i < colors.Length; i++)
                    {
                        int x = i * size;
                        int pad = size / 5;
                        using (var brush = new SolidBrush(colors[i]))
                        {
                            g.FillRectangle(brush, x + pad, pad, size - 2 * pad, size - 2 * pad);
                        }

                        // Draw a letter in the center
                        string letter = i == 0 ? "G" : i == 1 ? "P" : i == 2 ? "E" : "S";
                        using (var font = new Font("Arial", size * 0.35f, FontStyle.Bold))
                        using (var sf = new StringFormat())
                        {
                            sf.Alignment = StringAlignment.Center;
                            sf.LineAlignment = StringAlignment.Center;
                            var rect = new RectangleF(x, 0, size, size);
                            g.DrawString(letter, font, Brushes.White, rect, sf);
                        }
                    }

                    bmp.Save(path, ImageFormat.Bmp);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Failed to generate icon: " + ex.Message);
            }
        }

        // ----- Command Callbacks -------------------------------------------

        /// <summary>Callback: opens the Generate Code dialog.</summary>
        public void OnGenerateCode()
        {
            var form = new GenerateCodeCommand(ApiClient, ContextService, _config);
            form.Show();
        }

        /// <summary>Callback: opens the Parametrize dialog.</summary>
        public void OnParametrize()
        {
            var form = new ParametrizeCommand(ApiClient, ContextService);
            form.Show();
        }

        /// <summary>Callback: opens the Explain API dialog.</summary>
        public void OnExplainApi()
        {
            var form = new ExplainApiCommand(ApiClient, ContextService);
            form.Show();
        }

        /// <summary>Callback: opens the Settings dialog.</summary>
        public void OnSettings()
        {
            var form = new SettingsCommand(_config, updatedConfig =>
            {
                // Apply updated config
                _config = updatedConfig;

                // Recreate ApiClient if port changed
                int newPort = _config.BackendPort;
                var oldClient = ApiClient;
                ApiClient = new ApiClient("http://localhost:" + newPort);
                oldClient?.Dispose();

                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Settings saved. Active model: " + _config.ActiveModel);

                // Restart backend with new model if launcher exists
                if (_launcher != null && _config.AutoLaunchBackend)
                {
                    _launcher.StopServices();
                    _launcher.Dispose();
                    _launcher = new BackendLauncher(_config);
                    Task.Run(async () =>
                    {
                        await _launcher.EnsureServicesRunningAsync();

                        int actualPort = _launcher.ActualBackendPort;
                        if (actualPort != newPort)
                        {
                            var old = ApiClient;
                            ApiClient = new ApiClient("http://localhost:" + actualPort);
                            old?.Dispose();
                        }
                    });
                }
            });
            form.ShowDialog();
        }

        /// <summary>Enable-method callback. Returns 1 (enabled) always.</summary>
        public int EnableMethod()
        {
            return 1;
        }

        // ----- Config Loading ----------------------------------------------

        /// <summary>
        /// Loads <c>swse-config.json</c> from the directory containing this DLL.
        /// Returns <c>null</c> if the file does not exist or cannot be parsed.
        /// </summary>
        private static SwseConfig LoadConfig()
        {
            try
            {
                string dllDir = Path.GetDirectoryName(
                    Assembly.GetExecutingAssembly().Location);
                string configPath = Path.Combine(dllDir, "swse-config.json");

                if (!File.Exists(configPath))
                {
                    System.Diagnostics.Debug.WriteLine(
                        "[SWSE] No config file at " + configPath);
                    return null;
                }

                string json = File.ReadAllText(configPath);
                var config = JsonConvert.DeserializeObject<SwseConfig>(json);
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Config loaded from " + configPath);
                return config;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Failed to load config: " + ex.Message);
                return null;
            }
        }

        // ----- COM Registration Helpers ------------------------------------

        /// <summary>
        /// Registers this add-in in the Windows registry so SolidWorks can
        /// discover it at startup.
        /// </summary>
        [ComRegisterFunction]
        public static void RegisterFunction(Type t)
        {
            string keyPath = @"SOFTWARE\SolidWorks\Addins\{" + t.GUID.ToString() + "}";
            using (RegistryKey key = Registry.LocalMachine.CreateSubKey(keyPath))
            {
                key.SetValue(null, 0);                    // not loaded at startup by default
                key.SetValue("Description", "SolidWorks Semantic Engine - AI-powered code generation");
                key.SetValue("Title", "Semantic Engine");
            }
        }

        /// <summary>
        /// Removes registry entries when the add-in assembly is unregistered.
        /// </summary>
        [ComUnregisterFunction]
        public static void UnregisterFunction(Type t)
        {
            string keyPath = @"SOFTWARE\SolidWorks\Addins\{" + t.GUID.ToString() + "}";
            try
            {
                Registry.LocalMachine.DeleteSubKey(keyPath, false);
            }
            catch (Exception)
            {
                // Silently ignore if the key does not exist
            }
        }
    }
}
