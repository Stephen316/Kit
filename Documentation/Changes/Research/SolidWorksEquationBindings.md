# SOLIDWORKS dimension references in equations

The SOLIDWORKS part reader resolves quoted right-hand equation references to exact, unique `dimension@feature` parameters. It also resolves unqualified global variables as before. The reader keeps the original formula and records unresolved right-hand tokens when a reference has no unique match.

In the initial [discovery census](../../Reference/Research/SolidworksResearchReader.md#discovery-census), both P04 cut-centering formulas reached the neutral document in all 11 P04 parts. Their dependency lists were empty. The remote census now checks the two expected lists against the named dimensions in each part and retains the census report when a binding fails.

The change concerns dependency links. Formula evaluation and conversion behavior remain subject to their own verification. Static steering and syntax checks passed. The updated process check runs in remote CI.
