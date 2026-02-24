"""Interference detection, clearance verification, and collision detection
C# code generator for SolidWorks API training data.

Generates instruction/code training pairs covering:
  - Parameterized interference detection (ToolsCheckInterference)
  - Interference result iteration and filtering
  - Selective and batch interference checks
  - Clearance verification (Measure API, minimum distance)
  - Clearance threshold checks and reporting
  - Collision detection manager setup and configuration
  - Conceptual pairs: best practices, workflows, standards

Target: ~130 pairs across one generator class.

NOTE: A single basic interference-detection pair already exists in
``feature_code_generator.py`` (line ~431).  This module deliberately avoids
duplicating that exact pair.
"""

from __future__ import annotations

import textwrap
from typing import List, Tuple

TrainingPair = Tuple[str, str]
D = textwrap.dedent


class InterferenceClearanceGenerator:
    """Generates SolidWorks-API C# training pairs for interference detection,
    clearance verification, and collision detection."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_all(self) -> list[tuple[str, str]]:
        """Return all interference / clearance / collision training pairs."""
        p: list[tuple[str, str]] = []
        p.extend(self._interference_parameterized_pairs())
        p.extend(self._interference_result_pairs())
        p.extend(self._interference_selective_pairs())
        p.extend(self._interference_filtering_pairs())
        p.extend(self._interference_workflow_pairs())
        p.extend(self._clearance_measure_pairs())
        p.extend(self._clearance_threshold_pairs())
        p.extend(self._clearance_iteration_pairs())
        p.extend(self._clearance_report_pairs())
        p.extend(self._collision_setup_pairs())
        p.extend(self._collision_config_pairs())
        p.extend(self._collision_result_pairs())
        p.extend(self._conceptual_pairs())
        return p

    # ==================================================================
    # 1. Interference Detection  (~50 pairs)
    # ==================================================================

    def _interference_parameterized_pairs(self) -> list[tuple[str, str]]:
        """ToolsCheckInterference with different parameter combinations."""
        p: list[tuple[str, str]] = []

        # Varying coincidence + body flags
        for coincidence, coin_lbl in [(True, "treating coincidence as interference"),
                                      (False, "ignoring coincidence")]:
            for bodies, body_lbl in [(True, "creating interference bodies"),
                                     (False, "without creating interference bodies")]:
                coin_cs = "true" if coincidence else "false"
                body_cs = "true" if bodies else "false"
                code = D(f"""\
                    // Interference detection: {coin_lbl}, {body_lbl}
                    AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                    int nInterferences = 0;
                    object interferences = asmDoc.ToolsCheckInterference(
                        (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                        {coin_cs}, {body_cs}, out nInterferences);
                    Debug.WriteLine($"Found {{nInterferences}} interference(s).");""")
                p.append((
                    f"Run interference detection on a SolidWorks assembly {coin_lbl} "
                    f"and {body_lbl}.",
                    code))

        # Different interference levels
        for level, level_name in [
            ("swCheckInterferenceLevel_Default", "default"),
            ("swCheckInterferenceLevel_TightFit", "tight-fit"),
            ("swCheckInterferenceLevel_TouchingOnly", "touching-only"),
        ]:
            code = D(f"""\
                // Interference detection at {level_name} level
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int nInterferences = 0;
                object interferences = asmDoc.ToolsCheckInterference(
                    (int)swCheckInterferenceLevel_e.{level},
                    true, true, out nInterferences);
                Debug.WriteLine($"Level={level_name}: {{nInterferences}} interference(s).");""")
            p.append((
                f"Run interference detection at the {level_name} level in a SolidWorks assembly.",
                code))

        # Store results in a list for downstream use
        code = D("""\
            // Run interference check and store results
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            var results = new List<(string CompA, string CompB, double Volume)>();
            if (interferences != null) {
                object[] intfArray = (object[])interferences;
                foreach (IInterference intf in intfArray) {
                    object[] comps = (object[])intf.Components;
                    results.Add((
                        ((Component2)comps[0]).Name2,
                        ((Component2)comps[1]).Name2,
                        intf.Volume));
                }
            }""")
        p.append((
            "Run an interference check on a SolidWorks assembly and store the "
            "results in a typed list for later processing.",
            code))

        # Quick pass/fail check
        code = D("""\
            // Quick pass/fail interference check
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                false, false, out nInterferences);
            bool passed = nInterferences == 0;
            Debug.WriteLine(passed ? "[PASS] No interferences" : $"[FAIL] {nInterferences} interference(s)");""")
        p.append((
            "Perform a quick pass/fail interference check on a SolidWorks assembly "
            "without creating interference bodies.",
            code))

        # Check with resolved lightweight components first
        code = D("""\
            // Resolve lightweight components then check interference
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            asmDoc.ResolveAllLightWeightComponents(true);
            modelDoc.EditRebuild3();
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            Debug.WriteLine($"Found {nInterferences} interference(s) after resolving all components.");""")
        p.append((
            "Resolve all lightweight components and then run interference "
            "detection in a SolidWorks assembly.",
            code))

        # Rebuild before interference check
        code = D("""\
            // Force rebuild and then check interference
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            modelDoc.ForceRebuild3(true);
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                false, true, out nInterferences);
            Debug.WriteLine($"Post-rebuild: {nInterferences} interference(s).");""")
        p.append((
            "Force a full rebuild of the assembly before running interference "
            "detection in SolidWorks.",
            code))

        # Check interference and set custom property with result
        code = D("""\
            // Run interference check and store result as custom property
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                false, false, out nInterferences);
            CustomPropertyManager cpm = modelDoc.Extension.get_CustomPropertyManager("");
            cpm.Add3("InterferenceCount", (int)swCustomInfoType_e.swCustomInfoNumber,
                nInterferences.ToString(), (int)swCustomPropertyAddOption_e.swCustomPropertyReplaceValue);
            cpm.Add3("InterferenceDate", (int)swCustomInfoType_e.swCustomInfoText,
                DateTime.Now.ToString("yyyy-MM-dd HH:mm"),
                (int)swCustomPropertyAddOption_e.swCustomPropertyReplaceValue);
            Debug.WriteLine($"Stored interference count ({nInterferences}) in custom properties.");""")
        p.append((
            "Run interference detection and store the count and date as custom "
            "properties on the SolidWorks assembly document.",
            code))

        # Interference check returning boolean for CI/CD integration
        code = D("""\
            // Interference check returning boolean for automation
            public static bool CheckInterference(AssemblyDoc asmDoc) {
                int nInterferences = 0;
                asmDoc.ToolsCheckInterference(
                    (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                    false, false, out nInterferences);
                return nInterferences == 0;
            }""")
        p.append((
            "Create a helper method that returns true if a SolidWorks assembly "
            "has no interferences, suitable for automated validation.",
            code))

        # Interference with specific component types
        for comp_type, comp_desc in [("SLDPRT", "part"), ("SLDASM", "subassembly")]:
            code = D(f"""\
                // Interference check filtering results by component type
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int nInterferences = 0;
                object interferences = asmDoc.ToolsCheckInterference(
                    (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                    true, true, out nInterferences);
                int typeCount = 0;
                if (interferences != null) {{
                    foreach (IInterference intf in (object[])interferences) {{
                        object[] comps = (object[])intf.Components;
                        ModelDoc2 m0 = (ModelDoc2)((Component2)comps[0]).GetModelDoc2();
                        ModelDoc2 m1 = (ModelDoc2)((Component2)comps[1]).GetModelDoc2();
                        string path0 = m0 != null ? m0.GetPathName() : "";
                        string path1 = m1 != null ? m1.GetPathName() : "";
                        if (path0.EndsWith(".{comp_type}") || path1.EndsWith(".{comp_type}"))
                            typeCount++;
                    }}
                }}
                Debug.WriteLine($"Interferences involving {comp_desc} files: {{typeCount}}");""")
            p.append((
                f"Run interference detection and count only interferences involving "
                f"{comp_desc} files in a SolidWorks assembly.",
                code))

        return p

    def _interference_result_pairs(self) -> list[tuple[str, str]]:
        """Iterate and report interference results."""
        p: list[tuple[str, str]] = []

        # Full iteration with component names and volumes
        code = D("""\
            // Iterate interference results
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            if (interferences != null) {
                object[] intfArray = (object[])interferences;
                for (int i = 0; i < intfArray.Length; i++) {
                    IInterference intf = (IInterference)intfArray[i];
                    object[] comps = (object[])intf.Components;
                    string nameA = ((Component2)comps[0]).Name2;
                    string nameB = ((Component2)comps[1]).Name2;
                    double vol = intf.Volume;
                    Debug.WriteLine($"  [{i+1}] {nameA} <-> {nameB}, Volume={vol*1e9:F3} mm^3");
                }
            }""")
        p.append((
            "Run interference detection and print each interference with component "
            "names and volume in cubic millimeters.",
            code))

        # Get interference body for visualization
        code = D("""\
            // Get interference bodies for visualization
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            if (interferences != null) {
                object[] intfArray = (object[])interferences;
                foreach (IInterference intf in intfArray) {
                    Body2 intfBody = (Body2)intf.InterferenceBody;
                    if (intfBody != null) {
                        double[] bbox = (double[])intfBody.GetBodyBox();
                        Debug.WriteLine($"Interference body bbox: " +
                            $"({bbox[0]*1000:F2},{bbox[1]*1000:F2},{bbox[2]*1000:F2}) to " +
                            $"({bbox[3]*1000:F2},{bbox[4]*1000:F2},{bbox[5]*1000:F2}) mm");
                    }
                }
            }""")
        p.append((
            "Get the interference bodies after detection and print their bounding "
            "boxes for visualization in a SolidWorks assembly.",
            code))

        # Count unique interfering components
        code = D("""\
            // Count unique interfering components
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                false, false, out nInterferences);
            var involvedComps = new HashSet<string>();
            if (interferences != null) {
                foreach (IInterference intf in (object[])interferences) {
                    object[] comps = (object[])intf.Components;
                    involvedComps.Add(((Component2)comps[0]).Name2);
                    involvedComps.Add(((Component2)comps[1]).Name2);
                }
            }
            Debug.WriteLine($"{involvedComps.Count} unique component(s) involved in interferences.");""")
        p.append((
            "Find the number of unique components involved in interferences in a "
            "SolidWorks assembly.",
            code))

        # Total interference volume
        code = D("""\
            // Calculate total interference volume
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            double totalVolume = 0;
            if (interferences != null) {
                foreach (IInterference intf in (object[])interferences)
                    totalVolume += intf.Volume;
            }
            Debug.WriteLine($"Total interference volume: {totalVolume*1e9:F3} mm^3");""")
        p.append((
            "Calculate the total interference volume across all detected interferences "
            "in a SolidWorks assembly.",
            code))

        # Export interference report to CSV
        code = D("""\
            // Export interference report to CSV
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            using (var sw = new System.IO.StreamWriter(@"C:\\Reports\\InterferenceReport.csv")) {
                sw.WriteLine("Index,ComponentA,ComponentB,Volume_mm3");
                if (interferences != null) {
                    object[] intfArray = (object[])interferences;
                    for (int i = 0; i < intfArray.Length; i++) {
                        IInterference intf = (IInterference)intfArray[i];
                        object[] comps = (object[])intf.Components;
                        sw.WriteLine($"{i+1},{((Component2)comps[0]).Name2}," +
                            $"{((Component2)comps[1]).Name2},{intf.Volume*1e9:F3}");
                    }
                }
            }
            Debug.WriteLine("Interference report saved.");""")
        p.append((
            "Run interference detection and export the results to a CSV file with "
            "component names and volumes.",
            code))

        # Largest interference
        code = D("""\
            // Find the largest interference by volume
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            double maxVol = 0; string maxPair = "";
            if (interferences != null) {
                foreach (IInterference intf in (object[])interferences) {
                    if (intf.Volume > maxVol) {
                        maxVol = intf.Volume;
                        object[] comps = (object[])intf.Components;
                        maxPair = $"{((Component2)comps[0]).Name2} <-> {((Component2)comps[1]).Name2}";
                    }
                }
            }
            Debug.WriteLine($"Largest: {maxPair}, Vol={maxVol*1e9:F3} mm^3");""")
        p.append((
            "Find the largest interference by volume in a SolidWorks assembly and "
            "report the component pair.",
            code))

        # Group interferences by component
        code = D("""\
            // Group interferences by component name
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                false, false, out nInterferences);
            var compCount = new Dictionary<string, int>();
            if (interferences != null) {
                foreach (IInterference intf in (object[])interferences) {
                    object[] comps = (object[])intf.Components;
                    foreach (object c in comps) {
                        string name = ((Component2)c).Name2;
                        if (!compCount.ContainsKey(name)) compCount[name] = 0;
                        compCount[name]++;
                    }
                }
            }
            foreach (var kv in compCount.OrderByDescending(x => x.Value))
                Debug.WriteLine($"  {kv.Key}: involved in {kv.Value} interference(s)");""")
        p.append((
            "Group interference results by component and show which component is "
            "involved in the most interferences.",
            code))

        # Compare interference counts between two configurations
        code = D("""\
            // Compare interference counts across configurations
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            string[] configs = (string[])modelDoc.GetConfigurationNames();
            foreach (string cfg in configs) {
                modelDoc.ShowConfiguration2(cfg);
                modelDoc.EditRebuild3();
                int nIntf = 0;
                asmDoc.ToolsCheckInterference(
                    (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                    false, false, out nIntf);
                Debug.WriteLine($"Config '{cfg}': {nIntf} interference(s)");
            }""")
        p.append((
            "Compare interference detection results across all configurations "
            "of a SolidWorks assembly.",
            code))

        return p

    def _interference_selective_pairs(self) -> list[tuple[str, str]]:
        """Selective interference checks and subassembly-level detection."""
        p: list[tuple[str, str]] = []

        # Check only selected components
        code = D("""\
            // Interference check on selected components only
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            // Pre-select components of interest
            modelDoc.Extension.SelectByID2("Part1-1@Assy", "COMPONENT", 0, 0, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("Part2-1@Assy", "COMPONENT", 0, 0, 0, true, 0, null, 0);
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            Debug.WriteLine($"Selected-only check: {nInterferences} interference(s).");""")
        p.append((
            "Run interference detection only on two selected components in a "
            "SolidWorks assembly.",
            code))

        # Check between two groups of components
        code = D("""\
            // Check interference between two groups of components
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            // Select group A (mark 1)
            modelDoc.Extension.SelectByID2("Housing-1@Assy", "COMPONENT", 0, 0, 0, false, 1, null, 0);
            modelDoc.Extension.SelectByID2("Cover-1@Assy", "COMPONENT", 0, 0, 0, true, 1, null, 0);
            // Select group B (mark 2)
            modelDoc.Extension.SelectByID2("Shaft-1@Assy", "COMPONENT", 0, 0, 0, true, 2, null, 0);
            modelDoc.Extension.SelectByID2("Bearing-1@Assy", "COMPONENT", 0, 0, 0, true, 2, null, 0);
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            Debug.WriteLine($"Group check: {nInterferences} interference(s).");""")
        p.append((
            "Check interference between two groups of components in a SolidWorks "
            "assembly using selection marks.",
            code))

        # Subassembly-level interference detection
        code = D("""\
            // Interference detection at subassembly level
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] topComps = (object[])asmDoc.GetComponents(true);
            foreach (Component2 comp in topComps) {
                if (comp.GetSuppression() == (int)swComponentSuppressionState_e.swComponentSuppressed)
                    continue;
                ModelDoc2 subModel = (ModelDoc2)comp.GetModelDoc2();
                if (subModel == null || subModel.GetType() != (int)swDocumentTypes_e.swDocASSEMBLY)
                    continue;
                AssemblyDoc subAsm = (AssemblyDoc)subModel;
                int nIntf = 0;
                subAsm.ToolsCheckInterference(
                    (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                    false, false, out nIntf);
                Debug.WriteLine($"  Subassembly '{comp.Name2}': {nIntf} interference(s)");
            }""")
        p.append((
            "Run interference detection on each subassembly within a top-level "
            "SolidWorks assembly.",
            code))

        # Batch interference check across open assemblies
        code = D("""\
            // Batch interference check across all open assemblies
            var results = new List<(string Name, int Count)>();
            ModelDoc2 doc = (ModelDoc2)swApp.GetFirstDocument();
            while (doc != null) {
                if (doc.GetType() == (int)swDocumentTypes_e.swDocASSEMBLY) {
                    AssemblyDoc asm = (AssemblyDoc)doc;
                    int nIntf = 0;
                    asm.ToolsCheckInterference(
                        (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                        false, false, out nIntf);
                    results.Add((doc.GetTitle(), nIntf));
                }
                doc = (ModelDoc2)doc.GetNext();
            }
            foreach (var r in results)
                Debug.WriteLine($"{r.Name}: {r.Count} interference(s)");""")
        p.append((
            "Run a batch interference check across all open assembly documents "
            "in SolidWorks.",
            code))

        # Batch from file list
        code = D("""\
            // Batch interference check from file list
            string[] files = System.IO.File.ReadAllLines(@"C:\\Assemblies\\filelist.txt");
            foreach (string file in files) {
                int errors = 0, warnings = 0;
                ModelDoc2 doc = (ModelDoc2)swApp.OpenDoc6(file,
                    (int)swDocumentTypes_e.swDocASSEMBLY,
                    (int)swOpenDocOptions_e.swOpenDocOptions_Silent,
                    "", ref errors, ref warnings);
                if (doc == null) { Debug.WriteLine($"[SKIP] {file}"); continue; }
                AssemblyDoc asm = (AssemblyDoc)doc;
                int nIntf = 0;
                asm.ToolsCheckInterference(
                    (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                    false, false, out nIntf);
                Debug.WriteLine($"{System.IO.Path.GetFileName(file)}: {nIntf}");
                swApp.CloseDoc(doc.GetTitle());
            }""")
        p.append((
            "Open each assembly from a text file list, run interference detection, "
            "and report results.",
            code))

        # Exclude hidden components
        code = D("""\
            // Interference check excluding hidden components
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] comps = (object[])asmDoc.GetComponents(false);
            foreach (Component2 comp in comps) {
                if (!comp.Visible) {
                    comp.SetSuppression2(
                        (int)swComponentSuppressionState_e.swComponentSuppressed);
                }
            }
            modelDoc.EditRebuild3();
            int nInterferences = 0;
            asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                false, false, out nInterferences);
            Debug.WriteLine($"Interferences (visible only): {nInterferences}");
            // Restore suppression state after check
            foreach (Component2 comp in comps) {
                if (!comp.Visible)
                    comp.SetSuppression2(
                        (int)swComponentSuppressionState_e.swComponentSuppressed);
            }""")
        p.append((
            "Run interference detection excluding hidden components by temporarily "
            "suppressing them in a SolidWorks assembly.",
            code))

        return p

    def _interference_filtering_pairs(self) -> list[tuple[str, str]]:
        """Filter and categorize interference results."""
        p: list[tuple[str, str]] = []

        # Volume threshold filtering
        for thresh_mm3 in [0.1, 1.0, 10.0, 100.0]:
            thresh_m3 = thresh_mm3 * 1e-9
            code = D(f"""\
                // Filter interferences larger than {thresh_mm3} mm^3
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int nInterferences = 0;
                object interferences = asmDoc.ToolsCheckInterference(
                    (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                    true, true, out nInterferences);
                double threshold = {thresh_m3:.1E}; // {thresh_mm3} mm^3 in m^3
                int significant = 0;
                if (interferences != null) {{
                    foreach (IInterference intf in (object[])interferences) {{
                        if (intf.Volume > threshold) {{
                            significant++;
                            object[] comps = (object[])intf.Components;
                            Debug.WriteLine($"  {{((Component2)comps[0]).Name2}} <-> " +
                                $"{{((Component2)comps[1]).Name2}}, Vol={{intf.Volume*1e9:F3}} mm^3");
                        }}
                    }}
                }}
                Debug.WriteLine($"{{significant}} significant (>{thresh_mm3} mm^3) of {{nInterferences}} total.");""")
            p.append((
                f"Run interference detection and report only interferences larger "
                f"than {thresh_mm3} mm^3.",
                code))

        # Ignore threaded fasteners
        code = D("""\
            // Interference check ignoring threaded fastener components
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            string[] fastenerPrefixes = { "Bolt", "Screw", "Nut", "Washer", "SHC" };
            int nonFastener = 0;
            if (interferences != null) {
                foreach (IInterference intf in (object[])interferences) {
                    object[] comps = (object[])intf.Components;
                    string a = ((Component2)comps[0]).Name2;
                    string b = ((Component2)comps[1]).Name2;
                    bool isFastener = false;
                    foreach (string pfx in fastenerPrefixes) {
                        if (a.StartsWith(pfx) || b.StartsWith(pfx)) { isFastener = true; break; }
                    }
                    if (!isFastener) {
                        nonFastener++;
                        Debug.WriteLine($"  {a} <-> {b}, Vol={intf.Volume*1e9:F3} mm^3");
                    }
                }
            }
            Debug.WriteLine($"{nonFastener} non-fastener interference(s) of {nInterferences} total.");""")
        p.append((
            "Run interference detection in a SolidWorks assembly and ignore "
            "interferences involving threaded fasteners (bolts, screws, nuts, washers).",
            code))

        # Ignore press fits
        code = D("""\
            // Interference check ignoring press-fit pairs
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            // Define known press-fit component pairs
            var pressFits = new HashSet<string> { "Bearing-1|Shaft-1", "Pin-1|Housing-1" };
            int unexpected = 0;
            if (interferences != null) {
                foreach (IInterference intf in (object[])interferences) {
                    object[] comps = (object[])intf.Components;
                    string a = ((Component2)comps[0]).Name2;
                    string b = ((Component2)comps[1]).Name2;
                    string pair1 = $"{a}|{b}";
                    string pair2 = $"{b}|{a}";
                    if (!pressFits.Contains(pair1) && !pressFits.Contains(pair2)) {
                        unexpected++;
                        Debug.WriteLine($"  [UNEXPECTED] {a} <-> {b}, Vol={intf.Volume*1e9:F3} mm^3");
                    }
                }
            }
            Debug.WriteLine($"{unexpected} unexpected interference(s).");""")
        p.append((
            "Run interference detection but ignore known press-fit pairs such as "
            "bearings on shafts or pins in housings.",
            code))

        # Categorize by severity
        code = D("""\
            // Categorize interferences by severity (volume)
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            int critical = 0, warning = 0, minor = 0;
            if (interferences != null) {
                foreach (IInterference intf in (object[])interferences) {
                    double vol_mm3 = intf.Volume * 1e9;
                    if (vol_mm3 > 100) critical++;
                    else if (vol_mm3 > 1) warning++;
                    else minor++;
                }
            }
            Debug.WriteLine($"Critical (>100 mm^3): {critical}");
            Debug.WriteLine($"Warning  (>1 mm^3):   {warning}");
            Debug.WriteLine($"Minor    (<=1 mm^3):  {minor}");""")
        p.append((
            "Categorize interferences in a SolidWorks assembly by severity based on "
            "volume thresholds: critical, warning, and minor.",
            code))

        return p

    def _interference_workflow_pairs(self) -> list[tuple[str, str]]:
        """Interference resolution and advanced workflows."""
        p: list[tuple[str, str]] = []

        # Suppress interfering component
        code = D("""\
            // Suppress the first interfering component to resolve interference
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                false, false, out nInterferences);
            if (interferences != null) {
                IInterference intf = (IInterference)((object[])interferences)[0];
                object[] comps = (object[])intf.Components;
                Component2 comp = (Component2)comps[0];
                comp.SetSuppression2(
                    (int)swComponentSuppressionState_e.swComponentSuppressed);
                Debug.WriteLine($"Suppressed '{comp.Name2}' to resolve interference.");
                modelDoc.EditRebuild3();
            }""")
        p.append((
            "Resolve an interference by suppressing the first interfering component "
            "in a SolidWorks assembly.",
            code))

        # Move component to resolve
        code = D("""\
            // Move component to resolve interference
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                false, false, out nInterferences);
            if (interferences != null) {
                IInterference intf = (IInterference)((object[])interferences)[0];
                object[] comps = (object[])intf.Components;
                Component2 comp = (Component2)comps[1];
                // Translate 10mm in Z to clear
                MathUtility mathUtil = (MathUtility)swApp.GetMathUtility();
                double[] delta = { 0, 0, 0.010 }; // 10 mm in meters
                MathVector transVec = (MathVector)mathUtil.CreateVector(delta);
                MathTransform xform = comp.Transform2;
                double[] tData = (double[])xform.ArrayData;
                tData[9] += delta[0]; tData[10] += delta[1]; tData[11] += delta[2];
                xform.ArrayData = tData;
                comp.Transform2 = xform;
                modelDoc.EditRebuild3();
                Debug.WriteLine($"Moved '{comp.Name2}' 10mm in Z.");
            }""")
        p.append((
            "Resolve an interference by translating the second interfering component "
            "10mm along the Z axis.",
            code))

        # Iterative resolution: check, fix, re-check
        code = D("""\
            // Iterative interference resolution loop
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int maxIterations = 5;
            for (int iter = 0; iter < maxIterations; iter++) {
                int nIntf = 0;
                object interferences = asmDoc.ToolsCheckInterference(
                    (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                    false, false, out nIntf);
                if (nIntf == 0) {
                    Debug.WriteLine($"[PASS] No interferences after {iter} iteration(s).");
                    break;
                }
                Debug.WriteLine($"Iteration {iter+1}: {nIntf} interference(s) remain.");
                // Application-specific resolution logic here
                // e.g., adjust mate offsets, move components, etc.
            }""")
        p.append((
            "Implement an iterative interference resolution loop that re-checks "
            "after each fix attempt.",
            code))

        # Pre-release validation
        code = D("""\
            // Pre-release assembly validation: interference check
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nIntf = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nIntf);
            bool release = true;
            if (nIntf > 0) {
                // Check if all are known/allowed
                var allowed = new HashSet<string> { "Bearing-1|Shaft-1" };
                foreach (IInterference intf in (object[])interferences) {
                    object[] comps = (object[])intf.Components;
                    string key = $"{((Component2)comps[0]).Name2}|{((Component2)comps[1]).Name2}";
                    string keyRev = $"{((Component2)comps[1]).Name2}|{((Component2)comps[0]).Name2}";
                    if (!allowed.Contains(key) && !allowed.Contains(keyRev)) {
                        release = false;
                        Debug.WriteLine($"[BLOCK] Unexpected: {key}");
                    }
                }
            }
            Debug.WriteLine(release ? "[RELEASE] Assembly passed." : "[BLOCK] Fix interferences first.");""")
        p.append((
            "Validate an assembly for release by checking interferences and allowing "
            "known press-fit overlaps.",
            code))

        # Save interference screenshot
        code = D("""\
            // Save assembly with interference highlighted
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            if (nInterferences > 0) {
                // Zoom to first interference
                IInterference intf = (IInterference)((object[])interferences)[0];
                object[] comps = (object[])intf.Components;
                modelDoc.Extension.SelectByID2(
                    ((Component2)comps[0]).Name2 + "@" + modelDoc.GetTitle(),
                    "COMPONENT", 0, 0, 0, false, 0, null, 0);
                modelDoc.ViewZoomToSelection();
                // Save image
                modelDoc.SaveBMP(@"C:\\Reports\\Interference_001.bmp", 1920, 1080);
                Debug.WriteLine("Interference screenshot saved.");
            }""")
        p.append((
            "Highlight the first interference in a SolidWorks assembly and save "
            "a screenshot for reporting.",
            code))

        return p

    # ==================================================================
    # 2. Clearance Verification  (~30 pairs)
    # ==================================================================

    def _clearance_measure_pairs(self) -> list[tuple[str, str]]:
        """Minimum distance measurement between components."""
        p: list[tuple[str, str]] = []

        # Basic two-component clearance
        code = D("""\
            // Measure minimum distance between two components
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            modelDoc.Extension.SelectByID2("Part1-1@Assy", "COMPONENT", 0, 0, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("Part2-1@Assy", "COMPONENT", 0, 0, 0, true, 0, null, 0);
            if (measure.Calculate(null)) {
                double dist = measure.Distance;
                Debug.WriteLine($"Clearance: {dist * 1000:F3} mm");
            } else {
                Debug.WriteLine("[WARN] Measurement failed.");
            }""")
        p.append((
            "Measure the minimum distance (clearance) between two components in "
            "a SolidWorks assembly.",
            code))

        # Measure with coordinate output
        code = D("""\
            // Measure clearance with closest-point coordinates
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            modelDoc.Extension.SelectByID2("Bracket-1@Assy", "COMPONENT", 0, 0, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("Frame-1@Assy", "COMPONENT", 0, 0, 0, true, 0, null, 0);
            if (measure.Calculate(null)) {
                double dist = measure.Distance;
                double x1 = measure.X1, y1 = measure.Y1, z1 = measure.Z1;
                double x2 = measure.X2, y2 = measure.Y2, z2 = measure.Z2;
                Debug.WriteLine($"Clearance: {dist*1000:F3} mm");
                Debug.WriteLine($"  Point1: ({x1*1000:F3}, {y1*1000:F3}, {z1*1000:F3}) mm");
                Debug.WriteLine($"  Point2: ({x2*1000:F3}, {y2*1000:F3}, {z2*1000:F3}) mm");
            }""")
        p.append((
            "Measure the clearance between two components and output the closest "
            "point coordinates in millimeters.",
            code))

        # Face-to-face clearance
        code = D("""\
            // Measure face-to-face clearance
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            modelDoc.Extension.SelectByID2("", "FACE", 0.05, 0.02, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("", "FACE", 0.10, 0.02, 0, true, 0, null, 0);
            if (measure.Calculate(null)) {
                Debug.WriteLine($"Face-to-face clearance: {measure.Distance*1000:F3} mm");
                if (measure.IsParallel)
                    Debug.WriteLine("  Faces are parallel.");
            }""")
        p.append((
            "Measure the clearance between two selected faces in a SolidWorks "
            "assembly and check if they are parallel.",
            code))

        # Edge-to-face clearance
        code = D("""\
            // Measure edge-to-face clearance
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            modelDoc.Extension.SelectByID2("", "EDGE", 0.05, 0.02, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("", "FACE", 0.10, 0.02, 0, true, 0, null, 0);
            if (measure.Calculate(null)) {
                Debug.WriteLine($"Edge-to-face clearance: {measure.Distance*1000:F3} mm");
            }""")
        p.append((
            "Measure the clearance between an edge and a face in a SolidWorks assembly.",
            code))

        # Point-to-surface distance
        code = D("""\
            // Measure point-to-surface distance
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            modelDoc.Extension.SelectByID2("Point1@Sketch1", "EXTSKETCHPOINT", 0, 0, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("", "FACE", 0.05, 0.02, 0, true, 0, null, 0);
            if (measure.Calculate(null)) {
                Debug.WriteLine($"Point-to-surface distance: {measure.Distance*1000:F3} mm");
            }""")
        p.append((
            "Measure the distance from a sketch point to a surface face in "
            "a SolidWorks assembly.",
            code))

        # Clearance between named components (parametric)
        for compA, compB, desc in [
            ("Motor-1", "Enclosure-1", "motor and enclosure"),
            ("PCB-1", "Cover-1", "PCB and cover"),
            ("Pipe-1", "Wall-1", "pipe and wall"),
            ("Cable-1", "Frame-1", "cable routing and frame"),
        ]:
            code = D(f"""\
                // Measure clearance between {desc}
                Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
                modelDoc.Extension.SelectByID2("{compA}@Assy", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                modelDoc.Extension.SelectByID2("{compB}@Assy", "COMPONENT", 0, 0, 0, true, 0, null, 0);
                if (measure.Calculate(null)) {{
                    Debug.WriteLine($"Clearance ({desc}): {{measure.Distance*1000:F3}} mm");
                }}""")
            p.append((
                f"Measure the clearance between the {desc} in a SolidWorks assembly.",
                code))

        return p

    def _clearance_threshold_pairs(self) -> list[tuple[str, str]]:
        """Clearance threshold checks with various minimum values."""
        p: list[tuple[str, str]] = []

        for min_mm in [0.5, 1.0, 2.0, 3.0, 5.0]:
            min_m = min_mm / 1000.0
            code = D(f"""\
                // Check if clearance meets {min_mm}mm minimum
                Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
                modelDoc.Extension.SelectByID2("Part1-1@Assy", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                modelDoc.Extension.SelectByID2("Part2-1@Assy", "COMPONENT", 0, 0, 0, true, 0, null, 0);
                double minClearance = {min_m}; // {min_mm} mm
                if (measure.Calculate(null)) {{
                    double dist = measure.Distance;
                    bool ok = dist >= minClearance;
                    Debug.WriteLine(ok
                        ? $"[PASS] Clearance {{dist*1000:F3}} mm >= {min_mm} mm"
                        : $"[FAIL] Clearance {{dist*1000:F3}} mm < {min_mm} mm");
                }}""")
            p.append((
                f"Check if the clearance between two components in a SolidWorks "
                f"assembly meets the {min_mm}mm minimum requirement.",
                code))

        # Application-specific clearance standards
        for app, min_mm in [("electrical", 3.0), ("hydraulic", 5.0),
                            ("pneumatic", 2.0), ("thermal", 10.0)]:
            min_m = min_mm / 1000.0
            code = D(f"""\
                // {app.capitalize()} clearance check: {min_mm}mm minimum
                Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
                modelDoc.Extension.SelectByID2("Part1-1@Assy", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                modelDoc.Extension.SelectByID2("Part2-1@Assy", "COMPONENT", 0, 0, 0, true, 0, null, 0);
                double minClearance = {min_m}; // {min_mm} mm ({app} standard)
                if (measure.Calculate(null)) {{
                    bool ok = measure.Distance >= minClearance;
                    Debug.WriteLine(ok
                        ? $"[PASS] {app.capitalize()} clearance: {{measure.Distance*1000:F3}} mm"
                        : $"[FAIL] {app.capitalize()} clearance: {{measure.Distance*1000:F3}} mm < {min_mm} mm");
                }}""")
            p.append((
                f"Verify that the clearance between two components meets the {app} "
                f"standard minimum of {min_mm}mm.",
                code))

        return p

    def _clearance_iteration_pairs(self) -> list[tuple[str, str]]:
        """Iterate all component pairs for clearance checking."""
        p: list[tuple[str, str]] = []

        # All-pairs minimum clearance
        code = D("""\
            // Find minimum clearance across all component pairs
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] comps = (object[])asmDoc.GetComponents(false);
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            double globalMin = double.MaxValue;
            string minPair = "";
            for (int i = 0; i < comps.Length; i++) {
                for (int j = i + 1; j < comps.Length; j++) {
                    Component2 cA = (Component2)comps[i];
                    Component2 cB = (Component2)comps[j];
                    modelDoc.ClearSelection2(true);
                    modelDoc.Extension.SelectByID2(
                        cA.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    modelDoc.Extension.SelectByID2(
                        cB.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, true, 0, null, 0);
                    if (measure.Calculate(null) && measure.Distance < globalMin) {
                        globalMin = measure.Distance;
                        minPair = $"{cA.Name2} <-> {cB.Name2}";
                    }
                }
            }
            Debug.WriteLine($"Global minimum clearance: {globalMin*1000:F3} mm ({minPair})");""")
        p.append((
            "Find the minimum clearance across all pairs of components in a "
            "SolidWorks assembly.",
            code))

        # Pairs below threshold
        code = D("""\
            // Find all component pairs with clearance below threshold
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] comps = (object[])asmDoc.GetComponents(false);
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            double threshold = 0.002; // 2mm
            var violations = new List<(string Pair, double Dist)>();
            for (int i = 0; i < comps.Length; i++) {
                for (int j = i + 1; j < comps.Length; j++) {
                    Component2 cA = (Component2)comps[i];
                    Component2 cB = (Component2)comps[j];
                    modelDoc.ClearSelection2(true);
                    modelDoc.Extension.SelectByID2(
                        cA.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    modelDoc.Extension.SelectByID2(
                        cB.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, true, 0, null, 0);
                    if (measure.Calculate(null) && measure.Distance < threshold) {
                        violations.Add(($"{cA.Name2} <-> {cB.Name2}", measure.Distance));
                    }
                }
            }
            Debug.WriteLine($"{violations.Count} pair(s) below {threshold*1000}mm:");
            foreach (var v in violations)
                Debug.WriteLine($"  {v.Pair}: {v.Dist*1000:F3} mm");""")
        p.append((
            "Find all component pairs in a SolidWorks assembly where the clearance "
            "is below a 2mm threshold.",
            code))

        # Top-level components only (skip internal sub-parts)
        code = D("""\
            // Clearance check among top-level components only
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] comps = (object[])asmDoc.GetComponents(true); // top-level only
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            double minDist = double.MaxValue;
            string closest = "";
            for (int i = 0; i < comps.Length; i++) {
                for (int j = i + 1; j < comps.Length; j++) {
                    Component2 cA = (Component2)comps[i];
                    Component2 cB = (Component2)comps[j];
                    if (cA.GetSuppression() == (int)swComponentSuppressionState_e.swComponentSuppressed ||
                        cB.GetSuppression() == (int)swComponentSuppressionState_e.swComponentSuppressed)
                        continue;
                    modelDoc.ClearSelection2(true);
                    modelDoc.Extension.SelectByID2(
                        cA.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    modelDoc.Extension.SelectByID2(
                        cB.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, true, 0, null, 0);
                    if (measure.Calculate(null) && measure.Distance < minDist) {
                        minDist = measure.Distance;
                        closest = $"{cA.Name2} <-> {cB.Name2}";
                    }
                }
            }
            Debug.WriteLine($"Min clearance (top-level): {minDist*1000:F3} mm ({closest})");""")
        p.append((
            "Find the minimum clearance among top-level components only, skipping "
            "suppressed components, in a SolidWorks assembly.",
            code))

        return p

    def _clearance_report_pairs(self) -> list[tuple[str, str]]:
        """Clearance report generation."""
        p: list[tuple[str, str]] = []

        # CSV clearance report
        code = D("""\
            // Export clearance report to CSV
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] comps = (object[])asmDoc.GetComponents(true);
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            using (var sw = new System.IO.StreamWriter(@"C:\\Reports\\ClearanceReport.csv")) {
                sw.WriteLine("ComponentA,ComponentB,Clearance_mm,Status");
                double minReq = 0.002; // 2mm
                for (int i = 0; i < comps.Length; i++) {
                    for (int j = i + 1; j < comps.Length; j++) {
                        Component2 cA = (Component2)comps[i];
                        Component2 cB = (Component2)comps[j];
                        modelDoc.ClearSelection2(true);
                        modelDoc.Extension.SelectByID2(
                            cA.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, false, 0, null, 0);
                        modelDoc.Extension.SelectByID2(
                            cB.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, true, 0, null, 0);
                        if (measure.Calculate(null)) {
                            string status = measure.Distance >= minReq ? "PASS" : "FAIL";
                            sw.WriteLine($"{cA.Name2},{cB.Name2},{measure.Distance*1000:F3},{status}");
                        }
                    }
                }
            }
            Debug.WriteLine("Clearance report saved.");""")
        p.append((
            "Generate a CSV clearance report for all top-level component pairs "
            "in a SolidWorks assembly with pass/fail status.",
            code))

        # Summary statistics
        code = D("""\
            // Clearance summary statistics
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] comps = (object[])asmDoc.GetComponents(true);
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            var dists = new List<double>();
            for (int i = 0; i < comps.Length; i++) {
                for (int j = i + 1; j < comps.Length; j++) {
                    Component2 cA = (Component2)comps[i];
                    Component2 cB = (Component2)comps[j];
                    modelDoc.ClearSelection2(true);
                    modelDoc.Extension.SelectByID2(
                        cA.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    modelDoc.Extension.SelectByID2(
                        cB.Name2 + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, true, 0, null, 0);
                    if (measure.Calculate(null))
                        dists.Add(measure.Distance);
                }
            }
            if (dists.Count > 0) {
                dists.Sort();
                Debug.WriteLine($"Pairs measured: {dists.Count}");
                Debug.WriteLine($"Min clearance:  {dists[0]*1000:F3} mm");
                Debug.WriteLine($"Max clearance:  {dists[dists.Count-1]*1000:F3} mm");
                Debug.WriteLine($"Avg clearance:  {dists.Average()*1000:F3} mm");
            }""")
        p.append((
            "Calculate clearance summary statistics (min, max, average) across all "
            "component pairs in a SolidWorks assembly.",
            code))

        # Clearance heatmap data export
        code = D("""\
            // Export clearance matrix for heatmap visualization
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] comps = (object[])asmDoc.GetComponents(true);
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            int n = comps.Length;
            double[,] matrix = new double[n, n];
            string[] names = new string[n];
            for (int i = 0; i < n; i++)
                names[i] = ((Component2)comps[i]).Name2;
            for (int i = 0; i < n; i++) {
                for (int j = i + 1; j < n; j++) {
                    modelDoc.ClearSelection2(true);
                    modelDoc.Extension.SelectByID2(
                        names[i] + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    modelDoc.Extension.SelectByID2(
                        names[j] + "@" + modelDoc.GetTitle(), "COMPONENT", 0, 0, 0, true, 0, null, 0);
                    double dist = measure.Calculate(null) ? measure.Distance : -1;
                    matrix[i, j] = dist; matrix[j, i] = dist;
                }
            }
            using (var sw = new System.IO.StreamWriter(@"C:\\Reports\\ClearanceMatrix.csv")) {
                sw.WriteLine("," + string.Join(",", names));
                for (int i = 0; i < n; i++) {
                    var row = new List<string> { names[i] };
                    for (int j = 0; j < n; j++)
                        row.Add((matrix[i, j] * 1000).ToString("F3"));
                    sw.WriteLine(string.Join(",", row));
                }
            }
            Debug.WriteLine("Clearance matrix exported for heatmap.");""")
        p.append((
            "Export a clearance distance matrix for all component pairs as a CSV "
            "file suitable for heatmap visualization.",
            code))

        # Clearance check with tolerance deduction
        code = D("""\
            // Clearance check with tolerance stack-up deduction
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            modelDoc.Extension.SelectByID2("Plate1-1@Assy", "COMPONENT", 0, 0, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("Plate2-1@Assy", "COMPONENT", 0, 0, 0, true, 0, null, 0);
            double toleranceStack = 0.0006; // 0.6mm total stack-up (meters)
            double minRequired = 0.002;     // 2mm minimum clearance (meters)
            if (measure.Calculate(null)) {
                double nominal = measure.Distance;
                double worstCase = nominal - toleranceStack;
                bool ok = worstCase >= minRequired;
                Debug.WriteLine($"Nominal: {nominal*1000:F3} mm");
                Debug.WriteLine($"Worst-case: {worstCase*1000:F3} mm (after {toleranceStack*1000:F1} mm stack-up)");
                Debug.WriteLine(ok ? "[PASS]" : "[FAIL] Below minimum clearance");
            }""")
        p.append((
            "Check clearance between two plates accounting for tolerance stack-up "
            "to determine worst-case minimum clearance.",
            code))

        # Clearance along specific axis
        code = D("""\
            // Measure clearance along Z-axis (vertical gap)
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            modelDoc.Extension.SelectByID2("Upper-1@Assy", "COMPONENT", 0, 0, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("Lower-1@Assy", "COMPONENT", 0, 0, 0, true, 0, null, 0);
            if (measure.Calculate(null)) {
                double dx = Math.Abs(measure.X2 - measure.X1);
                double dy = Math.Abs(measure.Y2 - measure.Y1);
                double dz = Math.Abs(measure.Z2 - measure.Z1);
                Debug.WriteLine($"Total distance: {measure.Distance*1000:F3} mm");
                Debug.WriteLine($"X component: {dx*1000:F3} mm");
                Debug.WriteLine($"Y component: {dy*1000:F3} mm");
                Debug.WriteLine($"Z component: {dz*1000:F3} mm");
            }""")
        p.append((
            "Measure the clearance between two components and break it down into "
            "X, Y, and Z axis components.",
            code))

        # Concentric clearance (radial gap)
        code = D("""\
            // Measure radial clearance between concentric components (shaft/bore)
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            // Select the outer face (bore) and inner face (shaft)
            modelDoc.Extension.SelectByID2("", "FACE", 0.025, 0, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("", "FACE", 0.010, 0, 0, true, 0, null, 0);
            if (measure.Calculate(null)) {
                double radialGap = measure.Distance;
                double diametralGap = radialGap * 2;
                Debug.WriteLine($"Radial clearance: {radialGap*1000:F4} mm");
                Debug.WriteLine($"Diametral clearance: {diametralGap*1000:F4} mm");
            }""")
        p.append((
            "Measure the radial and diametral clearance between a shaft and bore "
            "by selecting their cylindrical faces.",
            code))

        # Multiple clearance checks with named pairs
        code = D("""\
            // Check multiple named clearance pairs against requirements
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            var checks = new[] {
                new { CompA = "Motor-1", CompB = "PCB-1", MinMM = 5.0, Desc = "Motor-to-PCB" },
                new { CompA = "Fan-1", CompB = "Cover-1", MinMM = 3.0, Desc = "Fan-to-Cover" },
                new { CompA = "Battery-1", CompB = "Frame-1", MinMM = 2.0, Desc = "Battery-to-Frame" },
                new { CompA = "Heatsink-1", CompB = "Enclosure-1", MinMM = 10.0, Desc = "Heatsink-to-Enclosure" },
            };
            string asmTitle = modelDoc.GetTitle();
            foreach (var chk in checks) {
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2(chk.CompA + "@" + asmTitle, "COMPONENT", 0, 0, 0, false, 0, null, 0);
                modelDoc.Extension.SelectByID2(chk.CompB + "@" + asmTitle, "COMPONENT", 0, 0, 0, true, 0, null, 0);
                if (measure.Calculate(null)) {
                    bool ok = measure.Distance >= chk.MinMM / 1000.0;
                    Debug.WriteLine($"{chk.Desc}: {measure.Distance*1000:F2} mm " +
                        (ok ? "[PASS]" : $"[FAIL] < {chk.MinMM} mm"));
                }
            }""")
        p.append((
            "Check multiple named component pairs against their individual minimum "
            "clearance requirements in a SolidWorks assembly.",
            code))

        return p

    # ==================================================================
    # 3. Collision Detection  (~20 pairs)
    # ==================================================================

    def _collision_setup_pairs(self) -> list[tuple[str, str]]:
        """Collision detection manager setup."""
        p: list[tuple[str, str]] = []

        # Basic activation
        code = D("""\
            // Activate collision detection
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            colMgr.Activate();
            colMgr.UseCoincidenceTreatment = true;
            colMgr.UseSoundNotification = true;
            colMgr.UseStopAtCollision = true;
            Debug.WriteLine("Collision detection activated.");""")
        p.append((
            "Activate collision detection with coincidence treatment, sound "
            "notification, and stop-at-collision in a SolidWorks assembly.",
            code))

        # Activate with all options
        code = D("""\
            // Full collision detection setup
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            colMgr.Activate();
            colMgr.UseCoincidenceTreatment = true;
            colMgr.UseSoundNotification = true;
            colMgr.UseStopAtCollision = true;
            colMgr.UseHighlightCollisionFaces = true;
            colMgr.UseDynamicClearance = true;
            colMgr.DynamicClearanceValue = 0.005; // 5mm
            Debug.WriteLine("Full collision detection configured.");""")
        p.append((
            "Set up collision detection with all options including face highlighting "
            "and 5mm dynamic clearance.",
            code))

        # Activate without sound
        code = D("""\
            // Silent collision detection
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            colMgr.Activate();
            colMgr.UseCoincidenceTreatment = false;
            colMgr.UseSoundNotification = false;
            colMgr.UseStopAtCollision = false;
            colMgr.UseHighlightCollisionFaces = true;
            Debug.WriteLine("Silent collision detection (visual only).");""")
        p.append((
            "Activate collision detection in silent mode with only visual face "
            "highlighting in a SolidWorks assembly.",
            code))

        # Deactivate
        code = D("""\
            // Deactivate collision detection
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            colMgr.Deactivate();
            Debug.WriteLine("Collision detection deactivated.");""")
        p.append((
            "Deactivate collision detection in a SolidWorks assembly.",
            code))

        # Toggle collision detection
        code = D("""\
            // Toggle collision detection on/off
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            if (colMgr.IsActive()) {
                colMgr.Deactivate();
                Debug.WriteLine("Collision detection OFF.");
            } else {
                colMgr.Activate();
                colMgr.UseStopAtCollision = true;
                colMgr.UseHighlightCollisionFaces = true;
                Debug.WriteLine("Collision detection ON.");
            }""")
        p.append((
            "Toggle collision detection on or off in a SolidWorks assembly.",
            code))

        return p

    def _collision_config_pairs(self) -> list[tuple[str, str]]:
        """Collision detection parameter configuration."""
        p: list[tuple[str, str]] = []

        # Dynamic clearance with different values
        for val_mm in [1.0, 2.0, 3.0, 5.0, 10.0]:
            val_m = val_mm / 1000.0
            code = D(f"""\
                // Set dynamic clearance to {val_mm}mm
                CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
                colMgr.Activate();
                colMgr.UseDynamicClearance = true;
                colMgr.DynamicClearanceValue = {val_m}; // {val_mm} mm
                Debug.WriteLine("Dynamic clearance set to {val_mm} mm.");""")
            p.append((
                f"Set up collision detection with a {val_mm}mm dynamic clearance zone "
                f"in a SolidWorks assembly.",
                code))

        # Exclude specific components
        code = D("""\
            // Exclude fasteners from collision detection
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            colMgr.Activate();
            colMgr.UseStopAtCollision = true;
            // Suppress fasteners to exclude them from collision
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] comps = (object[])asmDoc.GetComponents(false);
            string[] excludePrefixes = { "Bolt", "Screw", "Nut", "Washer" };
            foreach (Component2 comp in comps) {
                foreach (string pfx in excludePrefixes) {
                    if (comp.Name2.StartsWith(pfx)) {
                        comp.SetSuppression2(
                            (int)swComponentSuppressionState_e.swComponentLightweight);
                        break;
                    }
                }
            }
            Debug.WriteLine("Collision detection active (fasteners excluded).");""")
        p.append((
            "Set up collision detection in a SolidWorks assembly while excluding "
            "fastener components (bolts, screws, nuts, washers).",
            code))

        # Configure for component dragging
        code = D("""\
            // Configure collision detection for interactive component dragging
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            colMgr.Activate();
            colMgr.UseCoincidenceTreatment = true;
            colMgr.UseSoundNotification = true;
            colMgr.UseStopAtCollision = true;
            colMgr.UseHighlightCollisionFaces = true;
            colMgr.UseDynamicClearance = false;
            Debug.WriteLine("Collision detection ready for component dragging.");""")
        p.append((
            "Configure collision detection for interactive component dragging with "
            "stop-at-collision and face highlighting.",
            code))

        return p

    def _collision_result_pairs(self) -> list[tuple[str, str]]:
        """Collision detection result handling."""
        p: list[tuple[str, str]] = []

        # Get collision count
        code = D("""\
            // Check current collision status
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            if (!colMgr.IsActive()) {
                colMgr.Activate();
                colMgr.UseStopAtCollision = false;
            }
            int nCollisions = colMgr.GetCollisionCount();
            Debug.WriteLine($"Current collisions: {nCollisions}");""")
        p.append((
            "Get the current number of collisions detected by the collision "
            "detection manager in a SolidWorks assembly.",
            code))

        # Get colliding pairs
        code = D("""\
            // Get colliding component pairs
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            if (!colMgr.IsActive()) colMgr.Activate();
            int nCollisions = colMgr.GetCollisionCount();
            for (int i = 0; i < nCollisions; i++) {
                object comp1 = null, comp2 = null;
                colMgr.GetCollision(i, out comp1, out comp2);
                if (comp1 != null && comp2 != null) {
                    Debug.WriteLine($"  Collision {i+1}: " +
                        $"{((Component2)comp1).Name2} <-> {((Component2)comp2).Name2}");
                }
            }""")
        p.append((
            "Iterate over all detected collisions and print the colliding component "
            "pairs in a SolidWorks assembly.",
            code))

        # Monitor collisions during a programmatic move
        code = D("""\
            // Monitor collisions while moving a component programmatically
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            colMgr.Activate();
            colMgr.UseStopAtCollision = false;
            colMgr.UseHighlightCollisionFaces = true;
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            Component2 comp = (Component2)asmDoc.GetComponentByName("Slider-1");
            MathUtility mathUtil = (MathUtility)swApp.GetMathUtility();
            for (int step = 0; step < 20; step++) {
                MathTransform xform = comp.Transform2;
                double[] tData = (double[])xform.ArrayData;
                tData[9] += 0.001; // move 1mm per step in X
                xform.ArrayData = tData;
                comp.Transform2 = xform;
                modelDoc.EditRebuild3();
                int nCol = colMgr.GetCollisionCount();
                if (nCol > 0) {
                    Debug.WriteLine($"Collision at step {step} (X offset {step+1}mm)!");
                    break;
                }
            }
            colMgr.Deactivate();""")
        p.append((
            "Move a component incrementally and monitor for collisions at each "
            "step using the collision detection manager.",
            code))

        # Full activate-check-deactivate cycle
        code = D("""\
            // Complete collision detection workflow
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            // 1. Activate
            colMgr.Activate();
            colMgr.UseCoincidenceTreatment = true;
            colMgr.UseHighlightCollisionFaces = true;
            // 2. Check
            int nCollisions = colMgr.GetCollisionCount();
            Debug.WriteLine($"Collisions detected: {nCollisions}");
            for (int i = 0; i < nCollisions; i++) {
                object c1 = null, c2 = null;
                colMgr.GetCollision(i, out c1, out c2);
                Debug.WriteLine($"  {((Component2)c1).Name2} <-> {((Component2)c2).Name2}");
            }
            // 3. Deactivate
            colMgr.Deactivate();
            Debug.WriteLine("Collision detection cycle complete.");""")
        p.append((
            "Run a complete collision detection cycle: activate, check for "
            "collisions, report results, and deactivate.",
            code))

        # Log collisions to file
        code = D("""\
            // Log collisions to file
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            if (!colMgr.IsActive()) colMgr.Activate();
            int nCollisions = colMgr.GetCollisionCount();
            using (var sw = new System.IO.StreamWriter(@"C:\\Reports\\CollisionLog.txt", true)) {
                sw.WriteLine($"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] Collisions: {nCollisions}");
                for (int i = 0; i < nCollisions; i++) {
                    object c1 = null, c2 = null;
                    colMgr.GetCollision(i, out c1, out c2);
                    sw.WriteLine($"  {((Component2)c1).Name2} <-> {((Component2)c2).Name2}");
                }
            }
            colMgr.Deactivate();
            Debug.WriteLine($"Logged {nCollisions} collision(s).");""")
        p.append((
            "Log all detected collisions with timestamps to a text file in "
            "a SolidWorks assembly.",
            code))

        # Collision detection for linear motion path
        code = D("""\
            // Check collision-free linear travel distance
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            colMgr.Activate();
            colMgr.UseStopAtCollision = false;
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            Component2 comp = (Component2)asmDoc.GetComponentByName("Carriage-1");
            double stepSize = 0.001; // 1mm
            double maxTravel = 0;
            for (int step = 0; step < 200; step++) {
                MathTransform xform = comp.Transform2;
                double[] tData = (double[])xform.ArrayData;
                tData[9] += stepSize; // move in X
                xform.ArrayData = tData;
                comp.Transform2 = xform;
                modelDoc.EditRebuild3();
                if (colMgr.GetCollisionCount() > 0) break;
                maxTravel += stepSize;
            }
            colMgr.Deactivate();
            Debug.WriteLine($"Collision-free travel: {maxTravel*1000:F1} mm");""")
        p.append((
            "Determine the maximum collision-free linear travel distance for a "
            "sliding component in a SolidWorks assembly.",
            code))

        # Collision check between specific pair
        code = D("""\
            // Check collision between two specific components
            CollisionDetectionManager colMgr = modelDoc.Extension.GetCollisionDetectionManager();
            colMgr.Activate();
            colMgr.UseHighlightCollisionFaces = true;
            int nCollisions = colMgr.GetCollisionCount();
            bool targetCollision = false;
            for (int i = 0; i < nCollisions; i++) {
                object c1 = null, c2 = null;
                colMgr.GetCollision(i, out c1, out c2);
                string n1 = ((Component2)c1).Name2;
                string n2 = ((Component2)c2).Name2;
                if ((n1 == "Arm-1" && n2 == "Guard-1") || (n1 == "Guard-1" && n2 == "Arm-1")) {
                    targetCollision = true;
                    Debug.WriteLine("[COLLISION] Arm-1 <-> Guard-1 detected!");
                }
            }
            if (!targetCollision)
                Debug.WriteLine("[OK] No collision between Arm-1 and Guard-1.");
            colMgr.Deactivate();""")
        p.append((
            "Check if a specific pair of components (Arm and Guard) are colliding "
            "using the collision detection manager.",
            code))

        return p

    # ==================================================================
    # 4. Conceptual Pairs  (~30 pairs)
    # ==================================================================

    def _conceptual_pairs(self) -> list[tuple[str, str]]:
        """Conceptual, best-practice, and workflow explanation pairs."""
        p: list[tuple[str, str]] = []

        # --- Definitions and distinctions ---

        p.append((
            "What is the difference between interference detection, clearance "
            "verification, and collision detection in SolidWorks?",
            D("""\
                // Interference Detection:
                //   Static check that finds overlapping volumes between components
                //   in the current assembly state. Uses ToolsCheckInterference().
                //   Reports interference bodies, volumes, and involved components.
                //
                // Clearance Verification:
                //   Measures the minimum distance (gap) between components.
                //   Uses the Measure API to verify that components maintain required
                //   spacing. Returns distance, not overlap.
                //
                // Collision Detection:
                //   Dynamic, real-time check during component motion (dragging).
                //   Uses CollisionDetectionManager to prevent or warn about collisions
                //   as components are moved interactively or programmatically.
                //   Can include dynamic clearance zones.""")))

        p.append((
            "When should I use interference detection versus collision detection "
            "in a SolidWorks assembly?",
            D("""\
                // Use Interference Detection when:
                //   - Validating an assembly at a specific state (design review)
                //   - Running batch checks across multiple assemblies
                //   - Generating reports with exact overlap volumes
                //   - Checking after mate changes or design modifications
                //
                // Use Collision Detection when:
                //   - Moving or positioning components interactively
                //   - Simulating mechanism motion and checking clearance paths
                //   - Need real-time feedback (sound, visual highlighting)
                //   - Want to prevent components from overlapping during placement""")))

        p.append((
            "How do I interpret interference detection results that show very "
            "small volumes in SolidWorks?",
            D("""\
                // Very small interference volumes (< 0.001 mm^3) are often caused by:
                //   1. Numerical precision (floating-point tolerance in geometry kernel)
                //   2. Coincident faces touching (not true overlap)
                //   3. Tangent conditions at curved surfaces
                //
                // Recommendations:
                //   - Set a volume threshold filter (e.g., ignore < 0.1 mm^3)
                //   - Use the coincidence treatment flag to distinguish touching from overlap
                //   - Review the interference body shape: a paper-thin body suggests touching
                //   - Compare with the tolerance/fit specification for the joint
                //
                // Example threshold filter:
                // double threshold = 1e-10; // ~0.1 mm^3 in m^3
                // if (intf.Volume > threshold) { /* report */ }""")))

        p.append((
            "What is the difference between a true interference and a touching "
            "condition in SolidWorks?",
            D("""\
                // True Interference: Component bodies occupy the same physical space.
                //   The interference body has measurable volume (> 0).
                //   Must be resolved unless it represents an intentional press fit.
                //
                // Touching (Coincident): Component surfaces meet but do not overlap.
                //   The interference "volume" is zero or near-zero.
                //   This is usually normal for mating surfaces.
                //
                // The treatCoincidenceAsInterference parameter in ToolsCheckInterference
                // controls whether touching conditions are reported:
                //   true  -> touching pairs appear in results (volume ~= 0)
                //   false -> only true overlaps are reported""")))

        # --- Best practices ---

        p.append((
            "What are best practices for running interference detection on large "
            "SolidWorks assemblies?",
            D("""\
                // Best practices for large assembly interference checks:
                //
                // 1. Use Lightweight mode: Resolve only needed components
                //    asmDoc.ResolveAllLightWeightComponents(true);
                //
                // 2. Check subassemblies individually first, then top level
                //    (reduces combinatorial explosion of component pairs)
                //
                // 3. Set treatCoincidenceAsInterference = false to reduce noise
                //
                // 4. Set createInterferenceBodies = false for faster checking
                //    (only set true when you need volume/geometry data)
                //
                // 5. Filter results by volume threshold to ignore numerical noise
                //
                // 6. Suppress non-critical components (fasteners, cosmetic parts)
                //    before running the check
                //
                // 7. Run checks in background/batch overnight for very large assemblies
                //
                // 8. Cache results and only re-check modified subassemblies""")))

        p.append((
            "How can I optimize interference detection performance in SolidWorks?",
            D("""\
                // Performance optimization strategies:
                //
                // 1. Disable interference bodies (createInterferenceBodies = false)
                //    Speed increase: ~2-3x for assemblies with many interferences
                //
                // 2. Use selective checking (pre-select components of interest)
                //    instead of checking all vs. all
                //    N components = N*(N-1)/2 pairs. Selecting 10 of 1000 = 45 pairs vs 499,500
                //
                // 3. Suppress non-essential components before checking:
                //    cosmetic covers, labels, fasteners (if not structurally relevant)
                //
                // 4. Use simplified representations/configurations
                //    that remove internal detail but preserve external envelope
                //
                // 5. Check only top-level components first:
                //    asmDoc.GetComponents(true) // top-level only
                //    Then drill into flagged subassemblies
                //
                // 6. Close other SolidWorks documents to free memory""")))

        p.append((
            "How should I handle interference detection for assemblies with "
            "hidden or suppressed components?",
            D("""\
                // Hidden vs Suppressed components in interference detection:
                //
                // Suppressed components:
                //   - NOT included in interference detection (geometry not loaded)
                //   - This is the preferred way to exclude components from checks
                //
                // Hidden components:
                //   - ARE included in interference detection (geometry is still loaded)
                //   - Hiding only affects visibility, not the check
                //   - To exclude hidden components, temporarily suppress them
                //
                // Lightweight components:
                //   - May need to be resolved before interference detection
                //   - asmDoc.ResolveAllLightWeightComponents(true);
                //   - Unresolved lightweight components may give incomplete results
                //
                // Best practice: Create a configuration specifically for
                // interference checking where irrelevant components are suppressed.""")))

        # --- Press fit and intentional overlaps ---

        p.append((
            "How do I distinguish between intentional press fits and unintended "
            "interferences in SolidWorks?",
            D("""\
                // Distinguishing press fits from errors:
                //
                // 1. Maintain an allowed-interference list (component pairs with fit specs):
                //    var pressFits = new HashSet<string> {
                //        "Bearing-1|Shaft-1",     // H7/p6 press fit
                //        "Pin-1|Housing-1",        // H7/r6 press fit
                //        "Bushing-1|Bore-1"        // H7/s6 interference fit
                //    };
                //
                // 2. Check interference volume against expected overlap:
                //    For a shaft/bearing press fit with 0.02mm diametral interference
                //    on a 20mm diameter, 30mm long bearing:
                //    Expected volume ~ pi * 20 * 0.01 * 30 = ~18.85 mm^3
                //    Flag if actual volume deviates significantly from expected
                //
                // 3. Use custom properties on components to mark intentional fits:
                //    comp.CustomProperties("FitType") = "PressFit"
                //
                // 4. Store allowed pairs in an external config file for maintenance""")))

        p.append((
            "What are common interference fit designations and their typical "
            "overlap values?",
            D("""\
                // Common interference fit designations (ISO 286):
                //
                // Light Press Fits (H7/p6):
                //   Overlap: 0.001 - 0.025 mm (diameter-dependent)
                //   Use: Bearings, bushings that can be pressed in/out
                //
                // Medium Press Fits (H7/r6):
                //   Overlap: 0.015 - 0.045 mm
                //   Use: Permanent press fits, gear on shaft
                //
                // Heavy Press Fits (H7/s6):
                //   Overlap: 0.030 - 0.070 mm
                //   Use: Heavy-duty permanent fits, shrink fits
                //
                // Force Fits (H7/u6):
                //   Overlap: 0.060 - 0.110 mm
                //   Use: Extreme permanent assembly, requires heating/cooling
                //
                // When filtering interference results:
                //   - Press fit interferences should have small, consistent volumes
                //   - Unexpected interferences often have irregular volumes
                //   - Compare detected volume to calculated expected volume""")))

        # --- Clearance standards ---

        p.append((
            "What are typical minimum clearance requirements for different "
            "engineering applications?",
            D("""\
                // Typical minimum clearance standards by application:
                //
                // Electrical / Electronics:
                //   PCB to enclosure:     3.0 mm minimum
                //   High-voltage:         per IPC-2221 (voltage-dependent)
                //   Cable routing:        1.5x cable bend radius
                //
                // Hydraulic Systems:
                //   Hose routing:         5.0 mm to moving parts
                //   Fitting access:       25 mm for wrench clearance
                //   Pressure lines:       2x hose OD from heat sources
                //
                // Pneumatic Systems:
                //   Tube routing:         2.0 mm to structure
                //   Actuator stroke:      5.0 mm end clearance
                //
                // Thermal:
                //   Heat sink:            10.0 mm airflow gap
                //   Exhaust:              25.0 mm from plastic/rubber
                //
                // Mechanical / General:
                //   Moving parts:         2.0 mm minimum
                //   Service access:       50 mm for hand access
                //   Tool access:          per tool envelope dimensions""")))

        p.append((
            "How do GD&T tolerances relate to clearance verification in "
            "SolidWorks assemblies?",
            D("""\
                // GD&T and clearance relationship:
                //
                // Nominal clearance from CAD is the ideal gap. Real clearance depends on:
                //   1. Size tolerances: +/- on diameters, lengths
                //   2. Geometric tolerances: position, flatness, perpendicularity
                //   3. Assembly tolerances: how accurately parts are located
                //
                // Worst-case clearance = Nominal gap - tolerance stack-up
                //
                // Example: Two plates with 2.0mm nominal gap
                //   Plate A flatness: 0.1 mm
                //   Plate B flatness: 0.1 mm
                //   Position tolerance: 0.2 mm (each plate)
                //   Worst-case reduction: 0.1 + 0.1 + 0.2 + 0.2 = 0.6 mm
                //   Minimum real clearance: 2.0 - 0.6 = 1.4 mm
                //
                // In SolidWorks:
                //   CAD shows nominal geometry only. When verifying clearance,
                //   subtract the tolerance stack from the measured distance to get
                //   the minimum guaranteed clearance.
                //   Use TolAnalyst or manual stack-up analysis for critical gaps.""")))

        p.append((
            "How does tolerance stack-up affect clearance in assemblies?",
            D("""\
                // Tolerance stack-up and clearance:
                //
                // Linear stack (worst case):
                //   Min clearance = Nominal gap - Sum(all contributing tolerances)
                //   Conservative but may over-design
                //
                // RSS (Root Sum Square) statistical stack:
                //   Min clearance = Nominal gap - sqrt(Sum(tol_i^2))
                //   More realistic for high-volume production
                //
                // Example: 5 parts in a stack, each +/- 0.1mm, nominal gap 2.0mm
                //   Worst case: 2.0 - 5*0.1 = 1.5mm min clearance
                //   RSS:        2.0 - sqrt(5*0.01) = 2.0 - 0.224 = 1.776mm
                //
                // SolidWorks approach:
                //   1. Model at nominal dimensions
                //   2. Measure nominal clearance via API
                //   3. Subtract tolerance stack from nominal clearance
                //   4. Verify minimum clearance meets specification
                //
                // For automated checking:
                //   double nominal = measure.Distance;
                //   double stackUp = 0.6e-3; // 0.6mm from stack analysis
                //   double minClearance = nominal - stackUp;""")))

        # --- Workflows ---

        p.append((
            "What is a recommended assembly validation workflow before releasing "
            "a design in SolidWorks?",
            D("""\
                // Pre-release assembly validation workflow:
                //
                // Step 1: Resolve all components
                //   asmDoc.ResolveAllLightWeightComponents(true);
                //
                // Step 2: Rebuild and check for errors
                //   modelDoc.ForceRebuild3(true);
                //   Check FeatureManager for rebuild errors
                //
                // Step 3: Interference detection
                //   Run ToolsCheckInterference with createBodies=true
                //   Filter out known press fits
                //   Flag any unexpected interferences as BLOCK
                //
                // Step 4: Clearance verification
                //   Check critical gaps against minimum requirements
                //   Subtract tolerance stack-up from nominal clearance
                //
                // Step 5: Mass properties validation
                //   Compare assembly mass to target/estimate
                //
                // Step 6: Mate diagnostics
                //   Check for over-defined or conflicting mates
                //
                // Step 7: Generate report
                //   Export interference, clearance, and mass data to CSV/PDF
                //   Include screenshots of any flagged issues""")))

        p.append((
            "What is a design for assembly (DFA) checklist for clearance?",
            D("""\
                // Design for Assembly (DFA) clearance checklist:
                //
                // 1. Tool Access:
                //    [ ] Wrench/socket clearance around all fasteners (min 25mm)
                //    [ ] Screwdriver access (straight-line path, min 50mm length)
                //    [ ] Allen key clearance (min 15mm swing radius)
                //
                // 2. Hand Access:
                //    [ ] Two-finger grip: 25mm minimum gap
                //    [ ] Full hand: 50mm minimum gap
                //    [ ] Gloved hand: 75mm minimum gap
                //
                // 3. Component Insertion:
                //    [ ] Chamfers/lead-ins on mating features (0.5-1.0mm)
                //    [ ] Self-locating features where possible
                //    [ ] Adequate clearance for insertion path (no interference)
                //
                // 4. Service/Maintenance:
                //    [ ] Removable components have extraction clearance
                //    [ ] Inspection ports accessible (min 100mm opening)
                //    [ ] Wear items replaceable without major disassembly
                //
                // 5. Manufacturing Variation:
                //    [ ] Clearances account for tolerance stack-up
                //    [ ] Worst-case fit verified with tolerance analysis""")))

        p.append((
            "How do I set up an automated nightly interference check in SolidWorks?",
            D("""\
                // Automated nightly interference check approach:
                //
                // 1. Create a SolidWorks macro (.swp) or standalone C# executable
                //    that iterates over assembly files in a directory
                //
                // 2. Use Task Scheduler or Windows Scheduled Tasks to launch:
                //    - SolidWorks in background mode, or
                //    - sldworks.exe /m <macro path> for macro execution
                //
                // 3. Macro workflow:
                //    a. Read file list from folder or config file
                //    b. Open each assembly silently (swOpenDocOptions_Silent)
                //    c. Run ToolsCheckInterference
                //    d. Write results to CSV/log file
                //    e. Close document
                //    f. Email summary report
                //
                // 4. Key API flags:
                //    swOpenDocOptions_Silent - suppress all dialogs
                //    createInterferenceBodies = false - faster
                //    treatCoincidence = false - less noise
                //
                // 5. Error handling: wrap each file in try/catch
                //    so one bad file does not stop the entire batch""")))

        p.append((
            "How should I organize interference detection results for a design "
            "review meeting?",
            D("""\
                // Organizing interference results for design review:
                //
                // 1. Summary table:
                //    | Category      | Count | Action Required |
                //    |---------------|-------|-----------------|
                //    | Critical      |   2   | Must fix        |
                //    | Warning       |   5   | Review          |
                //    | Known fits    |   8   | Accepted        |
                //    | Numerical noise|  12  | Ignore          |
                //
                // 2. Detail per critical/warning item:
                //    - Component pair names
                //    - Interference volume (mm^3)
                //    - Screenshot with highlighted interference body
                //    - Proposed resolution (move, resize, redesign)
                //    - Owner/assignee for fix
                //
                // 3. Trend tracking:
                //    - Compare with previous check (new vs resolved)
                //    - Track interference count over design iterations
                //
                // 4. Export formats:
                //    - CSV for data analysis
                //    - PDF report with screenshots
                //    - Include in PDM/PLM workflow as checklist gate""")))

        p.append((
            "What are common causes of false-positive interferences in SolidWorks?",
            D("""\
                // Common false-positive interference causes:
                //
                // 1. Coincident/touching faces:
                //    Two flat faces sharing a plane report as interference
                //    Fix: Set treatCoincidence = false
                //
                // 2. Tangent conditions at curved surfaces:
                //    Cylindrical faces tangent to flat faces
                //    Fix: Apply volume threshold (< 0.001 mm^3)
                //
                // 3. Threaded fastener geometry:
                //    Cosmetic vs modeled threads overlap with hole
                //    Fix: Exclude fastener components or use cosmetic threads
                //
                // 4. Imported geometry imprecision:
                //    STEP/IGES imports may have surface gaps or overlaps
                //    Fix: Heal geometry (Import Diagnostics) before checking
                //
                // 5. Sheet metal bend allowance:
                //    Flattened vs formed state conflicts
                //    Fix: Check only in formed configuration
                //
                // 6. Weldment structural members:
                //    Trim/extend bodies may show small overlaps at joints
                //    Fix: Apply volume threshold filter""")))

        p.append((
            "How do I handle interference detection when components have multiple "
            "configurations?",
            D("""\
                // Multi-configuration interference checking:
                //
                // Assemblies can reference different component configurations.
                // Interference results may differ per configuration.
                //
                // Strategy 1: Check each assembly configuration
                //   string[] configs = (string[])modelDoc.GetConfigurationNames();
                //   foreach (string cfg in configs) {
                //       modelDoc.ShowConfiguration2(cfg);
                //       modelDoc.EditRebuild3();
                //       int nIntf = 0;
                //       asmDoc.ToolsCheckInterference(..., out nIntf);
                //       Debug.WriteLine($"Config '{cfg}': {nIntf} interferences");
                //   }
                //
                // Strategy 2: Check only active configuration
                //   Faster, but may miss config-specific issues
                //
                // Strategy 3: Check only "release" configurations
                //   Skip design exploration configs, check only production configs
                //
                // Important: Always rebuild after switching configurations
                // before running interference detection.""")))

        p.append((
            "What is the performance impact of interference detection on very "
            "large assemblies in SolidWorks?",
            D("""\
                // Performance characteristics of interference detection:
                //
                // Time complexity: O(N^2) where N = number of components
                //   100 components  ->  ~4,950 pairs  ->  seconds
                //   500 components  ->  ~124,750 pairs ->  minutes
                //   2000 components ->  ~2M pairs      ->  potentially hours
                //
                // Memory impact:
                //   createInterferenceBodies = true uses significant memory
                //   Each interference body is a B-rep stored in memory
                //   For 100+ interferences, memory usage can spike
                //
                // Mitigation strategies:
                //   1. Hierarchical checking: subassemblies first
                //   2. Bounding box pre-filter (API does this internally)
                //   3. Suppress irrelevant components
                //   4. Use simplified configurations
                //   5. Set createInterferenceBodies = false for initial scan
                //      then re-run with bodies only for flagged pairs
                //   6. Run overnight as batch process for very large assemblies""")))

        p.append((
            "How do I verify clearance for moving mechanisms in SolidWorks?",
            D("""\
                // Clearance verification for moving mechanisms:
                //
                // 1. Use Motion Study with collision detection:
                //    ModelDoc2 -> MotionStudy -> Configure collision detection
                //    Run the study and check for collision events
                //
                // 2. Programmatic approach: sweep through motion range
                //    a. Identify the driving dimension or mate
                //    b. Step through discrete positions
                //    c. At each position, measure clearance to nearby components
                //    d. Record minimum clearance and the position where it occurs
                //
                // 3. Key considerations:
                //    - Check at multiple positions, not just endpoints
                //    - Include tolerance stack-up in minimum clearance check
                //    - Consider thermal expansion at operating temperature
                //    - Account for dynamic effects (vibration, deflection)
                //
                // 4. Report format:
                //    | Position (deg) | Clearance (mm) | Status |
                //    |      0         |     5.2        | PASS   |
                //    |     45         |     2.1        | PASS   |
                //    |     90         |     0.8        | FAIL   |""")))

        p.append((
            "How do I check clearance around electrical connectors in a "
            "SolidWorks assembly?",
            D("""\
                // Electrical connector clearance verification:
                //
                // Requirements (typical):
                //   - Mating clearance: 25mm in front of connector face
                //   - Side clearance: 5mm for cable bend radius
                //   - Locking tab clearance: 10mm for finger access
                //   - Cable routing: 3x cable diameter minimum bend radius
                //
                // API approach:
                //   1. Select connector component
                //   2. Measure distance to all adjacent components
                //   3. Check each distance against minimum for that direction
                //
                // Measure measure = modelDoc.Extension.CreateMeasure();
                // // Select connector
                // modelDoc.Extension.SelectByID2("J1-1@Assy", "COMPONENT", ...);
                // // Select each nearby component and check
                // foreach (string neighbor in nearbyComponents) {
                //     modelDoc.Extension.SelectByID2(neighbor, "COMPONENT", ..., true, ...);
                //     if (measure.Calculate(null) && measure.Distance < 0.025)
                //         Debug.WriteLine($"[FAIL] {neighbor}: {measure.Distance*1000:F1}mm < 25mm");
                // }""")))

        p.append((
            "What clearance considerations apply to sheet metal assemblies "
            "in SolidWorks?",
            D("""\
                // Sheet metal assembly clearance considerations:
                //
                // 1. Bend relief clearance:
                //    - Internal bend radius affects adjacent part clearance
                //    - Account for springback (material-dependent)
                //    - Typical: 1-2x material thickness extra clearance
                //
                // 2. Tab-and-slot fits:
                //    - Tab width vs slot width: 0.1-0.2mm clearance per side
                //    - Tab length vs material thickness: tight or interference
                //    - Self-fixturing designs need precise clearance control
                //
                // 3. Assembly stack-up:
                //    - Bent parts accumulate angular tolerance
                //    - Each bend adds +/- 0.1-0.5mm positional uncertainty
                //    - Verify clearance at worst-case bend angles
                //
                // 4. Weld joint clearance:
                //    - Butt weld: 0-2mm gap depending on process
                //    - Fillet weld: leg size determines minimum clearance
                //    - Access for welding torch: typically 20mm minimum
                //
                // 5. Check in both flat and formed states:
                //    - Some interferences only appear in one state""")))

        p.append((
            "How do I verify clearance for rotating components in a "
            "SolidWorks assembly?",
            D("""\
                // Rotating component clearance verification:
                //
                // 1. Identify the rotation axis and range
                // 2. Step through angular positions and measure clearance
                //
                // Example: Check clearance of a rotating arm
                // AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                // Component2 arm = (Component2)asmDoc.GetComponentByName("Arm-1");
                // Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
                // double minClearance = double.MaxValue;
                // double worstAngle = 0;
                //
                // for (int deg = 0; deg <= 360; deg += 5) {
                //     // Set the driving mate angle
                //     Dimension dim = (Dimension)modelDoc.Parameter("Angle@Mate1");
                //     dim.SystemValue = deg * Math.PI / 180.0;
                //     modelDoc.EditRebuild3();
                //
                //     // Measure to nearest static component
                //     modelDoc.ClearSelection2(true);
                //     // Select arm and frame, measure
                //     if (measure.Calculate(null) && measure.Distance < minClearance) {
                //         minClearance = measure.Distance;
                //         worstAngle = deg;
                //     }
                // }
                // Debug.WriteLine($"Min clearance: {minClearance*1000:F2}mm at {worstAngle} deg");""")))

        p.append((
            "How should I document interference and clearance check results "
            "in a PDM system?",
            D("""\
                // Documenting interference/clearance results in PDM:
                //
                // 1. Store results as custom properties on the assembly:
                //    modelDoc.AddCustomInfo3("", "InterferenceCheckDate",
                //        (int)swCustomInfoType_e.swCustomInfoText, DateTime.Now.ToString("yyyy-MM-dd"));
                //    modelDoc.AddCustomInfo3("", "InterferenceCount",
                //        (int)swCustomInfoType_e.swCustomInfoNumber, nInterferences.ToString());
                //    modelDoc.AddCustomInfo3("", "InterferenceStatus",
                //        (int)swCustomInfoType_e.swCustomInfoText, passed ? "PASS" : "FAIL");
                //
                // 2. Attach report file to PDM vault:
                //    Save CSV/PDF report alongside assembly in vault
                //    Reference report in assembly metadata
                //
                // 3. Workflow gate:
                //    Use PDM workflow condition to require InterferenceStatus = "PASS"
                //    before allowing transition to "Released" state
                //
                // 4. Revision tracking:
                //    Log each check with date, user, result, and assembly revision
                //    Compare results across revisions to track resolution progress""")))

        p.append((
            "What is the relationship between assembly mates and interference "
            "in SolidWorks?",
            D("""\
                // Mates and interference relationship:
                //
                // 1. Mates constrain relative positions of components.
                //    They do NOT prevent interference - mates define geometry,
                //    not physical collision boundaries.
                //
                // 2. Common mate-related interference causes:
                //    - Coincident mate on wrong face -> components overlap
                //    - Distance mate with wrong sign -> pushed through instead of apart
                //    - Missing mates -> under-constrained component drifts into neighbor
                //    - Conflicting mates -> solver puts component in unexpected position
                //
                // 3. Mate diagnostics before interference check:
                //    - Check for over-defined mates (red in FeatureManager)
                //    - Check for under-defined mates (yellow minus sign)
                //    - Verify mate references are on correct geometry
                //
                // 4. After interference detection:
                //    - Check if interfering components share mates
                //    - Verify mate offsets and alignments
                //    - Consider adding limit mates to prevent future overlap""")))

        p.append((
            "How do I handle interference detection with flexible subassemblies "
            "in SolidWorks?",
            D("""\
                // Flexible subassembly interference considerations:
                //
                // Flexible subassemblies allow internal components to move relative
                // to each other at the top-level assembly. This means:
                //
                // 1. Internal mates are solved in context of the parent assembly
                //    - Component positions may differ from the subassembly's own state
                //    - Interference results at top level may differ from subassembly level
                //
                // 2. Always check interference at the top-level assembly
                //    - This captures the actual solved positions
                //    - Subassembly-level check may miss issues caused by top-level mates
                //
                // 3. Performance impact:
                //    - Flexible subassemblies are slower to solve
                //    - More component pairs to check at top level
                //    - Consider making rigid for interference check if internal
                //      geometry is already validated
                //
                // 4. Workflow:
                //    a. Check subassembly as rigid first (internal validation)
                //    b. Make flexible and check at top level (interaction validation)
                //    c. Document both check results""")))

        p.append((
            "How do I check clearance between a component and its swept "
            "motion envelope in SolidWorks?",
            D("""\
                // Clearance to motion envelope:
                //
                // A motion envelope is the volume swept by a moving component
                // through its full range of motion. To check clearance:
                //
                // 1. Create motion envelope:
                //    - Use Motion Study to capture positions
                //    - Export swept volume as a derived part
                //    - Or manually create envelope geometry (bounding cylinder, etc.)
                //
                // 2. Insert envelope as reference component in assembly
                //
                // 3. Run interference detection between envelope and static components:
                //    AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                //    // Select envelope component
                //    modelDoc.Extension.SelectByID2("Envelope-1@Assy",
                //        "COMPONENT", 0, 0, 0, false, 0, null, 0);
                //    // Select static components
                //    modelDoc.Extension.SelectByID2("Frame-1@Assy",
                //        "COMPONENT", 0, 0, 0, true, 0, null, 0);
                //    int nIntf = 0;
                //    asmDoc.ToolsCheckInterference(..., out nIntf);
                //
                // 4. Any interference with the envelope = insufficient clearance
                //    for the moving component through its full range""")))

        p.append((
            "What clearance guidelines apply to design for manufacturing "
            "and assembly (DFMA)?",
            D("""\
                // DFMA clearance guidelines:
                //
                // Assembly clearances:
                //   - Self-aligning features: chamfer = 0.5-1.0mm at 45 degrees
                //   - Insertion clearance: 0.2-0.5mm diametral for pins in holes
                //   - Snap-fit deflection clearance: 2x deflection distance
                //   - Robot gripper access: 10mm minimum around grip points
                //
                // Manufacturing clearances:
                //   - CNC milling tool access: tool diameter + 2mm
                //   - EDM electrode clearance: 0.1-0.3mm per side
                //   - Casting draft: 1-3 degrees per side (affects clearance at parting)
                //   - Injection molding: 0.05-0.1mm shrinkage per 25mm
                //
                // Inspection clearances:
                //   - CMM probe access: 5mm minimum around measurement points
                //   - Visual inspection: line-of-sight path to critical features
                //   - Caliper access: 15mm jaw depth clearance
                //
                // Service clearances:
                //   - Replaceable part extraction path: part size + 10mm
                //   - Lubrication port access: 20mm wrench clearance
                //   - Adjustment screw access: screwdriver length + 20mm""")))

        p.append((
            "How do I use SolidWorks interference detection results to estimate "
            "the force required to assemble press-fit components?",
            D("""\
                // Estimating press-fit assembly force from interference results:
                //
                // 1. Get the interference volume and dimensions:
                //    - Interference body gives overlap geometry
                //    - For shaft/bore: diametral interference = shaft OD - bore ID
                //
                // 2. Calculate contact pressure (Lame equations):
                //    For a shaft pressed into a hub:
                //    p = delta / (d * ((1/E_hub)*((D^2+d^2)/(D^2-d^2) + v_hub) +
                //                      (1/E_shaft)*(1 - v_shaft)))
                //    where:
                //      delta = diametral interference
                //      d = shaft diameter, D = hub outer diameter
                //      E = Young's modulus, v = Poisson's ratio
                //
                // 3. Calculate assembly force:
                //    F = p * pi * d * L * mu
                //    where L = engagement length, mu = friction coefficient
                //
                // 4. API workflow:
                //    a. Run interference detection
                //    b. Get interference body dimensions from bounding box
                //    c. Calculate using material properties from custom properties
                //    d. Report force estimate alongside interference data""")))

        p.append((
            "What are the limitations of SolidWorks interference detection API?",
            D("""\
                // Limitations of SolidWorks interference detection API:
                //
                // 1. Geometry-only check:
                //    - Does not account for tolerances or fits
                //    - Shows nominal geometry overlap only
                //    - Does not know about intended press fits
                //
                // 2. Performance with large assemblies:
                //    - O(N^2) pair checking is inherently slow
                //    - No built-in parallel/multi-threaded option
                //    - May require significant memory for interference bodies
                //
                // 3. API surface:
                //    - No built-in exclusion list (must filter results manually)
                //    - No incremental check (re-checks everything each time)
                //    - Limited control over internal tessellation tolerance
                //
                // 4. Component state requirements:
                //    - Lightweight components may give incomplete results
                //    - Suppressed components are silently excluded
                //    - Hidden components ARE included (may be unexpected)
                //
                // 5. Results are transient:
                //    - Not stored in the document automatically
                //    - Must be captured and persisted by the calling code""")))

        p.append((
            "How do I combine interference detection and clearance verification "
            "into a single assembly validation routine?",
            D("""\
                // Combined interference + clearance validation routine
                // public static (bool Passed, string Report) ValidateAssembly(
                //     ModelDoc2 modelDoc, double minClearanceMM) {
                //
                //     var sb = new StringBuilder();
                //     bool passed = true;
                //     AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                //
                //     // Phase 1: Interference Detection
                //     int nIntf = 0;
                //     object interferences = asmDoc.ToolsCheckInterference(
                //         (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                //         false, false, out nIntf);
                //     if (nIntf > 0) { passed = false; sb.AppendLine($"FAIL: {nIntf} interference(s)"); }
                //     else sb.AppendLine("PASS: No interferences");
                //
                //     // Phase 2: Clearance Verification
                //     Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
                //     object[] comps = (object[])asmDoc.GetComponents(true);
                //     double minFound = double.MaxValue;
                //     for (int i = 0; i < comps.Length; i++) {
                //         for (int j = i + 1; j < comps.Length; j++) {
                //             modelDoc.ClearSelection2(true);
                //             // Select pair and measure...
                //             if (measure.Calculate(null) && measure.Distance < minFound)
                //                 minFound = measure.Distance;
                //         }
                //     }
                //     if (minFound < minClearanceMM / 1000.0) {
                //         passed = false;
                //         sb.AppendLine($"FAIL: Min clearance {minFound*1000:F2}mm < {minClearanceMM}mm");
                //     }
                //     return (passed, sb.ToString());
                // }""")))

        p.append((
            "How do I detect if two components are touching but not interfering "
            "in SolidWorks?",
            D("""\
                // Detecting touching (coincident) components:
                //
                // Method 1: Use ToolsCheckInterference with coincidence flag
                //   asmDoc.ToolsCheckInterference(
                //       level, treatCoincidenceAsInterference: true,
                //       createBodies, out nIntf);
                //   // Touching pairs will appear with Volume ~= 0
                //   foreach (IInterference intf in results) {
                //       if (intf.Volume < 1e-12) // essentially zero
                //           Debug.WriteLine("Touching (not interfering)");
                //       else
                //           Debug.WriteLine("True interference");
                //   }
                //
                // Method 2: Use Measure API
                //   If measure.Distance == 0 (or < tolerance), components are touching
                //   This is more reliable for identifying exact contact
                //
                // Method 3: Compare two runs
                //   Run 1: treatCoincidence = true  -> count_with
                //   Run 2: treatCoincidence = false -> count_without
                //   Touching count = count_with - count_without""")))

        p.append((
            "How do I set up interference detection to run automatically "
            "when an assembly is saved in SolidWorks?",
            D("""\
                // Auto-run interference detection on save (Add-in approach):
                //
                // In your SolidWorks C# Add-in, subscribe to the FileSaveNotify event:
                //
                // private int OnFileSaveNotify(string fileName) {
                //     ModelDoc2 doc = (ModelDoc2)swApp.ActiveDoc;
                //     if (doc.GetType() != (int)swDocumentTypes_e.swDocASSEMBLY)
                //         return 0; // only check assemblies
                //
                //     AssemblyDoc asm = (AssemblyDoc)doc;
                //     int nIntf = 0;
                //     asm.ToolsCheckInterference(
                //         (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                //         false, false, out nIntf);
                //
                //     if (nIntf > 0) {
                //         DialogResult result = MessageBox.Show(
                //             $"{nIntf} interference(s) detected. Save anyway?",
                //             "Interference Warning",
                //             MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
                //         if (result == DialogResult.No)
                //             return 1; // cancel save
                //     }
                //     return 0; // allow save
                // }""")))

        return p
