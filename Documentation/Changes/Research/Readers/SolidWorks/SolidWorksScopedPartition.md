# SOLIDWORKS two-body active partition

The bounded [partition reader](../../../../../src/convert/adapters/solidworks/Core/Partition/ScopedPartition.py) takes one decompressed Parasolid partition payload and two stable design body IDs keyed by the recent atom IDs established by typed feature history. It returns the saved B-rep with one linked carrier per solid region and per-body bounds, topology counts, volume, and geometric centroid.

The native shell and region records must refer to each other and to the same body owner. Each shell has a complete face chain with reciprocal references. Its exact face IDs identify one decoded solid region, and the named `ATOM_ID_2001` attribute assigns the body's recent atom. The reader requires a distinct atom for each owner and an exact match with the supplied atom keys. Each decoded topology record belongs to exactly one region. The reader measures each closed planar region from its own oriented loops.

The scope is two linear, planar solid regions under partition schema `SCH_3701250_37102_13006`. The caller provides the stable IDs and establishes the feature that owns each result. Body labels, region order, and geometry play no part in the identity join. The public adapter retains its existing path while the feature history and authored scope integration remain open.

## Verification

Read-only replay verified the three retained archive hashes against the [licensed report](../../Workers/SolidWorks/ThroughAllScopeNativeEvidence.md). Both body bounds, centroids and topology counts agreed with the fresh-process measurements. A measured 7,200 mm³ in all three saves. B measured 600 mm³ with recent atom 104 in All bodies and Explicit A+B. In Explicit A, B retained its Boss atom 102 and measured 1,000 mm³. All three linked B-rep models passed document-level B-rep validation with their supplied body IDs. The ordinary P04 through-all capture still returned its existing linked single body at 7,200 mm³ through the public adapter. [Ordinary active partition](SolidWorksActivePartition.md)
