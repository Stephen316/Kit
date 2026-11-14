# Donor data ban for Fusion writers

## Purpose and scope

This page applies the [no donor blocks standard](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md) to the Fusion codecs in `src/convert/formats/Fusion/`.
Read it before you write or review a Fusion writer, a default table or a data file under `src/`.
The standard has the highest priority in the repository.
This page adds Fusion examples and checks. It does not relax the standard.

## The rule

Kit must make every byte of a Fusion document from format knowledge.
No byte that Fusion saved can ship in `src/` or in Kit output.
Donor files and donor blocks are banned without exception.
A "generic" template is a donor block.
A fallback to donor data is also banned.
A writer that cannot make a field from format knowledge must refuse the input.
It must not borrow the field from a saved document.

## Terms

| Term                | Meaning                                                                          | Fusion example                                         |
| ------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------ |
| donor file          | A vendor-saved file that a writer opens, copies or patches to make output        | A Fusion-saved drawing used as the base of a new sheet |
| donor block         | Vendor-saved bytes, rows or records kept in source or package data               | Header and table rows captured from one A3 ISO drawing |
| case-specific value | A value captured from one document or fitted to one case                         | Body path id 306, the body id of one control design    |
| per-case table      | A table with one captured or fitted entry for each layout, size or value         | Form stencil tables keyed by a hash of one cage layout |
| format vocabulary   | Declared facts about the format, such as class names, enum codes and field order | Feature record class names in the schema vocabulary    |
| proven constant     | A value that is the same in unrelated documents, with its reason recorded        | ZIP method 93, which marks a Zstandard member          |

## Banned in `src/` and in output

- Files, records or byte runs from a Fusion save, in any encoding.
- JSON, XZ or binary package data with captured rows, coordinates, ids, ratios or window states.
- A lookup keyed by a case, a layout hash, a paper size or a value, when its entries were captured or fitted.
- A default that is the first value found in a control, such as a point at (2, 1.5, 2).
- Runtime reads from `re/`, `tests/`, `examples/` or another research tree.
- A patch at known offsets over a recorded payload.
- A constant that nobody can explain field by field.

## Allowed

- Format vocabulary that is readable in source and that points to a finding in `re/`.
- A proven constant in its smallest form, with the documents that show it and the reason it cannot change.
- Values from the source document when Kit converts that same document.
- Values that Kit computes from the requested model, such as sizes, ids, positions and counts.

## The research exemption

The ban does not apply to the `re/` research directory.
`re/` can keep Fusion-saved controls, captured tables, fitted rows and experiment scripts.
A research script in `re/` can read those files.
Code in `src/` must never load a file from `re/`.
A captured table that moves from `re/` into `src/` becomes donor data.
A Fusion-saved control is an experiment baseline only. It never becomes part of the output.

## Scale

A rule must work for inputs that it was not fitted on.
Test each rule on held-out cases in local Fusion before you promote it.
A rule that needs one entry for each size, layout or value is a table, not a rule.
Find the relation that makes the entries.
Equal values in all controls are not proof when all controls share one design.
Make controls from unrelated designs before you call a value constant.

## Replace donor data

1. Find the value and the field that holds it.
2. Make controls in local Fusion through the public API. Change one input in each control.
3. Compare the saved values with the inputs. Write the relation in `re/`.
4. Put the relation in the writer and remove the captured value.
5. Make held-out cases with inputs that the steps above did not use.
6. Open the Kit output in local Fusion. Compare it with Fusion's own save of the same case.
7. Record the evidence in the change entry and in the [Fusion data model](FusionDataModel.md).

Use black-box experiments only.
Do not disassemble, decompile, debug or trace Fusion or its libraries.
Do not try to reproduce a vendor integrity or trust check.

## Review checklist

A change is not finished if the answer to any of these questions is yes:

- Does a file under `src/` hold a number, string or byte run copied from a Fusion save?
- Does a data file under `src/` hold rows captured from controls?
- Does a lookup use a hash of one case as its key?
- Does a default come from something other than the schema type or a recorded proven constant?
- Does a code path under `src/` read a file from `re/`?
- Are held-out cases missing from the acceptance evidence?

## Audit of the Fusion writers

An audit of `src/convert/formats/Fusion/` found the items below.
Each row names the data, why it is donor or case-specific data, and the general rule that replaces it.

| Item                                     | Data and origin                                                         | General rule                                              |
| ---------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------- |
| Drawing view body path                   | Path id 306 in every view representation, the body id of one design     | Take the ids from the view source                         |
| Drawing view source bytes and body key   | 16 opaque bytes and a 40-bit key, the same in all views of one design   | Decode them against other designs                         |
| Drawing view state mark                  | Five opaque bytes copied from one capture                               | Identify the field or prove it constant                   |
| Drawing sheet defaults                   | A captured circle and other values from one design                      | Keep format defaults only and place geometry from input   |
| Feature defaults                         | First-instance values from 16 controls                                  | Use schema type defaults and values from the feature      |
| Drawing viewport size                    | 673.449911 by 325.726989, the window state of one save                  | Compute from the paper size or omit                       |
| Drawing auto-created layout mark         | The extended data value 1048815 copied from one save                    | Decode or omit                                            |
| Drawing dimension text ratios            | Extent and digit ratios fitted from the single text "40"                | Use font metrics                                          |
| Form stencil and shape tables            | Eight per-layout tables and eight shapes, keyed by a hash of the layout | Derive stencils from the local cage neighbourhood         |
| Drawing ISO standard                     | 392 rows from one A3 ISO control, with save history                     | Make the header and tables from the format and paper size |
| Drawing view shape flags                 | Flags captured for base, right and top views only                       | Derive the flags for every projection                     |
| Drawing record numbering                 | Fixed local references, source id and act identifiers                   | Number each source and sheet                              |
| Drawing dimensions and material families | Horizontal linear dimensions and metal materials only                   | Add the other families from their records                 |
| Form crease thresholds                   | 0.65 and 1.15 degrees from probes, with a refused gap                   | Find the rule that Fusion applies                         |

The [donor audit change entry](../../Changes/Fusion/Policy/FusionDonorAudit.md) records the status of each item.

## Related information

- [No donor blocks standard](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md)
- [Research method](Methodology.md)
- [Fusion data model](FusionDataModel.md)
- [Fusion acceptance evidence](FusionAcceptanceEvidence.md)
- [Donor gotchas](../../Gotchas/Conversion/Fusion/Donors/)
