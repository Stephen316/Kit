# Active-project lookup can raise

## Expectation

A read-only inventory can obtain `Data.activeProject` before enumerating accessible hubs and projects.
An unavailable selection appears suitable for a null check.

## Actual behavior

The first native F3Z inventory raised `RuntimeError: 2 : InternalValidationError : id.size()` while reading `Data.activeProject`.
The exception occurred before a project object could be checked for null.
The cause of the missing internal identifier was not established by that failed observation.

The initial local report was preserved as `re/Fusion/LocalOracle/Bundles/ProjectInventory.InitialFailure.json`.
It is an operational inventory report and can contain account-specific metadata.

## Workaround

Treat active-project selection as optional inventory context.
Catch and record its `RuntimeError`, then enumerate projects through the relevant hub's `dataProjects` collection.
Do not infer that project access is unavailable from a failed active-selection lookup.

The corrected [inventory script](../../../../re/Fusion/LocalOracle/InspectBundleProjects.py) records the exception without selecting or creating a project.
See the [bundle upload boundary](FusionBundleUpload.md) before native acceptance.
