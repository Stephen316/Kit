# AssetSettings observer indices

## Conclusion

In the controlled archives, the two dimensions subscribe to AssetSettings at indices 4 and 5. Browser entries hold indices 0 and 1. No persisted entity holds 2 or 3.

Earlier binary inspection read these indices as positions in a shared runtime observer list, appended at its current length, with load-time repair of occupied positions. That evidence was removed. It is not confirmed by a black-box experiment.

No additional persisted entities should be invented to explain missing positions. The saved documents do not say what held positions 2 and 3, or whether anything did.

This refines the Design-only observation in the frozen [dimension model](DimensionModel.md). [ObserverSlots.json](ObserverSlots.json) inventories all three saved entity segments. The script that generated it was removed with the binary evidence.

## Persisted subscribers

| Archive | Design records | ACT records | Browser records | AssetSettings subscribers |
| --- | ---: | ---: | ---: | --- |
| Baseline | 256 | 9 | 34 | Browser2 DocumentSettingsBrowserEntry→0; Browser31 PMISettingsBrowserEntry→1 |
| WidthDimension | 262 | 9 | 34 | Same Browser subscribers; Design245 width dimension→4 |
| WidthDepthDimensions | 268 | 9 | 34 | Same Browser subscribers; Design245→4; Design255 depth dimension→5 |
| EditedDimensions | 268 | 9 | 34 | Same four subscribers and indices |
| Independently authored ProductionExtrusion | 172 | 8 | 33 | Browser202 DocumentSettingsBrowserEntry→0; Browser230 PMISettingsBrowserEntry→1 |

The native control's settings root is Design entity0. The independently authored accepted extrusion uses Design entity1000. Every inventoried segment fully decoded. Neither ACT nor another persisted Design/Browser entity contributes settings indices 2 or 3 in the controlled archives. Slots absent below the highest persisted index are evidence about the saved graph, not a serialized count of runtime objects.

## Independent constructor proposal

A future qualified linear-dimension author can allocate a fresh, consistent observer namespace per observed entity. The current author already allocates Design observer subjects first and seeds Browser allocation with `ObserverCounts(Design.Records)`, which computes `max(existingIndex+1)` per Design target. With two fresh dimensions, settings indices0/1 can belong to width/depth and Browser indices2/3 to DocumentSettings/PMISettings. This is a proposed author ordering, not a claim that the controlled native document used that ordering. It requires native acceptance before production support is claimed. Retained archives should preserve their existing subject indices unless an explicit graph transformation reallocates all affected subscribers.

The dimension constructor must derive the complete graph already documented in DimensionModel: dimension plus Dimension continuation; named model parameter; DcDoubleParam plus ManagedEntity continuation; DynamicAttribute; settings and endpoint subject edges; model/user parameter expression binding; parameter-name lookup; parent/child collections; sketch dimensions; DcSketch parameter list; compute ordering and reciprocal dependencies. Width uses the ordered lower-left/lower-right point pair and horizontal constraint bit; depth uses upper-left/lower-left and vertical bit. These are separate from geometric constraints and anchoring. Parameter IDs, object identities, annotation positions and all collections remain explicit semantic inputs or derived outputs.

Subject indices are not substitutes for dependency edges. For a shared lower-left point, the two dimensions need distinct observer positions. Subject serialization order can differ from the dimension's geometry order. No fixed slots, synthetic baseline entities, captured records or source payloads are needed by this proposal.

## Verification boundary

Completed: read-only decoding of five complete three-segment archives. No local tests, production execution or native calls ran in this task. No production author or reader changed. Native creation, editing, regeneration and save/reopen of independently authored driving dimensions remain pending acceptance.
