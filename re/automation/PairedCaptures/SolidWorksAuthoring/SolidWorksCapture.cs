using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
    static readonly UTF8Encoding Utf8 = new UTF8Encoding(false);
    readonly ISldWorks app;
    readonly string repo, output, template;
    readonly Dictionary<string, object>[] recipes;
    readonly string spec;

    SolidWorksCapture(string repo, string output)
        : this(repo, output, (ISldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")))
    {
    }

    SolidWorksCapture(string repo, string output, ISldWorks application)
    {
        app = application;
        this.repo = repo;
        this.output = output;
        template = app.GetDocumentTemplate(1, "", 0, 0, 0);
        spec = Path.Combine(repo, "re", "automation", "PairSpecs.json");
        var root = Json.Deserialize<Dictionary<string, object>>(File.ReadAllText(spec));
        recipes = Array((object)root["recipes"]).Cast<Dictionary<string, object>>().ToArray();
        Console.WriteLine("SOLIDWORKS " + app.RevisionNumber() + " PID " + app.GetProcessID());
    }

    static Dictionary<string, object> Row(params object[] values)
    {
        var row = new Dictionary<string, object>();
        for (int i = 0; i < values.Length; i += 2) row.Add((string)values[i], values[i+1]);
        return row;
    }

    static object[] Array(object value)
    {
        return value as object[] ?? (value as System.Collections.IEnumerable ?? new object[0]).Cast<object>().ToArray();
    }

    static double[] Vector(double x, double y, double z) { return new[] { x, y, z }; }
    static double[] V(ISketchPoint p) { return Vector(p.X, p.Y, p.Z); }
    static double[] Scale(double[] v, double factor) { return v.Select(x => x * factor).ToArray(); }
    static double[] World(string basis, double u, double v, double n)
    {
        if (basis == "YZ") return Vector(n,u,v);
        if (basis == "XZ") return Vector(u,-n,v);
        return Vector(u,v,n);
    }
    static void Check(bool ok, string failure) { if (!ok) throw new InvalidOperationException(failure); }
    static string Hash(string path)
    {
        using (var sha = SHA256.Create())
        using (var stream = new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.ReadWrite | FileShare.Delete))
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
    }
    static void Write(string path, object row) { File.WriteAllText(path, Json.Serialize(row) + "\n", Utf8); }
    double[] Transform(double[] xyz, MathTransform transform)
    {
        var util = (IMathUtility)app.GetMathUtility();
        return (double[])((IMathPoint)util.CreatePoint(xyz)).IMultiplyTransform(transform).ArrayData;
    }
    static void Select(ISketchSegment seg, bool append = false)
    {
        Check(seg.Select4(append, null), "Select sketch segment");
    }
    static void Select(ISketchPoint point, bool append = false)
    {
        Check(point.Select4(append, null), "Select sketch point");
    }
    static void Origin(IModelDoc2 doc, bool append = false)
    {
        Check(doc.Extension.SelectByID2("Point1@Origin","EXTSKETCHPOINT",0,0,0,append,0,null,0), "Select origin");
    }
    static void Units(IModelDoc2 doc, int mode)
    {
        Check(doc.Extension.SetUserPreferenceInteger(263,0,mode), "Set document units");
        Check(doc.Extension.GetUserPreferenceInteger(263,0) == mode, "Verify document units");
    }
    static IDimension SetName(IDisplayDimension display, string name, double value)
    {
        Check(display != null, "Create dimension " + name);
        var dimension = (IDimension)display.GetDimension2(0);
        dimension.Name = name;
        Check(dimension.Name == name, "Rename dimension " + name + ": " + dimension.Name);
        Check(Math.Abs(dimension.SystemValue - value) < 1e-8, "Dimension " + name + " measured " + dimension.SystemValue + " expected " + value);
        return dimension;
    }
    static IDimension EdgeDimension(IModelDoc2 doc, ISketchSegment edge, string name, double value)
    {
        doc.ClearSelection2(true);
        Select(edge);
        return SetName(doc.IAddDimension2(.075,.075,.075),name,value);
    }
    IDimension OriginDimension(IModelDoc2 doc, ISketch sketch, ISketchPoint p, string basis, int axis, string name, double value)
    {
        doc.ClearSelection2(true);
        Origin(doc);
        Select(p,true);
        var worldDir = axis == 0 ? World(basis,1,0,0) : World(basis,0,1,0);
        var localOrigin = Transform(Vector(0,0,0),sketch.ModelToSketchTransform);
        var localUnit = Transform(worldDir,sketch.ModelToSketchTransform);
        var display = Math.Abs(localUnit[0] - localOrigin[0]) > .5
            ? doc.IAddHorizontalDimension2(.072,.073,.074)
            : doc.IAddVerticalDimension2(.071,.073,.075);
        return SetName(display,name,value);
    }
    static IDimension FeatureDimension(IFeature feature, string name, double value)
    {
        for (object item = feature.GetFirstDisplayDimension(); item != null; item = feature.GetNextDisplayDimension(item))
        {
            var display = (IDisplayDimension)item;
            var d = (IDimension)display.GetDimension2(0);
            if (d != null && Math.Abs(d.SystemValue - value) < 1e-8) return SetName(display,name,value);
        }
        throw new InvalidOperationException("No " + name + " dimension on " + feature.Name);
    }
    ISketch BeginSketch(IModelDoc2 doc, string basis, IEntity face)
    {
        doc.ClearSelection2(true);
        if (face != null) Check(face.Select4(false,null), "Select parent top face");
        else
        {
            var plane = basis == "YZ" ? "Right Plane" : basis == "XZ" ? "Top Plane" : "Front Plane";
            Check(doc.Extension.SelectByID2(plane,"PLANE",0,0,0,false,0,null,0), "Select " + plane);
        }
        doc.SketchManager.InsertSketch(true);
        var sketch = (ISketch)doc.SketchManager.ActiveSketch;
        Check(sketch != null, "Enter sketch");
        return sketch;
    }
    static IFeature EndSketch(IModelDoc2 doc, ISketch sketch, string name)
    {
        int status = sketch.GetConstrainedStatus();
        Check(status == 3, name + " sketch constraint status " + status);
        doc.ClearSelection2(true);
        doc.SketchManager.InsertSketch(true);
        var feature = (IFeature)sketch;
        feature.Name = name;
        return feature;
    }
    ISketchSegment[] Rectangle(IModelDoc2 doc, ISketch sketch, string basis, double a, double b, double c, double d, double n)
    {
        var transform = sketch.ModelToSketchTransform;
        var start = Transform(World(basis,a,b,n),transform);
        var end = Transform(World(basis,c,d,n),transform);
        var segments = Array(doc.SketchManager.CreateCornerRectangle(start[0],start[1],0,end[0],end[1],0)).Cast<ISketchSegment>().ToArray();
        Check(segments.Length == 4, "Create four rectangle edges");
        return segments;
    }
    ISketchPoint Corner(ISketch sketch, string basis, double u, double v, double n)
    {
        var local = Transform(World(basis,u,v,n),sketch.ModelToSketchTransform);
        return Array(sketch.GetSketchPoints2()).Cast<ISketchPoint>().Single(p => Math.Abs(p.X-local[0]) < 1e-8 && Math.Abs(p.Y-local[1]) < 1e-8);
    }
    ISketchSegment Edge(ISketch sketch, ISketchSegment[] edges, string basis, int constantAxis, double value)
    {
        var inverse = sketch.ModelToSketchTransform.IInverse();
        var axis = basis == "YZ" ? constantAxis+1 : basis == "XZ" && constantAxis == 1 ? 2 : constantAxis;
        return edges.Single(seg =>
        {
            var line = (ISketchLine)seg;
            return Math.Abs(Transform(V(line.IGetStartPoint2()),inverse)[axis]-value) < 1e-8
                && Math.Abs(Transform(V(line.IGetEndPoint2()),inverse)[axis]-value) < 1e-8;
        });
    }
    static IFeature Extrusion(IModelDoc2 doc, IFeature sketch, string name, bool reverse, double depth, bool cut, bool through)
    {
        doc.ClearSelection2(true);
        Check(sketch.Select2(false,0), "Select " + sketch.Name);
        var manager = doc.FeatureManager;
        var feature = cut
            ? manager.FeatureCut4(true,false,reverse,through?1:0,0,depth,0,false,false,false,false,0,0,false,false,false,false,false,true,true,false,false,false,0,0,false,false)
            : manager.FeatureExtrusion2(true,false,reverse,0,0,depth,0,false,false,false,false,0,0,false,false,false,false,false,true,true,0,0,false);
        Check(feature != null, "Create " + name);
        feature.Name = name;
        if (!through) FeatureDimension(feature,cut?"cut_depth_mm":"depth_mm",depth);
        return feature;
    }

    IModelDoc2 Build(string id, string basis, bool reverse, bool through)
    {
        var doc = (IModelDoc2)app.INewDocument2(template,0,0,0);
        Check(doc != null,"New SOLIDWORKS part");
        try
        {
            Units(doc,5);
            var sketch = BeginSketch(doc,basis,null);
            if (id == "P02")
            {
                var circle = (ISketchSegment)doc.SketchManager.CreateCircleByRadius(0,0,0,.005);
                Check(circle != null,"Create origin circle");
                if (sketch.RelationManager.GetRelationsCount(0) == 0)
                {
                    doc.ClearSelection2(true);
                    Origin(doc);
                    Select(((ISketchArc)circle).IGetCenterPoint2(),true);
                    doc.SketchAddConstraints("sgCOINCIDENT");
                }
                doc.ClearSelection2(true);
                Select(circle);
                SetName(doc.IAddDiameterDimension2(.014,.014,.014),"diameter_mm",.010);
                EndSketch(doc,sketch,"CircleSketch");
            }
            else if (id == "P05")
            {
                var outline = Rectangle(doc,sketch,basis,.002,0,.006,.012,0);
                var inner = Corner(sketch,basis,.002,0,0);
                var outer = Corner(sketch,basis,.006,0,0);
                doc.ClearSelection2(true);
                Origin(doc);
                Select(inner,true);
                doc.SketchAddConstraints("sgHORIZPOINTS");
                OriginDimension(doc,sketch,inner,basis,0,"inner_radius_mm",.002);
                OriginDimension(doc,sketch,outer,basis,0,"outer_radius_mm",.006);
                EdgeDimension(doc,Edge(sketch,outline,basis,0,.002),"height_mm",.012);
                var end = Transform(World(basis,0,.02,0),sketch.ModelToSketchTransform);
                var manager = doc.SketchManager;
                manager.AddToDB = true;
                ISketchSegment axis;
                try { axis = (ISketchSegment)manager.CreateCenterLine(0,0,0,end[0],end[1],0); }
                finally { manager.AddToDB = false; }
                Check(axis != null,"Create world Z construction axis");
                doc.ClearSelection2(true);
                Select(axis);
                doc.SketchAddConstraints("sgFIXED");
                var profile = EndSketch(doc,sketch,"AnnulusProfile");
                Check(profile.Select2(false,0),"Select axis-bound profile");
                var feature = doc.FeatureManager.FeatureRevolve2(true,true,false,false,false,false,0,0,2*Math.PI,0,false,false,0,0,0,0,0,false,true,true);
                Check(feature != null,"Create full revolution");
                feature.Name = "Revolution";
                FeatureDimension(feature,"angle_deg",2*Math.PI);
            }
            else
            {
                var edges = Rectangle(doc,sketch,basis,0,0,.04,.02,0);
                EdgeDimension(doc,Edge(sketch,edges,basis,1,0),"width_mm",.04);
                EdgeDimension(doc,Edge(sketch,edges,basis,0,0),"height_mm",.02);
                var profile = EndSketch(doc,sketch,"RectangleSketch");
                if (id != "P01")
                {
                    Extrusion(doc,profile,"BlindBoss",reverse,.01,false,false);
                    if (id == "P04")
                    {
                        Check(doc.ForceRebuild3(false),"Rebuild parent boss");
                        var normal = World(basis,0,0,1);
                        var body = Array(((IPartDoc)doc).GetBodies2(0,false)).Cast<IBody2>().Single();
                        var face = Array(body.GetFaces()).Cast<IFace2>().Single(f =>
                            ((double[])f.Normal).Zip(normal,(a,b)=>Math.Abs(a-b)).Sum() < 1e-8);
                        var cut = BeginSketch(doc,basis,(IEntity)face);
                        var edgesCut = Rectangle(doc,cut,basis,.015,.006,.025,.014,.01);
                        var corner = Corner(cut,basis,.015,.006,.01);
                        EdgeDimension(doc,Edge(cut,edgesCut,basis,1,.006),"cut_width_mm",.010);
                        EdgeDimension(doc,Edge(cut,edgesCut,basis,0,.015),"cut_height_mm",.008);
                        var du = OriginDimension(doc,cut,corner,basis,0,"cut_left_mm",.015);
                        var dv = OriginDimension(doc,cut,corner,basis,1,"cut_bottom_mm",.006);
                        var cutProfile = EndSketch(doc,cut,"CutSketch");
                        var equations = doc.GetEquationMgr();
                        SetEquation(equations,du,"width_mm@RectangleSketch","cut_width_mm@CutSketch");
                        SetEquation(equations,dv,"height_mm@RectangleSketch","cut_height_mm@CutSketch");
                        Extrusion(doc,cutProfile,through?"ThroughAllCut":"BlindCut",false,.004,true,through);
                    }
                }
            }
            Rebuild(doc);
            doc.ShowNamedView2("", id == "P01" || id == "P02" ? (basis == "YZ" ? 4 : 1) : 7);
            doc.ViewZoomtofit2();
            return doc;
        }
        catch { Close(doc); throw; }
    }

    static void SetEquation(IEquationMgr manager, IDimension dimension, string parent, string width)
    {
        var equation = "\"" + dimension.Name + "@CutSketch\" = (\"" + parent + "\" - \"" + width + "\") / 2";
        Check(manager.Add2(-1,equation,true) >= 0,"Add " + equation);
    }
    static void Rebuild(IModelDoc2 doc) { Check(doc.ForceRebuild3(false),"Rebuild " + doc.GetTitle()); }
    void Close(IModelDoc2 doc) { app.CloseDoc(doc.GetTitle()); }
    IModelDoc2 Open(string path, out object status, bool readOnly = false)
    {
        int errors=0, warnings=0;
        var doc=app.OpenDoc6(path,1,readOnly ? 3 : 1,"",ref errors,ref warnings);
        status=Row("errors",errors,"warnings",warnings);
        if (doc == null || errors != 0 || (warnings != 0 && !(readOnly && warnings == 2)))
        {
            if (doc != null) Close(doc);
            throw new InvalidOperationException("Open " + path + ": errors " + errors + ", warnings " + warnings);
        }
        return doc;
    }
    Dictionary<string,object> Save(IModelDoc2 doc, string path, bool copy)
    {
        Check(!File.Exists(path),"Capture file already exists " + path);
        int errors=0,warnings=0;
        bool ok = doc.Extension.SaveAs(path,0,copy?3:1,null,ref errors,ref warnings);
        Check(ok && errors == 0 && warnings == 0 && File.Exists(path),"Save " + path + ": errors " + errors + ", warnings " + warnings);
        Console.WriteLine("Saved " + Path.GetFileName(path));
        return Row("file",Path.GetFileName(path),"sha256",Hash(path),"size_bytes",new FileInfo(path).Length,"save_errors",errors,"save_warnings",warnings);
    }
    static List<IFeature> Features(IModelDoc2 doc)
    {
        var collected = new List<IFeature>();
        var seen = new HashSet<string>();
        for (var f = (IFeature)doc.FirstFeature(); f != null; f = (IFeature)f.GetNextFeature())
            Collect(f,collected,seen);
        return collected;
    }
    static void Collect(IFeature f, List<IFeature> collected, HashSet<string> seen)
    {
        if (!seen.Add(f.Name + "/" + f.GetTypeName2())) return;
        collected.Add(f);
        for (var c = (IFeature)f.GetFirstSubFeature(); c != null; c = (IFeature)c.GetNextSubFeature()) Collect(c,collected,seen);
    }
    static IEnumerable<IDimension> Dimensions(IFeature f)
    {
        for (object d = f.GetFirstDisplayDimension(); d != null; d = f.GetNextDisplayDimension(d))
        {
            var dim = (IDimension)((IDisplayDimension)d).GetDimension2(0);
            if (dim != null && dim.FullName.Split('@')[1] == f.Name) yield return dim;
        }
    }
    static object DescribeEntity(object entity)
    {
        var segment=entity as ISketchSegment;
        var point=entity as ISketchPoint;
        if (point != null) return Row("point_local_mm",Scale(V(point),1000),"id",point.GetID());
        if (segment != null) return Row("segment_type",segment.GetType(),"id",segment.GetID());
        return Row("external_entity_type",(entity as IEntity) == null ? (object)null : ((IEntity)entity).GetType());
    }
    object DescribeSketch(IModelDoc2 doc, IFeature feature, ISketch sketch)
    {
        int supportType=0;
        var support = sketch.GetReferenceEntity(ref supportType);
        var inverse = sketch.ModelToSketchTransform.IInverse();
        var entities = new List<object>();
        foreach (var seg in Array(sketch.GetSketchSegments()).Cast<ISketchSegment>())
        {
            var row = Row("type",seg.GetType(),"id",seg.GetID(),"construction",seg.ConstructionGeometry,"length_mm",seg.GetLength()*1000);
            var line=seg as ISketchLine;
            var arc=seg as ISketchArc;
            if (line != null)
            {
                row["start_world_mm"] = Scale(Transform(V(line.IGetStartPoint2()),inverse),1000);
                row["end_world_mm"] = Scale(Transform(V(line.IGetEndPoint2()),inverse),1000);
            }
            if (arc != null)
            {
                row["center_world_mm"] = Scale(Transform(V(arc.IGetCenterPoint2()),inverse),1000);
                row["radius_mm"] = arc.GetRadius()*1000;
            }
            entities.Add(row);
        }
        var relations = Array(sketch.RelationManager.GetRelations(0)).Cast<ISketchRelation>().Select(rel =>
            Row("type",rel.GetRelationType(),"entity_types",rel.GetEntitiesType(),"entities",Array(rel.GetEntities()).Select(DescribeEntity).ToArray())).ToArray();
        doc.ClearSelection2(true);
        feature.Select2(false,0);
        var section = (double[])doc.Extension.GetSectionProperties2(new object[]{(IFeature)sketch});
        doc.ClearSelection2(true);
        bool measured = section != null && section.Length > 4 && section[0] == 0;
        Check(measured,"Section properties for " + feature.Name + ": " + (section==null?"null":section[0].ToString()));
        return Row("name",feature.Name,"support_type",supportType,"support_name",(support as IFeature)==null?null:((IFeature)support).Name,
            "model_to_sketch_transform",sketch.ModelToSketchTransform.ArrayData,"entities",entities,
            "relations",relations,"constraint_status",sketch.GetConstrainedStatus(),"fully_defined",sketch.GetConstrainedStatus()==3,
            "region_count",sketch.GetSketchRegionCount(),"section_area_mm2",section[1]*1e6,"section_center_world_mm",Scale(section.Skip(2).Take(3).ToArray(),1000));
    }
    Dictionary<string,object> Measure(IModelDoc2 doc, string label, bool scanSketches)
    {
        int bodies=Array(((IPartDoc)doc).GetBodies2(0,false)).Length;
        var row=Row("label",label,"units_code",doc.Extension.GetUserPreferenceInteger(263,0),
            "configuration",doc.IGetActiveConfiguration().Name,"body_count",bodies,"volume_mm3",null,"center_of_mass_mm",null);
        if (bodies > 0)
        {
            var mass = (IMassProperty2)doc.Extension.CreateMassProperty2();
            Check(mass != null,"Create mass properties");
            mass.UseSystemUnits=true;
            Check(mass.Recalculate(),"Recalculate mass properties");
            row["volume_mm3"]=mass.Volume*1e9;
            row["center_of_mass_mm"]=Scale((double[])mass.CenterOfMass,1000);
        }
        if (!scanSketches) return row;
        var tree=new List<object>();
        var sketches=new List<object>();
        foreach(var f in Features(doc))
        {
            bool warning=false;
            int code=f.GetErrorCode2(out warning);
            Check(code == 0,"Feature " + f.Name + " error/warning code " + code);
            var dimensions=Dimensions(f).Select(d=>Row("name",d.Name,"full_name",d.FullName,"driven_state",d.DrivenState,"system_value",d.SystemValue)).ToArray();
            var definition=f.GetDefinition();
            var ext=definition as IExtrudeFeatureData2;
            var revolve=definition as IRevolveFeatureData2;
            object operation=null;
            if (ext != null) operation=Row("end_condition",ext.GetEndCondition(true),"depth_m",ext.GetDepth(true),"reverse_direction",ext.ReverseDirection,"both_directions",ext.BothDirections);
            if (revolve != null) operation=Row("angle_rad",revolve.GetRevolutionAngle(true),"reverse_direction",revolve.ReverseDirection,"axis_type",revolve.GetAxisType());
            tree.Add(Row("name",f.Name,"type",f.GetTypeName2(),"suppressed",f.IsSuppressed(),"error_code",code,"warning",warning,"dimensions",dimensions,"operation",operation));
            if (f.GetTypeName2()=="ProfileFeature") sketches.Add(DescribeSketch(doc,f,(ISketch)f.GetSpecificFeature2()));
        }
        var equations=doc.GetEquationMgr();
        row["feature_tree"]=tree;
        row["sketches"]=sketches;
        row["equations"]=Enumerable.Range(0,equations.GetCount()).Select(i=>equations.Equation[i]).ToArray();
        return row;
    }
    Dictionary<string,object> Control(string label)
    {
        var path=Path.Combine(repo,"re","solidworks","examples",".SLDPRT","example.SLDPRT");
        object status;
        var doc=Open(path,out status,true);
        try
        {
            Rebuild(doc);
            var row=Measure(doc,label,false);
            Check((int)row["body_count"]>0 && (double)row["volume_mm3"]>0,"Healthy control " + label);
            row["native_sha256"]=Hash(path);
            row["open_status"]=status;
            Console.WriteLine("Control " + label + " volume " + row["volume_mm3"]);
            return row;
        }
        finally { Close(doc); }
    }
    static void Set(IModelDoc2 doc, string name, double value)
    {
        var d=Features(doc).SelectMany(Dimensions).Single(dim=>dim.Name==name);
        int status=d.SetSystemValue3(value,1,null);
        Check(status==0 && Math.Abs(d.SystemValue-value)<1e-8,"Set " + name + ": " + status+" value "+d.SystemValue);
        Rebuild(doc);
    }
    Dictionary<string,object> Reopen(string path)
    {
        object status;
        var doc=Open(path,out status);
        try
        {
            Rebuild(doc);
            var row=Measure(doc,"reopened and rebuilt",true);
            row["open_status"]=status;
            return row;
        }
        finally { Close(doc); }
    }
    static string Filename(string id, string suffix) { return id + "-solidworks-" + suffix + ".SLDPRT"; }
    string Basis(string id) { return id=="P05"?"XZ":"XY"; }
    void First(Dictionary<string,object> recipe)
    {
        var id=(string)recipe["id"];
        var dir=Path.Combine(output,id);
        Directory.CreateDirectory(dir);
        var observations=Row("healthy_control_before",Control("before"));
        var doc=Build(id,Basis(id),false,false);
        try
        {
            observations["baseline"]=Measure(doc,"as built",true);
            var save=Save(doc,Path.Combine(dir,Filename(id,"baseline-a")),false);
            Write(Path.Combine(dir,"first.json"),Row("observations",observations,"first_save",save,"authoring_process_id",app.GetProcessID()));
        }
        finally { Close(doc); }
    }
    void Second(Dictionary<string,object> recipe)
    {
        var id=(string)recipe["id"];
        var dir=Path.Combine(output,id);
        var first=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(dir,"first.json")));
        var observations=(Dictionary<string,object>)first["observations"];
        var saves=new List<Dictionary<string,object>> { (Dictionary<string,object>)first["first_save"] };
        var initial=(Dictionary<string,object>)recipe["driving_parameters"];
        var edits=new List<object>();
        var variants=new List<object>();
        string basis=Basis(id);
        Func<string,string> path=suffix=>Path.Combine(dir,Filename(id,suffix));
        object status;
        Check(Convert.ToInt32(first["authoring_process_id"])!=app.GetProcessID(),"Baseline repeat requires a fresh SOLIDWORKS process");
        Check(Hash(path("baseline-a"))==(string)saves[0]["sha256"],"Baseline A hash changed");
        var doc=Open(path("baseline-a"),out status);
        try
        {
            observations["fresh_reopen"]=Row("open_status",status,"measurements",Measure(doc,"baseline A as opened",true));
            Rebuild(doc);
            observations["unchanged_rebuild"]=Measure(doc,"baseline A after rebuild",true);
            saves.Add(Save(doc,path("baseline-b"),true));
            foreach(var edit in Array(recipe["independent_edits"]).Cast<Dictionary<string,object>>())
            {
                string name=(string)edit["parameter"];
                double multiplier=name=="angle_deg"?Math.PI/180:.001;
                var suffix="edit-"+name+"-"+edit["value"];
                Set(doc,name,Convert.ToDouble(edit["value"])*multiplier);
                var changed=Measure(doc,suffix,true);
                saves.Add(Save(doc,path(suffix),true));
                Set(doc,name,Convert.ToDouble(initial[name])*multiplier);
                edits.Add(Row("parameter",name,"edited",changed,"restored",Measure(doc,"restored "+name,true),"saved_file",Filename(id,suffix)));
            }
            Units(doc,3);
            Rebuild(doc);
            variants.Add(Row("variant","units-inch","reading",Measure(doc,"inch display units",true)));
            saves.Add(Save(doc,path("units-inch"),true));
        }
        finally { Close(doc); }
        if (id != "P05") CaptureVariant(id,dir,"plane-yz","YZ",false,false,saves,variants);
        if (id == "P03") CaptureVariant(id,dir,"direction-negative",basis,true,false,saves,variants);
        if (id == "P04") CaptureVariant(id,dir,"termination-through-all",basis,false,true,saves,variants);
        observations["edits"]=edits;
        observations["variants"]=variants;
        var reopened=new Dictionary<string,object>();
        foreach(var save in saves)
        {
            var file=(string)save["file"];
            var saved=Path.Combine(dir,file);
            reopened[file]=Reopen(saved);
            Check(Hash(saved)==(string)save["sha256"],"Saved bytes changed during reopen " + file);
        }
        observations["reopened_files"]=reopened;
        observations["healthy_control_after"]=Control("after");
        var measurements=Path.Combine(dir,"measurements.json");
        var binary=System.Diagnostics.Process.GetProcessById(app.GetProcessID()).MainModule.FileVersionInfo.FileVersion;
        Write(measurements,Row("recipe_id",id,"application","SOLIDWORKS 2026","exact_application_build",app.RevisionNumber(),"executable_file_version",binary,
            "specifications_sha256",Hash(spec),"authoring_origin","Independently authored in SOLIDWORKS from PairSpecs.json through the SOLIDWORKS API.",
            "world_basis",basis,"authoring_process_id",first["authoring_process_id"],"reopen_process_id",app.GetProcessID(),
            "observations",observations,"saves",saves,"errors",new object[0]));
        Write(Path.Combine(dir,"receipt.json"),Row("recipe_id",id,"measurements","measurements.json","measurement_receipt_sha256",Hash(measurements),"native_files",saves,"errors",0));
    }
    void CaptureVariant(string id, string dir, string suffix, string basis, bool reverse, bool through,
        List<Dictionary<string,object>> saves, List<object> variants)
    {
        var built=Build(id,basis,reverse,through);
        try
        {
            variants.Add(Row("variant",suffix,"reading",Measure(built,suffix,true)));
            saves.Add(Save(built,Path.Combine(dir,Filename(id,suffix)),false));
        }
        finally { Close(built); }
    }
    public static void Run(string repo, string output, string recipe, string phase)
    {
        var run=new SolidWorksCapture(repo,output);
        if (phase=="exit")
        {
            Check(run.app.GetDocumentCount()==0,"SOLIDWORKS contains open documents");
            Console.WriteLine("Ending empty SOLIDWORKS capture process " + run.app.GetProcessID());
            run.app.ExitApp();
            return;
        }
        bool preference=run.app.GetUserPreferenceToggle(10);
        run.app.SetUserPreferenceToggle(10,false);
        try
        {
            foreach(var row in run.recipes.Where(r=>recipe=="" || (string)r["id"]==recipe))
            {
                Console.WriteLine(phase + " " + row["id"]);
                if(phase=="first") run.First(row);
                else if(phase=="second") run.Second(row);
                else if(phase=="build")
                {
                    var doc=run.Build((string)row["id"],run.Basis((string)row["id"]),false,false);
                    try { Console.WriteLine(Json.Serialize(run.Measure(doc,"as built",true))); }
                    finally { run.Close(doc); }
                }
                else throw new ArgumentException("Unknown phase "+phase);
            }
        }
        finally { run.app.SetUserPreferenceToggle(10,preference); }
    }
}
