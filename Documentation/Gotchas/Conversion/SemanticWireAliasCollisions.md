# Distinct wire keys can address the same model slot

## Expectation

A sealed comparison input must not lose one supplied field when the codec reconstructs a record.

## Observed behavior

The shared codec accepts compatibility aliases such as `value` and `Value`.
Its argument map resolves both keys to the same storage slot, allowing one value to replace the other.
A registered migration can also add a canonical default beside a supplied alias, such as `role` beside `Role`.
Literal duplicate-key checks alone cannot detect either collision.

## Workaround

The comparison boundary checks supplied resolved slots before codec reconstruction.
It checks migration results against the same storage slots after validating child records.
Collisions are refused even when their supplied values agree.
Unambiguous compatibility aliases and migrations remain supported.
The shared codec is unchanged.

The check uses actual storage slots because compatibility metadata can rename reflected fields.
See the [reflection gotcha](CompatibilityModelReflection.md).
New process cases cover field aliases, typed feature slots, migration-generated defaults and valid legacy inputs.
Source inspection established these paths; local tests were not run.
