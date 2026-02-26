"""Motion study training data generator for SolidWorks Semantic Engine.

Generates instruction/code training pairs for SolidWorks motion studies:
motors, springs, dampers, forces, simulation results, and conceptual.

All dimensional values use meters (SolidWorks API internal convention).
Angular velocities in rad/s, forces in N, stiffness in N/m.

Target: ~220-280 training pairs across 5 motion study domains.
"""

from __future__ import annotations

import math
import textwrap
from typing import List, Tuple

TrainingPair = Tuple[str, str]
D = textwrap.dedent


def _mm(v: float) -> float:
    return v / 1000.0


def _rpm_to_rads(rpm: float) -> str:
    """Return C# expression converting RPM to rad/s."""
    return f"{rpm} * 2 * Math.PI / 60"


class MotionStudyGenerator:
    """~250 pairs: motors, springs/dampers, forces, results, conceptual."""

    def generate_all(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        p.extend(self._motor_pairs())
        p.extend(self._spring_damper_pairs())
        p.extend(self._force_gravity_pairs())
        p.extend(self._results_pairs())
        p.extend(self._conceptual_pairs())
        return p

    # ------------------------------------------------------------------
    # 1. Motor Pairs (~60)
    # ------------------------------------------------------------------
    def _motor_pairs(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []

        # Access motion study manager
        p.append(("Access the motion study manager from the active document.", D("""\
            ModelDocExtension ext = modelDoc.Extension;
            MotionStudyManager motionMgr = (MotionStudyManager)ext.GetMotionStudyManager();
            if (motionMgr == null) { Debug.WriteLine("[FAIL] Motion study manager unavailable."); return; }""")))

        p.append(("Get a motion study by name and activate it.", D("""\
            MotionStudyManager motionMgr = (MotionStudyManager)modelDoc.Extension.GetMotionStudyManager();
            MotionStudy study = (MotionStudy)motionMgr.GetMotionStudy("Motion Study 1");
            if (study == null) { Debug.WriteLine("[FAIL] Motion study not found."); return; }
            study.Activate();""")))

        p.append(("List all motion studies in the active document.", D("""\
            MotionStudyManager motionMgr = (MotionStudyManager)modelDoc.Extension.GetMotionStudyManager();
            int count = motionMgr.GetMotionStudyCount();
            for (int i = 0; i < count; i++) {
                string name = motionMgr.GetMotionStudyName(i);
                Debug.WriteLine("[->] Motion Study: " + name); }""")))

        p.append(("Create a new motion study.", D("""\
            MotionStudyManager motionMgr = (MotionStudyManager)modelDoc.Extension.GetMotionStudyManager();
            MotionStudy study = (MotionStudy)motionMgr.CreateMotionStudy();
            if (study == null) { Debug.WriteLine("[FAIL] Could not create motion study."); return; }
            study.Activate();""")))

        # Study type settings
        for stype, desc, enum_val in [
            ("Animation", "keyframe animation (no physics)",
             "swMotionStudyType_e.swMotionStudyTypeAnimation"),
            ("Basic Motion", "basic motion with gravity, springs, contact, and motors",
             "swMotionStudyType_e.swMotionStudyTypeBasicMotion"),
            ("Motion Analysis", "full dynamic motion analysis with friction and forces",
             "swMotionStudyType_e.swMotionStudyTypeMotionAnalysis"),
        ]:
            p.append((f"Set the motion study type to {stype} for {desc}.", D(f"""\
                study.StudyType = (int){enum_val};
                Debug.WriteLine("[OK] Study type set to {stype}.");""")))

        # Rotary motors at various RPM values
        for rpm in [30, 60, 120, 300, 600, 900, 1200, 1800, 3600]:
            p.append((f"Add a rotary motor spinning at {rpm} RPM.", D(f"""\
                SimulationMotorFeatureData motorData =
                    (SimulationMotorFeatureData)study.CreateDefinition("Motor");
                motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
                motorData.Speed = {_rpm_to_rads(rpm)}; // {rpm} RPM in rad/s
                study.AddFeature(motorData);""")))

        # Linear motors at various velocities
        for vel_mm in [10, 25, 50, 100, 200, 500]:
            vel_m = _mm(vel_mm)
            p.append((f"Add a linear motor with constant velocity of {vel_mm} mm/s.", D(f"""\
                SimulationMotorFeatureData motorData =
                    (SimulationMotorFeatureData)study.CreateDefinition("Motor");
                motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeLinear;
                motorData.Speed = {vel_m}; // {vel_mm} mm/s in m/s
                study.AddFeature(motorData);""")))

        # Oscillating motor
        p.append(("Add an oscillating rotary motor with amplitude and frequency.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.MotionType = (int)swMotionStudyMotionType_e.swMotionTypeOscillating;
            motorData.Amplitude = 30 * Math.PI / 180; // 30 degrees in radians
            motorData.Frequency = 2.0; // 2 Hz
            study.AddFeature(motorData);""")))

        p.append(("Add an oscillating linear motor with 10mm amplitude at 5 Hz.", D(f"""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeLinear;
            motorData.MotionType = (int)swMotionStudyMotionType_e.swMotionTypeOscillating;
            motorData.Amplitude = {_mm(10)}; // 10 mm in meters
            motorData.Frequency = 5.0; // 5 Hz
            study.AddFeature(motorData);""")))

        # Function-driven motor
        p.append(("Add a rotary motor with interpolated speed profile from data points.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.MotionType = (int)swMotionStudyMotionType_e.swMotionTypeInterpolated;
            // Data points: time (s), speed (rad/s)
            double[] dataPoints = new double[] { 0, 0, 0.5, 10.47, 1.0, 31.42, 2.0, 31.42, 3.0, 0 };
            motorData.SetInterpolatedData(dataPoints);
            study.AddFeature(motorData);""")))

        p.append(("Add a motor with expression-driven speed profile.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.MotionType = (int)swMotionStudyMotionType_e.swMotionTypeExpression;
            motorData.Expression = "10.47 * sin(2 * PI * t)"; // Sinusoidal speed
            study.AddFeature(motorData);""")))

        # Motor direction and reference
        p.append(("Set the motor rotation direction to clockwise.", D("""\
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.Speed = 60 * 2 * Math.PI / 60; // 60 RPM
            motorData.ReverseDirection = true; // Clockwise when viewed from reference""")))

        p.append(("Set the motor reference axis to a cylindrical face.", D("""\
            modelDoc.Extension.SelectByID2("", "FACE", 0.01, 0.02, 0, false, 0, null, 0);
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.Speed = 120 * 2 * Math.PI / 60; // 120 RPM
            // Motor reference is set from current selection
            study.AddFeature(motorData);""")))

        p.append(("Set motor reference to an edge for linear motor direction.", D("""\
            modelDoc.Extension.SelectByID2("", "EDGE", 0.01, 0, 0, false, 0, null, 0);
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeLinear;
            motorData.Speed = 0.1; // 100 mm/s
            study.AddFeature(motorData);""")))

        # Motor torque limit
        p.append(("Set a torque limit on a rotary motor.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.Speed = 300 * 2 * Math.PI / 60; // 300 RPM
            motorData.TorqueLimit = 5.0; // 5 Nm maximum torque
            motorData.UseTorqueLimit = true;
            study.AddFeature(motorData);""")))

        p.append(("Set a force limit on a linear motor.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeLinear;
            motorData.Speed = 0.05; // 50 mm/s
            motorData.ForceLimit = 100.0; // 100 N maximum force
            motorData.UseForceLimit = true;
            study.AddFeature(motorData);""")))

        # Motor with ramp-up
        p.append(("Add a rotary motor with gradual ramp-up over 2 seconds.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.MotionType = (int)swMotionStudyMotionType_e.swMotionTypeInterpolated;
            double[] ramp = new double[] { 0, 0, 0.5, 15.71, 1.0, 31.42, 2.0, 62.83, 5.0, 62.83 };
            motorData.SetInterpolatedData(ramp); // Ramp from 0 to 600 RPM over 2s
            study.AddFeature(motorData);""")))

        # Motor on specific component
        p.append(("Apply a rotary motor to a specific component in an assembly.", D("""\
            modelDoc.Extension.SelectByID2("Gear1-1@Assembly", "COMPONENT", 0, 0, 0, false, 0, null, 0);
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.Speed = 1800 * 2 * Math.PI / 60; // 1800 RPM
            study.AddFeature(motorData);""")))

        # Delete a motor
        p.append(("Delete a motor from the motion study.", D("""\
            SimulationFeature motor = (SimulationFeature)study.GetFeature("Rotary Motor1");
            if (motor != null) { study.DeleteFeature(motor);
                Debug.WriteLine("[OK] Motor deleted."); }""")))

        # Edit existing motor
        p.append(("Edit an existing motor speed in the motion study.", D("""\
            SimulationFeature motor = (SimulationFeature)study.GetFeature("Rotary Motor1");
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)motor.GetDefinition();
            motorData.Speed = 900 * 2 * Math.PI / 60; // Change to 900 RPM
            motor.SetDefinition(motorData);""")))

        # Motor with step function
        p.append(("Add a motor with step function speed profile.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.MotionType = (int)swMotionStudyMotionType_e.swMotionTypeExpression;
            motorData.Expression = "STEP(time, 0, 0, 0.5, 62.83)"; // Step to 600 RPM over 0.5s
            study.AddFeature(motorData);""")))

        # Additional motor pairs for variety
        p.append(("Add a rotary motor driven by torque instead of speed.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.InputType = (int)swMotionStudyMotorInputType_e.swMotorInputTypeTorque;
            motorData.Torque = 2.5; // 2.5 Nm constant torque
            study.AddFeature(motorData);""")))

        p.append(("Add a linear motor driven by force instead of velocity.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeLinear;
            motorData.InputType = (int)swMotionStudyMotorInputType_e.swMotorInputTypeForce;
            motorData.Force = 50.0; // 50 N constant force
            study.AddFeature(motorData);""")))

        p.append(("Add a rotary motor with cosine speed profile.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.MotionType = (int)swMotionStudyMotionType_e.swMotionTypeExpression;
            motorData.Expression = "31.42 * (1 - cos(2 * PI * t / 2))"; // Smooth start 0-600 RPM
            study.AddFeature(motorData);""")))

        # Disable/enable motor
        p.append(("Suppress (disable) a motor in the motion study.", D("""\
            SimulationFeature motor = (SimulationFeature)study.GetFeature("Rotary Motor1");
            if (motor != null) motor.Suppressed = true;
            Debug.WriteLine("[OK] Motor suppressed.");""")))

        p.append(("Unsuppress (enable) a motor in the motion study.", D("""\
            SimulationFeature motor = (SimulationFeature)study.GetFeature("Rotary Motor1");
            if (motor != null) motor.Suppressed = false;
            Debug.WriteLine("[OK] Motor unsuppressed.");""")))

        # Additional rotary motor RPM pairs with specific applications
        for rpm, app in [
            (15, "slow conveyor belt"),
            (45, "turntable indexer"),
            (90, "mixing paddle"),
            (150, "centrifugal pump"),
            (450, "grinding wheel"),
            (750, "compressor shaft"),
            (2400, "router spindle"),
            (5000, "high-speed spindle"),
            (7200, "turbine rotor"),
            (10000, "dental drill spindle"),
        ]:
            p.append((f"Add a rotary motor at {rpm} RPM for a {app}.", D(f"""\
                SimulationMotorFeatureData motorData =
                    (SimulationMotorFeatureData)study.CreateDefinition("Motor");
                motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
                motorData.Speed = {_rpm_to_rads(rpm)}; // {rpm} RPM for {app}
                study.AddFeature(motorData);""")))

        # Additional linear motor velocities with applications
        for vel_mm, app in [
            (1, "precision actuator"),
            (5, "slow feed drive"),
            (75, "pneumatic cylinder"),
            (150, "hydraulic press ram"),
            (350, "conveyor belt"),
            (750, "high-speed pick-and-place"),
            (1000, "pneumatic slider"),
        ]:
            vel_m = _mm(vel_mm)
            p.append((f"Add a linear motor at {vel_mm} mm/s for a {app}.", D(f"""\
                SimulationMotorFeatureData motorData =
                    (SimulationMotorFeatureData)study.CreateDefinition("Motor");
                motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeLinear;
                motorData.Speed = {vel_m}; // {vel_mm} mm/s for {app}
                study.AddFeature(motorData);""")))

        # Motor with trapezoidal profile
        p.append(("Add a rotary motor with trapezoidal velocity profile.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.MotionType = (int)swMotionStudyMotionType_e.swMotionTypeInterpolated;
            // Trapezoidal: ramp up, constant, ramp down
            double[] trapezoid = new double[] {
                0, 0, 0.5, 62.83, 1.0, 62.83, 3.0, 62.83, 3.5, 0 };
            motorData.SetInterpolatedData(trapezoid); // 600 RPM plateau
            study.AddFeature(motorData);""")))

        # Motor with polynomial profile
        p.append(("Add a motor with polynomial (S-curve) speed profile.", D("""\
            SimulationMotorFeatureData motorData =
                (SimulationMotorFeatureData)study.CreateDefinition("Motor");
            motorData.MotorType = (int)swMotionStudyMotorType_e.swMotorTypeRotary;
            motorData.MotionType = (int)swMotionStudyMotionType_e.swMotionTypeExpression;
            // 5th order polynomial for smooth S-curve acceleration
            motorData.Expression = "62.83 * (10*pow(time/2,3) - 15*pow(time/2,4) + 6*pow(time/2,5))";
            study.AddFeature(motorData);""")))

        return p

    # ------------------------------------------------------------------
    # 2. Spring and Damper Pairs (~50)
    # ------------------------------------------------------------------
    def _spring_damper_pairs(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []

        # Linear springs at various stiffness values
        for stiffness in [100, 500, 1000, 5000, 10000, 50000, 100000]:
            p.append((f"Add a linear spring with stiffness {stiffness} N/m.", D(f"""\
                SimulationLinearSpringFeatureData springData =
                    (SimulationLinearSpringFeatureData)study.CreateDefinition("LinearSpring");
                springData.SpringConstant = {stiffness}; // {stiffness} N/m
                springData.FreeLength = {_mm(50)}; // 50 mm free length
                study.AddFeature(springData);""")))

        # Free length variations
        for fl_mm in [20, 30, 50, 75, 100]:
            fl_m = _mm(fl_mm)
            p.append((f"Add a linear spring with {fl_mm} mm free length.", D(f"""\
                SimulationLinearSpringFeatureData springData =
                    (SimulationLinearSpringFeatureData)study.CreateDefinition("LinearSpring");
                springData.SpringConstant = 1000; // 1000 N/m
                springData.FreeLength = {fl_m}; // {fl_mm} mm
                study.AddFeature(springData);""")))

        # Preload variations
        for preload in [0, 5, 10, 25, 50, 100]:
            p.append((f"Add a linear spring with {preload} N preload.", D(f"""\
                SimulationLinearSpringFeatureData springData =
                    (SimulationLinearSpringFeatureData)study.CreateDefinition("LinearSpring");
                springData.SpringConstant = 5000; // 5000 N/m
                springData.FreeLength = {_mm(50)}; // 50 mm
                springData.Preload = {preload}; // {preload} N preload
                study.AddFeature(springData);""")))

        # Full spring definition with all parameters
        p.append(("Add a linear spring between two selected points with full parameters.", D(f"""\
            modelDoc.Extension.SelectByID2("", "VERTEX", 0.01, 0.02, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("", "VERTEX", 0.01, 0.07, 0, true, 0, null, 0);
            SimulationLinearSpringFeatureData springData =
                (SimulationLinearSpringFeatureData)study.CreateDefinition("LinearSpring");
            springData.SpringConstant = 10000; // 10,000 N/m
            springData.FreeLength = {_mm(75)}; // 75 mm
            springData.Preload = 25; // 25 N preload
            springData.DampingConstant = 10; // 10 Ns/m
            study.AddFeature(springData);""")))

        # Torsional springs
        for stiffness in [0.1, 0.5, 1.0, 5.0, 10.0]:
            p.append((f"Add a torsional spring with stiffness {stiffness} Nm/rad.", D(f"""\
                SimulationTorsionalSpringFeatureData tSpringData =
                    (SimulationTorsionalSpringFeatureData)study.CreateDefinition("TorsionalSpring");
                tSpringData.SpringConstant = {stiffness}; // {stiffness} Nm/rad
                tSpringData.FreeAngle = 0; // Zero free angle (radians)
                study.AddFeature(tSpringData);""")))

        # Torsional spring with preload
        p.append(("Add a torsional spring with 0.5 Nm preload torque.", D("""\
            SimulationTorsionalSpringFeatureData tSpringData =
                (SimulationTorsionalSpringFeatureData)study.CreateDefinition("TorsionalSpring");
            tSpringData.SpringConstant = 2.0; // 2.0 Nm/rad
            tSpringData.FreeAngle = 0;
            tSpringData.Preload = 0.5; // 0.5 Nm preload torque
            study.AddFeature(tSpringData);""")))

        # Linear dampers
        for damping in [1, 5, 10, 50, 100, 500]:
            p.append((f"Add a linear damper with {damping} Ns/m damping coefficient.", D(f"""\
                SimulationLinearDamperFeatureData damperData =
                    (SimulationLinearDamperFeatureData)study.CreateDefinition("LinearDamper");
                damperData.DampingConstant = {damping}; // {damping} Ns/m
                study.AddFeature(damperData);""")))

        # Torsional dampers
        for damping in [0.01, 0.05, 0.1, 0.5, 1.0]:
            p.append((f"Add a torsional damper with {damping} Nms/rad damping.", D(f"""\
                SimulationTorsionalDamperFeatureData tDamperData =
                    (SimulationTorsionalDamperFeatureData)study.CreateDefinition("TorsionalDamper");
                tDamperData.DampingConstant = {damping}; // {damping} Nms/rad
                study.AddFeature(tDamperData);""")))

        # Spring-damper combination
        p.append(("Add a parallel spring-damper system between two points.", D(f"""\
            // Select two connection points
            modelDoc.Extension.SelectByID2("", "VERTEX", 0, 0.05, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("", "VERTEX", 0, 0.10, 0, true, 0, null, 0);
            // Add spring
            SimulationLinearSpringFeatureData springData =
                (SimulationLinearSpringFeatureData)study.CreateDefinition("LinearSpring");
            springData.SpringConstant = 5000; // 5000 N/m
            springData.FreeLength = {_mm(50)}; // 50 mm
            springData.DampingConstant = 50; // 50 Ns/m (built-in damping)
            study.AddFeature(springData);""")))

        p.append(("Add a spring-damper between two faces for shock absorber modeling.", D(f"""\
            modelDoc.Extension.SelectByID2("", "FACE", 0.01, 0.03, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("", "FACE", 0.01, 0.08, 0, true, 0, null, 0);
            SimulationLinearSpringFeatureData springData =
                (SimulationLinearSpringFeatureData)study.CreateDefinition("LinearSpring");
            springData.SpringConstant = 20000; // 20,000 N/m (suspension spring)
            springData.FreeLength = {_mm(100)}; // 100 mm
            springData.DampingConstant = 200; // 200 Ns/m (shock absorber)
            springData.Preload = 50; // 50 N preload
            study.AddFeature(springData);""")))

        # Natural frequency calculation
        p.append(("Calculate the natural frequency of a spring-mass system.", D("""\
            double k = 5000; // Spring constant (N/m)
            double m = 2.0;  // Mass (kg)
            double fn = (1.0 / (2 * Math.PI)) * Math.Sqrt(k / m);
            Debug.WriteLine("[OK] Natural frequency: " + fn.ToString("F2") + " Hz");
            Debug.WriteLine("[OK] Period: " + (1.0 / fn).ToString("F4") + " s");""")))

        p.append(("Calculate the damped natural frequency.", D("""\
            double k = 5000;  // Spring constant (N/m)
            double m = 2.0;   // Mass (kg)
            double c = 50;    // Damping coefficient (Ns/m)
            double wn = Math.Sqrt(k / m);           // Natural frequency (rad/s)
            double zeta = c / (2 * Math.Sqrt(k * m)); // Damping ratio
            double wd = wn * Math.Sqrt(1 - zeta * zeta); // Damped frequency (rad/s)
            double fd = wd / (2 * Math.PI);           // Damped frequency (Hz)
            Debug.WriteLine("[OK] Damping ratio: " + zeta.ToString("F3"));
            Debug.WriteLine("[OK] Damped frequency: " + fd.ToString("F2") + " Hz");""")))

        # Edit existing spring
        p.append(("Edit an existing spring stiffness in the motion study.", D("""\
            SimulationFeature spring = (SimulationFeature)study.GetFeature("Linear Spring1");
            SimulationLinearSpringFeatureData springData =
                (SimulationLinearSpringFeatureData)spring.GetDefinition();
            springData.SpringConstant = 15000; // Change to 15,000 N/m
            spring.SetDefinition(springData);""")))

        # Delete spring
        p.append(("Delete a spring from the motion study.", D("""\
            SimulationFeature spring = (SimulationFeature)study.GetFeature("Linear Spring1");
            if (spring != null) { study.DeleteFeature(spring);
                Debug.WriteLine("[OK] Spring deleted."); }""")))

        # Nonlinear spring
        p.append(("Add a spring with nonlinear stiffness using expression.", D("""\
            SimulationLinearSpringFeatureData springData =
                (SimulationLinearSpringFeatureData)study.CreateDefinition("LinearSpring");
            springData.NonlinearSpring = true;
            springData.SpringExpression = "5000 * x + 50000 * x^3"; // Hardening spring
            study.AddFeature(springData);""")))

        # Spring at specific component connection points
        p.append(("Connect a spring between two component vertices.", D(f"""\
            modelDoc.Extension.SelectByID2("Vertex@Part1-1", "VERTEX", 0, 0.05, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("Vertex@Part2-1", "VERTEX", 0, 0.10, 0, true, 0, null, 0);
            SimulationLinearSpringFeatureData springData =
                (SimulationLinearSpringFeatureData)study.CreateDefinition("LinearSpring");
            springData.SpringConstant = 8000; // 8000 N/m
            springData.FreeLength = {_mm(60)}; // 60 mm
            study.AddFeature(springData);""")))

        # Suppress spring
        p.append(("Suppress a spring in the motion study.", D("""\
            SimulationFeature spring = (SimulationFeature)study.GetFeature("Linear Spring1");
            if (spring != null) spring.Suppressed = true;
            Debug.WriteLine("[OK] Spring suppressed.");""")))

        # Torsional spring with damping
        p.append(("Add a torsional spring with built-in damping.", D("""\
            SimulationTorsionalSpringFeatureData tSpringData =
                (SimulationTorsionalSpringFeatureData)study.CreateDefinition("TorsionalSpring");
            tSpringData.SpringConstant = 3.0; // 3.0 Nm/rad
            tSpringData.DampingConstant = 0.1; // 0.1 Nms/rad
            tSpringData.FreeAngle = 0;
            study.AddFeature(tSpringData);""")))

        # Critical damping calculation
        p.append(("Calculate the critical damping coefficient for a system.", D("""\
            double k = 10000; // Spring constant (N/m)
            double m = 5.0;   // Mass (kg)
            double cCritical = 2 * Math.Sqrt(k * m); // Critical damping
            Debug.WriteLine("[OK] Critical damping: " + cCritical.ToString("F2") + " Ns/m");
            Debug.WriteLine("[OK] For underdamped: c < " + cCritical.ToString("F2"));
            Debug.WriteLine("[OK] For overdamped: c > " + cCritical.ToString("F2"));""")))

        return p

    # ------------------------------------------------------------------
    # 3. Force and Gravity Pairs (~40)
    # ------------------------------------------------------------------
    def _force_gravity_pairs(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []

        # Gravity in different directions
        p.append(("Enable gravity in the default -Y direction.", D("""\
            study.SetGravity(true, 0, -9.81, 0); // Y-down (default SolidWorks orientation)
            Debug.WriteLine("[OK] Gravity enabled: -Y direction.");""")))

        p.append(("Enable gravity in the -Z direction.", D("""\
            study.SetGravity(true, 0, 0, -9.81); // Z-down
            Debug.WriteLine("[OK] Gravity enabled: -Z direction.");""")))

        p.append(("Enable gravity in the -X direction.", D("""\
            study.SetGravity(true, -9.81, 0, 0); // X-down
            Debug.WriteLine("[OK] Gravity enabled: -X direction.");""")))

        p.append(("Set gravity at a custom angle of 30 degrees from vertical.", D("""\
            double angle = 30 * Math.PI / 180; // 30 degrees
            double gx = -9.81 * Math.Sin(angle);
            double gy = -9.81 * Math.Cos(angle);
            study.SetGravity(true, gx, gy, 0);
            Debug.WriteLine("[OK] Gravity at 30 deg from -Y axis.");""")))

        p.append(("Set gravity at 45 degrees in the XY plane.", D("""\
            double angle = 45 * Math.PI / 180;
            study.SetGravity(true, -9.81 * Math.Sin(angle), -9.81 * Math.Cos(angle), 0);""")))

        p.append(("Disable gravity in the motion study.", D("""\
            study.SetGravity(false, 0, 0, 0);
            Debug.WriteLine("[OK] Gravity disabled.");""")))

        p.append(("Set lunar gravity (1.625 m/s^2) in -Y direction.", D("""\
            study.SetGravity(true, 0, -1.625, 0); // Moon gravity
            Debug.WriteLine("[OK] Lunar gravity enabled.");""")))

        p.append(("Set Mars gravity (3.72 m/s^2) in -Y direction.", D("""\
            study.SetGravity(true, 0, -3.72, 0); // Mars gravity
            Debug.WriteLine("[OK] Mars gravity enabled.");""")))

        # Applied forces at specific values
        for force_n in [1, 5, 10, 25, 50, 100, 250, 500, 1000]:
            p.append((f"Apply a constant {force_n} N downward force at a point.", D(f"""\
                SimulationForceFeatureData forceData =
                    (SimulationForceFeatureData)study.CreateDefinition("Force");
                forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeConstant;
                forceData.X = 0; forceData.Y = 0; forceData.Z = -{force_n}; // {force_n} N in -Z
                study.AddFeature(forceData);""")))

        # Force in different directions
        p.append(("Apply a 50 N force in the X direction.", D("""\
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)study.CreateDefinition("Force");
            forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeConstant;
            forceData.X = 50; forceData.Y = 0; forceData.Z = 0;
            study.AddFeature(forceData);""")))

        p.append(("Apply an angled force of 100 N at 45 degrees in the XZ plane.", D("""\
            double angle = 45 * Math.PI / 180;
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)study.CreateDefinition("Force");
            forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeConstant;
            forceData.X = 100 * Math.Cos(angle); forceData.Y = 0;
            forceData.Z = -100 * Math.Sin(angle);
            study.AddFeature(forceData);""")))

        # Applied torques
        p.append(("Apply a constant torque of 5 Nm about the Y axis.", D("""\
            SimulationTorqueFeatureData torqueData =
                (SimulationTorqueFeatureData)study.CreateDefinition("Torque");
            torqueData.TorqueType = (int)swMotionStudyTorqueType_e.swTorqueTypeConstant;
            torqueData.X = 0; torqueData.Y = 5.0; torqueData.Z = 0; // 5 Nm about Y
            study.AddFeature(torqueData);""")))

        p.append(("Apply a 10 Nm torque about the Z axis.", D("""\
            SimulationTorqueFeatureData torqueData =
                (SimulationTorqueFeatureData)study.CreateDefinition("Torque");
            torqueData.TorqueType = (int)swMotionStudyTorqueType_e.swTorqueTypeConstant;
            torqueData.X = 0; torqueData.Y = 0; torqueData.Z = 10.0;
            study.AddFeature(torqueData);""")))

        p.append(("Apply a time-varying force using expression.", D("""\
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)study.CreateDefinition("Force");
            forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeExpression;
            forceData.ExpressionZ = "-50 * sin(2 * PI * 10 * time)"; // 50 N oscillating at 10 Hz
            study.AddFeature(forceData);""")))

        p.append(("Apply a step force that activates at t=1 second.", D("""\
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)study.CreateDefinition("Force");
            forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeExpression;
            forceData.ExpressionZ = "STEP(time, 1.0, 0, 1.01, -200)"; // 200 N step at t=1s
            study.AddFeature(forceData);""")))

        # Friction coefficients for contact sets
        for mat_pair, static_f, kinetic_f in [
            ("steel-on-steel", 0.74, 0.57),
            ("steel-on-aluminum", 0.61, 0.47),
            ("steel-on-bronze", 0.50, 0.40),
            ("steel-on-plastic", 0.40, 0.30),
        ]:
            p.append((f"Set contact friction coefficients for {mat_pair}.", D(f"""\
                SimulationContactFeatureData contactData =
                    (SimulationContactFeatureData)study.CreateDefinition("Contact");
                contactData.Friction = true;
                contactData.StaticFrictionCoefficient = {static_f}; // {mat_pair} static
                contactData.KineticFrictionCoefficient = {kinetic_f}; // {mat_pair} kinetic
                study.AddFeature(contactData);""")))

        # Custom friction
        p.append(("Set custom friction coefficients on a contact set.", D("""\
            SimulationContactFeatureData contactData =
                (SimulationContactFeatureData)study.CreateDefinition("Contact");
            contactData.Friction = true;
            contactData.StaticFrictionCoefficient = 0.35;
            contactData.KineticFrictionCoefficient = 0.25;
            contactData.StaticFrictionVelocity = 0.001; // Transition velocity (m/s)
            study.AddFeature(contactData);""")))

        # Restitution
        p.append(("Set restitution coefficient for bouncing contact.", D("""\
            SimulationContactFeatureData contactData =
                (SimulationContactFeatureData)study.CreateDefinition("Contact");
            contactData.RestitutionCoefficient = 0.8; // 80% energy return (bouncy)
            contactData.Friction = true;
            contactData.StaticFrictionCoefficient = 0.5;
            contactData.KineticFrictionCoefficient = 0.3;
            study.AddFeature(contactData);""")))

        p.append(("Set restitution coefficient to 0 for perfectly inelastic contact.", D("""\
            SimulationContactFeatureData contactData =
                (SimulationContactFeatureData)study.CreateDefinition("Contact");
            contactData.RestitutionCoefficient = 0; // No bounce (perfectly inelastic)
            study.AddFeature(contactData);""")))

        p.append(("Set restitution coefficient to 1 for perfectly elastic contact.", D("""\
            SimulationContactFeatureData contactData =
                (SimulationContactFeatureData)study.CreateDefinition("Contact");
            contactData.RestitutionCoefficient = 1.0; // Perfect bounce (perfectly elastic)
            study.AddFeature(contactData);""")))

        # Delete force
        p.append(("Delete a force from the motion study.", D("""\
            SimulationFeature force = (SimulationFeature)study.GetFeature("Force1");
            if (force != null) { study.DeleteFeature(force);
                Debug.WriteLine("[OK] Force deleted."); }""")))

        # Edit force
        p.append(("Edit an existing force magnitude.", D("""\
            SimulationFeature force = (SimulationFeature)study.GetFeature("Force1");
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)force.GetDefinition();
            forceData.Z = -500; // Change to 500 N downward
            force.SetDefinition(forceData);""")))

        # Force applied to a specific face
        p.append(("Apply a distributed force on a selected face.", D("""\
            modelDoc.Extension.SelectByID2("", "FACE", 0.02, 0.03, 0, false, 0, null, 0);
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)study.CreateDefinition("Force");
            forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeConstant;
            forceData.X = 0; forceData.Y = -200; forceData.Z = 0; // 200 N downward
            forceData.ActionOnly = true; // Force on this component only
            study.AddFeature(forceData);""")))

        # Action-reaction force
        p.append(("Apply an action-reaction force between two components.", D("""\
            modelDoc.Extension.SelectByID2("", "FACE", 0.01, 0.02, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("", "FACE", 0.05, 0.02, 0, true, 0, null, 0);
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)study.CreateDefinition("Force");
            forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeConstant;
            forceData.X = 0; forceData.Y = 0; forceData.Z = -150;
            forceData.ActionOnly = false; // Action-reaction pair
            study.AddFeature(forceData);""")))

        # Impulse force
        p.append(("Apply a short impulse force using expression.", D("""\
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)study.CreateDefinition("Force");
            forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeExpression;
            // 500 N impulse lasting 0.01 seconds centered at t=1s
            forceData.ExpressionZ = "-500 * exp(-pow((time-1)/0.005, 2))";
            study.AddFeature(forceData);""")))

        # Harmonic force
        p.append(("Apply a harmonic force for vibration testing.", D("""\
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)study.CreateDefinition("Force");
            forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeExpression;
            forceData.ExpressionY = "-100 * sin(2 * PI * 25 * time)"; // 100N at 25 Hz
            study.AddFeature(forceData);""")))

        # Ramp force
        p.append(("Apply a linearly increasing ramp force.", D("""\
            SimulationForceFeatureData forceData =
                (SimulationForceFeatureData)study.CreateDefinition("Force");
            forceData.ForceType = (int)swMotionStudyForceType_e.swForceTypeExpression;
            forceData.ExpressionZ = "-50 * time"; // Increases 50 N/s
            study.AddFeature(forceData);""")))

        # Contact with stiffness
        p.append(("Set contact stiffness and damping for more accurate collision.", D("""\
            SimulationContactFeatureData contactData =
                (SimulationContactFeatureData)study.CreateDefinition("Contact");
            contactData.ContactStiffness = 1e6; // 1,000,000 N/m contact stiffness
            contactData.ContactDamping = 100; // 100 Ns/m contact damping
            contactData.RestitutionCoefficient = 0.6;
            study.AddFeature(contactData);""")))

        # Contact between specific components
        p.append(("Add contact between two specific components.", D("""\
            modelDoc.Extension.SelectByID2("Part1-1@Assembly", "COMPONENT", 0, 0, 0, false, 0, null, 0);
            modelDoc.Extension.SelectByID2("Part2-1@Assembly", "COMPONENT", 0, 0, 0, true, 0, null, 0);
            SimulationContactFeatureData contactData =
                (SimulationContactFeatureData)study.CreateDefinition("Contact");
            contactData.Friction = true;
            contactData.StaticFrictionCoefficient = 0.5;
            contactData.KineticFrictionCoefficient = 0.3;
            study.AddFeature(contactData);""")))

        # Suppress/unsuppress force
        p.append(("Suppress a force in the motion study.", D("""\
            SimulationFeature force = (SimulationFeature)study.GetFeature("Force1");
            if (force != null) force.Suppressed = true;
            Debug.WriteLine("[OK] Force suppressed.");""")))

        return p

    # ------------------------------------------------------------------
    # 4. Motion Results Pairs (~40)
    # ------------------------------------------------------------------
    def _results_pairs(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []

        # Run simulation
        p.append(("Run the motion study simulation.", D("""\
            study.Run();
            Debug.WriteLine("[OK] Motion study simulation complete.");""")))

        # Duration settings
        for duration in [1, 2, 5, 10, 30]:
            p.append((f"Run the motion study for {duration} seconds.", D(f"""\
                study.SetDuration(
                    (int)swMotionStudyDurationType_e.swMotionStudyDurationTypeTime, {duration}.0);
                study.Run();
                Debug.WriteLine("[OK] Simulation complete ({duration}s duration).");""")))

        p.append(("Set the motion study duration by number of frames.", D("""\
            study.SetDuration(
                (int)swMotionStudyDurationType_e.swMotionStudyDurationTypeFrames, 300);
            study.Run();""")))

        # Frame rate settings
        for fps in [15, 24, 30, 60]:
            p.append((f"Set the motion study frame rate to {fps} fps.", D(f"""\
                study.FrameRate = {fps}; // {fps} frames per second
                Debug.WriteLine("[OK] Frame rate set to {fps} fps.");""")))

        # Get results
        p.append(("Get displacement results from a motion study.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] displacements = (double[])results.GetDisplacement(component, 0); // X direction
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  x=" +
                    (displacements[i] * 1000).ToString("F2") + " mm");""")))

        p.append(("Get velocity results from a motion study.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] velocities = (double[])results.GetVelocity(component, 0); // X velocity
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  vx=" +
                    (velocities[i] * 1000).ToString("F2") + " mm/s");""")))

        p.append(("Get acceleration results from a motion study.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] accelerations = (double[])results.GetAcceleration(component, 0); // X accel
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  ax=" +
                    accelerations[i].ToString("F3") + " m/s^2");""")))

        # All three axes
        p.append(("Get displacement in all three axes (X, Y, Z).", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] dx = (double[])results.GetDisplacement(component, 0); // X
            double[] dy = (double[])results.GetDisplacement(component, 1); // Y
            double[] dz = (double[])results.GetDisplacement(component, 2); // Z
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  (" +
                    (dx[i]*1000).ToString("F2") + ", " +
                    (dy[i]*1000).ToString("F2") + ", " +
                    (dz[i]*1000).ToString("F2") + ") mm");""")))

        p.append(("Get angular velocity results from a motion study.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] angVel = (double[])results.GetAngularVelocity(component, 2); // About Z axis
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  omega=" +
                    (angVel[i] * 60 / (2 * Math.PI)).ToString("F1") + " RPM");""")))

        p.append(("Get angular displacement (rotation) results.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] angDisp = (double[])results.GetAngularDisplacement(component, 2); // About Z
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  theta=" +
                    (angDisp[i] * 180 / Math.PI).ToString("F1") + " deg");""")))

        # Export results to CSV
        p.append(("Export motion study results to a CSV file.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] dx = (double[])results.GetDisplacement(component, 0);
            double[] vx = (double[])results.GetVelocity(component, 0);
            using (var sw = new System.IO.StreamWriter(@"C:\\Output\\results.csv")) {
                sw.WriteLine("Time(s),Displacement_X(mm),Velocity_X(mm/s)");
                for (int i = 0; i < times.Length; i++)
                    sw.WriteLine(times[i] + "," + (dx[i]*1000) + "," + (vx[i]*1000)); }
            Debug.WriteLine("[OK] Results exported to CSV.");""")))

        p.append(("Export all motion results for multiple components to CSV.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            using (var sw = new System.IO.StreamWriter(@"C:\\Output\\multi_results.csv")) {
                sw.WriteLine("Time(s),Comp1_X(mm),Comp1_Y(mm),Comp2_X(mm),Comp2_Y(mm)");
                double[] c1x = (double[])results.GetDisplacement(comp1, 0);
                double[] c1y = (double[])results.GetDisplacement(comp1, 1);
                double[] c2x = (double[])results.GetDisplacement(comp2, 0);
                double[] c2y = (double[])results.GetDisplacement(comp2, 1);
                for (int i = 0; i < times.Length; i++)
                    sw.WriteLine(times[i]+","+(c1x[i]*1000)+","+(c1y[i]*1000)+","
                        +(c2x[i]*1000)+","+(c2y[i]*1000)); }""")))

        # Save animation to AVI
        for fps, w, h in [(30, 640, 480), (30, 1280, 720), (60, 1920, 1080)]:
            res_label = f"{w}x{h}"
            p.append((f"Save motion study animation as AVI at {res_label} {fps} fps.", D(f"""\
                study.SaveToAVI(@"C:\\Output\\animation.avi", {fps}, {w}, {h});
                Debug.WriteLine("[OK] Animation saved at {res_label}, {fps} fps.");""")))

        # Trace path
        p.append(("Trace the path of a point during the motion study.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] px = (double[])results.GetDisplacement(component, 0);
            double[] py = (double[])results.GetDisplacement(component, 1);
            double[] pz = (double[])results.GetDisplacement(component, 2);
            // Create 3D sketch of trace path
            modelDoc.SketchManager.Insert3DSketch(true);
            for (int i = 0; i < times.Length - 1; i++)
                modelDoc.SketchManager.CreateLine(px[i],py[i],pz[i], px[i+1],py[i+1],pz[i+1]);
            modelDoc.SketchManager.Insert3DSketch(true);
            Debug.WriteLine("[OK] Trace path created with " + times.Length + " points.");""")))

        # Reaction forces at mates
        p.append(("Get reaction forces at a mate from the motion study.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] rfx = (double[])results.GetMateReactionForce(mate, 0); // X component
            double[] rfy = (double[])results.GetMateReactionForce(mate, 1); // Y component
            double[] rfz = (double[])results.GetMateReactionForce(mate, 2); // Z component
            for (int i = 0; i < times.Length; i++) {
                double mag = Math.Sqrt(rfx[i]*rfx[i] + rfy[i]*rfy[i] + rfz[i]*rfz[i]);
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  F=" +
                    mag.ToString("F2") + " N"); }""")))

        p.append(("Get reaction torques at a mate.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] rtx = (double[])results.GetMateReactionTorque(mate, 0);
            double[] rty = (double[])results.GetMateReactionTorque(mate, 1);
            double[] rtz = (double[])results.GetMateReactionTorque(mate, 2);
            for (int i = 0; i < times.Length; i++) {
                double mag = Math.Sqrt(rtx[i]*rtx[i] + rty[i]*rty[i] + rtz[i]*rtz[i]);
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  T=" +
                    mag.ToString("F2") + " Nm"); }""")))

        # Plot generation
        p.append(("Generate a displacement vs time plot data set.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] disp = (double[])results.GetDisplacement(component, 1); // Y displacement
            Debug.WriteLine("[PLOT] Displacement vs Time");
            Debug.WriteLine("[PLOT] X-axis: Time (s), Y-axis: Displacement (mm)");
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[DATA] " + times[i] + "," + (disp[i] * 1000));""")))

        p.append(("Generate a velocity vs time plot data set.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] vel = (double[])results.GetVelocity(component, 1); // Y velocity
            Debug.WriteLine("[PLOT] Velocity vs Time");
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[DATA] " + times[i] + "," + (vel[i] * 1000));""")))

        p.append(("Generate kinetic energy vs time data.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] ke = (double[])results.GetKineticEnergy(component);
            Debug.WriteLine("[PLOT] Kinetic Energy vs Time");
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[DATA] " + times[i] + "," + ke[i] + " J");""")))

        # Stop/reset simulation
        p.append(("Stop a running motion study simulation.", D("""\
            study.Stop();
            Debug.WriteLine("[OK] Simulation stopped.");""")))

        p.append(("Reset the motion study to time zero.", D("""\
            study.Reset();
            Debug.WriteLine("[OK] Motion study reset to t=0.");""")))

        # Set playback speed
        p.append(("Set the motion study playback speed.", D("""\
            study.PlaybackSpeed = 0.5; // Half speed playback
            Debug.WriteLine("[OK] Playback speed set to 0.5x.");""")))

        p.append(("Set the motion study playback to 2x speed.", D("""\
            study.PlaybackSpeed = 2.0; // Double speed playback
            Debug.WriteLine("[OK] Playback speed set to 2x.");""")))

        # Time step control
        p.append(("Set the maximum time step for simulation accuracy.", D("""\
            study.MaxTimeStep = 0.001; // 1 ms maximum time step
            Debug.WriteLine("[OK] Max time step set to 1 ms for higher accuracy.");""")))

        p.append(("Set the simulation time step to automatic.", D("""\
            study.AutomaticTimeStep = true;
            Debug.WriteLine("[OK] Automatic time stepping enabled.");""")))

        # Get motor power/torque results
        p.append(("Get motor power consumption over time.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] power = (double[])results.GetMotorPower(motor);
            double maxPower = 0;
            for (int i = 0; i < times.Length; i++) {
                if (Math.Abs(power[i]) > maxPower) maxPower = Math.Abs(power[i]);
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  P=" +
                    power[i].ToString("F2") + " W"); }
            Debug.WriteLine("[OK] Peak power: " + maxPower.ToString("F2") + " W");""")))

        p.append(("Get motor torque over time.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] torque = (double[])results.GetMotorTorque(motor);
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  T=" +
                    torque[i].ToString("F3") + " Nm");""")))

        # Spring force results
        p.append(("Get spring force over time from a motion study.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] springForce = (double[])results.GetSpringForce(spring);
            double maxForce = 0;
            for (int i = 0; i < times.Length; i++) {
                if (Math.Abs(springForce[i]) > maxForce) maxForce = Math.Abs(springForce[i]);
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  F=" +
                    springForce[i].ToString("F2") + " N"); }
            Debug.WriteLine("[OK] Peak spring force: " + maxForce.ToString("F2") + " N");""")))

        # Damper force results
        p.append(("Get damper force over time from a motion study.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] damperForce = (double[])results.GetDamperForce(damper);
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  F=" +
                    damperForce[i].ToString("F2") + " N");""")))

        # Contact force results
        p.append(("Get contact force magnitude over time.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] contactForce = (double[])results.GetContactForce(contact);
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[->] t=" + times[i].ToString("F3") + "s  Fc=" +
                    contactForce[i].ToString("F2") + " N");""")))

        # Potential energy
        p.append(("Get potential energy over time.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] pe = (double[])results.GetPotentialEnergy(component);
            for (int i = 0; i < times.Length; i++)
                Debug.WriteLine("[DATA] " + times[i] + "," + pe[i] + " J");""")))

        # Total energy balance
        p.append(("Calculate total energy (kinetic + potential) over time.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] ke = (double[])results.GetKineticEnergy(component);
            double[] pe = (double[])results.GetPotentialEnergy(component);
            Debug.WriteLine("[PLOT] Total Energy vs Time");
            for (int i = 0; i < times.Length; i++) {
                double total = ke[i] + pe[i];
                Debug.WriteLine("[DATA] " + times[i] + "," + total + " J"); }""")))

        # Save results at specific time
        p.append(("Get all results at a specific time step.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double targetTime = 2.5; // Get results at t=2.5s
            double[] dx = (double[])results.GetDisplacement(component, 0);
            double[] vx = (double[])results.GetVelocity(component, 0);
            double[] ax = (double[])results.GetAcceleration(component, 0);
            double[] times = (double[])results.GetTimeValues();
            // Find nearest time index
            int idx = 0; double minDiff = double.MaxValue;
            for (int i = 0; i < times.Length; i++)
                if (Math.Abs(times[i] - targetTime) < minDiff)
                    { minDiff = Math.Abs(times[i] - targetTime); idx = i; }
            Debug.WriteLine("[OK] At t=" + times[idx].ToString("F3") + "s:");
            Debug.WriteLine("  Displacement: " + (dx[idx]*1000).ToString("F3") + " mm");
            Debug.WriteLine("  Velocity: " + (vx[idx]*1000).ToString("F3") + " mm/s");
            Debug.WriteLine("  Acceleration: " + ax[idx].ToString("F3") + " m/s^2");""")))

        # Maximum values
        p.append(("Find the peak velocity during the simulation.", D("""\
            MotionStudyResults results = (MotionStudyResults)study.GetResults();
            double[] times = (double[])results.GetTimeValues();
            double[] vx = (double[])results.GetVelocity(component, 0);
            double[] vy = (double[])results.GetVelocity(component, 1);
            double[] vz = (double[])results.GetVelocity(component, 2);
            double maxSpeed = 0; double maxTime = 0;
            for (int i = 0; i < times.Length; i++) {
                double speed = Math.Sqrt(vx[i]*vx[i] + vy[i]*vy[i] + vz[i]*vz[i]);
                if (speed > maxSpeed) { maxSpeed = speed; maxTime = times[i]; } }
            Debug.WriteLine("[OK] Peak speed: " + (maxSpeed*1000).ToString("F2") +
                " mm/s at t=" + maxTime.ToString("F3") + "s");""")))

        # Save animation as images
        p.append(("Save each frame of the motion study as an image.", D("""\
            double[] times = (double[])((MotionStudyResults)study.GetResults()).GetTimeValues();
            for (int i = 0; i < times.Length; i++) {
                study.SetTime(times[i]);
                modelDoc.Extension.SaveAs2(@"C:\\Output\\frame_" + i.ToString("D4") + ".png",
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                    (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null, "", false,
                    ref err, ref warn); }
            Debug.WriteLine("[OK] Saved " + times.Length + " frames.");""")))

        return p

    # ------------------------------------------------------------------
    # 5. Motion Study Conceptual Pairs (~30)
    # ------------------------------------------------------------------
    def _conceptual_pairs(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []

        p.append(("Explain the difference between Animation, Basic Motion, and Motion Analysis.",
            "Animation: keyframe-based, no physics -- used for presentations and walkthroughs. "
            "Basic Motion: includes gravity, springs, contact, and motors but no friction -- good "
            "for quick mechanism checks. Motion Analysis: full dynamics with friction, forces, "
            "dampers, and accurate contact -- requires SolidWorks Motion add-in (Simulation)."))

        p.append(("When should I use Animation mode?",
            "Use Animation for visual presentations, assembly/disassembly sequences, camera "
            "flyovers, and exploded view animations. No physics calculated. Components move "
            "along keyframed paths. Fastest to set up, lightest on resources."))

        p.append(("When should I use Basic Motion?",
            "Use Basic Motion for quick mechanism verification: gear trains, linkages, cam "
            "followers. Includes gravity, springs, contact (no friction), and motors. Does not "
            "require Motion add-in. Suitable for kinematic analysis of mechanisms."))

        p.append(("When should I use Motion Analysis?",
            "Use Motion Analysis for accurate dynamic simulation: calculating reaction forces, "
            "motor power requirements, vibration analysis, contact with friction. Required for "
            "force/torque results at mates, damper behavior, and accurate collision response. "
            "Requires SolidWorks Motion (Simulation package)."))

        p.append(("Explain how to interpret motion study displacement results.",
            "Displacement results show position change from t=0 in meters (API units). Positive "
            "values follow the positive axis direction. Plot displacement vs time to identify: "
            "linear motion (straight line), oscillation (sinusoidal), or runaway (exponential). "
            "Convert to mm by multiplying by 1000."))

        p.append(("Explain how to interpret motion study velocity results.",
            "Velocity results are in m/s. Constant velocity = no net force (Newton's 1st law). "
            "Velocity slope = acceleration. Sudden velocity changes indicate impacts or motor "
            "steps. Check if velocity magnitude matches expected motor speeds."))

        p.append(("Explain how to interpret motion study acceleration results.",
            "Acceleration results are in m/s^2. Constant accel = constant net force (F=ma). "
            "Spikes indicate impacts or sudden load changes. Use acceleration to calculate "
            "forces on components: F = mass * acceleration. High frequency noise may indicate "
            "numerical issues -- reduce time step."))

        p.append(("What are tips for optimizing motion study performance?",
            "Performance tips: (1) Use Basic Motion instead of Motion Analysis when possible. "
            "(2) Reduce number of contact pairs. (3) Increase time step if accuracy allows. "
            "(4) Suppress cosmetic features. (5) Use simplified representations. "
            "(6) Reduce simulation duration. (7) Disable unnecessary result output."))

        p.append(("Explain natural frequency and resonance in motion studies.",
            "Natural frequency fn = (1/2pi)*sqrt(k/m) where k=stiffness, m=mass. Resonance "
            "occurs when excitation frequency equals natural frequency, causing large amplitude "
            "oscillations. In motion studies, watch for growing oscillations. Avoid motor "
            "speeds near natural frequency. Add damping to reduce resonance amplitude."))

        p.append(("Explain underdamped, critically damped, and overdamped systems.",
            "Damping ratio zeta = c / (2*sqrt(k*m)). Underdamped (zeta<1): oscillates with "
            "decaying amplitude -- most mechanical systems. Critically damped (zeta=1): fastest "
            "return to equilibrium without oscillation -- ideal for shock absorbers. Overdamped "
            "(zeta>1): slow return without oscillation -- sluggish response."))

        p.append(("Explain energy conservation in motion studies.",
            "Total energy = kinetic + potential + dissipated. Kinetic: (1/2)mv^2 + (1/2)Iw^2. "
            "Potential: mgh (gravity) + (1/2)kx^2 (springs). Dissipated: friction and damping. "
            "Energy should be conserved (minus dissipation). Growing total energy indicates "
            "numerical instability -- reduce time step."))

        p.append(("Motion study vs FEA: when to use each?",
            "Motion study: rigid body dynamics, mechanism motion, motor sizing, reaction forces "
            "at joints. FEA (Simulation): stress/strain in flexible bodies, deformation under "
            "load, fatigue, thermal. Use motion study first to get reaction forces, then apply "
            "those as FEA loads for structural analysis."))

        p.append(("What are common motion study errors and solutions?",
            "Common errors: (1) Redundant constraints -- remove over-constraining mates. "
            "(2) Inconsistent initial conditions -- ensure components start in valid positions. "
            "(3) Simulation fails to converge -- reduce time step, simplify contacts. "
            "(4) Unexpected results -- check units (API uses meters, rad/s, N). "
            "(5) Motor not moving -- verify reference selection and direction."))

        p.append(("Explain kinematic vs dynamic analysis.",
            "Kinematic analysis: studies motion without considering forces. Determines positions, "
            "velocities, and accelerations from constraints and input motions. Dynamic analysis: "
            "includes forces (F=ma), torques, gravity, friction. Kinematics answers 'where does "
            "it go?'; dynamics answers 'what forces are needed?'"))

        p.append(("Explain degrees of freedom in mechanisms.",
            "DOF = 3*(n-1) - 2*j1 - j2 (Gruebler's equation for planar mechanisms). n=number "
            "of links, j1=full joints (pin, slider), j2=half joints (rolling). A mechanism "
            "needs DOF=1 for constrained motion. DOF=0 is a structure. DOF>1 needs multiple "
            "inputs. Each SolidWorks mate reduces DOF."))

        p.append(("Explain four-bar linkage analysis in motion studies.",
            "Four-bar linkage: ground link, input (crank), coupler, output (rocker/crank). "
            "Grashof condition: s+l <= p+q (s=shortest, l=longest). If met, shortest link "
            "can fully rotate. In SolidWorks: model as assembly with revolute mates. Add "
            "rotary motor on input link. Analyze coupler curves and output motion."))

        p.append(("Explain cam and follower motion profiles.",
            "Common profiles: (1) Constant velocity: uniform motion, infinite acceleration at "
            "start/end. (2) Simple harmonic: s = h*(1-cos(pi*theta/beta))/2, smooth but non-zero "
            "acceleration at ends. (3) Cycloidal: s = h*(theta/beta - sin(2*pi*theta/beta)/(2*pi)), "
            "zero acceleration at start/end -- best for high-speed cams."))

        p.append(("Explain the relationship between motor torque and angular acceleration.",
            "Newton's second law for rotation: T = I*alpha, where T=torque (Nm), I=moment of "
            "inertia (kg*m^2), alpha=angular acceleration (rad/s^2). In motion studies, "
            "if a motor has constant speed, the motor torque equals the load torque. "
            "During acceleration, motor torque = load torque + I*alpha."))

        p.append(("Explain how to size a motor using motion study results.",
            "From motion study: (1) Get peak torque from motor torque results. "
            "(2) Get peak speed from angular velocity results. (3) Calculate peak power: "
            "P = T*omega. (4) Apply safety factor (typically 1.5-2.0). (5) Select motor with "
            "rated torque >= peak*SF and rated speed >= max speed. Check duty cycle."))

        p.append(("Explain contact in motion studies.",
            "Contact detects collisions between components. Types: (1) Solid bodies -- prevents "
            "interpenetration. (2) Curves -- contact along edges. Contact parameters: friction "
            "(static/kinetic), restitution (0=inelastic, 1=elastic), stiffness. More contact "
            "pairs = slower simulation. Use selectively on interacting parts only."))

        p.append(("Explain how spring preload works in motion studies.",
            "Preload = initial force in spring at free length. Positive preload means the spring "
            "pushes at its nominal position. Force = k*(x - freeLength) + preload. In "
            "compression springs, preload ensures contact is maintained. In motion studies, "
            "preload shifts the equilibrium position: x_eq = -preload/k from free length."))

        p.append(("Explain how to model a pendulum in a motion study.",
            "Model: (1) Create arm + mass as part. (2) In assembly, add revolute mate at pivot. "
            "(3) Set study type to Basic Motion or Motion Analysis. (4) Enable gravity (-Y). "
            "(5) Position at initial angle. (6) Run. Period = 2*pi*sqrt(L/g) for small angles. "
            "Add damping to model air resistance."))

        p.append(("Explain how to model a slider-crank mechanism.",
            "Components: crank (rotates), connecting rod, slider (translates). Mates: "
            "(1) Revolute at crank pivot. (2) Revolute at crank-rod and rod-slider joints. "
            "(3) Slot or coincident+parallel for slider. Add rotary motor on crank. "
            "Analyze slider displacement, velocity, and acceleration vs crank angle."))

        p.append(("Explain how to model a gear train in a motion study.",
            "Use gear mates to enforce speed ratios. Gear ratio = N2/N1 = omega1/omega2. "
            "API: AddMate5 with swMateGEAR. Set ratio parameter. Add rotary motor on input "
            "gear. For compound trains, multiply individual ratios. Check for interference "
            "between gear teeth using contact."))

        p.append(("Explain vibration isolation using springs and dampers.",
            "Transmissibility T = sqrt(1+(2*zeta*r)^2) / sqrt((1-r^2)^2+(2*zeta*r)^2) where "
            "r = excitation_freq/natural_freq. For isolation (T<1), need r > sqrt(2) = 1.414. "
            "Design spring stiffness so natural frequency is below 0.707 * excitation frequency. "
            "Add damping to control resonance passage."))

        p.append(("Explain how to validate motion study results.",
            "Validation steps: (1) Check energy balance -- total energy should be conserved "
            "(minus dissipation). (2) Compare with analytical solutions for simple cases. "
            "(3) Verify conservation of momentum. (4) Check that reaction forces match "
            "free-body diagram expectations. (5) Refine time step until results converge."))

        p.append(("Explain how to export motion loads for FEA analysis.",
            "Workflow: (1) Run motion study to completion. (2) Identify critical time step "
            "(max force/acceleration). (3) Export reaction forces at mates for that time step. "
            "(4) In SolidWorks Simulation, import as external loads. (5) Run static or "
            "fatigue FEA. Alternatively, use Motion-to-FEA transfer built into Simulation."))

        p.append(("Explain how to set up a drop test in motion study.",
            "Setup: (1) Position component above ground plane. (2) Set Motion Analysis type. "
            "(3) Enable gravity. (4) Add contact between component and ground. "
            "(5) Set restitution (0.3 typical for steel-on-steel drop). (6) Set short duration "
            "(0.5-1s). (7) Use small time step for impact accuracy. Analyze peak deceleration."))

        p.append(("Explain the difference between displacement and trace path results.",
            "Displacement: change in position relative to initial position, given as X/Y/Z "
            "components at each time step -- numerical data. Trace path: the actual path a "
            "point follows through space -- geometric curve. Displacement is for analysis; "
            "trace path is for visualization and mechanism design (coupler curves)."))

        p.append(("Explain how to handle large assemblies in motion studies.",
            "Tips for large assemblies: (1) Suppress non-essential components. (2) Use "
            "simplified representations. (3) Reduce contact pairs to essential interactions. "
            "(4) Use larger time steps where acceptable. (5) Disable result types not needed. "
            "(6) Consider sub-assembly motion studies for isolated mechanisms."))

        return p
