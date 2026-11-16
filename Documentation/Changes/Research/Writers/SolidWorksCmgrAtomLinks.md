# SOLIDWORKS configuration manager atom links

The A12 [research encoder](../../../../re/solidworks/WriterResearch/CmgrLinks.py) writes the generation-19000 configuration manager's empty atom map or one independent atom-to-feature link. The caller supplies the model-assigned atom and feature IDs and the enclosing archive allocator. The encoder allocates the class and object when a link is present. It refuses nonpositive IDs, connected histories and unsupported allocation state. [Native field and owner evidence](../../../../re/solidworks/WriterResearch/CmgrAtoms.md#linked-atom-map)

The read-only replay verified the complete CMgr offset census for six P01 and eight P03 discovery saves. It reached EOF in all fourteen. P01's map is four bytes and preserves next index 9. P03's map is 62 bytes and advances to index 11 after the link class and object are allocated. The surrounding typed records confirm the saved atom owner. [Offset census and evidence digest](../../../../re/solidworks/WriterResearch/CmgrCoverage.md)

Hosted `CheckCmgr` uses the [pinned archive verifier](../../../../re/solidworks/WriterResearch/VerifyCmgrColor.py) to compare generated link bytes and allocation state against all fourteen pinned archives. The new hosted check awaits execution. Whole-part generation and native acceptance remain open.
