# Compare SOLIDWORKS discovery body measurements

The discovery census compares the neutral volume and geometric centroid from the active saved body with the licensed reopen volume and center of mass. The source values come from the independently measured single-solid P03 and P04 fixtures. The neutral values come from the ordinary reader's [typed active partition](SolidWorksActivePartition.md). P01 remains covered by its solid-count and sketch checks.

Run `python re/automation/SolidworksCensus.py --output /private/SolidworksDiscoveryCensus.json` and inspect the `neutral.body.volume_mm3` and `neutral.body.center_of_mass_mm` comparisons. The command uses the paired specification's absolute and relative volume tolerances and its absolute coordinate tolerance. These measurements describe the pinned source geometries. Editable conversion relies on separate destination acceptance. [Reader guide](../../../../Reference/Research/SolidworksResearchReader.md#discovery-census)
