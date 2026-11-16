// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Security.Cryptography;
using System.Threading;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public sealed partial class P04Readback
{
    static readonly string[] WitnessAxes = { "width", "height", "depth" };

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr OpenJobObject(uint access, bool inherit, string name);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool IsProcessInJob(IntPtr process, IntPtr job, out bool member);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool CloseHandle(IntPtr handle);

    [DllImport("ole32.dll", ExactSpelling = true)]
    static extern int GetRunningObjectTable(int reserved, out IRunningObjectTable table);

    [DllImport("ole32.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    static extern int CreateItemMoniker(string separator, string item, out IMoniker moniker);

    static Dictionary<string, object> WitnessObject(object value)
    {
        var result = value as Dictionary<string, object>;
        Require(result != null, "Expected a witness metadata object");
        return result;
    }

    static string WitnessDigest(string path)
    {
        using (var input = File.OpenRead(path))
        using (var hash = SHA256.Create())
            return BitConverter.ToString(hash.ComputeHash(input)).Replace("-", "").ToLowerInvariant();
    }

    static long WitnessTime(object value)
    {
        return Convert.ToInt64(value, CultureInfo.InvariantCulture);
    }

    static long WitnessCreation(Process process)
    {
        return process.StartTime.ToUniversalTime().ToFileTimeUtc();
    }

    static void VerifyWitnessPeer(Process process, Dictionary<string, object> launch, string executable)
    {
        Require(!process.HasExited && process.Id == (int)launch["pid"]
            && WitnessCreation(process) == WitnessTime(launch["created"])
            && process.SessionId == (int)launch["session"]
            && String.Equals(ResolveExecutablePath(process.MainModule.FileName),
                ResolveExecutablePath(executable), StringComparison.OrdinalIgnoreCase),
            "The held SOLIDWORKS identity changed");
        var job = OpenJobObject(4, false, (string)launch["job"]);
        if (job == IntPtr.Zero) throw new Win32Exception();
        try
        {
            bool member;
            if (!IsProcessInJob(process.Handle, job, out member)) throw new Win32Exception();
            Require(member && !process.HasExited, "SOLIDWORKS is outside the exact launch job");
        }
        finally
        {
            CloseHandle(job);
        }
    }

    static object FindWitnessPeer(int pid)
    {
        IRunningObjectTable table = null;
        IMoniker moniker = null;
        try
        {
            Marshal.ThrowExceptionForHR(GetRunningObjectTable(0, out table));
            var item = "SolidWorks_PID_" + pid.ToString(CultureInfo.InvariantCulture);
            Marshal.ThrowExceptionForHR(CreateItemMoniker(null, item, out moniker));
            object found;
            Marshal.ThrowExceptionForHR(table.GetObject(moniker, out found));
            return found;
        }
        finally
        {
            if (moniker != null) Marshal.ReleaseComObject(moniker);
            if (table != null) Marshal.ReleaseComObject(table);
        }
    }

    static ISldWorks AttachWitness(Process process, Dictionary<string, object> launch, string executable)
    {
        var clock = Stopwatch.StartNew();
        while (clock.Elapsed.TotalSeconds < 60)
        {
            VerifyWitnessPeer(process, launch, executable);
            object active = null;
            try
            {
                try { active = Marshal.GetActiveObject("SldWorks.Application"); }
                catch (COMException error)
                {
                    if (error.ErrorCode != unchecked((int)0x800401E3)) throw;
                    active = FindWitnessPeer(process.Id);
                }
                var application = active as ISldWorks;
                if (application != null)
                {
                    Require(application.GetProcessID() == process.Id, "COM returned another SOLIDWORKS process");
                    VerifyWitnessPeer(process, launch, executable);
                    active = null;
                    return application;
                }
            }
            catch (COMException error)
            {
                if (error.ErrorCode != unchecked((int)0x800401E3)
                    && error.ErrorCode != unchecked((int)0x80010001)) throw;
            }
            finally
            {
                if (active != null) Marshal.ReleaseComObject(active);
            }
            Thread.Sleep(200);
        }
        throw new InvalidOperationException("The held SOLIDWORKS process did not register for passive COM");
    }

    static double[] WitnessPoint(object coordinates)
    {
        var point = Items(coordinates).Select(value => Convert.ToDouble(value, CultureInfo.InvariantCulture)).ToArray();
        Require(point.Length == 3 && point.All(value => !Double.IsNaN(value) && !Double.IsInfinity(value)),
            "Expected three finite world coordinates");
        return point;
    }

    static bool IsWitnessPoint(double[] first, double[] second)
    {
        return first.Zip(second, (left, right) => Math.Abs(left - right) <= 1e-10).All(same => same);
    }

    double[][] WitnessCorners(ISketch sketch, Dictionary<string, object> shape)
    {
        var edges = (Dictionary<string, object>[])PrincipalPerimeter(sketch);
        var expected = Items(shape["corners_m"]).Select(WitnessPoint).ToArray();
        Require(expected.Length == 4, "Expected four ordered planned corners");
        var ordered = new double[4][];
        var used = new HashSet<int>();
        for (int index = 0; index < expected.Length; index++)
        {
            var current = expected[index];
            var next = expected[(index + 1) % expected.Length];
            var matches = new List<KeyValuePair<int, double[]>>();
            for (int edge = 0; edge < edges.Length; edge++)
            {
                var start = (double[])edges[edge]["start_world_m"];
                var end = (double[])edges[edge]["end_world_m"];
                if (IsWitnessPoint(start, current) && IsWitnessPoint(end, next))
                    matches.Add(new KeyValuePair<int, double[]>(edge, start));
                else if (IsWitnessPoint(end, current) && IsWitnessPoint(start, next))
                    matches.Add(new KeyValuePair<int, double[]>(edge, end));
            }
            Require(matches.Count == 1 && used.Add(matches[0].Key), "Native segments do not form the planned ordered rectangle");
            ordered[index] = matches[0].Value;
        }
        return ordered;
    }

    IDimension WitnessDriver(IFeature owner, string name)
    {
        var dimensions = new List<IDimension>();
        for (var item = owner.GetFirstDisplayDimension(); item != null; item = owner.GetNextDisplayDimension(item))
        {
            var dimension = ((IDisplayDimension)item).GetDimension2(0) as IDimension;
            if (dimension != null && dimension.Name == name && Same(dimension.GetFeatureOwner(), owner))
                dimensions.Add(dimension);
        }
        Require(dimensions.Count == 1 && dimensions[0].DrivenState == (int)swDimensionDrivenState_e.swDimensionDriving,
            "Expected an independent driving dimension on " + owner.Name + ": " + name);
        return dimensions[0];
    }

    double[] WitnessNormal(ISketch sketch, bool reversed)
    {
        var inverse = sketch.ModelToSketchTransform.IInverse();
        var start = WorldPoint(new[] { 0.0, 0.0, 0.0 }, inverse);
        var end = WorldPoint(new[] { 0.0, 0.0, 1.0 }, inverse);
        var normal = end.Zip(start, (last, first) => last - first).ToArray();
        var length = Math.Sqrt(normal.Sum(value => value * value));
        Require(length > 0 && !Double.IsInfinity(length), "Native sketch normal is unavailable");
        return normal.Select(value => (reversed ? -1.0 : 1.0) * value / length).ToArray();
    }

    Dictionary<string, object> MeasureWitness(IModelDoc2 model, string stage, string[] history,
        string[] drivers, Dictionary<string, object> shape)
    {
        var profile = NamedFeature(model, history[0], "ProfileFeature");
        var boss = NamedFeature(model, history[1], "Extrusion");
        var sketch = profile.GetSpecificFeature2() as ISketch;
        var parents = Items(boss.GetParents()).OfType<IFeature>()
            .Where(parent => parent.GetTypeName2() == "ProfileFeature").ToArray();
        Require(sketch != null && parents.Length == 1 && Same(parents[0], profile)
            && sketch.GetSketchRegionCount() == 1 && sketch.GetConstrainedStatus() == 3,
            "The Boss did not retain its fully constrained profile");
        int supportType = 0;
        var support = sketch.GetReferenceEntity(ref supportType) as IFeature;
        Require(support != null && support.GetTypeName2() == "RefPlane", "Expected an owned planar sketch");
        var extrusion = boss.GetDefinition() as IExtrudeFeatureData2;
        Require(extrusion != null && extrusion.GetEndCondition(true) == (int)swEndConditions_e.swEndCondBlind
            && !extrusion.BothDirections && extrusion.GetDepth(true) > 0, "Expected a one-sided blind Boss");
        var owners = new[] { profile, profile, boss };
        var dimensionRows = drivers.Select((name, slot) => Row(
            "axis", WitnessAxes[slot], "name", name, "owner", owners[slot].Name,
            "driving", true, "value_m", WitnessDriver(owners[slot], name).SystemValue)).ToArray();
        var body = (Dictionary<string, object>)FinalBody(model);
        return Row("stage", stage, "history", new[] { profile.Name, boss.Name }, "boss_profile", parents[0].Name,
            "blind", true, "fully_constrained", true, "rebuilt", stage != "before_rebuild",
            "body_count", body["solid_body_count"], "corners_m", WitnessCorners(sketch, shape),
            "direction", WitnessNormal(sketch, extrusion.ReverseDirection), "depth_m", extrusion.GetDepth(true),
            "drivers", dimensionRows, "volume_m3", body["volume_m3"], "centroid_m", body["center_of_mass_m"]);
    }

    IModelDoc2 OpenWitness(string path, bool readOnly, out Dictionary<string, object> report)
    {
        Require(app.GetDocumentCount() == 0, "The owned SOLIDWORKS process is not empty");
        int errors = 0, warnings = 0;
        var options = swOpenDocOptions_e.swOpenDocOptions_Silent;
        if (readOnly) options |= swOpenDocOptions_e.swOpenDocOptions_ReadOnly;
        var model = app.OpenDoc6(path, (int)swDocumentTypes_e.swDocPART, (int)options, "", ref errors, ref warnings) as IModelDoc2;
        report = Row("returned", model != null, "errors", errors, "warnings", warnings);
        Require(model != null && String.Equals(model.GetPathName(), path, StringComparison.OrdinalIgnoreCase)
            && app.GetDocumentCount() == 1, "SOLIDWORKS did not open the exact witness file: " + errors + " / " + warnings);
        return model;
    }

    static void CheckWitnessOpen(IModelDoc2 model, bool readOnly, Dictionary<string, object> report)
    {
        Require(model.IsOpenedReadOnly() == readOnly && (int)report["errors"] == 0 && (int)report["warnings"] == 0,
            "The exact witness did not open cleanly in the requested mode: " + report["errors"] + " / " + report["warnings"]);
    }

    void CloseWitness(IModelDoc2 model)
    {
        if (model != null) app.CloseDoc(model.GetTitle());
        Require(app.GetDocumentCount() == 0, "The owned SOLIDWORKS process did not close its witness file");
    }

    Dictionary<string, object> WitnessControl(string path)
    {
        IModelDoc2 model = null;
        try
        {
            Dictionary<string, object> opened;
            model = OpenWitness(path, true, out opened);
            CheckWitnessOpen(model, true, opened);
            Require(model.ForceRebuild3(false), "Stock control rebuild failed");
            var body = (Dictionary<string, object>)FinalBody(model);
            return Row("sha256", WitnessDigest(path), "open", opened, "rebuild", true,
                "body_count", body["solid_body_count"], "volume_m3", body["volume_m3"],
                "centroid_m", body["center_of_mass_m"]);
        }
        finally { CloseWitness(model); }
    }

    static double WitnessSize(Dictionary<string, object> shape, int slot)
    {
        if (slot == 2) return Convert.ToDouble(shape["depth_m"], CultureInfo.InvariantCulture);
        var corners = Items(shape["corners_m"]).Select(WitnessPoint).ToArray();
        return Math.Sqrt(corners[slot].Zip(corners[slot + 1], (left, right) => (right - left) * (right - left)).Sum());
    }

    void SetWitnessDriver(IModelDoc2 model, string[] history, string[] drivers, int slot, double metres)
    {
        var owner = slot < 2 ? NamedFeature(model, history[0], "ProfileFeature")
            : NamedFeature(model, history[1], "Extrusion");
        var driver = WitnessDriver(owner, drivers[slot]);
        int status = driver.SetSystemValue3(metres, 1, null);
        Require(status == 0 && model.ForceRebuild3(false), "Native driving edit did not rebuild: " + drivers[slot]);
    }

    List<object> EditWitness(IModelDoc2 model, string[] history, string[] drivers,
        Dictionary<string, object> shapes, out Dictionary<string, object> save)
    {
        var baseline = WitnessObject(shapes["baseline"]);
        Require(model.ForceRebuild3(false), "Candidate baseline rebuild failed");
        var measurements = new List<object> { MeasureWitness(model, "baseline", history, drivers, baseline) };
        for (int slot = 0; slot < WitnessAxes.Length; slot++)
        {
            var axis = WitnessAxes[slot];
            var shape = WitnessObject(shapes[axis]);
            SetWitnessDriver(model, history, drivers, slot, WitnessSize(shape, slot));
            measurements.Add(MeasureWitness(model, axis + "_edited", history, drivers, shape));
            SetWitnessDriver(model, history, drivers, slot, WitnessSize(baseline, slot));
            measurements.Add(MeasureWitness(model, axis + "_restored", history, drivers, baseline));
        }
        int errors = 0, warnings = 0;
        bool returned = model.Save3((int)swSaveAsOptions_e.swSaveAsOptions_Silent, ref errors, ref warnings);
        save = Row("returned", returned, "errors", errors, "warnings", warnings);
        Require(returned && errors == 0 && warnings == 0, "Native restored save did not complete cleanly: " + errors + " / " + warnings);
        return measurements;
    }

    Dictionary<string, object> ObserveWitness(string path, string control, bool readOnly,
        Dictionary<string, object> plan)
    {
        var history = Items(plan["history"]).Cast<string>().ToArray();
        var drivers = Items(plan["drivers"]).Cast<string>().ToArray();
        var shapes = WitnessObject(plan["shapes"]);
        var baseline = WitnessObject(shapes["baseline"]);
        var before = WitnessControl(control);
        IModelDoc2 model = null;
        Dictionary<string, object> opened;
        Dictionary<string, object> save = null;
        List<object> measurements;
        try
        {
            model = OpenWitness(path, readOnly, out opened);
            CheckWitnessOpen(model, readOnly, opened);
            if (readOnly)
            {
                measurements = new List<object> { MeasureWitness(model, "before_rebuild", history, drivers, baseline) };
                Require(model.ForceRebuild3(false), "Restored document did not rebuild");
                measurements.Add(MeasureWitness(model, "after_rebuild", history, drivers, baseline));
            }
            else measurements = EditWitness(model, history, drivers, shapes, out save);
        }
        finally { CloseWitness(model); }
        return Row("open", opened, "read_only", readOnly, "save", save, "measurements", measurements,
            "controls", Row("before", before, "after", WitnessControl(control)));
    }

    public static void RunBossPhase(string planPath, string documentPath, string controlPath,
        string executable, string launchPath, string rawPath)
    {
        var launch = WitnessObject(Json.DeserializeObject(File.ReadAllText(launchPath)));
        var plan = WitnessObject(Json.DeserializeObject(File.ReadAllText(planPath)));
        var owner = WitnessObject(launch["native"]);
        var collector = WitnessObject(launch["collector"]);
        var phase = (string)launch["phase"];
        Require(phase == "edit" || phase == "reopen", "Unexpected native witness phase");
        using (var caller = Process.GetCurrentProcess())
            Require(caller.Id == (int)collector["pid"] && WitnessCreation(caller) == WitnessTime(collector["created"])
                && caller.SessionId == (int)owner["session"], "Launch does not identify this exact collector");
        Require(WitnessDigest(planPath) == (string)launch["plan_sha256"]
            && WitnessDigest(executable) == (string)plan["image_sha256"]
            && WitnessDigest(documentPath) == (string)launch["input_sha256"]
            && WitnessDigest(controlPath) == (string)WitnessObject(plan["control"])["sha256"],
            "A private phase input differs from its pin");

        using (var process = Process.GetProcessById((int)owner["pid"]))
        {
            ISldWorks application = null;
            bool attached = false;
            try
            {
                application = AttachWitness(process, owner, executable);
                Require(application.GetDocumentCount() == 0 && (string)plan["build"] == Build
                    && application.RevisionNumber() == "34.4.1", "The held licensed build did not start empty");
                attached = true;
                var reading = new P04Readback(application).ObserveWitness(documentPath, controlPath, phase == "reopen", plan);
                VerifyWitnessPeer(process, owner, executable);
                Require(application.GetDocumentCount() == 0, "The owned process still has documents");
                application.ExitApp();
                attached = false;
                reading.Add("launch_sha256", WitnessDigest(launchPath));
                reading.Add("input_sha256", launch["input_sha256"]);
                reading.Add("output_sha256", WitnessDigest(documentPath));
                PublishTicket(rawPath, reading);
            }
            finally
            {
                if (application != null)
                {
                    try
                    {
                        if (attached && !process.HasExited && application.GetDocumentCount() == 0)
                        {
                            VerifyWitnessPeer(process, owner, executable);
                            application.ExitApp();
                        }
                    }
                    finally { Marshal.FinalReleaseComObject(application); }
                }
            }
        }
    }
}
