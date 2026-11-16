# Check-prefixed helpers become test entries

An undecorated helper is not automatically excluded from Kit's test discovery.
The root `pyproject.toml` sets `python_functions` to `test_*`, `Test*` and `Check*`.
A matching function in a discovered module becomes a test even when it exists only to support another process case.
Its arguments are then treated as fixture requests.

At `161885d8ec4442ddc2558a740fd2cd153a6c0819`, `CheckTargets(Document, RootPath)` and `CheckCachedBody(CaseName, Document)` produced two hosted setup errors for missing fixtures.
The same stage reported 477 passes, including all 54 intended cache and attestation cases; the errors still failed the stage.
[Hosted observation](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6931236006)

Reserve the configured prefixes for actual test entries.
Use a descriptive helper name outside those patterns and update its callers without changing assertions or discovery settings.
The [repair entry](../../../Changes/FreeCad/FreeCadProcessHelperCollection.md) records the exact scope.
Keep collection and execution in hosted CI under the local-test prohibition.
