# Principal sketch support evidence

A04c discovery reports now retain candidate principal-plane support records from each native sketch span.
The [research scanner](../../../re/automation/SolidworksSupportEvidence.py) checks bounded fields and finite, orthonormal, oriented bases.
Each candidate records its generation, plane id, opaque tag, axis code, basis and hashed source span.

Run the existing discovery census in remote CI, then check its support inventory:

```shell
python re/automation/SolidworksCensus.py --check-support-evidence SolidworksDiscoveryCensus.json
```

The check requires 25 measured principal-plane candidates, including three YZ variants.
It requires each candidate to remain explicitly unqualified.
Face support, constraints, editable output and native conversion require separate qualification.

## Evidence and limits

Read-only extraction examined the 25 committed P01/P03/P04 source files at `c1c3fcce5b8b67373113ec44ad5d122a52bd7260`.
Each rectangle span contained one candidate whose plane id matched the independent source measurement.
Licensed SOLIDWORKS resolved the plane class through the live archive map in P01 YZ, P03 YZ, P04 baseline A and P04 YZ. The P01 and P03 traces also located the enclosing profile's matrix flag immediately after the plane axis. The production reader still needs a structural walk to the profile occurrence before it can use this evidence. [Field layout and licensed traces](../../../re/solidworks/records/PrincipalSupportCandidates.md#licensed-loader-observations)
