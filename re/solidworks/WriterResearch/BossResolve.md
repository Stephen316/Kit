# Generation 19000 complete ordinary resolved boss suffix

`WriteResolvedBoss` takes the live allocator at the rectangular profile's trim return. It writes the [named operation](BossOpening.md), [body choosers](BossChoice.md), [partition and signed end](BossEndOpen.md), [distance display and end return](Display/EndOwner.md), and [the enclosing list footer](Resolved/EndMap.md). The caller supplies one `ResolvedBossState`, one explicit configuration atom binding, and the actual profile, file and edge identities. The display geometry's reversal controls the one-sided end word. The same display input provides the one named, positive driving depth and its two presentation copies.

## Fresh end properties

In installed SOLIDWORKS `34.4.1.1011` `sldmodu.dll` SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`, the exported ordinary `moBoss_c` constructor calls `moExtrusion_c` at `0x4bad1f8d`. The extrusion constructor invokes the default `moEndSpec_c` constructor at `0x4bad2fd5` and places the result into its owned `+0x818` field at `0x4bad2fdf`. This constructor clears `CapEnd[0]`, `CapEnd[1]`, `DelInitFace`, `KnitRes` and `CreateSolidFrmCappedMidPlaneSurfExt`. The terminal writer uses those five zero fields for the fresh ordinary solid.

The native kernel still receives these properties. In `sldgcu.dll` SHA-256 `797f81cba7080ea6edd37eca36abeaa9a2c0539f9319b980b92abc5a875edf24`, `gcEndSpec_c::setCapped` at `0x43ce99a0` stores both cap members and their combined presence. The ordinary blind branch of `ram_MakeExtrudedBody` clears a local modifier at `0x43cd970d` and stores it at `0x43cd98a8`, bypassing the known delete/knit block through `0x43cd99bf`. Further cap consumers have their own predicates. The initial values establish a fresh candidate, and native rebuild must show that this ordinary solid follows the intended path.

## Evidence and reproduction

Run `python -B re/solidworks/WriterResearch/VerifyBossResolve.py --read-only` in the Kit environment. All eight receipt-pinned P03 archives parse from the actual rectangle trim return to resolved EOF and advance the map from 257 to 306. They retain the independently measured direction and depth. Their five raw end properties have three observed tuples across the controls and remain separately recorded as saved evidence. Replay SHA-256 is `b90d5aa693f33eed082fc9250cf78bb79f54a545a22859f67ce714041eb74eab`.

Hosted `CheckBossWhole` compares the complete generated suffix to the independent map, selected profile, named depth and saved geometry observations. It checks exact archive bytes from the boss opening to the display and from the display return to the property interval. It separately checks the new clear end properties and exact extrusion return and list footer. The display's existing field-level coverage compares its intentional fresh appearance and annotation state with the saved form. Full generated-part open, rebuild, save/reopen and driving edit evidence is pending.
