# Legacy SOLIDWORKS display transform padding

A saved `ForeShortDimXForm` can contain a nonzero word between matrix status and translation. The generation-19000 binary transform writer leaves this temporary word unwritten at transform offset 76. The native reader consumes the word with the fixed-width record, reconstructs the rotation from the nine matrix doubles and reads translation starting at offset 80. All eight pinned P03 files show the same observed padding value even though the serializer gives it no defined origin.

Treat the word as padding during field comparison. Use the matrix, translation, scale and flags to compare transforms. The scoped constructor emits deterministic zero. Keep the exact archived word only as raw save evidence. [Native operator and archive evidence](../../../../re/solidworks/WriterResearch/DisplayFavorite.md#intervening-base-fields)
