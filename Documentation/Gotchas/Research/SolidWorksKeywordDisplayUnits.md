# SOLIDWORKS keyword dimension display units

The numeric dimension text in `swXmlContents/KeyWords` can change with the document display settings while the authored binary length stays fixed. In the paired P01 captures, the same 40 mm width appears as `40` and `1.57` in the keyword stream. Both files store `0.04` in the named, feature-owned resolved scalar.

Read the native display unit and decimal precision before using keyword text to corroborate a scalar. Read the canonical length from the typed value. P04 also has matching named dimensions in `Contents/Config-0`, where the reader still needs native ownership evidence before it can bind the six sketch dimensions. [Resolved-feature inch lengths](../../Changes/Research/SolidWorksResolvedInchLengths.md)
