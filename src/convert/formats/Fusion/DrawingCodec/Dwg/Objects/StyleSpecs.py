from convert.formats.Fusion.DrawingCodec.Dwg.Objects.SpecParts import (
    KCellStyle,
    KMapCommon,
    KTableCommon,
)

KStyleSpecs = {
    "DIMSTYLE": KTableCommon
    + (
        "TU DimPost; TU DimAltPost; BD DimScale; BD DimArrowSize; BD DimExtOffset; "
        "BD DimLineIncrement; BD DimExtExtend; BD DimRound; BD DimLineExtend; "
        "BD DimTolPlus; BD DimTolMinus; since AC1021 { BD DimFixedLength; "
        "BD DimJogAngle; BS DimTextFill; CMC DimFillColor }; B DimTol; B DimLimits; "
        "B DimTextInside; B DimTextOutside; B DimSuppressOne; B DimSuppressTwo; "
        "BS DimTextAbove; BS DimZeroSuppress; BS DimAngZero; "
        "since AC1021 { BS DimArcSymbol }; BD DimTextHeight; BD DimCenter; "
        "BD DimTickSize; BD DimAltFactor; BD DimLinearFactor; BD DimTextVertical; "
        "BD DimTolFactor; BD DimGap; BD DimAltRound; B DimAlt; BS DimAltDecimals; "
        "B DimTextOffLine; B DimSeparateArrows; B DimTextInsideX; "
        "B DimSuppressOutside; CMC DimLineColor; CMC DimExtColor; CMC DimTextColor; "
        "BS DimAngDecimals; BS DimDecimals; BS DimTolDecimals; BS DimAltUnits; "
        "BS DimAltTolDecimals; BS DimAngUnits; BS DimFraction; BS DimLinearUnits; "
        "BS DimDecimalSep; BS DimTextMove; BS DimJustify; B DimSuppressLineOne; "
        "B DimSuppressLineTwo; BS DimTolJustify; BS DimTolZero; BS DimAltZero; "
        "BS DimAltTolZero; B DimUserText; BS DimFit; since AC1021 { B DimFixedOn }; "
        "since AC1024 { B DimTextDirection; BD DimAltMzFactor; TU DimAltMzSuffix; "
        "BD DimMzFactor; TU DimMzSuffix }; BS DimLineWeight; BS DimExtWeight; "
        "B UnknownFlag; H XrefBlock; H DimTextStyle; H DimLeaderBlock; H DimBlock; "
        "H DimBlockOne; H DimBlockTwo; since AC1021 { H DimLtype; H DimExtLtypeOne; "
        "H DimExtLtypeTwo }"
    ),
    "MLINESTYLE": (
        "TU StyleName; TU Description; BS StyleFlags; CMC FillColor; "
        "BD StartAngle; BD EndAngle; RC LineCount; each Lines LineCount { BD Offset; "
        "CMC Color; since AC1032 { H Ltype } else { BS LtypeIndex } }"
    ),
    "MLEADERSTYLE": (
        "since AC1024 { BS StyleVersion }; BS ContentType; "
        "BS MleaderOrder; BS LeaderOrder; BL MaxPoints; BD FirstAngle; "
        "BD SecondAngle; BS LeaderType; CMC LineColor; H LineType; BL LineWeight; "
        "B LandingOn; BD LandingGap; B DoglegOn; BD DoglegLength; TU Description; "
        "H ArrowBlock; BD ArrowSize; TU DefaultText; H TextStyle; BS LeftAttach; "
        "BS RightAttach; BS TextAngleType; BS TextAlignType; CMC TextColor; "
        "BD TextHeight; B TextFrame; B AlignLeft; BD AlignSpace; H BlockContent; "
        "CMC BlockColor; 3BD BlockScale; B BlockScaleOn; BD BlockRotation; "
        "B BlockRotationOn; BS BlockConnection; BD StyleScale; B OverwriteValue; "
        "B Annotative; BD BreakGap; since AC1024 { BS AttachDirection; "
        "BS BottomAttach; BS TopAttach }; since AC1027 { B ExtendToText }"
    ),
    "TABLESTYLE": (
        "since AC1024 { RC StyleVersion; TU Description; BS StyleFlags; "
        "BS NextCellId; H TemplateTable; nest TableCell { "
    )
    + KCellStyle
    + " }; BL CellId; BL CellClass; TU CellName; BL CellCount; "
    + "each Cells CellCount { BL CellKey; "
    + KCellStyle
    + "; BL CellId; BL CellClass; TU CellName } }",
    "MATERIAL": (
        "TU MaterialName; TU Description; RC AmbientMethod; BD AmbientFactor; "
        "if AmbientMethod==1 { BL AmbientColor }; RC DiffuseMethod; "
        "BD DiffuseFactor; if DiffuseMethod==1 { BL DiffuseColor }; nest DiffuseMap { "
    )
    + KMapCommon
    + (
        " }; RC SpecularMethod; BD SpecularFactor; if SpecularMethod==1 { "
        "BL SpecularColor }; nest SpecularMap { "
    )
    + KMapCommon
    + " }; BD GlossFactor; nest ReflectionMap { "
    + KMapCommon
    + " }; BD OpacityPercent; nest OpacityMap { "
    + KMapCommon
    + " }; nest BumpMap { "
    + KMapCommon
    + " }; BD RefractionIndex; nest RefractionMap { "
    + KMapCommon
    + (
        " }; BD Translucence; BD SelfIllumination; BD Reflectivity; "
        "BL IlluminationModel; BL ChannelFlags; BL MaterialMode"
    ),
    "VISUALSTYLE": (
        "TU Description; BL StyleType; since AC1027 { BS UnknownShort; "
        "B InternalOnly; BS FaceLighting; BS FaceLightingOp; BS FaceQuality; "
        "BS FaceQualityOp; BS FaceColorMode; BS FaceColorModeOp; BL FaceModifiers; "
        "BS FaceModifiersOp; BD FaceOpacity; BS FaceOpacityOp; BD FaceSpecular; "
        "BS FaceSpecularOp; CMC FaceMono; BS FaceMonoOp; BS EdgeModel; "
        "BS EdgeModelOp; BL EdgeStyles; BS EdgeStylesOp; CMC EdgeIntersectColor; "
        "BS EdgeIntersectColorOp; CMC EdgeObscuredColor; BS EdgeObscuredColorOp; "
        "BS EdgeObscuredPattern; BS EdgeObscuredPatternOp; BS EdgeIntersectPattern; "
        "BS EdgeIntersectPatternOp; BD EdgeCreaseAngle; BS EdgeCreaseAngleOp; "
        "BL EdgeModifiers; BS EdgeModifiersOp; CMC EdgeColor; BS EdgeColorOp; "
        "BD EdgeOpacity; BS EdgeOpacityOp; BS EdgeWidth; BS EdgeWidthOp; "
        "BS EdgeOverhang; BS EdgeOverhangOp; BS EdgeJitter; BS EdgeJitterOp; "
        "CMC EdgeSilhouetteColor; BS EdgeSilhouetteColorOp; BS EdgeSilhouetteWidth; "
        "BS EdgeSilhouetteWidthOp; BS EdgeHaloGap; BS EdgeHaloGapOp; "
        "BS EdgeIsolines; BS EdgeIsolinesOp; B EdgeHidePrecision; "
        "BS EdgeHidePrecisionOp; BL DisplayStyles; BS DisplayStylesOp; "
        "BD Brightness; BS BrightnessOp; BL ShadowType; BS ShadowTypeOp; "
        "B UseDrawOrder; BS UseDrawOrderOp; B ViewTransparency; "
        "BS ViewTransparencyOp; B LightingEnabled; BS LightingEnabledOp; "
        "B PosterizeEffect; BS PosterizeEffectOp; B MonoEffect; BS MonoEffectOp; "
        "B BlurEffect; BS BlurEffectOp; B PencilEffect; BS PencilEffectOp; "
        "B BloomEffect; BS BloomEffectOp; B PastelEffect; BS PastelEffectOp; "
        "BL BlurAmount; BS BlurAmountOp; BD PencilAngle; BS PencilAngleOp; "
        "BD PencilScale; BS PencilScaleOp; BL PencilPattern; BS PencilPatternOp; "
        "CMC PencilColor; BS PencilColorOp; BL BloomThreshold; BS BloomThresholdOp; "
        "BL BloomRadius; BS BloomRadiusOp; CMC TintColor; BS TintColorOp; "
        "B FaceAdjustment; BS FaceAdjustmentOp; BL PostContrast; BS PostContrastOp; "
        "BL PostBrightness; BS PostBrightnessOp; BL PostPower; BS PostPowerOp; "
        "B TintEffect; BS TintEffectOp; BL BloomIntensity; BS BloomIntensityOp; "
        "CMC StyleColor; BS StyleColorOp; BD Transparency; BS TransparencyOp; "
        "BL EdgeWiggle; BS EdgeWiggleOp; TU EdgeTexture; BS EdgeTextureOp; "
        "B DepthOfField; BS DepthOfFieldOp; BD FocusDistance; BS FocusDistanceOp; "
        "BD FocusWidth; BS FocusWidthOp }"
    ),
}
