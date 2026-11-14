# SOLIDWORKS paired captures

A02c now has 37 native SOLIDWORKS part files for the five [paired recipes](../../../re/automation/PairSpecs.json).
The parts were independently authored from the recipes through the SOLIDWORKS API.
The application reports revision `34.4.1` and executable build `34.4.1.1011` (SOLIDWORKS 2026).

| Case | Parts | Baseline measurement | Capture |
| --- | ---: | --- | --- |
| P01 | 6 | Fully defined rectangle, 800 mm² | [Files and evidence](../../../re/automation/PairedCaptures/P01/solidworks-75b9308cf13e/) |
| P02 | 5 | Fully defined circle, 78.5398 mm² | [Files and evidence](../../../re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39/) |
| P03 | 8 | Blind boss, 8,000 mm³ | [Files and evidence](../../../re/automation/PairedCaptures/P03/solidworks-db1390476325/) |
| P04 | 11 | Face-supported blind cut, 7,680 mm³ | [Files and evidence](../../../re/automation/PairedCaptures/P04/solidworks-c1986308375a/) |
| P05 | 7 | Annular revolution, 1,206.3716 mm³ | [Files and evidence](../../../re/automation/PairedCaptures/P05/solidworks-c3d4361662e0/) |

Open `baseline-a` for the original part. Each capture includes a repeat baseline, independent parameter edits, an inch display variant, and the applicable YZ, reversed boss, or through-all cut variants. The measurements and SHA-256 receipts sit beside the native files.

SOLIDWORKS was restarted between baseline saves. All 37 parts reopened and rebuilt with zero load or save warnings or errors. The control part measured 881,814.3482 mm³ before and after each case. The recorded sketch areas, volumes, centres of mass, and edit-and-restore results were checked against the recipes.

The [authoring guide](../../Reference/Research/SolidWorksCaptureAuthoring.md) links the original C# capture source and gives a repository-relative launcher for repeat runs.

Rectangle corners use shared SOLIDWORKS sketch points. Two equations keep the P04 cut centred as the parent or cut dimensions change. P05 uses a fixed construction centreline on world +Z. Its 90° edit sweeps from +X towards +Y.

The captures are research evidence for the [A02c step](../../Reference/Research/AutomationSteps.md#a02-implementation-and-verification). The lineage and independent qualification audit remains in A02d.
