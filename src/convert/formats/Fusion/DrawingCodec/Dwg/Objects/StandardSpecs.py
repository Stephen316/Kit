from convert.formats.Fusion.DrawingCodec.Dwg.Objects.SpecParts import (
    KAttribCommon,
    KControlCommon,
    KDimCommon,
    KEntityCommon,
    KFieldValue,
    KMtextCommon,
    KPlotCommon,
    KTableCommon,
    KTextCommon,
)

KStandardSpecs = {
    "Object": "BL ReactorCount; B NoXdic; B HasDsData; H Owner; Hs Reactors ReactorCount; if NoXdic==0 { H Xdic }",
    "Entity": KEntityCommon,
    "LINE": "B ZeroDepth; RD StartX; DD EndX StartX; RD StartY; DD EndY StartY; if ZeroDepth==0 { RD StartZ; DD EndZ StartZ }; BT Thickness; B UnitExtrusion; if UnitExtrusion==0 { 3BD Extrusion }",
    "SOLID": "BT Thickness; BD Elevation; 2RD CornerOne; 2RD CornerTwo; 2RD CornerThree; 2RD CornerFour; BE Extrusion",
    "CIRCLE": "3BD Center; BD Radius; BT Thickness; BE Extrusion",
    "ARC": "3BD Center; BD Radius; BT Thickness; BE Extrusion; BD StartAngle; BD EndAngle",
    "POINT": "BD PointX; BD PointY; BD PointZ; BT Thickness; BE Extrusion; BD AxisAngle",
    "TEXT": KTextCommon,
    "ATTRIB": KTextCommon + KAttribCommon,
    "ATTDEF": KTextCommon + KAttribCommon + "RC DefVersion; TU Prompt",
    "BLOCK": "TU BlockName",
    "ENDBLK": "",
    "SEQEND": "",
    "INSERT": "3BD Insertion; BB ScaleFlags; if ScaleFlags==0 { RD ScaleX; DD ScaleY ScaleX; DD ScaleZ ScaleX }; if ScaleFlags==1 { DD ScaleY 1.0; DD ScaleZ 1.0 }; if ScaleFlags==2 { RD ScaleX }; BD Rotation; 3BD Extrusion; B HasAttribs; if HasAttribs==1 { BL OwnedCount }; H BlockHeader; if HasAttribs==1 { Hs Attribs OwnedCount; H SeqEnd }",
    "MTEXT": KMtextCommon,
    "DIMENSION_LINEAR": KDimCommon
    + "3BD PointThirteen; 3BD PointFourteen; 3BD PointTen; BD ExtRotation; BD DimRotation; H DimStyle; H DimBlock",
    "DIMENSION_ALIGNED": KDimCommon
    + "3BD PointThirteen; 3BD PointFourteen; 3BD PointTen; BD ExtRotation; H DimStyle; H DimBlock",
    "DIMENSION_ORDINATE": KDimCommon
    + "3BD PointTen; 3BD PointThirteen; 3BD PointFourteen; RC OrdinateFlags; H DimStyle; H DimBlock",
    "DIMENSION_RADIUS": KDimCommon
    + "3BD PointTen; 3BD PointFifteen; BD LeaderLength; H DimStyle; H DimBlock",
    "DIMENSION_DIAMETER": KDimCommon
    + "3BD PointTen; 3BD PointFifteen; BD LeaderLength; H DimStyle; H DimBlock",
    "DIMENSION_ANG3PT": KDimCommon
    + "3BD PointTen; 3BD PointThirteen; 3BD PointFourteen; 3BD PointFifteen; H DimStyle; H DimBlock",
    "DIMENSION_ANG2LN": KDimCommon
    + "2RD PointSixteen; 3BD PointThirteen; 3BD PointFourteen; 3BD PointFifteen; 3BD PointTen; H DimStyle; H DimBlock",
    "VIEWPORT": "3BD Center; BD Width; BD Height; 3BD ViewTarget; 3BD ViewDirection; BD TwistAngle; BD ViewHeight; BD LensLength; BD FrontClip; BD BackClip; BD SnapAngle; 2RD ViewCenter; 2RD SnapBase; 2RD SnapSpacing; 2RD GridSpacing; BS CircleZoom; BS GridMajor; BL FrozenCount; BL StatusFlags; TU StyleSheet; RC RenderMode; B UcsAtOrigin; B UcsPerViewport; 3BD UcsOrigin; 3BD UcsXAxis; 3BD UcsYAxis; BD UcsElevation; BS UcsOrtho; BS ShadePlot; B DefaultLights; RC LightingType; BD Brightness; BD Contrast; CMC Ambient; Hs Frozen FrozenCount; H ClipBoundary; H NamedUcs; H BaseUcs; H Background; H VisualStyle; H ShadePlotId; H SunHandle",
    "DICTIONARY": "BL ItemCount; BS Cloning; RC HardOwner; each Entries ItemCount { TU EntryName }; Hs Items ItemCount",
    "ACDBDICTIONARYWDFLT": "BL ItemCount; BS Cloning; RC HardOwner; each Entries ItemCount { TU EntryName }; Hs Items ItemCount; H DefaultEntry",
    "BLOCK_CONTROL": KControlCommon + "; H ModelSpace; H PaperSpace",
    "LAYER_CONTROL": KControlCommon,
    "STYLE_CONTROL": KControlCommon,
    "LTYPE_CONTROL": "BL EntryCount; Hs Entries EntryCount; H ByBlock; H ByLayer",
    "VIEW_CONTROL": KControlCommon,
    "UCS_CONTROL": KControlCommon,
    "VPORT_CONTROL": KControlCommon,
    "APPID_CONTROL": KControlCommon,
    "DIMSTYLE_CONTROL": "BL EntryCount; RC HardCount; Hs Entries EntryCount; Hs HardOwned HardCount",
    "LAYER": KTableCommon
    + "BS LayerValues; CMC Color; H XrefBlock; H PlotStyle; H Material; H Linetype; H Unknown",
    "STYLE": KTableCommon
    + "B Vertical; B ShapeFile; BD FixedHeight; BD WidthFactor; BD Oblique; RC Generation; BD LastHeight; TU FontName; TU BigFont; H XrefBlock",
    "LTYPE": KTableCommon
    + "TU Description; BD PatternLength; RC Alignment; RC DashCount; each Dashes DashCount { BD DashLength; BS ShapeCode; RD OffsetX; RD OffsetY; BD Scale; BD Rotation; BS ShapeFlag }; if Dashes.ShapeFlag&2 { Bytes TextArea 512 }; H XrefBlock; Hs Shapes DashCount",
    "APPID": KTableCommon + "RC Unknown; H XrefBlock",
    "BLOCK_HEADER": KTableCommon
    + "B Anonymous; B HasAttribs; B IsXref; B IsOverlay; B Loaded; if IsXref==0 { if IsOverlay==0 { BL OwnedCount } }; 3BD BasePoint; TU XrefPath; Zeros InsertCounts; TU Description; BL PreviewSize; Bytes Preview PreviewSize; BS InsertUnits; B Explodable; RC BlockScaling; H XrefBlock; H BlockEntity; if IsXref==0 { if IsOverlay==0 { Hs Owned OwnedCount } }; H EndBlock; Hs Inserts InsertCounts; H Layout",
    "XRECORD": "BL DataSize; Groups Items DataSize; BS Cloning; HRest Refs",
    "DICTIONARYVAR": "RC Schema; TU VarValue",
    "SCALE": "BS Unknown; TU ScaleName; BD PaperUnits; BD DrawingUnits; B UnitScale",
    "ACDBPLACEHOLDER": "",
    "LAYOUT": KPlotCommon
    + "TU LayoutName; BS TabOrder; BS LayoutFlags; 3BD UcsOrigin; 2RD LimitMin; 2RD LimitMax; 3BD InsertBase; 3BD UcsXAxis; 3BD UcsYAxis; BD Elevation; BS OrthoType; 3BD ExtentMin; 3BD ExtentMax; BL ViewportCount; H PlotView; H VisualStyle; H BlockRecord; H LastViewport; H BaseUcs; H NamedUcs; Hs Viewports ViewportCount",
    "VPORT": KTableCommon
    + "BD ViewHeight; BD ViewWidth; 2RD ViewCenter; 3BD ViewTarget; 3BD ViewDirection; BD TwistAngle; BD LensLength; BD FrontClip; BD BackClip; B ViewModeFirst; B ViewModeSecond; B ViewModeThird; B ViewModeFourth; RC RenderMode; since AC1021 { B DefaultLights; RC LightingType; BD Brightness; BD Contrast; CMC Ambient }; 2RD LowerLeft; 2RD UpperRight; B UcsFollow; BS CircleZoom; B FastZoom; BB UcsIcon; B GridOn; 2RD GridSpacing; B SnapOn; B SnapStyle; BS SnapIsoPair; BD SnapAngle; 2RD SnapBase; 2RD SnapSpacing; B UnknownBit; B UcsPerViewport; 3BD UcsOrigin; 3BD UcsXAxis; 3BD UcsYAxis; BD UcsElevation; BS UcsOrtho; since AC1021 { BS GridFlags; BS GridMajor }; H XrefBlock; since AC1021 { H Background; H VisualStyle; H SunHandle }; H NamedUcs; H BaseUcs",
    "FIELD": "TU EvaluatorId; TU FieldCode; BL ChildCount; Hs Children ChildCount; BL ObjectCount; Hs Objects ObjectCount; BL EvalOptions; BL FilingOptions; BL FieldState; BL EvalStatus; BL EvalError; TU ErrorMessage; nest FieldValue { "
    + KFieldValue
    + " }; TU ValueString; BL ValueLength; BL EntryCount; each Entries EntryCount { TU EntryKey; nest EntryValue { "
    + KFieldValue
    + " } }",
    "FIELDLIST": "BL FieldCount; B UnknownBit; Hs Fields FieldCount",
    "SORTENTSTABLE": "BL EntryCount; H BlockOwner; each Entries EntryCount { DH SortHandle; H Entity }",
}
