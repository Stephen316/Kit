# Fusion Browser relationships require the constraint collection

A Browser entry's generic persisted entity reference does not permit arbitrary target classes.
`RelationshipsBrowserEntry` expects the component's `AssyConstraints` collection, despite its name.
Pointing the five relationship folders at the separate `Relationships` entity loads successfully but crashes during Browser activation.

The controlled failure passed all three segment loads and initialized the asset before the crash.
A corrected candidate binds the folders to `AssyConstraints`.
Fusion accepted it through read, edit, save and reopen.

Bind these Browser folders, their subjects, and their root map keys to `AssyConstraints`.
Validate semantic target classes in addition to generic reference framing.
The [captured crash](../../../../re/Fusion/LocalOracle/Authored/ParameterBrowserCrash.json) identifies the exact candidate and failure stage.
The [container model](../../../../re/Fusion/Reconstruction/ContainerAuthoring/ContainerModel.md) records the corrective candidate and its verification status.
