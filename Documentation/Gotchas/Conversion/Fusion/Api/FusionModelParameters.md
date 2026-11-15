# Fusion model parameters are not user parameters

## Expectation

`Design.userParameters` lists the parameters of a design, so a script that reads it sees every
parameter Fusion shows in the parameter dialog.

## Actual behavior

`Design.userParameters` lists only the parameters a user added by hand.
A sketch dimension or a feature dimension is a model parameter and appears in `Design.allParameters`
instead.

A Fusion-saved design with `d1`, `d2` and `d3` reported an empty `userParameters` collection and a
`bRepBodies` count of zero, while `allParameters` held all three:

```
userParameters.count   0
allParameters          d1 30.00 mm, d2 35.00 mm, d3 56.309932474 deg
```

## Workaround

Read `Design.allParameters` when the question is "what parameters does this design have".
Read `Design.userParameters` only when the question is "which parameters did a user add".

Bodies can also sit in child occurrences, so count `rootComponent.bRepBodies` and the bodies of
`rootComponent.allOccurrences` before concluding that a design has no bodies.

## Evidence

The run that found this is recorded in the
[parameter edit change entry](../../../../Changes/Fusion/Authoring/FusionParamEditAcceptance.md).
The first attempt reported no parameters and no bodies for both the control and the edited file, and
the same files reported three parameters once the script read `allParameters`.
