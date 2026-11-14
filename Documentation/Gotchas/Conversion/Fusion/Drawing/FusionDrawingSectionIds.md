# A gap in the DWG section ids makes the drawing invalid

Fusion 2706.1.17 rejects a drawing DWG whose section ids leave a gap.
It shows the dialog `Fusion Drawings Message` with the text `Drawing file is not valid.`
The open then never returns.

Each variant below starts from `Q1NoDataStore`.
That base is the A1 control without unused blocks and AutoCAD Mechanical objects.
It has no `AcDb:AcDsPrototype_1b` section, and every object has its data-store flag cleared.

| Variant              | Sections removed                                  | Section ids         | Result                      |
| -------------------- | ------------------------------------------------- | ------------------- | --------------------------- |
| `Q1NoDataStore`      | `AcDb:AcDsPrototype_1b`, which had the highest id | 1 to 12             | Opened in 4.7 s with 3 views and 1 dimension |
| `Q5NoRevHistory`     | Also `AcDb:RevHistory`                            | 1 to 12 without 8   | Dialog after 10 s           |
| `Q3NoOptional`       | Also `AcDb:Preview`, `AcDb:RevHistory` and `AcDb:AppInfoHistory` | 1 to 11 without 8 and 10 | Dialog after 8 s |

`Q8AuthoredSections` removes `AcDb:Preview` and `AcDb:AppInfoHistory` and numbers the rest 1 to 10.
It opened in 5.2 s with 3 views and 1 dimension.
Fusion therefore accepts a drawing without those two sections when the ids stay contiguous.

`Q5NoRevHistory` removes one section and leaves one gap.
It does not show whether Fusion needs `AcDb:RevHistory` itself or only contiguous ids.

Kit's authored shell writes the ten sections of `Q8AuthoredSections` with ids 1 to 10.
It writes no data-store section and clears every data-store flag.
