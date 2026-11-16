# Embedded inline snapshots can become stale

The two matching Kit manifest copies describe the original source graph. Their matching hashes do not establish agreement with native FreeCAD controls after edits.

`ReadSource` selects the embedded document whenever it is present. Its specialized reconcilers have separate proven scopes. The existing extrusion reconciler handles qualified `DistanceExtrude` graphs, and the standalone spreadsheet reconciler requires its model-free workbook binding. Generic inline `ExtrudeFeature` graphs have neither contract. A native control change could therefore leave a valid but stale embedded graph selected by an ordinary strict read.

The [inline manifest guard](../../../Changes/FreeCad/FreeCadInlineManifestGuard.md) checks the supported inline owners, controls, profile geometry, construction membership, constraint rows, placement and end bindings before returning that snapshot. Added native geometric owners also refuse. Unsupported changes or ambiguous ownership refuse explicitly. Cached BREP contents and full edited-graph reconstruction remain outside this guard. Keep the original archive and use explicit snapshot inspection when investigating a refusal. Do not remove the manifests or relabel native records to make conversion pass.

The defect and its new rejection controls are source-backed and exercised by authored process fixtures. The earlier [operator copies](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6931047492) restored values before save and do not establish a retained discrepant native save. Full edit reconstruction and independent native edit-save evidence remain unfinished.
