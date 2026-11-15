# Independently authored cuboids use a distance-controlled extrusion

## Expectation

A test that builds `AdapterCase("cuboid")` might search its history for an `ExtrudeFeature` to vary an end condition.

## Actual behavior

The independently authored Fusion fixture uses `DistanceExtrude`, whose parameter identity and unit direction define a distance-controlled feature. It is a separate model class and has no generic `end_condition` field. The [remote end-condition cases](https://github.com/TryUniCAD/Kit/actions/runs/43668887044/job/132674284143) failed at `ef431a17` because that class search found no matching step.

## Workaround

Keep the independent cuboid as the positive control. For generic end-condition refusal cases, construct an explicit `ExtrudeFeature` from the same independent driving parameter value and direction, then vary its primary or secondary end field. These intentionally unresolved fixtures establish refusal behavior, not native writer acceptance.
