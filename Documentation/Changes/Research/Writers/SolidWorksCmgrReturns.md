# SOLIDWORKS configuration base return and manager aliases

The A12 [base-return constructor](../../../../re/solidworks/WriterResearch/CmgrBaseEnd.py) writes the 34-byte generation-19000 record for the default standalone configuration. The caller identifies the ordinary archive condition, the initialized modern thread reference mode and a zero- or one-atom history. Populated collections, alternate modes and nondefault inherited state require separate evidence. [Base constructor and store routes](../../../../re/solidworks/WriterResearch/CmgrAtoms.md#base-return)

The [manager alias constructor](../../../../re/solidworks/WriterResearch/CmgrPartEnd.py) writes two compact references to the first active part object. It takes the current archive allocator, the allocated object index, configuration ID zero and an external-object count of one. It writes the next configuration ID separately from the compact list count. Both returns preserve the archive allocation map. [Manager field owners](../../../../re/solidworks/WriterResearch/CmgrAtoms.md#part-return-and-manager-aliases)

Read-only replay checked six P01 and eight P03 pinned saves. All fourteen base returns have SHA-256 `09c4b9259191e2551e2113b623f9835dfdcb061e534ec0f74920cc6e56bd5890`. All alias records have SHA-256 `e5f9b36d163ace0f12265dcf7e98bbbfc5637a79dcfefcbe3e945f14ca9833f6`. Both saved references resolved to the already allocated part. The shared next index stayed 9 for P01 and 11 for P03.

The replay SHA-256 is `8820c1389e1b03f3e43d61138366cc471bdd577c6f265953566a0165157f1ba2`. Its compact JSON rows contain the file SHA-256, base start and return, base SHA-256, alias start and return, alias SHA-256 and next archive index, in receipt order. [Offsets and scope](../../../../re/solidworks/WriterResearch/CmgrCoverage.md)

Hosted `CheckCmgr` appended the links, base return, part return and aliases to one archive writer for both families. It compared each saved boundary and verified the final allocator and class map at `f832a3b8`. Complete stream composition and native acceptance remain open. [Hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43865736099/job/133293681800)
