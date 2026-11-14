from convert.formats.Fusion.DrawingCodec.Dwg.Objects.StandardSpecs import (
    KStandardSpecs,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.ViewParts import (
    KActionBody,
    KActionParam,
    KAssocAction,
    KAssocDependency,
    KCachedCurve,
    KExternalPers,
    KExternalTrans,
    KLabelStyle,
    KModelDocStyle,
    KNodeTable,
    KPersEdge,
    KPersVertex,
    KProjectedEdge,
    KProjectedVertex,
    KSingleParam,
    KSourceKey,
    KViewBody,
    KViewTrailer,
)

KViewSpecs: dict[str, str] = {
    "ACDBASSOCNETWORK": KAssocAction
    + "BL NetworkVersion; BL MaxActionIndex; BL ActionCount; "
    + "each Actions ActionCount { B IsOwned; H Action }; BL ErasedCount",
    "ACDBASSOCACTION": KAssocAction,
    "ACDBASSOCDEPENDENCY": KAssocDependency,
    "ACDBASSOCGEOMDEPENDENCY": KAssocDependency
    + "BL GeomVersion; BL GeomLongTwo; BL GeomLongThree; BL GeomLongFour; "
    + "BL SubentType; BL SubentIndex; B GeomFlag",
    "ACDBASSOCOBJECTACTIONPARAM": KSingleParam + "BL ObjectVersion",
    "ACDBASSOCVIEWBORDERACTIONPARAM": KSingleParam
    + "BL ObjectVersion; BL BorderVersion",
    "ACDBASSOCVIEWREPACTIONPARAM": KSingleParam + "BL ObjectVersion; BL ViewVersion",
    "ACDBASSOCVERTEXACTIONPARAM": KSingleParam + "BL VertexVersion; 3BD VertexPoint",
    "ACDBASSOCEDGEACTIONPARAM": KSingleParam
    + "BL EdgeVersion; B HasCurve; if HasCurve==1 { "
    + KCachedCurve
    + " }; H EdgeObject",
    "ACDBASSOCOSNAPPOINTREFACTIONPARAM": KActionParam
    + "BL CompoundVersion; BL CompoundLong; BL ChildCount; "
    + "Hs ChildParams ChildCount; BL PointLongOne; BL PointLongTwo; "
    + "BL PointLongThree; BL PointLongFour; RC OsnapMode; BD NearParam; "
    + "H PointObject; H PointParam; H PeerParam",
    "ACDBASSOCVIEWREPHATCHMANAGER": KActionParam
    + "BL ManagerVersion; BL ManagerLongTwo; BL ManagerLongThree; "
    + "BL ManagerLongFour; BL ManagerLongFive",
    "ACDBASSOCVIEWREPACTIONBODY": KActionBody
    + "BL BodyVersion; BL ViewKind; BD ViewAngle; H ViewRep",
    "AcDbCenterMarkActionBody": KActionBody + "BL CenterVersion",
    "ACDBASSOCROTATEDDIMACTIONBODY": KActionBody
    + "BL AnnotationVersion; H AnnotationDependency; BL DimensionVersion; "
    + "H FirstPointParam; H SecondPointParam",
    "ACDBVIEWREPBLOCKREFERENCE": KStandardSpecs["INSERT"] + "; H Viewport",
    "ACDBVIEWREPORIENTATION": "3BD EyePoint; 3BD TargetPoint; 3BD UpVector",
    "ACDBVIEWREPORIENTATIONDEF": "",
    "ACDBVIEWREPFUSIONSOURCE": "",
    "DRAWINGVIEW": "BS ClassVersion; 2RD BorderMin; 2RD BorderMax; RD ViewScale; "
    + "RD RealSix; 2RD ViewCenter; H Viewport; H ScaleObject",
    "ACDBDETAILVIEWSTYLE": KModelDocStyle
    + "BS DetailVersion; BL DetailFlags; H IdentifierStyle; CMC IdentifierColor; "
    + "BD IdentifierHeight; BD IdentifierOffset; RC IdentifierPlacement; "
    + "H ArrowSymbol; CMC ArrowColor; BD ArrowSize; TU IdentifierExclude; "
    + "H BoundaryLineType; BL BoundaryLineWeight; CMC BoundaryLineColor; "
    + KLabelStyle
    + "H ConnectionLineType; BL ConnectionLineWeight; CMC ConnectionLineColor; "
    + "H BorderLineType; BL BorderLineWeight; CMC BorderLineColor; RC ModelEdge",
    "ACDBSECTIONVIEWSTYLE": KModelDocStyle
    + "BS SectionVersion; BL SectionFlags; H IdentifierStyle; CMC IdentifierColor; "
    + "BD IdentifierHeight; H ArrowStartSymbol; H ArrowEndSymbol; CMC ArrowColor; "
    + "BD ArrowSize; TU IdentifierExclude; BD ArrowExtension; H PlaneLineType; "
    + "BL PlaneLineWeight; CMC PlaneLineColor; H BendLineType; BL BendLineWeight; "
    + "CMC BendLineColor; BD BendLineLength; BD EndLineOvershoot; "
    + KLabelStyle
    + "CMC HatchColor; CMC HatchBackColor; TU HatchPattern; BD HatchScale; "
    + "BL HatchTransparency; B FlagOne; B FlagTwo; BL SectionLongOne; "
    + "BD SectionRealOne; BL SectionLongTwo; BD SectionRealTwo; BL HatchAngleCount; "
    + "each HatchAngles HatchAngleCount { BD HatchAngle }",
    "ACDBVIEWREPSTANDARD": "BS StandardVersion; BL StandardLongOne; "
    + "BL StandardLongTwo; BL StandardLongThree; BL StandardLongFour; "
    + "BL StandardLongFive",
    "ACDBSYNERGYMAPPINGS": "BL SourceMappingCount; if SourceMappingCount!=0 { "
    + "Unsupported SourceMappingCount }; BL LayerMappingCount; "
    + "each LayerMappings LayerMappingCount { BL EdgeCategory; H Layer }",
    "ACDBREFERENCEDATA": "B FlagOne; BL LongOne; B FlagTwo; BL LongTwo; "
    + "B FlagThree; BL LongThree; TU TextOne; TU TextTwo; TU TextThree; "
    + "TU TextFour; TU TextFive",
    "ACDBASSOCINVENTORPERSSUBENTIDMANAGER": "BL ManagerVersion; B ManagerFlag; "
    + "BL ManagerLong; RL ManagerRaw; BL ManagerCount; TU SourceKey; H ViewRep",
    "ACDBVIEWREPSOURCEMGR": "B SourceFlag; BL SourceLong",
    "ACDBVIEWREP": "BS ClassVersion; BL ViewLongA; BL ViewLongB; BL ViewLongC; "
    + "BL ViewFlags; BL ViewLongD; BL ViewLongE; BLL ViewRepKey; B ViewFlagA; "
    + "BL BodyCount; each Bodies BodyCount { "
    + KViewBody
    + "}; "
    + KViewTrailer,
    "ACDBASSOCEXTERNALPERSSUBENTIDHOLDER": "BL HolderLong; B SourceFlag; "
    + KSourceKey
    + KNodeTable
    + "if NodeClass==1 { "
    + KExternalTrans
    + " } else { if NodeClass==2 { "
    + KExternalPers
    + " } else { Unsupported NodeClass } } }; H Manager",
    "ACDBASSOCPROJECTEDENTITYPERSSUBENTIDHOLDER": "BL HolderVersion; "
    + "BL HolderLongA; BL HolderLongB; B HasCompoundId; if HasCompoundId==1 { "
    + "TU CompoundClass; BL CompoundVersion; BL PathCount; "
    + "each PathWords PathCount { RS PathWord }; Hs PathObjects PathCount }; "
    + "B SourceFlag; "
    + KSourceKey
    + "BL ProjLong; Bits ProjBits 73; "
    + KNodeTable
    + "if NodeClass==1 { "
    + KProjectedEdge
    + " } else { if NodeClass==2 { "
    + KProjectedVertex
    + " } else { if NodeClass==3 { "
    + KPersEdge
    + " } else { if NodeClass==4 { "
    + KPersVertex
    + " } else { Unsupported NodeClass } } } } }; H ViewRep",
}
