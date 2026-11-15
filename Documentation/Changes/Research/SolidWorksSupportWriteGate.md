# SOLIDWORKS sketch support write gate

Public document writing now rejects SOLIDWORKS sketch supports that retain fallback or unframed evidence.
Registry writes and the JSON, Fusion, CATIA, and FreeCAD direct writers call the focused `SupportWrite.CheckSupports` guard before output mutation.
Existing research-marker, inch-dimension, and equation diagnostics retain their earlier priority.

## Evidence and behavior

The native reader can assign a decoded plane by stream order when it cannot resolve the sketch's actual support reference.
The projected sketch retains `support_plane_source` and `unframed_support_plane_native_id` attributes.
The [review finding](https://github.com/TryUniCAD/Kit/pull/94#discussion_r4576597583) identified that ordinary reads lacked the research marker used by the existing write refusal.
Those documents could therefore reach JSON output while retaining an unqualified frame association.

The new guard checks each root and embedded component sketch attributed to SOLIDWORKS.
Attribution uses the document source, sketch provenance, or the existing native support attributes.
It therefore also checks native-derived documents restored through interchange JSON.
Changing the document's source format does not remove retained sketch evidence from this check.

The guard requires the existing `plane-reference` source classification and no unframed support identifier.
Stream-order, unresolved, unknown, and missing classifications fail closed for native-derived sketches.
The error identifies the source path and affected sketch identifiers.
Existing files and streams remain unchanged. Missing output directories are not created.
Setting `WriteOptions(validate=False)` does not disable the guard.

The reader and manual document serialization remain available for inspection and research evidence.
The guard does not infer YZ orientation, change any decoded support plane, or invent a supporting face.
Independent neutral and Fusion sketches without SOLIDWORKS attribution retain their existing write behavior.
Permitting an existing explicit reference does not qualify the remaining source semantics or any conversion route.

## Verification

New remote integration cases use the saved SOLIDWORKS 2026 YZ parts from P01, P03, and P04.
They cover root and nested documents, persisted JSON, retained native attributes after source relabeling, and the public conversion path.
All seven direct writer method spellings must reject before file or stream mutation, including when validation is disabled.
Additional cases require rejection of missing, unknown, and contradictory unframed evidence after JSON readback.

The [first remote run](https://github.com/TryUniCAD/Kit/actions/runs/43665357887/job/132663393914) exposed an invalid positive fixture at `3a432ea0d732186f6df4ae074f0fc7d91765faa9`.
The bundled `example.SLDPRT` retains unqualified support evidence for `sldprt:sketch:40` and cannot establish a successful export case.
Its direct JSON case now requires refusal with destination preservation.
The P04 baseline case separately proves both cut-centering formula texts and their exact parameter dependencies before requiring support-based export refusal.
Resolved equations do not qualify the remaining sketch history.

An independently authored Fusion rectangle supplies the positive direct JSON write and reopen case.
It also passes through native file creation, public reading, and public JSON writing.
That positive case retains no SOLIDWORKS support attributes.
No support attribute is relabeled to make a positive fixture pass.

No local tests, decoding, or CAD application experiments verified this change.
Remote integration results and current-head review remain required.
The SOLIDWORKS support-reference class and ownership proof remains unfinished under A04c.
See [the fallback gotcha](../../Gotchas/Conversion/SolidWorksSupportFallbackExport.md) and [the reader guide](../../Reference/Research/SolidworksResearchReader.md).
