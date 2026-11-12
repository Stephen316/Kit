<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Independent documentation entries

## Behavior

New change records and gotchas use separate PascalCase Markdown files.
Their directory listings provide navigation without a shared list to update.
Gotchas are grouped in topic directories.
The existing landing pages explain how to write and find entries.
All 40 previously listed gotchas retain their titles, text, and source links.

Update the affected guide and link the specific entries in the PR.
Use a filename that identifies the change or the behavior.
Record later behavior in a new entry and the current guide.
Correct a historical entry if it misstates the original event or its evidence.

PRs that edit the same guide or choose the same filename can still conflict.
When updating an older branch, move its new gotcha text into a separate file.
Keep its change entry and discard the redundant change-index line.

## Conflict audit

The audit window was November 10, 2026 at 23:23 PST through November 11 at 23:23 PST.
The audit inspected 19 reachable merge commits in local refs, reflogs, and the retained heads of recent PRs.
`git show --remerge-diff` reconstructed each recorded merge from its two parents.
The audit counts repeated repairs separately.
It cannot see conflicts resolved only in a rebase, squash, or unreachable history.

Fifteen commits had documentation conflicts, with 50 file conflicts across those commits.
The gotcha log conflicted nine times and the change index five times.
Twelve merge commits hit at least one of these shared files.
Two commits also recorded an add/add conflict for the same change-entry filename.
The remaining conflicts involved overlapping work on the same guides and historical entries.

In the table, paths are relative to `Documentation/` except for the repository README.

| Merge commit                                                                                  | Documentation paths in conflict                                                                                                                                                                                                                                                                            |
| --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [d64005bfa](https://github.com/TryUniCAD/Kit/commit/d64005bfa16fd1bf0d56103dd3ed74b03ec9386f) | `Changes/ConfigurableReviewers.md`, `Changes/QueueScorecard.md`, `Changes/ReviewProviderExclusions.md`, `Gotchas/README.md`, `Reference/Operations/Policy.md`                                                                                                                                              |
| [3a6a9b784](https://github.com/TryUniCAD/Kit/commit/3a6a9b784e55681520bab400d27afe0dbb0dd3a0) | `Gotchas/README.md`                                                                                                                                                                                                                                                                                        |
| [ba479b86f](https://github.com/TryUniCAD/Kit/commit/ba479b86f9347f58b84173a9183058004021fba1) | `GettingStarted.md`, `Gotchas/README.md`, `Index.md`, repository README                                                                                                                                                                                                                                    |
| [c838594df](https://github.com/TryUniCAD/Kit/commit/c838594df824090328057f484b046dec5057bc0a) | `Changes/Index.md`                                                                                                                                                                                                                                                                                         |
| [8d012f3e3](https://github.com/TryUniCAD/Kit/commit/8d012f3e3fe0c84220371a752c0db37a915c188c) | `Changes/ConfigurableReviewers.md`, `Changes/DocumentationFoundation.md`, `Changes/QueueScorecard.md`, `Changes/ReadmePresentation.md`, `Changes/ReviewBotConfiguration.md`, `Changes/ReviewProviderExclusions.md`, `Gotchas/README.md`, `Index.md`, `Publishing.md`, `Reference/Overview/Contributing.md` |
| [e83a796b8](https://github.com/TryUniCAD/Kit/commit/e83a796b857f320d11cf65855cf023425a6842e4) | `Changes/ConfigurableReviewers.md`, `Changes/ReviewBotConfiguration.md`, `Reference/Overview/Contributing.md`                                                                                                                                                                                              |
| [22dd625ce](https://github.com/TryUniCAD/Kit/commit/22dd625cecaf9bcde3deb6b01fb39a6f01b5e75f) | `Changes/ConfigurableReviewers.md` (add/add), `Changes/Index.md`, `Changes/ReviewBotConfiguration.md`, `Gotchas/README.md`, `Reference/Overview/Contributing.md`                                                                                                                                           |
| [f8b43c458](https://github.com/TryUniCAD/Kit/commit/f8b43c458a99d5b2d87b6b5975085796ec0bbe88) | `Changes/ConfigurableReviewers.md` (add/add), `Changes/ReviewBotConfiguration.md`, `Reference/Overview/Contributing.md`                                                                                                                                                                                    |
| [e2d3b0325](https://github.com/TryUniCAD/Kit/commit/e2d3b03256be313ed6fb69a82d8f0f4b354a27d6) | `Gotchas/README.md`                                                                                                                                                                                                                                                                                        |
| [094acb3b7](https://github.com/TryUniCAD/Kit/commit/094acb3b77480688914270d8bd1d8e7ce86b97d8) | `Gotchas/README.md`                                                                                                                                                                                                                                                                                        |
| [ee2f2d456](https://github.com/TryUniCAD/Kit/commit/ee2f2d4568dd0261fded88bd44f9188bd7942cd2) | `Changes/Index.md`                                                                                                                                                                                                                                                                                         |
| [0747939a7](https://github.com/TryUniCAD/Kit/commit/0747939a781d829fbc997c01f91661b7161aed73) | `Changes/ConfigurableReviewers.md`, `Gotchas/README.md`, `Publishing.md`                                                                                                                                                                                                                                   |
| [447e9858f](https://github.com/TryUniCAD/Kit/commit/447e9858fffb766803d9626585adc3a10c0b299e) | `Changes/DocumentationFoundation.md`, `Changes/QueueScorecard.md`, `Changes/ReadmePresentation.md`, `Changes/ReviewBotConfiguration.md`, `Changes/ReviewProviderExclusions.md`, `Gotchas/README.md`, `Index.md`, `Publishing.md`, `Reference/Overview/Contributing.md`                                     |
| [e581582ce](https://github.com/TryUniCAD/Kit/commit/e581582cef54a15d7b5832761aaefd2b90b11d79) | `Changes/Index.md`                                                                                                                                                                                                                                                                                         |
| [c69fe468e](https://github.com/TryUniCAD/Kit/commit/c69fe468eb5d6bd8f3b3cd198e6b071378377e58) | `Changes/Index.md`, repository README                                                                                                                                                                                                                                                                      |

## Verification

Compared the relocated gotcha text and link destinations with the source list on `main`.
Inspected the changed navigation and contribution instructions.
Product tests run in remote CI.
The audit does not measure the future conflict rate or verify wiki publication.
