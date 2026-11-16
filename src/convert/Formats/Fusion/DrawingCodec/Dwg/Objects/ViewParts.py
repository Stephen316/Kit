# eval value must remain consistent across callers so section boundaries and object references remain consistent
KEvalValue = (
    "BS ValueType; if ValueType==1 { TU TextValue } else { "
    "if ValueType==40 { BD RealValue } else { "
    "if ValueType==330 { H ObjectValue } else { Unsupported ValueType } } }"
)

# action head must remain consistent across callers so section boundaries and object references remain consistent
KActionHead = (
    "BS ClassVersion; BL GeometryStatus; H OwningNetwork; H ActionBody; "
    "BL ActionIndex; BL MaxDependencyIndex; BL DependencyCount; "
    "each Dependencies DependencyCount { B IsOwned; H Dependency }; "
    "BL ActionLongOne; BL OwnedParamCount; Hs OwnedParams OwnedParamCount; "
    "BL ActionLongTwo; BL ValueParamCount; "
    "each ValueParams ValueParamCount { BL ParamLongOne; TU ParamName; "
    "BL ParamLongTwo; BL ValueCount; each Values ValueCount { "
)

# assoc action must remain consistent across callers so section boundaries and object references remain consistent
KAssocAction = KActionHead + KEvalValue + " }; H ParamRefOne; H ParamRefTwo }; "

# assoc dependency must remain consistent across callers so section boundaries and object references remain consistent
KAssocDependency = (
    "BS ClassVersion; BL DependencyStatus; B IsReadDependency; "
    "B IsWriteDependency; B FlagThree; B FlagFour; BL EvalOrder; "
    "B HasCompoundId; if HasCompoundId==1 { TU CompoundClass; "
    "BL CompoundVersion; BL PathCount; each PathWords PathCount { RS PathWord } }; "
    "BL DependencyIndex; H DependentOn; "
    "if HasCompoundId==1 { Hs PathObjects PathCount }; "
    "H PrevDependency; H NextDependency; H DependencyBody; "
)

# action parameter must remain consistent across callers so section boundaries and object references remain consistent
KActionParam = "BS ParamVersion; BL ParamLong; TU ParamName; "

# single parameter must remain consistent across callers so section boundaries and object references remain consistent
KSingleParam = KActionParam + "BL SingleVersion; H Dependency; "

# cached curve must remain consistent across callers so section boundaries and object references remain consistent
KCachedCurve = (
    "BS CurveKind; if CurveKind==11 { 3BD Center; 3BD Normal; 3BD RefAxis; "
    "BD Radius; BD StartAngle; BD EndAngle; BD CurveReal } else { "
    "if CurveKind==23 { 3BD StartPoint; 3BD Direction } else { "
    "Unsupported CurveKind } }"
)

# action body must remain consistent across callers so section boundaries and object references remain consistent
KActionBody = "BS ClassVersion; "

# model doc style must remain consistent across callers so section boundaries and object references remain consistent
KModelDocStyle = (
    "BS DocVersion; TU Description; B IsModified; "
    "since AC1032 { TU DisplayName; BL DocFlags }; "
)

# label style must remain consistent across callers so section boundaries and object references remain consistent
KLabelStyle = (
    "H LabelTextStyle; CMC LabelTextColor; BD LabelTextHeight; "
    "BL LabelAttachment; BD LabelOffset; BL LabelAlignment; TU LabelPattern; "
)

# edge curve must remain consistent across callers so section boundaries and object references remain consistent
KEdgeCurve = "B HasCurve; if HasCurve==1 { " + KCachedCurve + " }; "

# source key must remain consistent across callers so section boundaries and object references remain consistent
KSourceKey = "BL GuidHead; BS GuidMiddle; BS GuidLow; Bytes GuidTail 8; B GuidFlag; "

# body key must remain consistent across callers so section boundaries and object references remain consistent
KBodyKey = "BL KeyLong; Bits KeyBits 40; B KeyFlag; "

# body path needs a stable location so native drawing reconstruction resolves inputs independently of the caller working directory
KBodyPath = "BL PathCount; each Path PathCount { BLL PathId }; "

# view body must remain consistent across callers so section boundaries and object references remain consistent
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

# view trailer must remain consistent across callers so section boundaries and object references remain consistent
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

# node table must remain consistent across callers so section boundaries and object references remain consistent
KNodeTable = (
    "BL NodeCount; BL TableLongA; BL TableLongB; B TableFlag; BL ClassCount; "
    "each NodeClasses ClassCount { TU ClassName }; BL ItemCount; "
    "each Nodes ItemCount { B NodeFlag; BL NodeClass; BL NodeKey }; "
    "zip NodeData Nodes { BL NodeId; BL RefCount; "
    "each Refs RefCount { BL RefId }; "
)

# external trans must remain consistent across callers so section boundaries and object references remain consistent
KExternalTrans = (
    "BL SubentType; BL EdgeId; BL TransLongA; BL TransLongB; B TransFlagA; "
    + "B TransFlagB; "
    + KEdgeCurve
    + "B TransFlagC; BL TransLongC; BL TransLongD; BL TransLongE; "
    + "BL TransLongF; BL TransLongG"
)

# external pers must remain consistent across callers so section boundaries and object references remain consistent
KExternalPers = "BL PersLongA; BL SubentType; BL PersIndex; BL PersLongB; BL PersLongC"

# projected edge must remain consistent across callers so section boundaries and object references remain consistent
KProjectedEdge = (
    "B EdgeFlag; BL SubentType; BL EdgeId; B EdgeFlagB; BL StartNode; "
    + "BL EndNode; "
    + KEdgeCurve
)

# projected vertex must remain consistent across callers so section boundaries and object references remain consistent
KProjectedVertex = (
    "B VertexFlag; BL SubentType; BL EdgeId; B VertexFlagB; BL VertexKind; "
    "BL VertexLong; 3BD VertexPoint"
)

# pers edge must remain consistent across callers so section boundaries and object references remain consistent
KPersEdge = (
    "BL PersLongA; B PersFlag; BL PersLongB; BL PersLongC; BL SubentType; "
    "BL PersIndex; BL PersLongD; BL PersLongE; BL PersLongF"
)

# pers vertex must remain consistent across callers so section boundaries and object references remain consistent
KPersVertex = (
    "B PersFlag; B PersFlagB; BL PersLongA; BL VertexSlot; BL PersLongC; "
    "BL SubentType; BL PersLongD"
)
