# SOLIDWORKS offset bosses save depth and start offset separately

The automatic-scope control's second Boss exposes two typed distance displays. The blind end stores `D1` at 5 mm. The `moFromEndSpec_c` record with raw mode 5 owns a second display holding `D19` at 10 mm. Both displays have raw mode 200 and carry two matching presentation copies of their own parameter. Treating both distance displays as extrusion depths would lose the start offset and change the body placement.

Read the length from its enclosing end or start record, then check both display copies against that parameter. The two pinned archives place the second body at Z = −10 to −5 mm in the authoring specification and save its centre at Z = −7.5 mm. The distinct start offset magnitude is observed in both archives. Its raw trailer token differs between saves and is retained without assigning it a meaning. [Typed archive replay](../../Changes/Research/Workers/SolidWorks/AutomaticScopeTypedCut.md)
