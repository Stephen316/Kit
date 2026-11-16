# SOLIDWORKS configuration visual properties

The [Config-0 visual codec](../../../../../re/solidworks/WriterResearch/ConfigVisual.py) allocates the model's visual object and uses the typed CMgr material, RealView and DSPBR constructors for its inline body. The caller supplies the owned PW appearance ID, separate RealView and DSPBR presence states, target installation material locator and colors. The codec admits the generation-19000 standalone appearance with both inline objects present. [Native owners and replay](../../../../../re/solidworks/WriterResearch/ConfigVisual.md)

Read-only replay matched all 817 visual body bytes to the corresponding CMgr visual object in each of the 14 pinned P01 and P03 saves. The reconstructed allocation ends before the units table at next index 8. Hosted byte comparison and native acceptance remain pending.
