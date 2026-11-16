# Conversion SDK completion roadmap

Kit has working SDK infrastructure and qualified format subsets.
It does not yet provide complete editable conversion across its intended CAD families.
The next product milestone is a measured, editable SOLIDWORKS ↔ Fusion conversion through the public SDK.

Use the [conversion backlog](Documentation/Maintenance/ConversionBacklog.md) for task IDs, ownership, dependencies, open PRs and completion evidence.
That register is the entry point for available work.
PR #94's step register remains authoritative for its research programme.
Read the linked PR and its current head before claiming a task.

## Current position

This snapshot describes main `e04e7b78699d3f567409937007b00b567620078a`, inspected on 2026-11-15.
Open PR work is listed separately in the backlog.
The previous 22/100 estimate is retired because it counted historical capabilities that no longer describe the production adapter.
No replacement percentage is claimed without a complete acceptance matrix.

| Family                  | Production position at this revision                                                                       | Remaining product requirement                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| SOLIDWORKS              | Part and assembly reader. The recorded-payload writer was removed.                                         | Generative native output, broader semantic reads and qualified editable routes.                     |
| Fusion                  | Public reader and writer for qualified parameter, circle, rectangle, cylinder, cuboid and frustum graphs.  | General portable feature graphs, broader schemas, configurations and qualified cross-format routes. |
| FreeCAD                 | Archive reader and writer with geometry, feature and assembly paths.                                       | Per-version semantic coverage and measured acceptance for each claimed conversion direction.        |
| CATIA V5                | Part/product adapter with bounded native interpretation and preservation paths.                            | Complete geometry, parametric history and independently measured native conversion.                 |
| NX                      | No production adapter on this main revision. PR #115 adds native research and adapter work.                | Qualified semantic reads and independent editable writing.                                          |
| Creo                    | No production adapter on this main revision. PR #117 adds PSB research and adapter work.                   | Qualified semantic reads and independent editable writing.                                          |
| Rhino                   | No production adapter on this main revision.                                                               | Format/version contract, reader, writer and target acceptance.                                      |
| AutoCAD                 | No standalone production adapter on this main revision. Fusion drawing codecs are a separate bounded path. | Format/version contract, neutral drawing model and qualified standalone routes.                     |
| Parashell               | No separate public format contract or adapter on this main revision.                                       | Define its format identity and relationship to FreeCAD, then qualify its routes.                    |
| Kit JSON and shared SDK | Neutral model, serialization, discovery, conversion API, CLI and packaging exist.                          | Complete route evidence, operational hardening, user evaluation and release qualification.          |

Registration, same-format reconstruction and retained native bytes do not establish cross-format editability.
See [format selection](Documentation/Tasks/SelectFormat.md) and the [Fusion public contract](Documentation/Changes/Fusion/Adapter/FusionPublicAdapter.md).
The [SOLIDWORKS guide](Documentation/Reference/Adapters/Solidworks.md) documents the production write restriction.

## Destination

A fully functional release covers all nine CAD families above through one documented public SDK and CLI.
Every claimed input type, vendor version, feature family and conversion direction has explicit scope and acceptance evidence.
The release matrix must identify unsupported combinations before a conversion starts.
An unsupported route remains unfinished roadmap work and fails explicitly at runtime.

Each supported route must meet every [CAD success criterion](Documentation/Reference/Operations/CadSuccessCriteria.md).
Conversion uses no CAD runtime or donor data.
It preserves geometry, editable history, sketches, dimensions, constraints, expressions, materials and applicable assembly, configuration and drawing semantics.
Target applications must open, rebuild and measure the output correctly.
Independent driving edits, restoration, save and fresh-process reopen must pass on held-out inputs.
Source and target controls must bracket the measurements.

The release also needs reproducible installation, bounded resource use, secure file handling and clear failure reports.
Documentation and CLI tasks must be evaluated by their intended users.
Completion concerns a published version matrix, not every future vendor release.
Choosing that matrix is backlog task B01, not permission to discard required source information.

## Ordered milestones

| Milestone                                 | Work and dependencies                                                                                                | Evidence required to finish                                                                                                               |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| M0: establish the baseline                | B01 records file types, versions, features, fixtures and directional routes. Maintain this roadmap and PR ownership. | Every family and intended route has a supported, unsupported or unverified entry with evidence and an owner.                              |
| M1: qualify the first paired designs      | B02 closes PR #94's independent source evidence and semantic qualification.                                          | Qualified initial sketches, bosses and cuts preserve every required relation. Reserved holdouts remain independent.                       |
| M2: deliver the first editable conversion | B03–B05 compare graphs, prove field rules, build portable writers and validate both directions.                      | SOLIDWORKS → neutral → Fusion and Fusion → neutral → SOLIDWORKS pass the public SDK and all applicable CAD criteria.                      |
| M3: cover ordinary part histories         | B06 expands sketches, references, operations, geometry and historical schemas. Integrate B08's existing format work. | Each feature/version extension has held-out, editable target acceptance. No required native semantics remain opaque on a supported route. |
| M4: cover complete documents              | B07 adds assemblies, mates, configurations, external references and drawings.                                        | Component resolution, placements, constraints, variants, dimensions and model links survive conversion and edits.                         |
| M5: complete all intended families        | B09 extends qualified readers and writers to every family. B12 closes the directional route matrix.                  | Every promised route and version passes full preservation and independent target acceptance, including failure cases.                     |
| M6: qualify the release                   | B10, B11, B13 and B14 complete user evaluation, packaging, security and operational evidence.                        | Published support matrix, reproducible release, passing required CI/reviews and merge-group acceptance.                                   |

M0 and user-facing improvements can proceed alongside the conversion critical path.
Each broader format can advance when its own prerequisites are available.
M5 still depends on complete-document acceptance for every promised route.
Do not delay narrow qualified releases until every family is complete.
Label each release with its actual supported matrix and remaining roadmap gaps.

## Next action

Continue **B02 on PR #94**, rather than starting another Fusion decoder PR.
Its inspected register still requires fresh native Fusion readback for the pinned P01, P03 and P04 discovery captures.
The captures cover rectangular sketches, blind bosses and cuts.
Record exact source hashes, native observations, load/rebuild errors and the control results.
Use the observations to address the remaining A02d, A04c and A05c requirements before qualifying A06 graph comparisons.
P05 remains reserved for independent holdout acceptance.
Licensed application access is a prerequisite for this evidence, not a production conversion dependency.

The next independent task outside that programme is **B01: publish the supported version and route matrix**.
It can proceed while native evidence is unavailable.
It must reuse current adapter facts and PR ownership rather than create a second research plan.

## Maintenance

Update the backlog whenever a task is claimed, changes scope, becomes blocked, opens a PR or gains completion evidence.
Update this roadmap when a milestone or the production support boundary changes.
Keep implementation status in its owning register and link it here.
An open PR, successful decode, green PR check or application screenshot alone never completes a conversion milestone.
Follow [AGENTS.md](AGENTS.md) and the [documentation review procedure](Documentation/Maintenance/Review.md).
