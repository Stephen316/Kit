# An F3Z upload future need not identify the graph root

## Expectation

After uploading an F3Z archive, `DataFileFuture.dataFile` identifies the document named by `Manifest.json` and the design graph root.

## Actual behavior

The production nine-document bundle uploaded successfully, but the completed future returned `PCB`, a referenced child with no child references. The bundle root was `Patch Chess Robo Portal V2`. All nine documents were present and complete in the isolated destination project.

## Workaround

Resolve the expected root from the typed bundle graph, enumerate the destination folder, and identify the corresponding uploaded document. Verify the entire expected document set and every root reference before opening the assembly. A completed future and a loadable child alone do not prove assembly acceptance.

The [native report](../../../../re/Fusion/LocalOracle/Bundles/NativeBundleAcceptance.json) records the initial child result, nine uploaded documents, the independently selected root, and eight resolved references. The [native inspection script](../../../../re/Fusion/LocalOracle/InspectUploadedBundle.py) performs these checks. This observation does not establish a deterministic rule for which child the future returns.
