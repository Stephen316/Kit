using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public sealed class P04Readback
{
    const string Build = "34.4.1.1011";
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
    readonly ISldWorks app;

    P04Readback(ISldWorks app) { this.app = app; }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    static extern uint GetFinalPathNameByHandleW(SafeFileHandle file, StringBuilder path, uint capacity, uint flags);

    static string ResolveExecutablePath(string path)
    {
        using (var file = File.Open(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
        {
            var resolved = new StringBuilder(32768);
            uint length = GetFinalPathNameByHandleW(file.SafeFileHandle, resolved, (uint)resolved.Capacity, 0);
            if (length == 0) throw new Win32Exception(Marshal.GetLastWin32Error());
            Require(length < resolved.Capacity, "The resolved SOLIDWORKS executable path exceeds the Windows path limit");
            return resolved.ToString();
        }
    }

    static Dictionary<string, object> Row(params object[] values)
    {
        var row = new Dictionary<string, object>();
        for (int index = 0; index < values.Length; index += 2)
            row.Add((string)values[index], values[index + 1]);
        return row;
    }

    static object[] Items(object value)
    {
        return value == null ? new object[0] : ((IEnumerable)value).Cast<object>().ToArray();
    }

    static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    static object Error(Exception error)
    {
        return Row("type", error.GetType().Name, "hresult", error.HResult, "message", error.Message);
    }

    static object Feature(IFeature feature)
    {
        return feature == null ? null : Row("name", feature.Name, "type", feature.GetTypeName2(),
            "id", feature.GetID(), "suppressed", feature.IsSuppressed());
    }

    bool Same(object first, object second)
    {
        return first != null && second != null && app.IsSame(first, second) == (int)swObjectEquality.swObjectSame;
    }

    static IFeature NamedFeature(IModelDoc2 document, string name, string type)
    {
        var feature = ((IPartDoc)document).FeatureByName(name) as IFeature;
        Require(feature != null && feature.GetTypeName2() == type && !feature.IsSuppressed(),
            "Expected unsuppressed native " + name + " (" + type + ")");
        return feature;
    }

    object Participant(object entity, ISketch expectedSketch, Dictionary<string, ISketch> sketchOwners)
    {
        try
        {
            var point = entity as ISketchPoint;
            if (point != null)
            {
                var sketch = point.GetSketch();
                // Compare native objects because sketch point IDs repeat across owners.
                string owner = sketchOwners.FirstOrDefault(candidate => Same(sketch, candidate.Value)).Key;
                return Row("kind", "sketch_point", "id", point.GetID(),
                    "same_sketch", Same(sketch, expectedSketch), "local_m", new[] { point.X, point.Y, point.Z },
                    "native_sketch_owner", owner, "native_sketch_available", sketch != null);
            }
            var segment = entity as ISketchSegment;
            if (segment != null)
                return Row("kind", "sketch_segment", "type", segment.GetType(),
                    "id", segment.GetID(), "same_sketch", Same(segment.GetSketch(), expectedSketch));
            return Row("kind", entity == null ? "null" : "unsupported");
        }
        catch (COMException error)
        {
            return Row("kind", "unavailable", "diagnostic", Error(error));
        }
    }

    object Relation(ISketchRelation relation, ISketch sketch, Dictionary<string, ISketch> sketchOwners)
    {
        var row = Row("type", relation.GetRelationType());
        try
        {
            row["entity_types"] = relation.GetEntitiesType();
            row["entities"] = Items(relation.GetEntities()).Select(entity => Participant(entity, sketch, sketchOwners)).ToArray();
            row["definition_entities"] = Items(relation.GetDefinitionEntities2())
                .Select(entity => Participant(entity, sketch, sketchOwners)).ToArray();
        }
        catch (COMException error)
        {
            row["diagnostic"] = Error(error);
        }
        return row;
    }

    object Dimension(IDisplayDimension display, IDimension dimension, IFeature feature, ISketch sketch,
        Dictionary<string, ISketch> sketchOwners)
    {
        var row = Row("name", dimension.Name, "full_name", dimension.FullName, "type", display.Type2,
            "system_value", dimension.SystemValue, "driven_state", dimension.DrivenState);
        try
        {
            var owner = dimension.GetFeatureOwner() as IFeature;
            row["owner"] = Feature(owner);
            row["same_owner"] = Same(owner, feature);
            var annotation = display.GetAnnotation() as IAnnotation;
            if (annotation == null)
            {
                row["attachment_status"] = "annotation_unavailable";
                return row;
            }
            row["dangling"] = annotation.IsDangling();
            row["attachment_count"] = annotation.GetAttachedEntityCount3();
            row["attachment_types"] = annotation.GetAttachedEntityTypes();
            var attachments = Items(annotation.GetAttachedEntities3());
            row["attachments"] = attachments.Select(entity => Participant(entity, sketch, sketchOwners)).ToArray();
            row["attachment_status"] = attachments.Length != (int)row["attachment_count"]
                ? "count_mismatch" : attachments.Length == 0 ? "empty" : "observed_slots";
        }
        catch (COMException error)
        {
            row["attachment_status"] = "unavailable";
            row["diagnostic"] = Error(error);
        }
        return row;
    }

    object Sketch(IFeature feature, ISketch sketch, Dictionary<string, ISketch> sketchOwners)
    {
        var dimensions = new List<object>();
        for (object current = feature.GetFirstDisplayDimension(); current != null;
             current = feature.GetNextDisplayDimension(current))
        {
            var display = (IDisplayDimension)current;
            var dimension = display.GetDimension2(0) as IDimension;
            if (dimension != null && dimension.FullName.Split('@').Skip(1).FirstOrDefault() == feature.Name)
                dimensions.Add(Dimension(display, dimension, feature, sketch, sketchOwners));
        }
        var segments = new List<object>();
        foreach (var segment in Items(sketch.GetSketchSegments()).Cast<ISketchSegment>())
        {
            var line = segment as ISketchLine;
            segments.Add(Row("entity", Participant(segment, sketch, sketchOwners), "construction", segment.ConstructionGeometry,
                "start", line == null ? null : Participant(line.IGetStartPoint2(), sketch, sketchOwners),
                "end", line == null ? null : Participant(line.IGetEndPoint2(), sketch, sketchOwners)));
        }
        return Row("feature", Feature(feature), "model_to_sketch_transform", sketch.ModelToSketchTransform.ArrayData,
            "points", Items(sketch.GetSketchPoints2()).Select(point => Participant(point, sketch, sketchOwners)).ToArray(),
            "segments", segments, "dimensions", dimensions,
            "relations", Items(sketch.RelationManager.GetRelations(0)).Cast<ISketchRelation>()
                .Select(relation => Relation(relation, sketch, sketchOwners)).ToArray());
    }

    Dictionary<string, object> Support(IModelDoc2 document, ISketch sketch, IFeature boss, byte[] priorReference)
    {
        var row = Row("verified", false);
        try
        {
            int kind = 0;
            var face = sketch.GetReferenceEntity(ref kind) as IFace2;
            row["reference_kind"] = kind;
            if (kind != (int)swSelectType_e.swSelFACES || face == null)
            {
                row["status"] = "no_native_face";
                return row;
            }
            var owner = face.GetFeature() as IFeature;
            row["oldest_owning_feature"] = Feature(owner);
            bool sameBoss = Same(owner, boss);
            row["same_as_expected_boss"] = sameBoss;
            row["normal_world"] = face.Normal;
            row["area_m2"] = face.GetArea();
            var reference = document.Extension.GetPersistReference3(face) as byte[];
            if (reference == null || reference.Length == 0)
            {
                row["status"] = "persistent_reference_unavailable";
                return row;
            }
            row["reference_base64"] = Convert.ToBase64String(reference);
            int resolveStatus = 0;
            var resolved = document.Extension.GetObjectByPersistReference3(reference, out resolveStatus) as IFace2;
            row["resolve_state"] = resolveStatus;
            bool sameFace = Same(face, resolved);
            row["roundtrip_same_face"] = sameFace;
            row["other_boss_faces"] = OtherBossFaces(document, boss, face);
            bool priorMatches = true;
            if (priorReference != null)
            {
                int priorState = 0;
                var priorFace = document.Extension.GetObjectByPersistReference3(priorReference, out priorState) as IFace2;
                row["before_rebuild_resolve_state"] = priorState;
                priorMatches = priorState == (int)swPersistReferencedObjectStates_e.swPersistReferencedObject_Ok
                    && Same(face, priorFace);
                row["before_rebuild_reference_matches"] = priorMatches;
            }
            bool verified = sameBoss && sameFace && priorMatches
                && resolveStatus == (int)swPersistReferencedObjectStates_e.swPersistReferencedObject_Ok;
            row["verified"] = verified;
            row["status"] = verified ? "verified" : "unresolved";
        }
        catch (COMException error)
        {
            row["status"] = "unavailable";
            row["diagnostic"] = Error(error);
        }
        return row;
    }

    object OtherBossFaces(IModelDoc2 document, IFeature boss, IFace2 support)
    {
        try
        {
            var extension = document.Extension;
            var rows = new List<object>();
            foreach (var candidate in Items(boss.GetFaces()).OfType<IFace2>())
            {
                if (Same(support, candidate) || !Same(candidate.GetFeature(), boss)) continue;
                var reference = extension.GetPersistReference3(candidate) as byte[];
                var row = Row("normal_world", candidate.Normal, "area_m2", candidate.GetArea());
                rows.Add(row);
                if (reference == null || reference.Length == 0)
                {
                    row["status"] = "persistent_reference_unavailable";
                    continue;
                }
                int state;
                var resolved = extension.GetObjectByPersistReference3(reference, out state) as IFace2;
                row["reference_base64"] = Convert.ToBase64String(reference);
                row["resolve_state"] = state;
                row["status"] = state == (int)swPersistReferencedObjectStates_e.swPersistReferencedObject_Ok
                    && Same(candidate, resolved) && !Same(support, resolved) ? "verified_distinct" : "unresolved";
            }
            return Row("status", rows.Count > 0 ? "observed" : "no_distinct_faces", "faces", rows);
        }
        catch (COMException error)
        {
            return Row("status", "unavailable", "diagnostic", Error(error));
        }
    }

    object ObserveSketch(IFeature feature, ISketch sketch, Dictionary<string, ISketch> sketchOwners)
    {
        try
        {
            return Sketch(feature, sketch, sketchOwners);
        }
        catch (COMException error)
        {
            return Row("feature", Feature(feature), "diagnostic", Error(error));
        }
    }

    static double[] BodyExtent(IBody2 body, double sign)
    {
        var coordinates = new double[3];
        for (int axis = 0; axis < coordinates.Length; axis++)
        {
            var direction = new double[3];
            direction[axis] = sign;
            double x, y, z;
            Require(body.GetExtremePoint(direction[0], direction[1], direction[2], out x, out y, out z),
                "The solid body did not report an axis extremum");
            coordinates[axis] = new[] { x, y, z }[axis];
            Require(!double.IsNaN(coordinates[axis]) && !double.IsInfinity(coordinates[axis]),
                "The solid body reported a nonfinite axis extremum");
        }
        return coordinates;
    }

    static object FinalBody(IModelDoc2 document)
    {
        var bodies = Items(((IPartDoc)document).GetBodies2((int)swBodyType_e.swSolidBody, false));
        Require(bodies.Length == 1, "Readback topology requires one solid body");
        var body = (IBody2)bodies[0];
        var lower = BodyExtent(body, -1);
        var upper = BodyExtent(body, 1);
        Require(lower.Zip(upper, (minimum, maximum) => minimum < maximum).All(ordered => ordered),
            "The solid body reported invalid extent bounds");
        var mass = document.Extension.CreateMassProperty2() as IMassProperty2;
        Require(mass != null, "Readback mass properties are unavailable");
        mass.UseSystemUnits = true;
        Require(mass.Recalculate(), "Readback mass calculation failed");
        return Row("solid_body_count", bodies.Length, "face_count", body.GetFaceCount(),
            "edge_count", body.GetEdgeCount(), "vertex_count", body.GetVertexCount(),
            "bounds_min_m", lower, "bounds_max_m", upper, "volume_m3", mass.Volume,
            "center_of_mass_m", mass.CenterOfMass);
    }

    Dictionary<string, object> Observe(IModelDoc2 document, byte[] priorReference)
    {
        var boss = NamedFeature(document, "BlindBoss", "Extrusion");
        var profile = NamedFeature(document, "RectangleSketch", "ProfileFeature");
        var cut = NamedFeature(document, "CutSketch", "ProfileFeature");
        var origin = ((IPartDoc)document).FeatureByName("Origin") as IFeature;
        var originSketch = origin == null ? null : origin.GetSpecificFeature2() as ISketch;
        var profileSketch = (ISketch)profile.GetSpecificFeature2();
        var cutSketch = (ISketch)cut.GetSpecificFeature2();
        var sketchOwners = new Dictionary<string, ISketch>
        {
            { profile.Name, profileSketch }, { cut.Name, cutSketch }
        };
        if (originSketch != null) sketchOwners.Add(origin.Name, originSketch);
        var support = Support(document, cutSketch, boss, priorReference);
        var equations = document.GetEquationMgr();
        return Row("configuration", document.IGetActiveConfiguration().Name, "support", support,
            "final_body", FinalBody(document),
            "equations", Enumerable.Range(0, equations.GetCount()).Select(index => equations.Equation[index]).ToArray(),
            "origin_feature", Feature(origin), "origin_returns_sketch", originSketch != null,
            "origin_points", originSketch == null ? null : Items(originSketch.GetSketchPoints2())
                .Select(point => Participant(point, originSketch, sketchOwners)).ToArray(),
            "sketches", new[] { ObserveSketch(profile, profileSketch, sketchOwners), ObserveSketch(cut, cutSketch, sketchOwners) });
    }

    double[] WorldPoint(double[] local, MathTransform inverse)
    {
        var utility = (IMathUtility)app.GetMathUtility();
        var point = (IMathPoint)utility.CreatePoint(local);
        return (double[])point.IMultiplyTransform(inverse).ArrayData;
    }

    object PrincipalPerimeter(ISketch sketch)
    {
        var segments = Items(sketch.GetSketchSegments()).Cast<ISketchSegment>().ToArray();
        Require(segments.Length == 4 && segments.All(segment => !segment.ConstructionGeometry && segment is ISketchLine),
            "The principal profile does not contain four authored straight edges");
        var inverse = sketch.ModelToSketchTransform.IInverse();
        return segments.Select(segment =>
        {
            var line = (ISketchLine)segment;
            var start = line.IGetStartPoint2();
            var end = line.IGetEndPoint2();
            return Row("id", segment.GetID(),
                "start_world_m", WorldPoint(new[] { start.X, start.Y, start.Z }, inverse),
                "end_world_m", WorldPoint(new[] { end.X, end.Y, end.Z }, inverse));
        }).ToArray();
    }

    object PrincipalBoss(IModelDoc2 document, IFeature profile)
    {
        var boss = NamedFeature(document, "BlindBoss", "Extrusion");
        var profiles = Items(boss.GetParents()).OfType<IFeature>()
            .Where(parent => parent.GetTypeName2() == "ProfileFeature").ToArray();
        Require(profiles.Length == 1 && Same(profiles[0], profile),
            "The native Boss does not own the observed rectangle");
        var extrusion = boss.GetDefinition() as IExtrudeFeatureData2;
        Require(extrusion != null && extrusion.GetEndCondition(true) == (int)swEndConditions_e.swEndCondBlind
            && !extrusion.BothDirections && extrusion.GetDepth(true) > 0,
            "The native Boss does not have one blind extent");
        return Row("feature", Feature(boss), "profile", Feature(profiles[0]),
            "end_condition", extrusion.GetEndCondition(true), "depth_m", extrusion.GetDepth(true),
            "reverse_direction", extrusion.ReverseDirection, "both_directions", extrusion.BothDirections);
    }

    object ObservePrincipal(IModelDoc2 document, bool includesBoss)
    {
        var profile = NamedFeature(document, "RectangleSketch", "ProfileFeature");
        var sketch = (ISketch)profile.GetSpecificFeature2();
        var origin = ((IPartDoc)document).FeatureByName("Origin") as IFeature;
        var originSketch = origin == null ? null : origin.GetSpecificFeature2() as ISketch;
        var owners = new Dictionary<string, ISketch> { { profile.Name, sketch } };
        if (originSketch != null) owners.Add(origin.Name, originSketch);
        int supportType = 0;
        var support = sketch.GetReferenceEntity(ref supportType) as IFeature;
        Require(support != null && support.GetTypeName2() == "RefPlane"
            && sketch.GetConstrainedStatus() == 3 && sketch.GetSketchRegionCount() == 1,
            "The saved rectangle did not reopen on a plane as one fully constrained region");
        var bodies = Items(((IPartDoc)document).GetBodies2((int)swBodyType_e.swSolidBody, false));
        Require(bodies.Length == (includesBoss ? 1 : 0), "The principal part has an unexpected solid count");
        return Row("configuration", document.IGetActiveConfiguration().Name,
            "units_code", document.Extension.GetUserPreferenceInteger(263, 0),
            "support", Feature(support), "support_type", supportType, "region_count", sketch.GetSketchRegionCount(),
            "constraint_status", sketch.GetConstrainedStatus(), "perimeter", PrincipalPerimeter(sketch),
            "sketch", Sketch(profile, sketch, owners), "origin_feature", Feature(origin),
            "boss", includesBoss ? PrincipalBoss(document, profile) : null,
            "solid_body_count", bodies.Length, "final_body", includesBoss ? FinalBody(document) : null);
    }

    Dictionary<string, object> Read(string path, bool control)
    {
        int errors = 0, warnings = 0;
        var row = Row("file", Path.GetFileName(path), "status", "failed");
        IModelDoc2 owned = null;
        try
        {
            Require(app.GetDocumentCount() == 0, "SOLIDWORKS session has an open document");
            var options = (int)(swOpenDocOptions_e.swOpenDocOptions_Silent | swOpenDocOptions_e.swOpenDocOptions_ReadOnly);
            var document = app.OpenDoc6(path, (int)swDocumentTypes_e.swDocPART, options, "", ref errors, ref warnings) as IModelDoc2;
            row["open"] = Row("document_returned", document != null, "errors", errors, "warnings", warnings);
            Require(document != null && string.Equals(document.GetPathName(), path, StringComparison.OrdinalIgnoreCase),
                "SOLIDWORKS did not open the owned scratch document");
            owned = document;
            Require(document.IsOpenedReadOnly(), "SOLIDWORKS did not open the scratch document read-only");
            Require(errors == 0 && (warnings & ~(int)swFileLoadWarning_e.swFileLoadWarning_ReadOnly) == 0,
                "SOLIDWORKS open returned an error or an unexpected warning");
            if (control)
            {
                Require(document.ForceRebuild3(false), "Control rebuild failed");
                var bodies = Items(((IPartDoc)document).GetBodies2((int)swBodyType_e.swSolidBody, false));
                var mass = document.Extension.CreateMassProperty2() as IMassProperty2;
                Require(mass != null, "Control mass is unavailable");
                mass.UseSystemUnits = true;
                Require(mass.Recalculate(), "Control mass calculation failed");
                row["body_count"] = bodies.Length;
                row["volume_mm3"] = mass.Volume * 1e9;
                row["center_of_mass_m"] = mass.CenterOfMass;
                Require(bodies.Length == 1 && Math.Abs(mass.Volume * 1e9 - 881814.3482038013) <= .001,
                    "Control geometry differs from its pinned observation");
            }
            else if (row["file"].ToString().StartsWith("P01-", StringComparison.Ordinal) ||
                     row["file"].ToString().StartsWith("P03-", StringComparison.Ordinal))
            {
                bool includesBoss = row["file"].ToString().StartsWith("P03-", StringComparison.Ordinal);
                row["before_rebuild"] = ObservePrincipal(document, includesBoss);
                Require(document.ForceRebuild3(false), "Principal profile rebuild failed");
                row["after_rebuild"] = ObservePrincipal(document, includesBoss);
            }
            else
            {
                var before = Observe(document, null);
                row["before_rebuild"] = before;
                var previous = (Dictionary<string, object>)before["support"];
                byte[] reference = previous.ContainsKey("reference_base64")
                    ? Convert.FromBase64String((string)previous["reference_base64"]) : null;
                Require(document.ForceRebuild3(false), "P04 rebuild failed");
                var after = Observe(document, reference);
                row["after_rebuild"] = after;
                var current = (Dictionary<string, object>)after["support"];
                row["face_verified_before_and_after_rebuild"] = (bool)previous["verified"] && (bool)current["verified"];
            }
            row["status"] = "observed";
        }
        catch (Exception error)
        {
            if (!row.ContainsKey("open"))
                row["open"] = Row("document_returned", null, "errors", errors, "warnings", warnings);
            row["diagnostic"] = Error(error);
        }
        finally
        {
            try
            {
                if (owned != null) app.CloseDoc(owned.GetTitle());
                Require(app.GetDocumentCount() == 0, "SOLIDWORKS document cleanup did not leave an empty session");
            }
            catch (Exception error)
            {
                row["status"] = "failed";
                row["cleanup_diagnostic"] = Error(error);
            }
        }
        return row;
    }

    public static string Run(string workspace, string[] files, string expectedExecutable)
    {
        return Run(workspace, files, expectedExecutable, null, null);
    }

    public static string RunOwned(string workspace, string[] files, string expectedExecutable, string launchPath, string ticketPath)
    {
        var launch = Json.Deserialize<Dictionary<string, object>>(File.ReadAllText(launchPath, Encoding.UTF8));
        Require(launch != null && (int)launch["version"] == 1
            && ResolveExecutablePath((string)launch["image"]).Equals(ResolveExecutablePath(expectedExecutable), StringComparison.OrdinalIgnoreCase),
            "Queued launch does not identify the registered installation");
        return Run(workspace, files, expectedExecutable, launch, ticketPath);
    }

    static ISldWorks Attach()
    {
        var clock = Stopwatch.StartNew();
        while (true)
        {
            try { return (ISldWorks)Marshal.GetActiveObject("SldWorks.Application"); }
            catch (COMException error)
            {
                if (error.ErrorCode != unchecked((int)0x800401E3) || clock.Elapsed.TotalSeconds >= 60) throw;
                Thread.Sleep(250);
            }
        }
    }

    static void PublishTicket(string path, object value)
    {
        string staged = path + "." + Guid.NewGuid().ToString("N");
        try
        {
            using (var target = new FileStream(staged, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                byte[] bytes = Encoding.UTF8.GetBytes(Json.Serialize(value));
                target.Write(bytes, 0, bytes.Length);
                target.Flush(true);
            }
            File.Move(staged, path);
        }
        finally { File.Delete(staged); }
    }

    static string Run(string workspace, string[] files, string expectedExecutable, Dictionary<string, object> launch, string ticketPath)
    {
        var observations = new List<object>();
        var result = Row("status", "failed", "observations", observations);
        ISldWorks application = null;
        Process process = null;
        bool owned = false;
        try
        {
            if (launch == null)
                Require(Process.GetProcessesByName("SLDWORKS").Length == 0, "Use a dedicated session with SOLIDWORKS stopped");
            string expectedPath = ResolveExecutablePath(expectedExecutable);
            int desktopSession;
            using (var caller = Process.GetCurrentProcess()) desktopSession = caller.SessionId;
            var requestedAt = DateTime.UtcNow;
            application = launch == null
                ? (ISldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application", true))
                : Attach();
            process = Process.GetProcessById(application.GetProcessID());
            var startedAt = process.StartTime.ToUniversalTime();
            var module = process.MainModule;
            var observedApplication = Row("pid", process.Id, "started_utc", startedAt.ToString("O"),
                "session_id", process.SessionId, "executable", module.FileName, "expected_resolved_executable", expectedPath);
            result["application"] = observedApplication;
            string runningPath = ResolveExecutablePath(module.FileName);
            observedApplication["resolved_executable"] = runningPath;
            string created = "windows:" + startedAt.ToFileTimeUtc().ToString(CultureInfo.InvariantCulture);
            bool expectedProcess = process.SessionId == desktopSession
                && string.Equals(runningPath, expectedPath, StringComparison.OrdinalIgnoreCase);
            if (launch == null)
            {
                owned = expectedProcess && startedAt >= requestedAt;
                Require(owned, "COM did not start the expected SOLIDWORKS installation");
            }
            else
            {
                Require(expectedProcess && process.Id == (int)launch["pid"] && process.SessionId == (int)launch["session"]
                    && created == (string)launch["created"], "Passive COM did not attach to the exact directly launched SOLIDWORKS process");
            }
            string revision = application.RevisionNumber();
            string fileVersion = module.FileVersionInfo.FileVersion;
            observedApplication["build"] = fileVersion;
            observedApplication["revision"] = revision;
            Require(fileVersion == Build && revision == "34.4.1", "Unexpected SOLIDWORKS application build");
            if (launch != null)
            {
                Require(application.GetDocumentCount() == 0, "The directly launched SOLIDWORKS process did not start empty");
                var owner = Row("version", 1, "request_sha256", launch["request_sha256"],
                    "source_revision", launch["source_revision"], "pid", process.Id, "created", created,
                    "session", process.SessionId, "image", launch["image"], "build", fileVersion, "initial_documents", 0);
                PublishTicket(ticketPath, owner);
                result["native_owner"] = owner;
                owned = true;
            }
            var worker = new P04Readback(application);
            var before = worker.Read(Path.Combine(workspace, "control.SLDPRT"), true);
            result["control_before"] = before;
            Require((string)before["status"] == "observed", "Pre-run control did not pass");
            foreach (var file in files)
            {
                var reading = worker.Read(Path.Combine(workspace, file), false);
                observations.Add(reading);
                Require(!reading.ContainsKey("cleanup_diagnostic"), "Readback cleanup did not leave an empty session");
            }
            var after = worker.Read(Path.Combine(workspace, "control.SLDPRT"), true);
            result["control_after"] = after;
            Require((string)after["status"] == "observed", "Post-run control did not pass");
            if (observations.Cast<Dictionary<string, object>>().All(row => (string)row["status"] == "observed"))
                result["status"] = "observed";
        }
        catch (Exception error)
        {
            result["diagnostic"] = Error(error);
        }
        finally
        {
            if (owned)
            {
                try
                {
                    Require(application.GetDocumentCount() == 0, "The owned SOLIDWORKS process still has open documents");
                    application.ExitApp();
                    Marshal.FinalReleaseComObject(application);
                    GC.Collect();
                    GC.WaitForPendingFinalizers();
                    Require(process.WaitForExit(60000), "The owned SOLIDWORKS process did not exit");
                    result["owned_process_exit_observed"] = true;
                }
                catch (Exception error)
                {
                    result["status"] = "failed";
                    result["cleanup_diagnostic"] = Error(error);
                }
            }
            if (process != null) process.Dispose();
        }
        return Json.Serialize(result);
    }
}
