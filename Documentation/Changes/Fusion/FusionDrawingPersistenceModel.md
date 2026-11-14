# Historical Fusion drawing persistence model

The [drawing research model](../../../re/Fusion/Reconstruction/DrawingModel/DrawingModel.md) documents an installed public example containing a drawing-root F3Z, one F2D and three dependent F3D files. Seven installed copies share one digest; they are one unique sample. No application sample binary is added to the repository.

`InspectDrawing.py` performs bounded read-only ZIP and scalar analysis of the installed resource. It records archive/member hashes, manifests, dependency joins, the historical metadata index and partially decoded entity fields in `DrawingInventory.json`. `UpstreamEvidence.json` pins the supporting open-source revision and primary documentation. The script does not invoke production codecs, local tests, Fusion operations or cloud projects.

## Findings

The F2D contains a 5,030-byte version-two metadata stream, a 2,593-byte entity bulk with 27 primaries and two inherited continuations, and a 110,873-byte DWG. All metadata bytes and both manifest envelopes are framed, and all 44 class identifiers have resolved names. Three drawing-specific records have recovered persisted fields, including the external file name, model-tracking collections and ten drawing settings. Explicitly unresolved inherited fields and manifest controls remain labeled in the detailed model.

The saved u32 header value reads as software version 2.0.1703, not a modern metadata sentinel. This reading came from binary inspection and is not confirmed by a black-box experiment. The three companion F3D models use the same older segment organization, so the lack of ACT/Browser segments is not by itself a drawing-family invariant. A historical registered class identifier is not a conventional UUID spelling; blindly normalizing all type identities would reject this source.

The drawing root and source assembly are joined through distinct `DERIVED` and `XREF` references. Role strings, document IDs, asset IDs, archive names and service URNs have separate namespaces. The detailed model connects the F3Z graph, redirection table and two manifests without dereferencing the sample's historical workstation paths.

The embedded DWG declares `AC1027`, the AutoCAD 2013 family. Upstream identification does not decode the database or establish independent writing of that version. Actual drawing sheets, views and annotations remain an unresolved semantic boundary; no F2D reader/writer or native acceptance is claimed by this addition. See [the historical drawing boundary](../../Gotchas/Conversion/Fusion/Drawing/FusionHistoricalDrawingMetadata.md).

## Verification evidence

The source bundle SHA-256 is `4e67c7a5487c3c1d3f3c193571206e87a0fb67da7990bd23f6638759aefe734b`; its F2D member SHA-256 is `33589d0ef64461fd366246f28786067305ade9c10c2e8d2869ba6909bdbbc483`. The read-only metadata cursor consumes all 5,030 bytes with no tail. Reports retain offsets, counts, file hashes and source references so structural claims can be distinguished from unresolved semantics. No local automated tests or target-application acceptance ran for this research.
