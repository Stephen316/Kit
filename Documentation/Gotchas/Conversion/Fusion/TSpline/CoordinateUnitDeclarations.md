# Fusion TSM unit declarations do not imply a scale conversion

The controlled Fusion TSM files declare `units 1 meters`, while primary control-point numeric coordinates equal the native Fusion API centimeter coordinates. Applying a meter-to-centimeter conversion from that text changes the geometry by a factor of 100.

Preserve the declaration and stored coordinate values independently. The current component authoring API follows this captured Fusion route; interpretation of other applications' TSM unit declarations is unqualified.

[Control inventory](../../../../../re/Fusion/Reconstruction/TSpline/ControlInventory.json) binds the declarations, native coordinate comparisons and embedded F3D descriptions.
