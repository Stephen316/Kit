# Read the SOLIDWORKS two-body scope configuration

The configuration reader follows the zero-equation model map for the three licensed two-body through-all saves. This route accepts the observed three or four declared atom objects, the active sketch-block concept and one top annotation. Each of the two model region groups contains two ordered rows followed by one properties record. The reader preserves the raw body and region IDs and the scalar on each row. Two zero fields precede the exploded-view manager.

| Licensed save | Relation manager offset | Region groups start | Configuration end | Next archive index |
| --- | ---: | ---: | ---: | ---: |
| All bodies | 3514 | 25278 | 26118 | 112 |
| Explicit A | 3426 | 25190 | 26030 | 111 |
| Explicit A+B | 3514 | 25278 | 26118 | 112 |

The read-only replay verified the three archive hashes, consumed each configuration through its exact end and matched the resulting index to the independently framed resolved stream. Explicit A has three declared atoms and two region rows per group. Body B retains region ID 135 in both groups. The earlier provisional captures use the zero-region layout. [Licensed native scope evidence](../../Workers/SolidWorks/ThroughAllScopeNativeEvidence.md), [prior archive replay](../../Workers/SolidWorks/AutomaticScopeTypedCut.md)
