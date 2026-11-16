# SOLIDWORKS empty configuration mass record

The A12 [research codec](../../../../re/solidworks/WriterResearch/CmgrMass.py) constructs and reads the 254-byte mass property record of a generation-19000 standalone configuration with zero bodies. The caller supplies the generation and body count. The constructor uses native scalar defaults, two empty wide coordinate-system names and the Cartesian frame. The reader validates each group and returns the offset of the following configuration field. [Native field and constructor evidence](../../../../re/solidworks/WriterResearch/CmgrMiddle.md#mass-property-record)

The reader consumed all six receipt-pinned P01 records through byte 1488. It rejected all 19 receipt-pinned P03 and P04 mass records at their populated geometry fields, including when given a zero body count. Licensed open, rebuild, edit and save of a generated archive require separate verification.

The [rectangular boss calculation](../../../../re/solidworks/WriterResearch/CmgrBossMass.py) derives the twelve physical quantities from proven axis-aligned world bounds and explicit density. It matched all eight independent P03 geometry controls within tolerance. Writing the populated SOLIDWORKS cache requires separate evidence.
