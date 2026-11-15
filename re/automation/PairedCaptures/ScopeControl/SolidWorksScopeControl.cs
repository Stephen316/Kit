using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public sealed class SolidWorksScopeControl
{
    const string Build = "34.4.1.1011";
    const double Mm = 1000;
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
            var mass = (IMassProperty2)doc.Extension.CreateMassProperty2();
            mass.UseSystemUnits = true;
            mass.SelectedItems = new object[] { body };
            Check(mass.Recalculate() && mass.Volume > 0, "Could not measure isolated solid " + item.Key);
            return (object)Row("bounds_mm", new[] { Extremes(body, -1), Extremes(body, 1) },
                "volume_mm3", mass.Volume * 1e9, "centroid_mm", Numbers(mass.CenterOfMass).Select(value => value * Mm).ToArray(),
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

    void Cut(IModelDoc2 doc, Dictionary<string, IBody2> bodies, Dictionary<string, object> control)
    {
        var sketch = Rectangle(doc, (string)cutSpec["sketch"], Bounds(cutSpec["profile_bounds_mm"]), TopFace(bodies["A"]));
        bool automatic = control["input_body_ids"] == null;
        Check(sketch.Select2(false, 0), "Could not select the through-all sketch");
        foreach (string id in Strings(control["input_body_ids"]))
        {
            var data = doc.ISelectionManager.CreateSelectData();
            data.Mark = 1;
            Check(bodies[id].Select2(true, data), "Could not append scoped solid " + id);
        }
        var feature = doc.FeatureManager.FeatureCut4(true, false, false, (int)swEndConditions_e.swEndCondThroughAll,
            0, 0, 0, false, false, false, false, 0, 0, false, false, false, false, false,
            true, automatic, false, false, false, (int)swStartConditions_e.swStartSketchPlane, 0, false, false);
        Check(feature != null, "Could not create the scoped through-all Cut");
        feature.Name = (string)cutSpec["feature"];
        doc.ClearSelection2(true);
        Check(doc.ForceRebuild3(false), "Could not rebuild the scoped through-all Cut");
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
            var selectedIds = selected.Cast<IBody2>().Select(body => BodyId(body, producers)).OrderBy(id => id).ToArray();
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

    object Observe(IModelDoc2 doc, Dictionary<string, object> before)
    {
        var measured = MeasureBodies(doc, Bodies(doc));
        var cut = CutRecord(doc);
        cut["target_body_ids"] = measured.Keys.OrderBy(id => id).Where(id =>
            Convert.ToDouble(ObjectValue(before[id])["volume_mm3"]) -
                Convert.ToDouble(ObjectValue(measured[id])["volume_mm3"]) > volumeTolerance).ToArray();
        return Row("cut", cut, "bodies", measured);
    }

    Dictionary<string, object> Create(string directory, Dictionary<string, object> control)
    {
        var mode = (string)control["mode"];
        var file = "solidworks-scope-" + mode + ".SLDPRT";
        var path = Path.Combine(directory, file);
        Check(!File.Exists(path) && app.GetDocumentCount() == 0, "The scope authoring workspace is not empty");
        var doc = (IModelDoc2)app.INewDocument2(template, 0, 0, 0);
        Check(doc != null, "Could not create licensed scope part");
        try
        {
            Boss(doc, "A");
            Boss(doc, "B");
            Check(doc.ForceRebuild3(false), "Could not rebuild the two uncut solids");
            var bodies = Bodies(doc);
            var before = MeasureBodies(doc, bodies);
            Cut(doc, bodies, control);
            var saved = Observe(doc, before);
            var status = 0;
            var warnings = 0;
            Check(doc.Extension.SaveAs3(path, 0, (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null, null,
                ref status, ref warnings) && status == 0 && warnings == 0, "Could not save scoped through-all control");
            return Row("mode", mode, "archive", Row("file", file, "sha256", Hash(path), "size_bytes", new FileInfo(path).Length),
                "before_cut", Row("bodies", before), "before_save", saved);
        }
        finally { app.CloseDoc(doc.GetTitle()); }
    }

    void Reopen(string directory, Dictionary<string, object> control)
    {
        var archive = ObjectValue(control["archive"]);
        var path = Path.Combine(directory, (string)archive["file"]);
        Check(Hash(path) == (string)archive["sha256"] && app.GetDocumentCount() == 0,
            "Could not reopen the exact saved scope control");
        int errors = 0, warnings = 0;
        int options = (int)(swOpenDocOptions_e.swOpenDocOptions_Silent | swOpenDocOptions_e.swOpenDocOptions_ReadOnly);
        var doc = app.OpenDoc6(path, (int)swDocumentTypes_e.swDocPART, options, "", ref errors, ref warnings) as IModelDoc2;
        Check(doc != null, "The licensed application did not reopen the scope control");
        try
        {
            Check(doc.IsOpenedReadOnly() && errors == 0
                && (warnings & ~(int)swFileLoadWarning_e.swFileLoadWarning_ReadOnly) == 0
                && string.Equals(doc.GetPathName(), path, StringComparison.OrdinalIgnoreCase),
                "The exact scope control did not open cleanly and read-only");
            var before = ObjectValue(ObjectValue(control["before_cut"])["bodies"]);
            control["after_reopen"] = Observe(doc, before);
            Check(doc.ForceRebuild3(false), "The reopened scope control did not rebuild");
            control["after_rebuild"] = Observe(doc, before);
        }
        finally { app.CloseDoc(doc.GetTitle()); }
        Check(Hash(path) == (string)archive["sha256"], "The scope control bytes changed during native readback");
    }

    static string Phase(string specification, string directory, string executable, string priorJson)
    {
        Check(Process.GetProcessesByName("SLDWORKS").Length == 0, "Use an isolated desktop with SOLIDWORKS stopped");
        var requested = DateTime.UtcNow;
        var application = (ISldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application", true));
        using (var process = Process.GetProcessById(application.GetProcessID()))
        using (var caller = Process.GetCurrentProcess())
        {
            var started = process.StartTime.ToUniversalTime();
            var module = process.MainModule;
            Check(started >= requested && process.SessionId == caller.SessionId && Hash(module.FileName) == Hash(executable),
                "Activation did not establish a fresh process for the registered SOLIDWORKS image");
            var processRow = Row("pid", process.Id, "started_utc", started.ToString("O"));
            Dictionary<string, object> output;
            try
            {
                Check(application.GetDocumentCount() == 0 && application.RevisionNumber() == "34.4.1"
                    && module.FileVersionInfo.FileVersion == Build, "The expected licensed SOLIDWORKS build did not start empty");
                var worker = new SolidWorksScopeControl(application, ObjectValue(Json.DeserializeObject(specification)));
                output = worker.Collect(directory, priorJson, processRow);
                Check(application.GetDocumentCount() == 0, "The scope worker left an open document");
            }
            finally
            {
                if (application.GetDocumentCount() == 0) application.ExitApp();
                Marshal.FinalReleaseComObject(application);
                GC.Collect();
                GC.WaitForPendingFinalizers();
                Check(process.WaitForExit(60000), "The owned SOLIDWORKS process did not exit");
            }
            processRow["exited_observed"] = true;
            return Json.Serialize(output);
        }
    }

    Dictionary<string, object> Collect(string directory, string priorJson, Dictionary<string, object> process)
    {
        var scopes = Items(spec["cases"]).Select(ObjectValue).ToArray();
        Check(scopes.Select(item => (string)item["mode"]).SequenceEqual(new[] { "automatic", "explicit_a", "explicit_ab" }),
            "The fixed scope control cases changed");
        if (priorJson == null)
        {
            var cases = scopes.Select(item => Create(directory, item)).ToArray();
            return Row("native_processes", Row("authoring", process), "cases", cases);
        }
        var prior = ObjectValue(Json.DeserializeObject(priorJson));
        var owners = ObjectValue(prior["native_processes"]);
        var author = ObjectValue(owners["authoring"]);
        Check((bool)author["exited_observed"] && (int)author["pid"] != (int)process["pid"]
            && DateTime.Parse((string)author["started_utc"]).ToUniversalTime()
                < DateTime.Parse((string)process["started_utc"]).ToUniversalTime(), "The reopen phase did not use a fresh process");
        foreach (var control in Items(prior["cases"]).Select(ObjectValue)) Reopen(directory, control);
        owners["reopen"] = process;
        return prior;
    }

    public static string Author(string specification, string directory, string executable)
    {
        return Phase(specification, directory, executable, null);
    }

    public static string Measure(string specification, string directory, string executable, string authored)
    {
        return Phase(specification, directory, executable, authored);
    }
}
