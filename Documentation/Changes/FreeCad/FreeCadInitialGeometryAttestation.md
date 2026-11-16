# Initial FreeCAD extrusion geometry remains unqualified

Fresh history-generated FreeCAD Create extrusions no longer report `application_usable=True` or `vendor_loadable=True` merely because their inputs contain no unsupported retained BREP.
The scoped reconstructed path now reports both fields as false in the write result and its metadata.
It covers standalone documents whose sole active non-reference history step is a supported extrusion with an explicit Create or omitted operation and no retained BREP or usable mesh representation.
Empty or unusable meshes and nonreserved auxiliary or verification notes do not supply initial geometry and no longer exclude that scope.
The existing native-document and native-binding payload predicates preserve their separate native routes.
Sketch-reference dependencies remain in scope because they do not supply a native solid base.
The emitter defaults an omitted operation to Create.
The initial empty-dependency shortcut did not represent that emitter contract and is replaced by this bounded history classification.
Exact native replay and histories with other solid, Boolean, native or imported steps keep their existing behavior and remain outside this audit.
Other retained-payload roles, BREP and usable mesh routes remain separate audit boundaries; a nonempty container does not prove initial native geometry or acceptance.
The [base-selection gotcha](../../Gotchas/Conversion/FreeCad/ExtrusionBaseAttestation.md) records the distinction between history dependencies and native solid ownership.

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

New public process coverage exercises forward, reversed, implicit-direction and symmetric authored controls through the neutral JSON codec, plus explicit/default Create with a sketch-reference dependency and omitted operation without dependencies.
It checks research output and false flags, plus strict refusal with unchanged empty and existing streams, an absent path and an existing path.
Additional empty-mesh and auxiliary/verification-note controls preserve these checks.
Notes retain their native-payload carrier classification and strict opaque-source refusal instead of being treated as a shape.
Local verification is static only; hosted process execution and independent fresh native acceptance remain required.
The [source-owner hosted observation](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6931236006) at `161885d8ec4442ddc2558a740fd2cd153a6c0819` reports all 54 intended cache and attestation cases passed, within a stage that failed on two unintended helper entries.
The [helper naming repair](FreeCadProcessHelperCollection.md) changes only those names and their callers, preserving the cases and assertions.
See the [initial recompute limitation](../../Gotchas/Conversion/FreeCad/GeneratedExtrusionRequiresRecompute.md) and [CAD success criteria](../../Reference/Operations/CadSuccessCriteria.md).
