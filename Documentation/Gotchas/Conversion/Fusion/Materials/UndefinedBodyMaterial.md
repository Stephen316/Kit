# Undefined body materials produce zero mass and centre of mass

A body can have valid geometry and a geometric mass cache while its physical material is undefined.
The body then reports zero density, mass, inertia, and centre of mass.

This occurred in independently authored cylinder and cuboid documents.
Their bounds, volume, topology, feature edits, rebuilds, and save/reopen operations succeeded.
Their `PhysicalMaterialValue` fields contained an empty material identity and no manager reference.
The native `body.material` getter failed with `InternalValidationError : !materialId.empty()`.

The [native mass probe](../../../../../re/Fusion/LocalOracle/RectangleAuthoring/MassProbe.json) isolates the cause.
Assigning a physical material corrected all physical properties immediately, without changing the geometry.
The cuboid centre changed from `(0, 0, 0)` to `(0.85, 1.15, 1.55)` centimetres.
The control density was `0.00785 kg/cm³`.

Provide a complete physical material assignment when authoring a body.
Link the body's physical and visual material values to a `ProteinAssetManager` and its typed Protein package.
Keep the package instance identifiers, definition identifiers, library identity, manager reference lists, and reference counts consistent.
Changing `MassPropertyCache.cog` or setting a density override does not repair an undefined material identity.

[Independent material authoring](../../../../Changes/Fusion/Materials/FusionAuthoredMaterials.md) constructs these relationships from explicit specifications and declarative schemas.
Native acceptance must measure mass and centre of mass as well as volume and topology.

[Strict cuboid acceptance](../../../../../re/Fusion/LocalOracle/RectangleAuthoring/NativeAcceptance.json) now confirms the independently authored package repairs the defect.
The initial 31 mm solid reports mass 0.012121 kg and centre `(0.85, 1.15, 1.55)` cm.
These properties remain correct after a 37 mm height edit, rebuild, save, and reopen.

[Strict cylinder acceptance](../../../../../re/Fusion/LocalOracle/Authored/ProductionMaterialDocumentAcceptance.json) also confirms correct mass and centre after editing and reopening.
