# Native material labels can be localization keys

A native physical material does not always store the name shown in Fusion's interface. An empty `physmat_Label` can accompany a `UIName` such as `PrismMaterial-018`. Fusion displays this material as Steel using its installed library resources.

The strict native projector preserves the nonempty stored label, or the stored `UIName` when the label is empty. It does not invent a localized name. The complete asset definitions, properties, identities, and alias relationships remain in typed native state.

Appearance color is also distinct from its rounded interface display. The ordinary rectangle stores channels `0.626209681225`, while Fusion displays 160/160/160/255. Preserve the floating-point channels instead of replacing them with 160/255.

The [public preparation report](../../../../../re/Fusion/LocalOracle/NativePublicAdapter/Preparation.json) records both stored material names and color values. Its output matches the [native-accepted archive](../../../../../re/Fusion/LocalOracle/NativeDocuments/NativeAcceptance.json) exactly. See the [reference-driven projector](../../../../Changes/Fusion/Adapter/FusionNativeRectangleProjection.md) for the qualified scope.
