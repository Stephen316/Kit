# SOLIDWORKS ModelHeader self reference and spatial frame

The [research constructor](../../../../../re/solidworks/WriterResearch/HeaderTail.py) writes the complete generation-19000 model header on one archive allocator. It composes revision logs, the self reference, the empty replaced-components list and the bounding frame. The caller supplies the document times and stamps, license words, saved reference and sketch settings and evaluated world bounds. The constructor derives the frame midpoint and radius from those bounds. [Native field ownership](../../../../../re/solidworks/WriterResearch/ModelHeader.md#continuation-and-spatial-frame)

The old apparent empty class near the end is the overlap between a signed `-1` field and the next unsigned license-type word. The typed read consumes both without allocating a slot. The self reference allocates five slots and the subsequent replaced-components list allocates one.

Read-only replay reached EOF on 25 P01, P03 and P04 receipt-pinned saves from `466dcb172dfa3803463e07ccde963ba01671d200`. All 25 matched the shared file identifiers in CMgr and the independent creation, update and body values in `ModelStamps`. The two header stream copies are identical. The largest absolute difference between the saved frame and the independently calculated frame values was `3.47e-18 m`. The SHA-256 of the canonical sorted map from each native file digest to its full header digest is `d577d96774b072bef17a237fc13a39eb1b876531bd52a5782df53b1821bd6787`.

The new hosted comparison checks the complete native bytes outside the geometric frame, the ten derived values and the final archive allocation. Execution of that comparison and licensed acceptance of a composed part remain pending.
