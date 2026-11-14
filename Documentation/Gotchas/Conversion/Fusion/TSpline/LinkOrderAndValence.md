# TSM link order and valence offsets

Kit reads the first two fields of a TSM `l` record as previous then next. Reciprocal-ring validation alone cannot distinguish them because swapping both labels still produces reciprocal rings. Kit-authored box cages that use this order import into Fusion and match its own box primitive.

Kit reads the low two bits of the final link word as a valence offset. Kit also reads bit zero of a face record's second word as hidden state. Those meanings come from earlier binary inspection and are not confirmed by a black-box experiment. Name these fields explicitly and reject unproved high bits. Validate opposite endpoints as well as reciprocal rings so the intended orientation is observable.

The [root-variant capture](../../../../../re/Fusion/LocalOracle/TSplineCodec/RootVariants/Capture.json) records the box cage comparison.
