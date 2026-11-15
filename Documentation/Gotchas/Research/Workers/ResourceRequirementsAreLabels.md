# Job resource requirements use labels

## Expectation

A job can request an application resource with `"resources": {"application:local": 1}`, matching the supervisor capacity configuration.

## Actual behavior

The controller job schema requires an array of resource labels. Each running logical job consumes one slot for every listed resource. Capacities belong in the supervisor resource map or controller resource definition.
The [Windows process gate at `6fb599a9`](https://github.com/TryUniCAD/Kit/actions/runs/43672428040/job/132685202260) rejected both parking fixtures before dispatch because they supplied a map; eleven existing cases passed.

## Workaround

Use `"resources": ["application:local"]` in the job and keep the counted capacity in the supervisor configuration.
The parking fixtures now follow that existing contract; current-head remote execution remains required.
See the [controller guide](../../../Reference/Research/ResearchController.md#pools-and-counted-resources) and [application dispatch change](../../../Changes/Research/Workers/LocalApplicationDispatch.md).
