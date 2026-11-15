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
It does not qualify face support, constraints, editable output or native conversion.
The production reader remains unchanged until class-reference and tag-domain proof is available.

## Evidence and limits

Read-only extraction examined the 25 committed P01/P03/P04 source files at `c1c3fcce5b8b67373113ec44ad5d122a52bd7260`.
Each rectangle span contained one candidate whose plane id matched the independent source measurement.
The [finding](../../../re/solidworks/records/PrincipalSupportCandidates.md) records offsets, field widths and the refuted fixed-signature assumption.
No local tests, collection, neutral decoding or native application ran.
Static syntax and source-link checks are separate from pending remote process verification.
A04c remains open.
