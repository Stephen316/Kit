KTextCommon = (
    "RC DataFlags; if DataFlags!&1 { RD Elevation }; 2RD Insertion; "
    "if DataFlags!&2 { 2DD Alignment Insertion }; BE Extrusion; BT Thickness; "
    "if DataFlags!&4 { RD Oblique }; if DataFlags!&8 { RD Rotation }; RD Height; "
    "if DataFlags!&16 { RD WidthFactor }; TU TextValue; "
    "if DataFlags!&32 { BS Generation }; if DataFlags!&64 { BS HorizAlign }; "
    "if DataFlags!&128 { BS VertAlign }; H Style; "
)
KTableCommon = "TU EntryName; B FlagBit; B XrefDependent; "
KDimCommon = (
    "RC DimVersion; 3BD Extrusion; 2RD TextMidpoint; BD Elevation; RC DimFlags; "
    "TU UserText; BD TextRotation; BD HorizDirection; 3BD InsertScale; "
    "BD InsertRotation; BS Attachment; BS SpacingStyle; BD SpacingFactor; "
    "BD Measurement; B Unknown; B FlipFirst; B FlipSecond; 2RD PointTwelve; "
)
KControlCommon = "BL EntryCount; Hs Entries EntryCount"
KEntityBody = (
    "BB EntityMode; BL ReactorCount; B NoXdic; B HasDsData; BS ColorIndex; "
    "if ColorIndex&0x8000 { BL ColorRgb }; if ColorIndex&0x2000 { BL Transparency }; "
    "BD LtypeScale; BB LtypeFlags; BB MaterialFlags; BB PlotFlags; RC ShadowFlags; "
    "B HasFullStyle; B HasFaceStyle; B HasEdgeStyle; BS Invisible; RC LineWeight; "
    "if EntityMode==0 { H Owner }; Hs Reactors ReactorCount; if NoXdic==0 { H Xdic }; "
    "if ColorIndex&0x4000 { H ColorBook }; H Layer; if LtypeFlags==3 { H Ltype }; "
    "if MaterialFlags==3 { H Material }; if ShadowFlags==3 { H Shadow }; "
    "if PlotFlags==3 { H PlotStyle }; "
    "if HasFullStyle==1 { H FullStyle }; if HasFaceStyle==1 { H FaceStyle }; "
    "if HasEdgeStyle==1 { H EdgeStyle }; "
)
KEntityCommon = (
    "B HasGraphics; if HasGraphics==1 { BLL GraphicSize; Bytes Graphics GraphicSize }; "
    + KEntityBody
)
KMtextCommon = (
    "3BD Insertion; 3BD Extrusion; 3BD XAxis; BD RectWidth; BD RectHeight; "
    "BD TextHeight; BS Attachment; BS DrawDirection; BD ExtentHeight; "
    "BD ExtentWidth; TU TextValue; BS SpacingStyle; BD SpacingFactor; "
    "B UnknownBit; BL BackFlags; if BackFlags&0x11 { BD BackScale; "
    "CMC BackColor; BL BackAlpha }; H Style; since AC1032 { B NotAnnotative; "
    "if NotAnnotative==1 { BS ContextVersion; B DefaultFlag; H AppId; "
    "BL AttachPoint; 3BD ContextXAxis; 3BD ContextInsertion; BD ContextWidth; "
    "BD ContextHeight; BD ContextExtWidth; BD ContextExtHeight; BS ColumnType; "
    "if ColumnType!=0 { BL ColumnCount; BD ColumnWidth; BD Gutter; "
    "B AutoHeight; B FlowReversed; if AutoHeight==0 { if ColumnType==2 { "
    "each Columns ColumnCount { BD ColumnHeight } } } } } }; "
)
KAttribCommon = (
    "RC AttribVersion; since AC1032 { RC AttribType; if AttribType>=2 { "
    + "nest MultiText { "
    + KEntityBody
    + KMtextCommon
    + "}; BS AnnotativeSize; if AnnotativeSize>=1 { Bytes AnnotativeData "
    + "AnnotativeSize; H AnnotativeApp; BS AnnotativeFlag } } }; TU Tag; "
    + "BS FieldLength; RC AttribFlags; B LockPosition; "
)
KPlotCommon = (
    "TU PageName; TU PrinterName; BS PlotFlags; BD LeftMargin; BD BottomMargin; "
    "BD RightMargin; BD TopMargin; BD PaperWidth; BD PaperHeight; TU PaperSize; "
    "2BD PlotOrigin; BS PaperUnits; BS PlotRotation; BS PlotType; 2BD WindowMin; "
    "2BD WindowMax; BD RealUnits; BD DrawingUnits; TU StyleSheet; BS ScaleType; "
    "BD ScaleFactor; 2BD ImageOrigin; BS ShadeMode; BS ShadeQuality; BS ShadeDpi; "
)
KMapCommon = (
    "BD BlendFactor; RC Projection; RC Tiling; RC AutoTransform; "
    "each Transform 16 { BD Element }; RC MapSource; if MapSource==1 { TU FileName }"
)
KCellStyle = (
    "BL CellType; BS DataFlags; if DataFlags==1 { BL OverrideFlags; "
    "BL MergeFlags; CMC Background; BL LayoutFlags; BL FormatOverride; "
    "BL FormatFlags; BL DataType; BL UnitType; TU FormatText; BD Rotation; "
    "BD BlockScale; BL Alignment; CMC TextColor; H TextStyle; BD TextHeight; "
    "BS MarginFlags; if MarginFlags==1 { BD VertMargin; BD HorizMargin; "
    "BD BottomMargin; BD RightMargin; BD HorizSpacing; BD VertSpacing }; "
    "BL BorderCount; each Borders BorderCount { BL EdgeFlags; BL BorderOverride; "
    "BL BorderType; CMC BorderColor; BL LineWeight; H BorderLtype; BL Invisible; "
    "BD LineSpacing } }"
)
KFieldValue = (
    "BL ValueFlags; BL DataType; if DataType==1 { BL LongValue }; "
    "if DataType==2 { BD RealValue }; if DataType==4 { BL DataSize; "
    "Wide TextValue DataSize }; if DataType==64 { H ObjectValue }; "
    "BL UnitType; TU FormatText; TU ValueText"
)
