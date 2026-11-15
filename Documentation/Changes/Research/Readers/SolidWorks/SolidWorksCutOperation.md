# Saved SOLIDWORKS P04 cut operation

The public part reader follows the P04 configuration and its two profile references into the resolved CutSketch. It bounds the saved kernel packet, checks the ordered profile edge references against the earlier Boss cap, reads the selected face plane, and verifies the archived profile placement and trim cache. [Centering dependencies](../SolidWorksCutCentering.md), [face support](../SolidWorksFaceSupportDecoder.md)

The cut feature reads its distinct configuration transfer and its earlier Boss transfer, target body, saved result face identifiers and aliases, then its end specification and the resolved stream footer. The neutral cut target references the historical Boss feature and its saved body identifier. Blind cuts retain the authored scalar and through-all has no depth parameter. Both carry the saved profile, target and end spans through the normal public reader. [Public archive checks](../../../../../tests/Research/Archives/ArchiveEvidenceTests.py)

All eleven pinned P04 captures corroborate this path, including the YZ rotation, the 5 mm cut-depth edit and the through-all variant. Full sketch reconstruction, regeneration and editable acceptance have separate evidence requirements.
