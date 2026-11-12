<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Write technical information

## Purpose and scope

Use this page when you write or change maintained Kit documentation.
These project rules apply ASD-STE100 principles to software information.
The [standards scope](Scope.md) states the limits of the available source evidence.

## Language

Use direct statements with a clear subject.
Give each term one meaning in its context.
Use the same term for the same item throughout a procedure.
Define technical terms in the [term register](Terminology.md).

Use dictionary-approved words with their approved meaning and part of speech when the complete dictionary is available.
Check technical nouns and technical verbs against the applicable ASD categories.
A term in the project register is not automatically an approved ASD word.
Record an unresolved word as a language-review gap.

## Sentences and paragraphs

Use no more than 20 words in a procedural sentence.
Use no more than 25 words in a descriptive sentence.
Give one instruction per sentence, except for actions that must occur together.
Put a necessary condition before its instruction.
Use the imperative form for instructions.

Use one subject per paragraph.
Keep paragraphs short enough to read without losing the subject.
Do not remove articles to shorten a sentence.
Avoid semicolons, idioms, contractions, and ambiguous pronouns.
Use positive instructions when they are clearer.
Use a prohibition when it identifies a necessary restriction.

Count words with the ASD rules during a complete language review.
A simple whitespace count is only a screening aid.
Code, filenames, abbreviations, and parenthetical text need the standard's specific treatment.

## Procedure structure

Each task page contains the following information:

| Element             | Required content                                 |
| ------------------- | ------------------------------------------------ |
| Purpose             | The task outcome and intended reader             |
| Before you start    | Access, software, files, and initial conditions  |
| Procedure           | Ordered actions with exact commands where useful |
| Expected result     | Observable output and success conditions         |
| If the task fails   | A symptom, an action, and a stop condition       |
| Related information | Relevant reference and next-task links           |

Place a data-loss caution before the action that can cause the loss.
Keep required actions out of notes.
Put limits and expected results beside their related steps.
Do not hide a necessary condition in another page.

## Code and API names

Copy API names, keyword names, and error codes exactly.
Use inline code for these identifiers.
Use fenced blocks with a language identifier for examples.
Do not add explanatory comments or comment-oriented docstrings to code examples.
Explain the example in the surrounding text.

State all input-file prerequisites before an example.
Identify user-selected paths as examples.
Do not present a fictitious output as an observed result.
Do not claim that an example ran unless execution evidence exists.

## Tables and diagrams

Use tables for comparable values.
Give each column a clear heading.
Keep the units with the value or column heading.
Use `MiB` for 1,048,576 bytes and `GiB` for 1,073,741,824 bytes.
Escape a literal pipe in a Markdown table cell.

Use diagrams when a relationship is difficult to describe in prose.
Provide the essential relationship in text beside the diagram.
Do not make color the only carrier of meaning.
Use descriptive link text and meaningful image alternatives.

## Examples of project editing

| Avoid                                           | Use                                                        |
| ----------------------------------------------- | ---------------------------------------------------------- |
| The converter seamlessly handles all formats.   | The registry lists the available adapters.                 |
| Simply enable strict mode to get perfect files. | Set `allow_carrier=False` to apply the output policy.      |
| If this fails, try relaxing the checks.         | Record the error code before you change the input.         |
| The hash proves authenticity.                   | The hash detects a change relative to the expected digest. |

These examples describe Kit behavior.
They do not replace the complete ASD dictionary review.

## Review

1. Read the page as the intended user.
2. Check each instruction against the source.
3. Check each technical term against the term register.
4. Check sentence length and grammar.
5. Check the rendered tables, code, links, and diagrams.
6. Record the review result in the PR.

See [documentation review](../Maintenance/Review.md) for evidence requirements.
