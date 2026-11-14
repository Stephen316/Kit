# An id that matches every control can belong to one design

## Expectation

A value that is the same in every Fusion drawing control is a format constant.
A writer can then declare it as format vocabulary.

## Actual behavior

The drawing writer wrote path id 306 twice in every view representation body path.
Every control drawing had the same value, so it looked like a constant.
All of those controls came from one source design.
The value 306, or `0x132`, is the body id of that design, and the drawing source records it as `"5","132"`.
A drawing of any other design gets a body path that points at a body that does not exist.

The same audit found two more values with this shape.
The view source bytes and the 40-bit body key were the same in all views of that design.
No research note explained them.

## Workaround

Make controls from at least two unrelated designs before you call a value constant.
Compare each candidate field with the ids of the source design.
Take body ids and keys from the view source of the design that Kit draws.
Refuse a view whose ids Kit cannot derive.
See the [donor data ban](../../../../Reference/Research/FusionDonorBan.md).
