# Classify exterior rings on saved planar faces

The Parasolid reader now identifies the exterior when all trimming rings on a planar face are closed chains of straight edges and exactly one simple ring strictly encloses the rest. The proof checks planarity and rules out contact, crossings, disjoint exteriors and nested holes before assigning roles. It bounds the pairwise work to 128 coedges per face. Native face and loop order, topology IDs and edge senses stay in the saved order.

Single rings and faces outside the geometric proof keep their existing role handling. The Parasolid writer accepts a saved later exterior on proven faces and verifies the same roles when it decodes the emitted payload. The existing first-loop rule still applies when the proof is unavailable. This change covers the Parasolid B-rep path used by the SOLIDWORKS reader.

The normal SOLIDWORKS reader opened all eleven receipt-pinned P04 discovery archives in an offline read. It labelled the 80–100 mm² loops as holes and their 800–960 mm² enclosing rings as exteriors on all twelve holed caps, including the YZ variant and both through-all caps. All eleven B-reps validated with their linked design bodies. The observed face, ring and coedge IDs stayed in the same order. [P04 capture corpus](../../../../Reference/Research/PinnedCorpus.md)

At PR head `5605c58f` and tested merge `c4f34448`, the hosted archive step passed its P04 through-all Parasolid re-export. It read back both caps and verified an 800 mm² exterior ring and an 80 mm² hole on each. The writer verifies each face's ordered loops and each loop's role using the exact record IDs assigned during emission. The decoded global loop collection can follow a different order when new face record IDs are allocated. The witness covers the Parasolid B-rep exchange. Licensed editable acceptance remains open. [Hosted archive checks](https://github.com/TryUniCAD/Kit/actions/runs/43794606581/job/133060521405)

See [the saved loop-order gotcha](../../../../Gotchas/Conversion/SolidWorks/ParasolidLoopOrder.md).
