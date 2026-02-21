// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Application.cs
// ISwAddin implementation: entry point for the SolidWorks add-in.
// ---------------------------------------------------------------------------

using System;
using System.Runtime.InteropServices;
using Microsoft.Win32;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
using SolidWorks.Interop.swpublished;
using SolidWorksSemanticEngine.Bridge;
using SolidWorksSemanticEngine.Commands;
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

        // ----- Fields ------------------------------------------------------

        private ISldWorks _swApp;
        private ICommandManager _cmdMgr;
        private int _addinCookie;

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

            // Initialize services
            ApiClient = new ApiClient("http://localhost:8000");
            ContextService = new SolidWorksContextService(_swApp);

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
        /// </summary>
        private void CreateCommandGroup()
        {
            _cmdMgr = _swApp.GetCommandManager(_addinCookie);

            int[] commandIds = new int[] { CmdIdGenerateCode, CmdIdParametrize, CmdIdExplainApi };
            int errors = 0;

            ICommandGroup cmdGroup = _cmdMgr.CreateCommandGroup2(
                CommandGroupId,
                "Semantic Engine",
                "SolidWorks Semantic Engine - AI-powered code generation",
                "",       // tooltip
                -1,       // position
                true,
                ref errors);

            cmdGroup.LargeIconList  = ""; // TODO: provide icon bitmap paths
            cmdGroup.SmallIconList  = "";
            cmdGroup.LargeMainIcon  = "";
            cmdGroup.SmallMainIcon  = "";

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

            cmdGroup.HasToolbar = true;
            cmdGroup.HasMenu = true;
            cmdGroup.Activate();
        }

        /// <summary>Removes the command group during teardown.</summary>
        private void RemoveCommandGroup()
        {
            _cmdMgr?.RemoveCommandGroup2(CommandGroupId, false);
        }

        // ----- Command Callbacks -------------------------------------------

        /// <summary>Callback: opens the Generate Code dialog.</summary>
        public void OnGenerateCode()
        {
            var form = new GenerateCodeCommand(ApiClient, ContextService);
            form.Show();
        }

        /// <summary>Callback: placeholder for Parametrize functionality.</summary>
        public void OnParametrize()
        {
            // TODO: implement parametrize dialog
            _swApp.SendMsgToUser2(
                "Parametrize command is not yet implemented.",
                (int)swMessageBoxIcon_e.swMbInformation,
                (int)swMessageBoxBtn_e.swMbOk);
        }

        /// <summary>Callback: placeholder for Explain API functionality.</summary>
        public void OnExplainApi()
        {
            // TODO: implement API reference lookup dialog
            _swApp.SendMsgToUser2(
                "Explain API command is not yet implemented.",
                (int)swMessageBoxIcon_e.swMbInformation,
                (int)swMessageBoxBtn_e.swMbOk);
        }

        /// <summary>Enable-method callback. Returns 1 (enabled) always.</summary>
        public int EnableMethod()
        {
            return 1;
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
