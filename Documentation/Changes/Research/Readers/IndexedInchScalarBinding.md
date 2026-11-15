# Indexed inch scalar binding

## Behavior

A04c builds one scalar-name index for each resolved owner when the document displays linear dimensions in inches.
Feature construction and linked-child rebinding share those indexes during the same native decode.
Each index entry retains every original candidate scalar in the original roster order.
The index preserves duplicate names instead of replacing a candidate with the last matching scalar.

The inch binder continues to require one candidate with a native identifier, an eligible role, and a matching rounded display value.
Missing precision, excessive display precision, duplicate names, display-only roles, and unmatched values remain unresolved.
Resolved dimensions retain the scalar's value, offset, role, and operands.
Non-inch value matching keeps its existing behavior.

## Scope and source review

Previously, each inch dimension scanned its owner's complete scalar tuple by name.
Many dimensions under one stable owner repeated that scan during construction and linked-child rebinding.
The new owner indexes are built once and passed through both stages.
The binder then uses a name lookup rather than a scalar-roster comprehension.
The index has expected linear construction cost and expected constant-time lookup cost per dimension name.
This statement describes that binding work only.
It does not claim that every native decoding stage is linear.
Other scalar ownership and non-inch value searches retain their previous algorithms.

## Verification

New process scenarios write complete synthetic keyword XML and serialized scalar rosters to files.
A separate Python process reads them through the genuine native parser and returns its typed feature and scalar data.
One and 256-dimension rosters exercise direct ownership and four parents sharing the same child owner.
The scenarios compare values, native offsets, roles, operands, and unresolved-display markers.
Additional cases retain duplicate-name ambiguity, missing identity, display-only roles, rounding mismatches, and excessive precision.
The existing P02 inch-diameter public reader scenario remains part of the remote source gate.

Local work used source inspection, syntax parsing, formatting, and static policy checks only.
No local test, parser reproduction, native application, or model call ran.
Remote execution remains pending when this entry is introduced.
Synthetic parser inputs do not establish vendor-loadability or cross-format conversion acceptance.
See the [research reader guide](../../../Reference/Research/SolidworksResearchReader.md) and [ambiguity gotcha](../../../Gotchas/Research/Readers/InchNamesRemainAmbiguous.md).
