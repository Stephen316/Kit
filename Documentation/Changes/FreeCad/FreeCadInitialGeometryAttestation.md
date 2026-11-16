# Initial FreeCAD extrusion geometry remains unqualified

Fresh history-generated FreeCAD Create extrusions no longer report `application_usable=True` or `vendor_loadable=True` merely because their inputs contain no unsupported retained BREP.
The scoped reconstructed path now reports both fields as false in the write result and its metadata.
It covers standalone documents with an active no-base Create extrusion and no retained BREP, BREP payloads or meshes.
Exact native replay and other retained-BREP or mesh routes keep their existing behavior.

The [independent initial-open witness](FreeCadEndNativeWitness.md) measured zero solids in all three original generated packages before native recompute.
The earlier geometry predicate skipped documents without BREP, so it could return true without examining any generated initial solid.
Post-recompute geometry and saved-copy reopen evidence do not establish the initial originals' usability.
Computed initial shape caches also remain unqualified until independent initial-open measurement establishes the required native acceptance.

The public writer retains its existing policy.
`WriteDocument(..., AllowCarrier=False)` refuses these unqualified reconstructions before committing the caller's stream or path.
Use explicit `AllowCarrier=True` only to obtain an honestly attested research artifact for inspection.
This option permits output; it does not establish application usability, vendor loadability or product acceptance.
The current two-length readiness, binding and reversal observers now select that explicit research mode and check false result and metadata flags while retaining their XML, owner, geometry and refusal assertions.
Historical reports, hashes and source observations remain unchanged.

New public process coverage exercises forward, reversed, implicit-direction and symmetric authored controls through the neutral JSON codec.
It checks research output and false flags, plus strict refusal with unchanged empty and existing streams, an absent path and an existing path.
Local verification is static only; hosted process execution and independent fresh native acceptance remain required.
See the [initial recompute limitation](../../Gotchas/Conversion/FreeCad/GeneratedExtrusionRequiresRecompute.md) and [CAD success criteria](../../Reference/Operations/CadSuccessCriteria.md).
