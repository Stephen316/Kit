# A saved viewport size is window state, not a sheet property

## Expectation

The viewport width and height in a Fusion drawing belong to the sheet.
A writer can copy them for each paper size.

## Actual behavior

The drawing writer wrote a viewport of 673.449911 by 325.726989 for every sheet.
These values came from one A1 control.
They do not follow from the A1 paper size.
They record the window that was open when Fusion saved that control.
The same writer also copied an auto-created layout value of 1048815 with no known meaning.

## Workaround

Compute a viewport from the paper size, or omit it when Fusion makes it again on open.
Test both choices in local Fusion with more than one paper size.
Decode a copied value before you write it.
If you cannot decode it, test whether Fusion accepts the record without it.
See the [donor data ban](../../../../Reference/Research/FusionDonorBan.md).
