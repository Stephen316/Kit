using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public sealed partial class SolidWorksCapture
{
    static readonly string[] TwoPadCases = { "baseline-a", "baseline-b", "depth-3", "depth-8", "support-11" };

    static double[] TwoPadDepths(string name)
    {
        if (!TwoPadCases.Contains(name)) throw new ArgumentException("Unrecognized two-pad case");
        return new[] { name == "support-11" ? 11d : 10d, name == "depth-3" ? 3d : name == "depth-8" ? 8d : 5d };
    }

    IModelDoc2 BuildTwoPad(double baseMm, double upperMm)
    {
        var doc = Build("P03", "XY", false, false);
        try
        {
            if (baseMm != 10) Set(doc, "depth_mm", baseMm / 1000);
            var baseBoss = Features(doc).Single(feature => feature.Name == "BlindBoss");
            baseBoss.Name = "BaseBoss";
            var body = Array(((IPartDoc)doc).GetBodies2(0, false)).Cast<IBody2>().Single();
            var top = Array(body.GetFaces()).Cast<IFace2>().Single(face =>
                ((double[])face.Normal).Zip(World("XY", 0, 0, 1), (a, b) => Math.Abs(a - b)).Sum() < 1e-8);
            Check(app.IsSame(top.GetFeature(), baseBoss) == (int)swObjectEquality.swObjectSame, "Top face must belong to BaseBoss");
            var sketch = BeginSketch(doc, "XY", (IEntity)top);
            var z = baseMm / 1000;
            var edges = Rectangle(doc, sketch, "XY", .015, .005, .025, .015, z);
            var origin = Corner(sketch, "XY", .015, .005, z);
            EdgeDimension(doc, Edge(sketch, edges, "XY", 1, .005), "upper_width_mm", .010);
            EdgeDimension(doc, Edge(sketch, edges, "XY", 0, .015), "upper_height_mm", .010);
            OriginDimension(doc, sketch, origin, "XY", 0, "upper_left_mm", .015);
            OriginDimension(doc, sketch, origin, "XY", 1, "upper_bottom_mm", .005);
            var profile = EndSketch(doc, sketch, "UpperSketch");
            Check(profile.Select2(false, 0), "Select the face-supported profile");
            var boss = doc.FeatureManager.FeatureExtrusion2(
                true, false, false, (int)swEndConditions_e.swEndCondBlind, 0, upperMm / 1000, 0,
                false, false, false, false, 0, 0, false, false, false, false,
                true, true, true, (int)swStartConditions_e.swStartSketchPlane, 0, false);
            Check(boss != null, "Create the merged upper blind boss");
            boss.Name = "UpperBoss";
            FeatureDimension(boss, "upper_depth_mm", upperMm / 1000);
            Rebuild(doc);
            return doc;
        }
        catch { Close(doc); throw; }
    }

    Dictionary<string, object> ObserveTwoPad(IModelDoc2 doc, string label, double baseMm, double upperMm)
    {
        var row = Measure(doc, label, true);
        var lowerVolume = 800 * baseMm;
        var upperVolume = 100 * upperMm;
        var volume = lowerVolume + upperVolume;
        var center = new[] { 20d, 10d, (lowerVolume * baseMm / 2 + upperVolume * (baseMm + upperMm / 2)) / volume };
        Check((int)row["body_count"] == 1 && Math.Abs((double)row["volume_mm3"] - volume) <= .001
            && ((double[])row["center_of_mass_mm"]).Zip(center, (actual, expected) => Math.Abs(actual - expected)).Max() <= .00001,
            "Observed merged solid disagrees with the independent stacked-prism volume or centroid");
        var features = Features(doc);
        var lower = features.Single(feature => feature.Name == "BaseBoss");
        var upper = features.Single(feature => feature.Name == "UpperBoss");
        var sketch = (ISketch)features.Single(feature => feature.Name == "UpperSketch").GetSpecificFeature2();
        int supportKind = 0;
        var face = sketch.GetReferenceEntity(ref supportKind) as IFace2;
        Check(supportKind == (int)swSelectType_e.swSelFACES && face != null
            && app.IsSame(face.GetFeature(), lower) == (int)swObjectEquality.swObjectSame,
            "UpperSketch does not resolve to BaseBoss's native face");
        var bound = Dimensions(lower).Single(value => value.Name == "depth_mm");
        var drive = Dimensions(upper).Single(value => value.Name == "upper_depth_mm");
        var operation = (IExtrudeFeatureData2)upper.GetDefinition();
        Check(Math.Abs(bound.SystemValue * 1000 - baseMm) <= .00001
            && Math.Abs(drive.SystemValue * 1000 - upperMm) <= .00001
            && operation.GetEndCondition(true) == (int)swEndConditions_e.swEndCondBlind && operation.Merge,
            "The two embedded driving lengths and merged blind operation did not survive");
        var body = Array(((IPartDoc)doc).GetBodies2(0, false)).Cast<IBody2>().Single();
        var reference = doc.Extension.GetPersistReference3(face) as byte[];
        int state = -1;
        Check(reference != null && reference.Length > 0
            && app.IsSame(face, doc.Extension.GetObjectByPersistReference3(reference, out state)) == (int)swObjectEquality.swObjectSame
            && state == (int)swPersistReferencedObjectStates_e.swPersistReferencedObject_Ok,
            "The supporting face did not round-trip its native reference in the observation");
        row["expected_volume_mm3"] = volume;
        row["expected_centroid_mm"] = center;
        row["upper_support"] = Row("kind", supportKind, "parent_feature", lower.Name,
            "normal_world", face.Normal, "area_mm2", face.GetArea() * 1e6,
            "reference", Convert.ToBase64String(reference), "resolve_state", state);
        row["native_body"] = Row("faces", body.GetFaceCount(), "edges", body.GetEdgeCount(), "vertices", body.GetVertexCount());
        return row;
    }

    Dictionary<string, object> SaveTwoPad(string name)
    {
        var sizes = TwoPadDepths(name);
        var doc = BuildTwoPad(sizes[0], sizes[1]);
        try
        {
            return Row("variant", name, "base_depth_mm", sizes[0], "upper_depth_mm", sizes[1],
                "authored", ObserveTwoPad(doc, "authored", sizes[0], sizes[1]),
                "save", Save(doc, Path.Combine(output, name + ".SLDPRT"), false));
        }
        finally { Close(doc); }
    }

    void ReopenTwoPad(Dictionary<string, object> evidence)
    {
        var name = (string)evidence["variant"];
        var sizes = TwoPadDepths(name);
        var save = (Dictionary<string, object>)evidence["save"];
        var path = Path.Combine(output, (string)save["file"]);
        Check(Hash(path) == (string)save["sha256"], "Authored save changed before reopen");
        object status;
        var doc = Open(path, out status, true);
        try
        {
            evidence["open"] = status;
            evidence["before_rebuild"] = ObserveTwoPad(doc, "before rebuild", sizes[0], sizes[1]);
            Rebuild(doc);
            evidence["after_rebuild"] = ObserveTwoPad(doc, "after rebuild", sizes[0], sizes[1]);
            if (name == "baseline-a")
            {
                Set(doc, "upper_depth_mm", .007);
                evidence["edit_upper"] = ObserveTwoPad(doc, "upper edit", 10, 7);
                Set(doc, "upper_depth_mm", .005);
                Set(doc, "depth_mm", .011);
                evidence["edit_base"] = ObserveTwoPad(doc, "support moves with base", 11, 5);
                Set(doc, "depth_mm", .010);
                evidence["restored"] = ObserveTwoPad(doc, "restored", 10, 5);
            }
        }
        finally { Close(doc); }
        Check(Hash(path) == (string)save["sha256"], "Reopen modified the saved bytes");
    }

    public static string CaptureTwoPad(
        string repository, string directory, string executable, string priorJson)
    {
        return SolidWorksScopeControl.WithOwnedProcess(executable, (application, process) =>
        {
            var capture = new SolidWorksCapture(repository, directory, application);
            bool preference = application.GetUserPreferenceToggle(10);
            application.SetUserPreferenceToggle(10, false);
            try
            {
                var before = capture.Control("before two-pad phase");
                if (String.IsNullOrEmpty(priorJson))
                {
                    var cases = TwoPadCases.Where(name => name != "baseline-b").Select(capture.SaveTwoPad).ToArray();
                    return Row("authoring_process", process, "authoring_control_before", before,
                        "authoring_control_after", capture.Control("after authoring"), "cases", cases);
                }
                var prior = Json.Deserialize<Dictionary<string, object>>(priorJson);
                var owner = (Dictionary<string, object>)prior["authoring_process"];
                Check((bool)owner["exited_observed"] && (int)owner["pid"] != (int)process["pid"],
                    "Reopen must use a fresh owned SOLIDWORKS process");
                var reopened = Array(prior["cases"]).Cast<Dictionary<string, object>>().ToList();
                Check(reopened.Select(row => (string)row["variant"]).SequenceEqual(TwoPadCases.Where(name => name != "baseline-b")),
                    "Unexpected saved case roster");
                reopened.Add(capture.SaveTwoPad("baseline-b"));
                foreach (var row in reopened) capture.ReopenTwoPad(row);
                prior["cases"] = reopened;
                prior["reopen_process"] = process;
                prior["reopen_control_before"] = before;
                prior["reopen_control_after"] = capture.Control("after reopen");
                return prior;
            }
            finally { application.SetUserPreferenceToggle(10, preference); }
        });
    }
}
