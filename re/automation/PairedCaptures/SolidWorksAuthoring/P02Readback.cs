// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.Linq;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public sealed partial class P04Readback
{
    bool IsOwnedEntity(object Candidate, object Expected)
    {
        var SeenPoint = Candidate as ISketchPoint;
        var KnownPoint = Expected as ISketchPoint;
        if (SeenPoint != null && KnownPoint != null)
            return Same(SeenPoint, KnownPoint)
                || (Same(SeenPoint.GetSketch(), KnownPoint.GetSketch())
                    && Items(SeenPoint.GetID()).SequenceEqual(Items(KnownPoint.GetID())));
        var SeenCurve = Candidate as ISketchSegment;
        var KnownCurve = Expected as ISketchSegment;
        return SeenCurve != null && KnownCurve != null
            && (Same(SeenCurve, KnownCurve)
                || (SeenCurve.GetType() == KnownCurve.GetType()
                    && Same(SeenCurve.GetSketch(), KnownCurve.GetSketch())
                    && Items(SeenCurve.GetID()).SequenceEqual(Items(KnownCurve.GetID()))));
    }

    Dictionary<string, object> CircleDimension(IFeature Profile, ISketch SketchCurve,
        ISketchSegment Circle, Dictionary<string, ISketch> Owners)
    {
        var Values = new List<IDisplayDimension>();
        for (object Current = Profile.GetFirstDisplayDimension(); Current != null;
             Current = Profile.GetNextDisplayDimension(Current))
            Values.Add((IDisplayDimension)Current);
        Require(Values.Count == 1, "Expected exactly one displayed dimension on the saved circle");
        var Display = Values[0];
        var Value = Display.GetDimension2(0) as IDimension;
        Require(Value != null, "The circle's display dimension has no underlying model dimension");
        var Witness = (Dictionary<string, object>)Dimension(Display, Value, Profile, SketchCurve, Owners);
        var Annotation = Display.GetAnnotation() as IAnnotation;
        var Targets = Annotation == null ? new object[0] : Items(Annotation.GetAttachedEntities3());
        Witness["targets_circle"] = Targets.Length == 1 && IsOwnedEntity(Targets[0], Circle);
        Witness["verified"] = Value.Name == "diameter_mm" && Display.Type2 == (int)swDimensionType_e.swDiameterDimension
            && Value.DrivenState == (int)swDimensionDrivenState_e.swDimensionDriving
            && Same(Value.GetFeatureOwner(), Profile) && Annotation != null && !Annotation.IsDangling()
            && Annotation.GetAttachedEntityCount3() == Targets.Length && (bool)Witness["targets_circle"];
        return Witness;
    }

    bool HasPointPair(object[] Targets, ISketchPoint Center, ISketchPoint Origin)
    {
        return Targets.Length == 2 && Targets.Count(Target => IsOwnedEntity(Target, Center)) == 1
            && Targets.Count(Target => IsOwnedEntity(Target, Origin)) == 1;
    }

    object CircleRelation(ISketchRelation RelationItem, ISketch SketchCurve,
        Dictionary<string, ISketch> Owners, ISketchPoint Center, ISketchPoint Origin, ISketchSegment Circle)
    {
        var Witness = (Dictionary<string, object>)Relation(RelationItem, SketchCurve, Owners);
        var Targets = Items(RelationItem.GetDefinitionEntities2());
        var Kind = RelationItem.GetRelationType();
        Witness["verified"] = Kind == (int)swConstraintType_e.swConstraintType_COINCIDENT
            ? HasPointPair(Targets, Center, Origin)
            : Kind == (int)swConstraintType_e.swConstraintType_DIAMETER
              && Targets.Length == 1 && IsOwnedEntity(Targets[0], Circle);
        return Witness;
    }

    double[] CircleSection(IModelDoc2 Model, IFeature Profile, ISketch SketchCurve)
    {
        Model.ClearSelection2(true);
        try
        {
            Require(Profile.Select2(false, 0), "Selecting the circle sketch for section measurement failed");
            var Section = Model.Extension.GetSectionProperties2(new object[] { (IFeature)SketchCurve }) as double[];
            Require(Section != null && Section.Length >= 5 && Section[0] == 0,
                "SOLIDWORKS did not return the circle section properties");
            return Section;
        }
        finally
        {
            Model.ClearSelection2(true);
        }
    }

    bool IsNearPoint(double[] Coordinates, double[] Expected)
    {
        return Coordinates.Length == Expected.Length
            && Coordinates.Zip(Expected, (First, Second) => Math.Abs(First - Second) <= 1e-9).All(InRange => InRange);
    }

    bool HasCircleData(double Radius, double Diameter, double[] Center, double[] Section, string FileName)
    {
        var Expected = FileName == "P02-solidworks-edit-diameter_mm-16.SLDPRT" ? .016 : .010;
        var Area = Math.PI * Radius * Radius;
        var ZeroPoint = new[] { 0.0, 0.0, 0.0 };
        return Math.Abs(Diameter - Expected) <= 1e-9 && Math.Abs(2 * Radius - Diameter) <= 1e-9
            && Math.Abs(Section[1] - Area) <= 1e-12 && IsNearPoint(Center, ZeroPoint)
            && IsNearPoint(Section.Skip(2).Take(3).ToArray(), ZeroPoint);
    }

    Dictionary<string, object> ObserveCircle(IModelDoc2 Model, string FileName)
    {
        var Profile = NamedFeature(Model, "CircleSketch", "ProfileFeature");
        var Origin = NamedFeature(Model, "Origin", "OriginProfileFeature");
        var SketchCurve = (ISketch)Profile.GetSpecificFeature2();
        var OriginSketch = (ISketch)Origin.GetSpecificFeature2();
        var OriginPoint = Items(OriginSketch.GetSketchPoints2()).Cast<ISketchPoint>().Single();
        var Circle = Items(SketchCurve.GetSketchSegments()).Cast<ISketchSegment>().Single();
        var CircleArc = Circle as ISketchArc;
        Require(CircleArc != null && CircleArc.IsCircle() != 0 && !Circle.ConstructionGeometry,
            "The saved profile does not contain one authored full circle");
        var CenterPoint = (ISketchPoint)CircleArc.IGetCenterPoint2();
        var Owners = new Dictionary<string, ISketch> { { Profile.Name, SketchCurve }, { Origin.Name, OriginSketch } };
        var DimensionRow = CircleDimension(Profile, SketchCurve, Circle, Owners);
        var Relations = Items(SketchCurve.RelationManager.GetRelations(0)).Cast<ISketchRelation>().ToArray();
        var RelationRows = Relations.Select(Item => (Dictionary<string, object>)CircleRelation(
            Item, SketchCurve, Owners, CenterPoint, OriginPoint, Circle)).ToArray();
        var Reading = CircleState(Model, FileName, Profile, SketchCurve, CircleArc, CenterPoint, DimensionRow);
        Reading["circle"] = Participant(Circle, SketchCurve, Owners);
        Reading["center_point"] = Participant(CenterPoint, SketchCurve, Owners);
        Reading["origin_point"] = Participant(OriginPoint, SketchCurve, Owners);
        Reading["dimension"] = DimensionRow;
        Reading["relations"] = RelationRows;
        Reading["verified"] = (bool)Reading["profile_verified"] && (bool)DimensionRow["verified"]
            && Relations.Length == 2 && Relations.Select(Item => Item.GetRelationType()).Distinct().Count() == 2
            && RelationRows.All(Item => (bool)Item["verified"]);
        return Reading;
    }

    Dictionary<string, object> CircleState(IModelDoc2 Model, string FileName, IFeature Profile, ISketch SketchCurve,
        ISketchArc CircleArc, ISketchPoint CenterPoint, Dictionary<string, object> DimensionRow)
    {
        int SupportType = 0;
        var Support = SketchCurve.GetReferenceEntity(ref SupportType) as IFeature;
        var Inverse = SketchCurve.ModelToSketchTransform.IInverse();
        var CenterWorld = WorldPoint(new[] { CenterPoint.X, CenterPoint.Y, CenterPoint.Z }, Inverse);
        var Section = CircleSection(Model, Profile, SketchCurve);
        var Radius = CircleArc.GetRadius();
        var BodyCount = Items(((IPartDoc)Model).GetBodies2((int)swBodyType_e.swSolidBody, false)).Length;
        var Units = Model.Extension.GetUserPreferenceInteger(263, 0);
        bool Warning;
        var FeatureError = Profile.GetErrorCode2(out Warning);
        var ExpectedDatum = FileName == "P02-solidworks-plane-yz.SLDPRT" ? "Right Plane" : "Front Plane";
        var ExpectedUnits = FileName == "P02-solidworks-units-inch.SLDPRT" ? 3 : 5;
        var Verified = Support != null && Support.GetTypeName2() == "RefPlane" && Support.Name == ExpectedDatum
            && Units == ExpectedUnits && SketchCurve.GetConstrainedStatus() == 3 && SketchCurve.GetSketchRegionCount() == 1
            && BodyCount == 0 && FeatureError == 0 && !Warning
            && HasCircleData(Radius, (double)DimensionRow["system_value"], CenterWorld, Section, FileName);
        return Row("profile_verified", Verified, "feature", Feature(Profile), "feature_error", FeatureError,
            "feature_warning", Warning, "support", Feature(Support), "support_type", SupportType,
            "constraint_status", SketchCurve.GetConstrainedStatus(), "region_count", SketchCurve.GetSketchRegionCount(),
            "units_code", Units, "solid_body_count", BodyCount, "radius_m", Radius, "center_world_m", CenterWorld,
            "model_to_sketch_transform", SketchCurve.ModelToSketchTransform.ArrayData, "section_area_m2", Section[1],
            "section_center_world_m", Section.Skip(2).Take(3).ToArray());
    }
}
