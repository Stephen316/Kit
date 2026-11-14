from convert.formats.Fusion.GraphicsCodec.Schema.FieldRule import FieldRule

KAttrRules: dict[str, tuple[FieldRule, ...]] = {
    "HWSelectionPostProcessingAttribute": (),
    "DepthPriorityAttribute": (FieldRule("DepthPriority", "i32"),),
    "VisibilityAttribute": (FieldRule("Visibility", "bool"),),
    "TransformAttribute": (
        FieldRule("Transform", "f32", 16),
        FieldRule("Absolute", "bool"),
    ),
    "OverrideTransformAttribute": (
        FieldRule("Transform", "f32", 16),
        FieldRule("Absolute", "bool"),
        FieldRule("NodePath", "path"),
        FieldRule("Target", "target"),
        FieldRule("Overrides", "overrides"),
    ),
    "OverrideVisibilityAttribute": (
        FieldRule("Visibility", "bool"),
        FieldRule("NodePath", "path"),
        FieldRule("Target", "target"),
        FieldRule("Overrides", "overrides"),
    ),
    "OverrideInActivatedVisibilityAttribute": (
        FieldRule("Visibility", "bool"),
        FieldRule("NodePath", "path"),
    ),
    "FColorEffectAttribute": (FieldRule("Color", "f32", 4),),
    "OpacityAttribute": (FieldRule("Absolute", "bool"), FieldRule("Opacity", "f32")),
    "GroupAttribute": (FieldRule("GroupID", "i32"),),
    "OrderInTransparentGroupAttribute": (FieldRule("OrderInTransparentGroup", "i32"),),
    "TransparentLayerAttribute": (FieldRule("TransparentLayerType", "i32"),),
    "BillBoardAttribute": (
        FieldRule("Style", "i32"),
        FieldRule("Anchor", "f32", 3),
        FieldRule("Axis", "f32", 3),
        FieldRule("Compensation", "f32", 3),
        FieldRule("FlipVisibility", "i32"),
    ),
    "PixelScaleAttribute": (
        FieldRule("ScreenSpaceSize", "f64"),
        FieldRule("ModelSpaceSize", "f64"),
        FieldRule("ScaleCenter", "f32", 3),
    ),
    "PixelScaleTranslationAttribute": (
        FieldRule("ScreenSpaceDistance", "f64"),
        FieldRule("Translation", "f32", 3),
    ),
    "SelectabilityAttribute": (
        FieldRule("Selectability", "bool"),
        FieldRule("SelectionPriority", "i32"),
        FieldRule("AlphaImageSelectionQualifier", "qualifier"),
    ),
    "FOccludedEffectAttribute": (
        FieldRule("Color", "f32", 4),
        FieldRule("ImagePartName", "opt-text"),
        FieldRule("Path", "opt-text"),
        FieldRule("VisibleOpacity", "f32"),
        FieldRule("OccludedOpacity", "f32"),
    ),
    "FOccludedFatPointEffectAttribute": (
        FieldRule("Color", "f32", 4),
        FieldRule("ImagePartName", "opt-text"),
        FieldRule("Path", "opt-text"),
        FieldRule("PointSize", "f32", 2),
        FieldRule("VisibleOpacity", "f32"),
        FieldRule("OccludedOpacity", "f32"),
    ),
    "FLineStyleAttribute": (
        FieldRule("Weight", "f32"),
        FieldRule("Space", "i32"),
        FieldRule("LinePatternName", "opt-text"),
        FieldRule("XScale", "f32"),
        FieldRule("YScale", "f32"),
    ),
    "TextureMappingAttribute": (FieldRule("TextureMapping", "texture"),),
    "FProteinEffectAttribute": (FieldRule("AssetReference", "text"),),
    "FPrioritizedProteinAttribute": (
        FieldRule("AssetReference", "text"),
        FieldRule("Category", "u32"),
    ),
}
