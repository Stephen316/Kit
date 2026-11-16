# Read both bodies and the saved Cut policy in SOLIDWORKS

The public SOLIDWORKS reader now projects the licensed two-body through-all layout into the existing `CadDocument` contract. It follows the original Boss sketches, typed plane and face support, signed Boss starts and depths, and the complete saved Cut scope. It joins both original body identities to the active partition before returning a new document. If a required join fails, the reader retains the fallback result with an unresolved diagnostic. [Typed history](SolidWorksScopedBossHistory.md), [scope contract](ScopedExtrusionContract.md), [active partition](SolidWorksScopedPartition.md)

The Cut retains its authored selections independently of the affected bodies. A projected explicit selection references the original stable body ID. In Explicit A, body 102 keeps Boss 40 as its final feature, while body 101 ends at Cut 47. The other two cases end both bodies at Cut 47. The second Boss starts at −10 mm and extrudes +5 mm from its own sketch. Its separate native start parameter retains the positive saved magnitude and the sign used by the neutral offset.

| Licensed source | Authored selection | Affected bodies | Body 101 volume | Body 102 volume |
| --- | --- | --- | ---: | ---: |
| All bodies | Empty | 101, 102 | 7,200 mm³ | 600 mm³ |
| Explicit A | 101 | 101 | 7,200 mm³ | 1,000 mm³ |
| Explicit A+B | 101, 102 | 101, 102 | 7,200 mm³ | 600 mm³ |

All three hash-pinned archives passed the normal reader with and without B-rep retention, and their scoped history survived JSON serialization. With B-rep enabled, each saved solid region links to its own design body. The two body volumes, centroids and topology counts agree with the independent licensed rebuild measurements. The pinned ordinary P04 through-all document retains exactly the same 246,000-byte JSON, SHA-256 `c209f52d9eb3ead391f5cb8d65d63fca71fad254dff29fec10165a2cf32a84ff`. [Licensed controls](../../Workers/SolidWorks/ThroughAllScopeNativeEvidence.md)

This reader covers the witnessed source layout. Paired Fusion qualification, generated native output and editable round-trip acceptance remain open.
