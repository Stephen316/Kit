# SOLIDWORKS configuration manager stream composition

The [research constructor](../../../../../re/solidworks/WriterResearch/CmgrComposition.py) writes the whole generation-19000 `Contents/CMgr` stream for the supported default standalone configuration. It uses one archive allocator from the manager to EOF. The optional single rectangular boss supplies the body update stamp, feature ID, inherited FILETIME, native atom ID, cuboid bounds and material density. The same ID values feed the material map, the linked node, the part map and the terminal feature stamp.

Read-only replay built six P01 streams byte-for-byte and matched eight P03 streams outside the twelve derived mass geometry fields. Those fields agreed within the measured tolerance, and all fourteen streams ended with the saved allocator state. The [hosted archive verifier](../../../../../re/solidworks/WriterResearch/VerifyCmgrColor.py) includes this check. [Field attribution and evidence](../../../../../re/solidworks/WriterResearch/CmgrComposition.md)

Production stream integration and licensed acceptance of a fully generated part remain pending.
