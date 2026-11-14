# TSM numbered attributes are not editor selections

An external structural parser labels `100edges`, `100verts` and `50000grip` as editor selection records. Native crease contrasts show that they carry surface state instead.

A native interior-edge crease changes the namespace-100 edge set and can add compound secondary smart grips. Treating these records as disposable UI selection loses surface semantics. Preserve typed crease edge/vertex sets and smart-grip indices, including a present empty crease extension.

[Native crease contrasts](../../../../../re/Fusion/Reconstruction/TSpline/CreaseInventory.json) record the geometric correspondence.
