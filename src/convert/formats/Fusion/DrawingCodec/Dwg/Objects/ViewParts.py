KEvalValue = (
    "BS ValueType; if ValueType==1 { TU TextValue } else { "
    "if ValueType==40 { BD RealValue } else { "
    "if ValueType==330 { H ObjectValue } else { Unsupported ValueType } } }"
)
KActionHead = (
    "BS ClassVersion; BL GeometryStatus; H OwningNetwork; H ActionBody; "
    "BL ActionIndex; BL MaxDependencyIndex; BL DependencyCount; "
    "each Dependencies DependencyCount { B IsOwned; H Dependency }; "
    "BL ActionLongOne; BL OwnedParamCount; Hs OwnedParams OwnedParamCount; "
    "BL ActionLongTwo; BL ValueParamCount; "
    "each ValueParams ValueParamCount { BL ParamLongOne; TU ParamName; "
    "BL ParamLongTwo; BL ValueCount; each Values ValueCount { "
)
KAssocAction = KActionHead + KEvalValue + " }; H ParamRefOne; H ParamRefTwo }; "
KAssocDependency = (
    "BS ClassVersion; BL DependencyStatus; B IsReadDependency; "
    "B IsWriteDependency; B FlagThree; B FlagFour; BL EvalOrder; "
    "B HasCompoundId; if HasCompoundId==1 { TU CompoundClass; "
    "BL CompoundVersion; BL PathCount; each PathWords PathCount { RS PathWord } }; "
    "BL DependencyIndex; H DependentOn; "
    "if HasCompoundId==1 { Hs PathObjects PathCount }; "
    "H PrevDependency; H NextDependency; H DependencyBody; "
)
KActionParam = "BS ParamVersion; BL ParamLong; TU ParamName; "
KSingleParam = KActionParam + "BL SingleVersion; H Dependency; "
KCachedCurve = (
    "BS CurveKind; if CurveKind==11 { 3BD Center; 3BD Normal; 3BD RefAxis; "
    "BD Radius; BD StartAngle; BD EndAngle; BD CurveReal } else { "
    "if CurveKind==23 { 3BD StartPoint; 3BD Direction } else { "
    "Unsupported CurveKind } }"
)
KActionBody = "BS ClassVersion; "
KModelDocStyle = (
    "BS DocVersion; TU Description; B IsModified; "
    "since AC1032 { TU DisplayName; BL DocFlags }; "
)
KLabelStyle = (
    "H LabelTextStyle; CMC LabelTextColor; BD LabelTextHeight; "
    "BL LabelAttachment; BD LabelOffset; BL LabelAlignment; TU LabelPattern; "
)
KEdgeCurve = "B HasCurve; if HasCurve==1 { " + KCachedCurve + " }; "
KSourceKey = "BL GuidHead; BS GuidMiddle; BS GuidLow; Bytes GuidTail 8; B GuidFlag; "
KBodyKey = "BL KeyLong; Bits KeyBits 40; B KeyFlag; "
KBodyPath = "BL PathCount; each Path PathCount { BLL PathId }; "
KViewBody = (
    KBodyKey
    + KSourceKey
    + "Bits MatrixHead 7; BD MatrixXX; BD MatrixXY; BD MatrixXZ; BD OffsetX; "
    + "BD MatrixYX; BD MatrixYY; BD MatrixYZ; BD OffsetY; BD MatrixZX; "
    + "BD MatrixZY; BD MatrixZZ; BD OffsetZ; BL BodyLongA; BL BodyLongB; "
    + "BL BodyLongC; B BodyFlagA; B BodyFlagB; "
    + KBodyPath
    + "BL BodyLongD; BL BodyLongE; BL EdgeCount; each Edges EdgeCount { "
    + "BL EdgeId; BL EdgeLongA; BL EdgeLongB; B EdgeFlagA; BL EdgeLongC; "
    + KEdgeCurve
    + "B EdgeFlagB; H EdgeEntity }; "
)
KViewTrailer = (
    "2RD ViewCenter; BL TrailLongA; B TrailFlagA; BL TrailLongB; "
    + "BL TrailLongC; BL TrailLongD; B TrailFlagB; BL HolderCount; "
    + "each HolderKeys HolderCount { "
    + KBodyKey
    + "}; BL BodyKeyCount; each BodyKeys BodyKeyCount { "
    + KBodyKey
    + "BL KeyLongB; "
    + KBodyPath
    + "B KeyFlagB }; TU TextA; TU TextB; H BlockRef; H DrawingView; "
    + "H FusionSource; H Orientation; H OrientationDef; H NullA; H Viewport; "
    + "H NullB; H SelfRef; H ModelBlockRef; H NullC; "
    + "Hs ProjectedHolders HolderCount; H NullD"
)
KNodeTable = (
    "BL NodeCount; BL TableLongA; BL TableLongB; B TableFlag; BL ClassCount; "
    "each NodeClasses ClassCount { TU ClassName }; BL ItemCount; "
    "each Nodes ItemCount { B NodeFlag; BL NodeClass; BL NodeKey }; "
    "zip NodeData Nodes { BL NodeId; BL RefCount; "
    "each Refs RefCount { BL RefId }; "
)
KExternalTrans = (
    "BL SubentType; BL EdgeId; BL TransLongA; BL TransLongB; B TransFlagA; "
    + "B TransFlagB; "
    + KEdgeCurve
    + "B TransFlagC; BL TransLongC; BL TransLongD; BL TransLongE; "
    + "BL TransLongF; BL TransLongG"
)
KExternalPers = "BL PersLongA; BL SubentType; BL PersIndex; BL PersLongB; BL PersLongC"
KProjectedEdge = (
    "B EdgeFlag; BL SubentType; BL EdgeId; B EdgeFlagB; BL StartNode; "
    + "BL EndNode; "
    + KEdgeCurve
)
KProjectedVertex = (
    "B VertexFlag; BL SubentType; BL EdgeId; B VertexFlagB; BL VertexKind; "
    "BL VertexLong; 3BD VertexPoint"
)
KPersEdge = (
    "BL PersLongA; B PersFlag; BL PersLongB; BL PersLongC; BL SubentType; "
    "BL PersIndex; BL PersLongD; BL PersLongE; BL PersLongF"
)
KPersVertex = (
    "B PersFlag; B PersFlagB; BL PersLongA; BL VertexSlot; BL PersLongC; "
    "BL SubentType; BL PersLongD"
)
