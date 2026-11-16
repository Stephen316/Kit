# SOLIDWORKS configuration environment

`WriteConfigEnvironment` writes the Lights and Cameras folder with one ambient and three directional lights. It takes typed light coefficients, directional vectors and feature bookkeeping. Its return is the environment object slot used by the resolved archive alias.

All 14 pinned P01 and P03 saves have the same 1,488-byte layout and thirteen new slots. The hosted comparison writes the environment and standard views on one allocator and checks the exact environment bytes and object map. Fresh-process native acceptance remains open. [Native ownership and saved range](../../../../../../re/solidworks/WriterResearch/ConfigEnvironment.md)
