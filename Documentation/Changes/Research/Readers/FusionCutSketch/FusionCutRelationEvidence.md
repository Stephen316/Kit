# Fusion P04 saved rectangle relation ownership

This research command checks the complete saved constraint and dimension lists for the two P04 sketches. It reads only the eleven discovery archives and the historical measurements pinned at `89c25945f5833ad9c3a1c6c683df510b5702dd54`. Run from the repository root with Python 3.14 or later. [Evidence command](../../../../../re/automation/FusionP04RelationEvidence.py)

```text
python -B re/automation/FusionP04RelationEvidence.py > FusionP04RelationEvidence.json
```

The typed sketch definitions `202` and `330` each list five geometric constraints and respectively two or four dimensions. The report requires each counted list to account for the independently parsed records and checks the definition's owning feature. It joins each of the eight axis constraints per archive to one unique side of the boss or cut feature's saved selected loop. Each matched side also agrees with the historical line's authored flags and independently measured world orientation. The YZ archive swaps the local horizontal and vertical roles. The cut's four cap projections and construction diagonal remain outside its perimeter. [Saved contour ownership](FusionCutProfileEvidence.md), [Saved constraint and dimension record parsing](../FusionCutSketchEvidence.md)

Each size dimension names the two ordered endpoints of one selected side, whose axis agrees with the relation and whose historical length agrees with the stored dimension. The two boss size sides share corner `228`. The saved Coincident operand lists name this corner and distinct sketch anchor `205`, which lies at the measured sketch origin. The two cut size sides share corner `389`, one endpoint of the excluded construction diagonal `405`. The saved MidPoint relation names that diagonal and point `406`, which is also the second operand of both center dimensions. [Saved cut center and parameter names](FusionCutCenterEvidence.md)

The result covers 110 geometric relations, 66 dimensions and 88 distinct archive-specific sides. Boss width 44 mm, boss height 24 mm, cut width 12 mm and cut height 10 mm each match their changed historical side length. The inch-display and through-all files retain the same physical operands and historical scalar sizes as baseline. Historical API data supplies relation type inventories, sketch frames, curve flags and endpoints, and dimension and parameter values. It omits native IDs and direct relation/dimension participant getters. Participant identity and order come from the saved records.

The document graph is reciprocal, with 41 edges in ten archives and 43 in the through-all archive. The only six edges incident to the sketch dimensions, their bindings or their numeric parameters are feature-to-binding edges with stored flag `1`. The boss sketch references two bindings and the cut sketch references four. This includes literal dimensions as well as the two expression-driven center dimensions, with the same incidence in every archive. The six numeric parameter objects have no incident edges in this graph. [Document dependency graph parser](../../../../../re/Fusion/Study/decode_dependencies.py), [Dependency coverage limitation](../../../../Gotchas/Research/Readers/FusionCutExpressionGraphScope.md)

Independent process readback and editable acceptance remain open. [Pinned source provenance](../../../../Reference/Research/PinnedCorpus.md)
