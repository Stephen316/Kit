# A template drawing is a donor file

## Expectation

A drawing writer can start from a sheet that Fusion saved, keep its header and tables, and add Kit views and dimensions.
If Fusion opens the result, the writer works.

## Actual behavior

A template carries hundreds of header variables and table rows from one save.
These include float noise in the extents, the active viewport, the plot scale and save history identifiers.
Every Kit drawing then ships the same vendor bytes, whatever its paper size, standard or design.
The writer does not show that Kit can make a drawing.
It only shows that Fusion can open a file that Fusion saved.
A template is a donor file under the [donor data ban](../../../../Reference/Research/FusionDonorBan.md), even when it is called generic.

## Workaround

Make the header, the tables and the sheet objects from format knowledge and the requested paper size and standard.
Keep Fusion-saved drawings in `re/` as controls only.
To test Kit objects in isolation, put them into a control in `re/` and open that control in local Fusion.
Never ship that control or any part of it.
