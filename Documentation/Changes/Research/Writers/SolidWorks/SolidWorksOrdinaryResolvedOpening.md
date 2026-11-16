# Framed SOLIDWORKS system and profile opening

`BeginOrdinaryResolved` starts the generation-19000 resolved stream from the generated Config-0 map. It writes the system roots, geometry-derived principal datums and Origin in native order. The list count includes the pending authored sketch and the boss indicated by the configuration's atom. The returned Origin sketch slot belongs to the same live writer used for the authored profile.

`WriteLocalComponent` shares the ordinary component reference fields between local features. It uses the generated part alias and accepts an explicit ghost body ID. Origin uses zero. The sketch proxy can bind to the ghost manager's allocated ID.

The hosted archive check compares the composed header and body through the first authored point count with 14 pinned P01 and P03 saves. The remaining authored geometry and fresh-process native acceptance are still separate steps. [Resolved stream construction](../../../../../re/solidworks/WriterResearch/OrdinaryResolved.py)
