# Text-only metadata can retain a vendor object graph

FreeCAD's archive writer reads `metadata.freecad.objects` separately from the
typed model. `AddReplayMut` reconstructs those saved objects and XML properties,
and the adapter can mark their history native when a retained graph exists.
A binary-payload scan therefore does not identify every replay path. Geometry
contract comparison deliberately excludes incidental metadata, so it cannot
qualify this separate object graph.

The CLI refuses every nonempty object collection at root and nested document
levels before any destination writer runs. Empty collections request no replay;
ordinary text provenance remains subject to its existing checks. Use `kit decode`
or deterministic research inspection to examine saved graphs.

See [the captured-object guard](../../../Changes/Commands/CapturedObjectGuard.md).
