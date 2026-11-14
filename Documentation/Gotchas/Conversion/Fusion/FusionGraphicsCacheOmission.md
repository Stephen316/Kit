# OGS graphics caches are optional in the controlled native document

The archive's OGS world and mesh members initially looked like mandatory parts of a writable Fusion document.
A controlled experiment showed that they are optional for this document.

The controlled experiment removed all five `OGS.BlobFolder` entries from the reconstructed 19 mm extrusion archive.
Fusion opened it with correct initial geometry, retained both timeline entries, rebuilt, accepted a 23 mm edit, and saved/reopened successfully.
A later experiment also verified healthy feature states, rollback to the sketch-only state, and restoration of the solid.

Evidence: [removed members](../../../../re/Fusion/LocalOracle/Features/NoGraphicsRewrite.json), [load/edit/reopen](../../../../re/Fusion/LocalOracle/Features/NoGraphicsAcceptance.json), and [rollback and feature health](../../../../re/Fusion/LocalOracle/Features/RollbackAcceptance.json).
This establishes omission for the recorded control and build. It does not establish arbitrary cache-family omission or a visual rendering comparison.
