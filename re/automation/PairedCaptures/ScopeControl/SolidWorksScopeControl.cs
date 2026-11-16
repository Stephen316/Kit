using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public sealed class SolidWorksScopeControl
{
    const string Build = "34.4.1.1011";
    const string DirectRoute = "feature_cut4";
    const string RecoveryRoute = "modify_feature_scope";
    const double Mm = 1000;
    const int RotUnavailable = unchecked((int)0x800401E3);
    const int CallRejected = unchecked((int)0x80010001);
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = 1024 * 1024 };
    readonly ISldWorks app;
    readonly Dictionary<string, object> spec;
    readonly Dictionary<string, object> cutSpec;
    readonly Dictionary<string, object> bodySpecs;
    readonly double lengthTolerance;
    readonly double volumeTolerance;
    readonly string template;

    SolidWorksScopeControl(ISldWorks application, Dictionary<string, object> specification)
    {
        app = application;
        spec = specification;
        Check((int)spec["schema"] == 1 && (string)spec["scope"] == "two-body-through-all-discovery"
            && (string)spec["units"] == "mm", "Scope control requires the fixed millimeter specification");
        cutSpec = ObjectValue(spec["cut"]);
        bodySpecs = ObjectValue(spec["bodies"]);
        var tolerances = ObjectValue(spec["tolerances"]);
        lengthTolerance = Convert.ToDouble(tolerances["length_mm_absolute"]);
        volumeTolerance = Convert.ToDouble(tolerances["volume_mm3_absolute"]);
        Check(bodySpecs.Keys.OrderBy(key => key).SequenceEqual(new[] { "A", "B" })
            && Numbers(cutSpec["direction_world"]).SequenceEqual(new double[] { 0, 0, -1 })
            && (string)cutSpec["support_body"] == "A"
            && (string)cutSpec["end_condition"] == "through_all" && cutSpec["depth_mm"] == null,
            "Scope control requires two fixed producers and an inward through-all tool");
        template = app.GetDocumentTemplate((int)swDocumentTypes_e.swDocPART, "", 0, 0, 0);
        Check(File.Exists(template), "The licensed default part template is unavailable");
    }

    static Dictionary<string, object> Row(params object[] pairs)
    {
        var result = new Dictionary<string, object>();
        for (int index = 0; index < pairs.Length; index += 2)
            result.Add((string)pairs[index], pairs[index + 1]);
        return result;
    }

    static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    static Dictionary<string, object> ObjectValue(object value)
    {
        return (Dictionary<string, object>)value;
    }

    static object[] Items(object value)
    {
        return value == null ? new object[0] : ((IEnumerable)value).Cast<object>().ToArray();
    }

    static double[] Numbers(object value)
    {
        return Items(value).Select(item => Convert.ToDouble(item)).ToArray();
    }

    static string[] Strings(object value)
    {
        return Items(value).Cast<string>().ToArray();
    }

    static double[][] Bounds(object value)
    {
        return Items(value).Select(Numbers).ToArray();
    }

    static string Hash(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var algorithm = SHA256.Create())
            return BitConverter.ToString(algorithm.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
    }

    static object Identity(IFeature feature)
    {
        return Row("name", feature.Name, "native_id", feature.GetID());
    }

    IFeature Feature(IModelDoc2 doc, string name)
    {
        var feature = ((IPartDoc)doc).FeatureByName(name) as IFeature;
        Check(feature != null && !feature.IsSuppressed(), "Missing native feature " + name);
        return feature;
    }

    bool Same(object a, object b)
    {
        return a != null && b != null && app.IsSame(a, b) == (int)swObjectEquality.swObjectSame;
    }

    double[] PointInSketch(double[] millimeters, ISketch sketch)
    {
        var utility = (IMathUtility)app.GetMathUtility();
        var point = (IMathPoint)utility.CreatePoint(millimeters.Select(value => value / Mm).ToArray());
        return (double[])point.IMultiplyTransform(sketch.ModelToSketchTransform).ArrayData;
    }

    IFeature Rectangle(IModelDoc2 doc, string name, double[][] world, IFace2 face)
    {
        doc.ClearSelection2(true);
        var selected = face == null
            ? doc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0)
            : ((IEntity)face).Select4(false, null);
        Check(selected, "Could not select the rectangle datum for " + name);
        doc.SketchManager.InsertSketch(true);
        var sketch = doc.SketchManager.ActiveSketch as ISketch;
        Check(sketch != null, "Did not enter the rectangle sketch");
        var low = PointInSketch(world[0], sketch);
        var high = PointInSketch(world[1], sketch);
        Check(Math.Abs(low[2]) < 1e-9 && Math.Abs(high[2]) < 1e-9, "Rectangle does not lie on the selected datum");
        var edges = Items(doc.SketchManager.CreateCornerRectangle(low[0], low[1], 0, high[0], high[1], 0));
        Check(edges.Length == 4 && edges.All(edge => edge is ISketchLine), "Did not create four line segments");
        doc.ClearSelection2(true);
        doc.SketchManager.InsertSketch(true);
        var feature = (IFeature)sketch;
        feature.Name = name;
        return feature;
    }

    void Boss(IModelDoc2 doc, string bodyId)
    {
        var bodySpec = ObjectValue(bodySpecs[bodyId]);
        var bounds = Bounds(bodySpec["bounds_mm"]);
        var name = (string)bodySpec["producer"];
        var sketch = Rectangle(doc, name + "Sketch", new[]
        {
            new[] { bounds[0][0], bounds[0][1], 0 },
            new[] { bounds[1][0], bounds[1][1], 0 },
        }, null);
        Check(sketch.Select2(false, 0), "Failed to select " + name + " rectangle");
        double start = bounds[0][2] / Mm;
        double length = (bounds[1][2] - bounds[0][2]) / Mm;
        var startType = start == 0 ? swStartConditions_e.swStartSketchPlane : swStartConditions_e.swStartOffset;
        var boss = doc.FeatureManager.FeatureExtrusion2(true, false, false, (int)swEndConditions_e.swEndCondBlind,
            0, length, 0, false, false, false, false, 0, 0, false, false, false, false, false, true, true,
            (int)startType, Math.Abs(start), start < 0);
        Check(boss != null, "Could not create independent solid " + name);
        boss.Name = name;
        doc.ClearSelection2(true);
    }

    static double[] Extremes(IBody2 body, double sign)
    {
        var result = new double[3];
        for (int axis = 0; axis < 3; axis++)
        {
            var direction = new double[3];
            direction[axis] = sign;
            double x, y, z;
            Check(body.GetExtremePoint(direction[0], direction[1], direction[2], out x, out y, out z),
                "The native solid did not report an axis extremum");
            result[axis] = new[] { x, y, z }[axis] * Mm;
        }
        return result;
    }

    bool MatchesBounds(double[][] actual, double[][] expected)
    {
        return actual.SelectMany(row => row).Zip(expected.SelectMany(row => row),
            (left, right) => Math.Abs(left - right) <= lengthTolerance).All(match => match);
    }

    string BodyId(IBody2 body, Dictionary<string, IFeature> producers)
    {
        var authors = Items(body.GetFeatures()).OfType<IFeature>().ToArray();
        var matching = producers.Where(item => authors.Any(owner => Same(owner, item.Value))).ToArray();
        Check(matching.Length == 1, "The native body did not identify exactly one scope producer");
        var id = matching[0].Key;
        var nativeBounds = new[] { Extremes(body, -1), Extremes(body, 1) };
        Check(MatchesBounds(nativeBounds, Bounds(ObjectValue(bodySpecs[id])["bounds_mm"])),
            "The selected body disagrees with the independent " + id + " bounds");
        return id;
    }

    Dictionary<string, IFeature> Producers(IModelDoc2 doc)
    {
        return bodySpecs.ToDictionary(item => item.Key,
            item => Feature(doc, (string)ObjectValue(item.Value)["producer"]));
    }

    Dictionary<string, IBody2> Bodies(IModelDoc2 doc)
    {
        var bodies = Items(((IPartDoc)doc).GetBodies2((int)swBodyType_e.swSolidBody, false));
        Check(bodies.Length == 2, "Expected two disjoint native solids");
        var producers = Producers(doc);
        return bodies.Cast<IBody2>().ToDictionary(body => BodyId(body, producers));
    }

    Dictionary<string, object> MeasureBodies(IModelDoc2 doc, Dictionary<string, IBody2> bodies)
    {
        var producers = Producers(doc);
        return bodies.ToDictionary(item => item.Key, item =>
        {
            var body = item.Value;
            var mass = Numbers(body.GetMassProperties(1.0));
            Check(mass.Length == 12 && mass.Take(4).All(value => !double.IsNaN(value) && !double.IsInfinity(value))
                && mass[3] > 0, "Could not measure isolated solid " + item.Key);
            return (object)Row("bounds_mm", new[] { Extremes(body, -1), Extremes(body, 1) },
                "volume_mm3", mass[3] * 1e9, "centroid_mm", mass.Take(3).Select(value => value * Mm).ToArray(),
                "face_count", body.GetFaceCount(), "edge_count", body.GetEdgeCount(),
                "vertex_count", body.GetVertexCount(), "producer", Identity(producers[item.Key]));
        });
    }

    static IFace2 TopFace(IBody2 solid)
    {
        return Items(solid.GetFaces()).Cast<IFace2>().Single(face =>
        {
            var normal = Numbers(face.Normal);
            return normal.Length == 3 && normal[2] > 0.999;
        });
    }

    sealed class MissingExplicitCut : InvalidOperationException
    {
        public MissingExplicitCut(string mode)
            : base("FeatureCut4 returned null after verifying the explicit selection for " + mode) { }
    }

    void ApplyExplicitScope(IModelDoc2 doc, IFeature feature, string[] intended, ref string step)
    {
        step = "access_scope_definition";
        var native = feature.GetDefinition() as IExtrudeFeatureData2;
        Check(native != null && native.AccessSelections(doc, null), "Could not access the Cut definition for scope editing");
        bool attempted = false;
        Exception failure = null;
        try
        {
            Check(native.FeatureScope && native.AutoSelect, "The fallback did not recreate the automatic Cut scope");
            step = "resolve_rolled_back_scope_bodies";
            var bodies = Bodies(doc);
            var selected = intended.Select(id => (object)bodies[id]).ToArray();
            step = "set_explicit_scope_definition";
            native.FeatureScope = true;
            native.AutoSelect = false;
            native.FeatureScopeBodies = selected;
            step = "apply_explicit_scope_definition";
            attempted = true;
            Check(feature.ModifyDefinition(native, doc, null), "ModifyDefinition refused the explicit Cut scope");
        }
        catch (Exception error) { failure = error; throw; }
        finally
        {
            if (!attempted)
            {
                try { native.ReleaseSelectionAccess(); }
                catch (Exception error)
                {
                    if (failure == null) throw;
                    failure.GetBaseException().Data["scope_selection_release_hresult"] = error.GetBaseException().HResult;
                }
            }
        }
    }

    static void RebuildCut(IModelDoc2 doc, IFeature feature)
    {
        bool rebuilt = doc.ForceRebuild3(false);
        bool warning;
        int error = feature.GetErrorCode2(out warning);
        Check(rebuilt && error == 0, "Could not rebuild the scoped through-all Cut (rebuild " + rebuilt
            + ", feature code " + error + ", warning " + (error != 0 && warning) + ")");
    }

    void Cut(IModelDoc2 doc, Dictionary<string, IBody2> bodies, Dictionary<string, object> control,
        string route, ref string step)
    {
        step = "create_cut_profile";
        var sketch = Rectangle(doc, (string)cutSpec["sketch"], Bounds(cutSpec["profile_bounds_mm"]), TopFace(bodies["A"]));
        step = "select_cut_inputs";
        var intended = Strings(control["input_body_ids"]);
        bool recovery = route == RecoveryRoute;
        bool automatic = recovery || control["input_body_ids"] == null;
        var selectedIds = automatic ? new string[0] : intended;
        if (!automatic) bodies = Bodies(doc);
        Check(doc.Extension.SelectByID2(sketch.Name, "SKETCH", 0, 0, 0, false, 0, null, 0),
            "Could not select the through-all sketch");
        foreach (string id in selectedIds)
            Check(doc.Extension.SelectByID2(bodies[id].Name, "SOLIDBODY", 0, 0, 0, true, 1, null, 0),
                "Could not append scoped solid " + id);
        var selection = doc.ISelectionManager;
        var selectedSketch = selection.GetSelectedObject6(1, 0);
        Check(selection.GetSelectedObjectCount2(0) == 1
            && (Same(selectedSketch, sketch) || Same(selectedSketch, sketch.GetSpecificFeature2()))
            && selection.GetSelectedObjectCount2(1) == selectedIds.Length
            && selection.GetSelectedObjectCount2(-1) == selectedIds.Length + 1,
            "The Cut scope selections do not match the requested roster");
        for (int index = 0; index < selectedIds.Length; index++)
            Check(Same(selection.GetSelectedObject6(index + 1, 1), bodies[selectedIds[index]]),
                "The Cut scope selection did not resolve to the intended native body");
        var supportBounds = Bounds(ObjectValue(bodySpecs["A"])["bounds_mm"]);
        double apiDepth = (supportBounds[1][2] - supportBounds[0][2]) / Mm;
        step = recovery ? "create_automatic_fallback_cut" : "create_cut_feature";
        var feature = doc.FeatureManager.FeatureCut4(true, false, false, (int)swEndConditions_e.swEndCondThroughAll,
            0, apiDepth, apiDepth, false, false, false, false, 0, 0, false, false, false, false, false,
            true, automatic, false, false, false, (int)swStartConditions_e.swStartSketchPlane, 0, false, false);
        if (feature == null && !automatic) throw new MissingExplicitCut((string)control["mode"]);
        Check(feature != null, "Could not create the automatic through-all Cut for " + control["mode"]);
        feature.Name = (string)cutSpec["feature"];
        doc.ClearSelection2(true);
        step = "rebuild_cut_feature";
        RebuildCut(doc, feature);
        if (recovery)
        {
            ApplyExplicitScope(doc, feature, intended, ref step);
            step = "rebuild_explicit_scope_definition";
            RebuildCut(doc, feature);
        }
    }

    Dictionary<string, object> CutRecord(IModelDoc2 doc)
    {
        var feature = Feature(doc, (string)cutSpec["feature"]);
        var profileFeature = Feature(doc, (string)cutSpec["sketch"]);
        var profile = (ISketch)profileFeature.GetSpecificFeature2();
        int supportType = 0;
        var support = profile.GetReferenceEntity(ref supportType) as IFace2;
        var producers = Producers(doc);
        Check(support != null && BodyId(support.GetBody() as IBody2, producers) == "A",
            "The Cut support does not belong to the first producer");
        Check(Items(feature.GetParents()).OfType<IFeature>().Any(parent => Same(parent, profileFeature)),
            "The Cut does not consume its saved sketch");
        var native = (IExtrudeFeatureData2)feature.GetDefinition();
        Check(native.AccessSelections(doc, null), "Could not resolve native Cut scope selections");
        try
        {
            bool scope = native.FeatureScope;
            bool auto = native.AutoSelect;
            int end = native.GetEndCondition(true);
            Check(scope && end == (int)swEndConditions_e.swEndCondThroughAll && !native.BothDirections && !native.ReverseDirection,
                "The saved Cut switched away from the intended inward one-sided through-all scope");
            var selected = Items(native.FeatureScopeBodies);
            int selectedCount = native.GetFeatureScopeBodiesCount();
            Check(selected.Length == selectedCount, "Cut scope body inventory does not agree with its native count");
            var rolledBackProducers = Producers(doc);
            var selectedIds = selected.Cast<IBody2>().Select(body => BodyId(body, rolledBackProducers)).OrderBy(id => id).ToArray();
            var depth = native.GetDepth(true);
            return Row("end_condition", "through_all", "direction_world", new[] { 0, 0, -1 }, "depth_mm", null,
                "observed_policy", auto ? "automatic" : "explicit",
                "native", Row("feature_scope", scope, "auto_select", auto, "feature_scope_body_ids", selectedIds,
                    "feature_scope_body_count", selectedCount, "end_condition", end,
                    "reverse_direction", native.ReverseDirection, "both_directions", native.BothDirections,
                    "raw_blind_depth_m", depth, "producer", Identity(feature), "support_body_id", "A",
                    "profile", Identity(profileFeature)));
        }
        finally { native.ReleaseSelectionAccess(); }
    }

    object Observe(IModelDoc2 doc, Dictionary<string, object> before, Dictionary<string, object> intended)
    {
        var measured = MeasureBodies(doc, Bodies(doc));
        var cut = CutRecord(doc);
        var targets = measured.Keys.OrderBy(id => id).Where(id =>
            Convert.ToDouble(ObjectValue(before[id])["volume_mm3"]) -
                Convert.ToDouble(ObjectValue(measured[id])["volume_mm3"]) > volumeTolerance).ToArray();
        var native = ObjectValue(cut["native"]);
        bool automatic = intended["input_body_ids"] == null;
        Check((bool)native["auto_select"] == automatic
            && (automatic || Strings(native["feature_scope_body_ids"]).SequenceEqual(
                Strings(intended["input_body_ids"]).OrderBy(id => id))),
            "The freshly read Cut policy or selected bodies differ from the intended scope");
        Check(targets.SequenceEqual(Strings(intended["expected_affected_body_ids"]).OrderBy(id => id)),
            "The measured Cut did not affect exactly the intended bodies");
        cut["target_body_ids"] = targets;
        return Row("cut", cut, "bodies", measured);
    }

    void CloseCaseDocument(IModelDoc2 doc, Exception failure, ref string step)
    {
        if (failure == null) step = "close_document";
        try { app.CloseDoc(doc.GetTitle()); }
        catch (Exception error)
        {
            if (failure == null) throw;
            failure.GetBaseException().Data["scope_document_close_hresult"] = error.GetBaseException().HResult;
        }
    }

    Dictionary<string, object> Create(string directory, Dictionary<string, object> control, ref string step,
        Dictionary<string, object> process, Dictionary<string, object> provenance)
    {
        string route = DirectRoute;
        Dictionary<string, object> primary = null;
        try
        {
            try { return CreateAttempt(directory, control, route, ref step); }
            catch (MissingExplicitCut error)
            {
                primary = Row("status", "null_feature", "step", step, "managed_hresult", error.HResult,
                    "message", error.Message, "verified_selection_body_ids", Strings(control["input_body_ids"]));
                if (error.Data.Contains("scope_document_close_hresult")) throw;
                step = "publish_primary_creation_failure";
                var mode = (string)control["mode"];
                PublishCheckpoint(directory, mode, "primary_creation_failure",
                    Row("mode", mode, "authoring_route", route, "primary_creation_failure", primary), process, provenance);
                route = RecoveryRoute;
                var result = CreateAttempt(directory, control, route, ref step);
                result["primary_creation_failure"] = primary;
                return result;
            }
        }
        catch (Exception error)
        {
            var detail = error.GetBaseException().Data;
            detail["scope_authoring_route"] = route;
            if (primary != null) detail["scope_primary_creation_failure"] = Json.Serialize(primary);
            throw;
        }
    }

    Dictionary<string, object> CreateAttempt(string directory, Dictionary<string, object> control,
        string route, ref string step)
    {
        var mode = (string)control["mode"];
        var file = "solidworks-scope-" + mode + ".SLDPRT";
        var path = Path.Combine(directory, file);
        step = "open_part_template";
        Check(!File.Exists(path) && app.GetDocumentCount() == 0, "The scope authoring workspace is not empty");
        var doc = (IModelDoc2)app.INewDocument2(template, 0, 0, 0);
        Check(doc != null, "Could not create licensed scope part");
        Dictionary<string, object> before;
        object saved;
        Exception failure = null;
        try
        {
            step = "create_boss_a";
            Boss(doc, "A");
            step = "create_boss_b";
            Boss(doc, "B");
            step = "measure_uncut_bodies";
            Check(doc.ForceRebuild3(false), "Could not rebuild the two uncut solids");
            var bodies = Bodies(doc);
            before = MeasureBodies(doc, bodies);
            Cut(doc, bodies, control, route, ref step);
            step = "measure_authored_cut";
            saved = Observe(doc, before, control);
            step = "save_archive";
            var status = 0;
            var warnings = 0;
            var savedFile = doc.Extension.SaveAs3(path, 0, (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null, null,
                ref status, ref warnings);
            Check(savedFile && status == 0 && warnings == 0,
                "Could not save scoped through-all control (errors " + status + ", warnings " + warnings + ")");
        }
        catch (Exception error) { failure = error; throw; }
        finally { CloseCaseDocument(doc, failure, ref step); }
        step = "hash_saved_archive";
        return Row("mode", mode, "authoring_route", route,
            "archive", Row("file", file, "sha256", Hash(path), "size_bytes", new FileInfo(path).Length),
            "before_cut", Row("bodies", before), "before_save", saved);
    }

    void Reopen(string directory, Dictionary<string, object> control, Dictionary<string, object> intended, ref string step)
    {
        var archive = ObjectValue(control["archive"]);
        var file = "solidworks-scope-" + (string)control["mode"] + ".SLDPRT";
        Check((string)archive["file"] == file, "The scope control archive name differs from its case");
        var path = Path.Combine(directory, file);
        Check(Hash(path) == (string)archive["sha256"] && app.GetDocumentCount() == 0,
            "Could not reopen the exact saved scope control");
        int errors = 0, warnings = 0;
        int options = (int)(swOpenDocOptions_e.swOpenDocOptions_Silent | swOpenDocOptions_e.swOpenDocOptions_ReadOnly);
        var doc = app.OpenDoc6(path, (int)swDocumentTypes_e.swDocPART, options, "", ref errors, ref warnings) as IModelDoc2;
        Check(doc != null, "The licensed application did not reopen the scope control (errors " + errors
            + ", warnings " + warnings + ")");
        Exception failure = null;
        try
        {
            step = "verify_read_only_open";
            Check(doc.IsOpenedReadOnly() && errors == 0
                && (warnings & ~(int)swFileLoadWarning_e.swFileLoadWarning_ReadOnly) == 0
                && string.Equals(doc.GetPathName(), path, StringComparison.OrdinalIgnoreCase),
                "The exact scope control did not open cleanly and read-only (errors " + errors + ", warnings " + warnings + ")");
            var before = ObjectValue(ObjectValue(control["before_cut"])["bodies"]);
            step = "measure_reopened_cut";
            control["after_reopen"] = Observe(doc, before, intended);
            step = "rebuild_reopened_cut";
            RebuildCut(doc, Feature(doc, (string)cutSpec["feature"]));
            step = "measure_rebuilt_cut";
            control["after_rebuild"] = Observe(doc, before, intended);
        }
        catch (Exception error) { failure = error; throw; }
        finally { CloseCaseDocument(doc, failure, ref step); }
        step = "verify_reopened_archive_hash";
        Check(Hash(path) == (string)archive["sha256"], "The scope control bytes changed during native readback");
    }

    const uint TokenQuery = 8;
    const int TokenSessionId = 12;
    const uint WaitObject = 0;
    const uint WaitTimeout = 258;

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern uint GetProcessId(SafeProcessHandle process);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool GetProcessTimes(SafeProcessHandle process, out long created, out long exited,
        out long kernel, out long user);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    static extern bool QueryFullProcessImageNameW(SafeProcessHandle process, uint flags,
        StringBuilder path, ref int length);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    static extern uint GetFinalPathNameByHandleW(SafeFileHandle file, StringBuilder path, uint capacity, uint flags);

    [DllImport("advapi32.dll", SetLastError = true)]
    static extern bool OpenProcessToken(SafeProcessHandle process, uint access, out SafeAccessTokenHandle token);

    [DllImport("advapi32.dll", SetLastError = true)]
    static extern bool GetTokenInformation(SafeAccessTokenHandle token, int kind, out int value, int size, out int length);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern uint WaitForSingleObject(SafeProcessHandle process, uint milliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool TerminateProcess(SafeProcessHandle process, uint exitCode);

    static SecurityIdentifier ReadOwner(SafeProcessHandle process, out int session)
    {
        SafeAccessTokenHandle token;
        if (!OpenProcessToken(process, TokenQuery, out token)) throw new Win32Exception();
        using (token)
        using (var identity = new WindowsIdentity(token.DangerousGetHandle()))
        {
            int length;
            if (!GetTokenInformation(token, TokenSessionId, out session, sizeof(int), out length))
                throw new Win32Exception();
            var owner = identity.User;
            Check(owner != null && length == sizeof(int), "The SOLIDWORKS process token identity is incomplete");
            return owner;
        }
    }

    static long CreatedAt(SafeProcessHandle process)
    {
        long created, exited, kernel, user;
        if (!GetProcessTimes(process, out created, out exited, out kernel, out user)) throw new Win32Exception();
        Check(created > 0, "The held process lacks a creation FILETIME");
        return created;
    }

    static string CanonicalImage(string path)
    {
        using (var file = File.Open(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
        {
            var resolved = new StringBuilder(32768);
            uint length = GetFinalPathNameByHandleW(file.SafeFileHandle, resolved, (uint)resolved.Capacity, 0);
            if (length == 0) throw new Win32Exception();
            Check(length < resolved.Capacity, "The resolved SOLIDWORKS image path exceeds the Windows limit");
            return resolved.ToString();
        }
    }

    sealed class OwnedProcess
    {
        readonly SafeProcessHandle handle;
        readonly SecurityIdentifier owner;
        readonly int session;
        readonly string image;
        readonly string imageHash;
        public readonly int Pid;
        public readonly long Created;

        public OwnedProcess(Process process, SecurityIdentifier caller, int desktop, string executable, string digest)
        {
            handle = process.SafeHandle;
            Pid = process.Id;
            Created = CreatedAt(handle);
            owner = caller;
            session = desktop;
            image = executable;
            imageHash = digest;
        }

        public bool Exited(uint milliseconds)
        {
            uint state = WaitForSingleObject(handle, milliseconds);
            if (state == WaitObject) return true;
            if (state == WaitTimeout) return false;
            throw new Win32Exception();
        }

        public void Verify()
        {
            Check(!Exited(0) && GetProcessId(handle) == (uint)Pid && CreatedAt(handle) == Created,
                "The direct SOLIDWORKS launch identity changed");
            int measuredSession;
            var measuredOwner = ReadOwner(handle, out measuredSession);
            Check(owner.Equals(measuredOwner) && measuredSession == session,
                "The direct SOLIDWORKS launch changed user or desktop session");
            var path = new StringBuilder(32768);
            int length = path.Capacity;
            if (!QueryFullProcessImageNameW(handle, 0, path, ref length)) throw new Win32Exception();
            string measuredImage = path.ToString();
            Check(string.Equals(CanonicalImage(measuredImage), image, StringComparison.OrdinalIgnoreCase)
                && Hash(measuredImage) == imageHash && !Exited(0),
                "The held SOLIDWORKS process does not match the registered image");
        }

        public bool Stop()
        {
            if (Exited(0)) return false;
            Verify();
            if (!TerminateProcess(handle, 1))
            {
                int error = Marshal.GetLastWin32Error();
                if (Exited(0)) return false;
                throw new Win32Exception(error);
            }
            Check(Exited(5000), "Forced exit did not signal the held SOLIDWORKS process");
            return true;
        }
    }

    static void RequireIsolated(int ownedPid)
    {
        var processes = Process.GetProcessesByName("SLDWORKS");
        try
        {
            Check(processes.All(process => process.Id == ownedPid),
                "Use an isolated desktop with no unrelated SOLIDWORKS process");
        }
        finally
        {
            foreach (var process in processes) process.Dispose();
        }
    }

    [DllImport("ole32.dll", ExactSpelling = true)]
    static extern int GetRunningObjectTable(int reserved, out IRunningObjectTable table);

    [DllImport("ole32.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    static extern int CreateItemMoniker(string separator, string item, out IMoniker moniker);

    static object FindOwnedRegistration(int pid)
    {
        IRunningObjectTable table = null;
        IMoniker moniker = null;
        try
        {
            Marshal.ThrowExceptionForHR(GetRunningObjectTable(0, out table));
            string item = "SolidWorks_PID_" + pid.ToString(CultureInfo.InvariantCulture);
            Marshal.ThrowExceptionForHR(CreateItemMoniker(null, item, out moniker));
            object registration;
            int lookup = table.GetObject(moniker, out registration);
            Marshal.ThrowExceptionForHR(lookup);
            return registration;
        }
        finally
        {
            if (moniker != null) Marshal.ReleaseComObject(moniker);
            if (table != null) Marshal.ReleaseComObject(table);
        }
    }

    static ISldWorks AttachOwned(OwnedProcess process)
    {
        var elapsed = Stopwatch.StartNew();
        int unavailable = 0;
        int ownedMissing = 0;
        int rejected = 0;
        while (!process.Exited(0) && elapsed.Elapsed.TotalSeconds < 60)
        {
            RequireIsolated(process.Pid);
            object active = null;
            try
            {
                process.Verify();
                try { active = Marshal.GetActiveObject("SldWorks.Application"); }
                catch (COMException error)
                {
                    if (error.ErrorCode != RotUnavailable) throw;
                    unavailable++;
                    try { active = FindOwnedRegistration(process.Pid); }
                    catch (COMException lookup)
                    {
                        if (lookup.ErrorCode != RotUnavailable) throw;
                    }
                    if (active == null)
                    {
                        ownedMissing++;
                        Thread.Sleep(250);
                        continue;
                    }
                }
                var application = (ISldWorks)active;
                Check(application.GetProcessID() == process.Pid && !process.Exited(0),
                    "COM returned a different SOLIDWORKS process");
                process.Verify();
                active = null;
                return application;
            }
            catch (COMException error)
            {
                if (error.ErrorCode != CallRejected) throw;
                rejected++;
                Thread.Sleep(250);
            }
            finally
            {
                if (active != null) Marshal.ReleaseComObject(active);
            }
        }
        throw new InvalidOperationException(
            "The directly launched SOLIDWORKS process did not expose its COM object" +
            " (global ROT unavailable: " + unavailable + ", owned ROT unavailable: " + ownedMissing +
            ", RPC rejected: " + rejected +
            ", process exited: " + process.Exited(0) + ")");
    }

    static void Release(ref ISldWorks application)
    {
        var current = application;
        application = null;
        if (current == null) return;
        Marshal.FinalReleaseComObject(current);
        GC.Collect();
        GC.WaitForPendingFinalizers();
    }

    static void RequestExit(OwnedProcess process, ref ISldWorks application)
    {
        process.Verify();
        try { application.ExitApp(); }
        finally { Release(ref application); }
    }

    static Dictionary<string, object> Recover(OwnedProcess process, int pid, ref ISldWorks application, bool mayStop)
    {
        try
        {
            Check(process != null, "The original launch handle identity was not captured");
            if (process.Exited(0)) return Row("status", "exit_observed", "pid", pid);
            process.Verify();
        }
        catch (Exception error)
        {
            return Row("status", "preserved_unproven_identity", "pid", pid, "reason", error.Message);
        }
        try
        {
            if (application != null)
            {
                try
                {
                    if (application.GetDocumentCount() != 0)
                        return Row("status", "preserved_open_documents", "pid", pid);
                    mayStop = true;
                    RequestExit(process, ref application);
                    if (process.Exited(60000)) return Row("status", "exit_observed", "pid", pid);
                }
                catch (Exception error)
                {
                    if (process.Exited(0)) return Row("status", "exit_observed", "pid", pid);
                    if (!mayStop)
                        return Row("status", "preserved_unverified_documents", "pid", pid, "reason", error.Message);
                }
            }
            if (!mayStop) return Row("status", "preserved_unverified_documents", "pid", pid);
            return Row("status", process.Stop() ? "terminated_owned_process" : "exit_observed", "pid", pid);
        }
        catch (Exception error)
        {
            return Row("status", "owned_exit_unconfirmed", "pid", pid, "reason", error.Message);
        }
    }

    static string Phase(string specification, string directory, string executable, string provenance, string priorJson)
    {
        var launch = new ProcessStartInfo(executable)
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            WorkingDirectory = Path.GetDirectoryName(executable),
        };
        string image = CanonicalImage(executable);
        string digest = Hash(executable);
        int session;
        SecurityIdentifier owner;
        using (var caller = Process.GetCurrentProcess()) owner = ReadOwner(caller.SafeHandle, out session);
        RequireIsolated(0);
        using (var process = Process.Start(launch))
        {
            Check(process != null, "The registered SOLIDWORKS executable did not start");
            int pid = 0;
            OwnedProcess owned = null;
            ISldWorks application = null;
            bool mayStop = true;
            try
            {
                pid = process.Id;
                owned = new OwnedProcess(process, owner, session, image, digest);
                owned.Verify();
                application = AttachOwned(owned);
                if (application.GetDocumentCount() != 0)
                {
                    mayStop = false;
                    throw new InvalidOperationException("The licensed SOLIDWORKS launch did not start empty");
                }
                Check(application.RevisionNumber() == "34.4.1" && FileVersionInfo.GetVersionInfo(executable).FileVersion == Build,
                    "The expected licensed SOLIDWORKS build did not start");
                var worker = new SolidWorksScopeControl(application, ObjectValue(Json.DeserializeObject(specification)));
                var started = DateTime.FromFileTimeUtc(owned.Created);
                var processRow = Row("pid", pid, "started_utc", started.ToString("O"));
                mayStop = false;
                var output = worker.Collect(directory, priorJson, processRow, ObjectValue(Json.DeserializeObject(provenance)));
                Check(application.GetDocumentCount() == 0, "The scope worker left an open document");
                mayStop = true;
                RequestExit(owned, ref application);
                Check(owned.Exited(60000), "The owned SOLIDWORKS process did not exit");
                processRow["exited_observed"] = true;
                return Json.Serialize(output);
            }
            catch (Exception error)
            {
                var cleanup = Recover(owned, pid, ref application, mayStop);
                try { Release(ref application); }
                catch (Exception releaseError) { cleanup["release_error"] = releaseError.Message; }
                error.GetBaseException().Data["scope_cleanup"] = Json.Serialize(cleanup);
                throw;
            }
        }
    }

    static void PublishCheckpoint(string directory, string mode, string phase, Dictionary<string, object> evidence,
        Dictionary<string, object> process, Dictionary<string, object> provenance)
    {
        var target = Path.Combine(directory, mode + "." + phase + ".checkpoint.json");
        var stage = target + "." + Guid.NewGuid().ToString("N");
        var row = Row("schema", 1, "scope", "two-body-through-all-discovery", "kind", "scope_case_checkpoint",
            "application", "solidworks", "application_build", Build, "phase", phase, "case", evidence,
            "process", process, "campaign_completed", false, "process_exit_observed", false, "provenance", provenance);
        var payload = Encoding.UTF8.GetBytes(Json.Serialize(row) + "\n");
        using (var file = new FileStream(stage, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        {
            file.Write(payload, 0, payload.Length);
            file.Flush(true);
        }
        File.Move(stage, target);
    }

    Dictionary<string, object> CollectCase(string directory, Dictionary<string, object> intended,
        Dictionary<string, object> control, string phase, Dictionary<string, object> process,
        Dictionary<string, object> provenance)
    {
        var mode = (string)intended["mode"];
        var step = phase == "authoring" ? "open_part_template" : "open_saved_archive";
        try
        {
            if (phase == "authoring") control = Create(directory, intended, ref step, process, provenance);
            else Reopen(directory, control, intended, ref step);
            step = "publish_case_checkpoint";
            PublishCheckpoint(directory, mode, phase, control, process, provenance);
            return control;
        }
        catch (Exception error)
        {
            var detail = error.GetBaseException().Data;
            detail["scope_case"] = mode;
            detail["scope_step"] = step;
            if (control != null && control.ContainsKey("authoring_route"))
                detail["scope_authoring_route"] = control["authoring_route"];
            if (control != null && control.ContainsKey("primary_creation_failure"))
                detail["scope_primary_creation_failure"] = Json.Serialize(control["primary_creation_failure"]);
            throw;
        }
    }

    Dictionary<string, object> Collect(string directory, string priorJson, Dictionary<string, object> process,
        Dictionary<string, object> provenance)
    {
        var scopes = Items(spec["cases"]).Select(ObjectValue).ToArray();
        Check(scopes.Select(item => (string)item["mode"]).SequenceEqual(new[] { "automatic", "explicit_a", "explicit_ab" }),
            "The fixed scope control cases changed");
        if (priorJson == null)
        {
            var cases = scopes.Select(item => CollectCase(directory, item, null, "authoring", process, provenance)).ToArray();
            return Row("native_processes", Row("authoring", process), "cases", cases);
        }
        var prior = ObjectValue(Json.DeserializeObject(priorJson));
        var owners = ObjectValue(prior["native_processes"]);
        var author = ObjectValue(owners["authoring"]);
        Check((bool)author["exited_observed"] && (int)author["pid"] != (int)process["pid"]
            && DateTime.Parse((string)author["started_utc"]).ToUniversalTime()
                < DateTime.Parse((string)process["started_utc"]).ToUniversalTime(), "The reopen phase did not use a fresh process");
        var authored = Items(prior["cases"]).Select(ObjectValue).ToArray();
        Check(authored.Select(item => (string)item["mode"]).SequenceEqual(scopes.Select(item => (string)item["mode"])),
            "The authored scope roster differs from the requested cases");
        for (int index = 0; index < authored.Length; index++)
            CollectCase(directory, scopes[index], authored[index], "reopen", process, provenance);
        owners["reopen"] = process;
        return prior;
    }

    public static string Author(string specification, string directory, string executable, string provenance)
    {
        return Phase(specification, directory, executable, provenance, null);
    }

    public static string Measure(string specification, string directory, string executable, string provenance, string authored)
    {
        return Phase(specification, directory, executable, provenance, authored);
    }
}
