# SOLIDWORKS sketch style fields

Run `python re/solidworks/authoring/SketchStyleFields.py` for the six Git-pinned P01 discovery archives. The experiment uses constructor defaults to generate the 17-byte visual record and the standard-width payload from an explicit weight. It matches 60 visual records and 60 widths, plus the initialized display state of the six structural members. The compact JSON report has SHA-256 `a6f43b9c775be4ed0414db6d0cb9f48bba11b5b2eac5480b487534174cfec1c7` before its terminal newline. The earlier rectangle field report remains byte-identical. [Exact store and constructor evidence](../../../../re/solidworks/authoring/SketchStyleFields.md)

Physical member state remains observed. The next step is to trace how solve updates member color and constraint status before save. SOLIDWORKS remains read-only through the registry. Generated native document acceptance remains open. [CAD acceptance](../../../Reference/Operations/CadSuccessCriteria.md)
