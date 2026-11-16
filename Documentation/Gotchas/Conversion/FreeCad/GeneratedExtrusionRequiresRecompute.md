# Generated extrusion geometry requires initial recompute

## Expectation

A generated editable FreeCAD document also exposes usable solid geometry when first opened.

## Observed behavior

The [independent FreeCAD 1.1.4 witness](../../../Changes/FreeCad/FreeCadEndNativeWitness.md) found that the original packages generated at `b32222b5` contained parametric extrusion histories and driver expressions but no cached BREP.
All three returned zero solids before native recompute and one valid solid afterward.
Edited, restored and saved copies reopened with geometry already present in a fresh process.
That later success does not establish the initial package's geometry availability.

## Handling and remaining work

Record the initial state separately from post-recompute and saved-copy observations.
Native recompute is an observed research verification action, not permission to add a production CAD-runtime fallback.
Initial application usability remains incomplete under CAD success criterion C5, which rejects zero bodies and an empty viewport on opening.
The required next implementation is derived shape data attached to the actual editable feature owners, followed by independent initial-open measurement before explicit recompute.
Do not hide this distinction through the embedded neutral manifest or qualify the whole route from the saved copies alone.
The [calculated-cache follow-up](../../../Changes/FreeCad/FreeCadInitialOpenWitness.md) measured valid initial geometry before recompute for three rectangular controls at `161885d8`.
It leaves this earlier failure intact and does not establish other cache families or broader route qualification.
