# Configuration root visual properties

After the [named part root](ConfigRoot.md), the model's inherited concept calls the typed `moVisualProperties_c` pointer operator at `sldmodu+0x1038455` using the concept's own `+0x78` field. This matches the [CMgr part configuration hook](CmgrVisual.md#saved-spans) because both fields dispatch the same class serializer. The preferred address and installed module hash are in the [root field evidence](ConfigRoot.md#native-field-authority).

The Config-0 tag allocates class 6 and visual object 7 on the already active part archive map. The visual body uses inline records and consumes no further allocations. The model serializer then saves its units-table pointer at `sldmodu+0x10ec62e`. The checked parser reaches this definition with next index 8. The units-table tag would allocate class 8 and object 9.

The [material and RealView writer](CmgrVisualPrefix.py) supplies the first 517 bytes in the measured installation. It is followed by the [300-byte DSPBR constructor](ColorAppearance.py). The RealView presence comes from the inline material object's own pointer and the DSPBR presence comes from the visual object's separate pointer. Their stores are `0x3c861c29` and `0x3c930dba` in the [pinned sldmfcu module](CmgrVisual.md#version-and-ownership). The saved default-appearance option has its own field. The RealView ID is the caller's allocated 64-bit PW appearance ID. It is independent of the class and object IDs and stored inside the RealView body. The DSPBR colors come from the owning surface color.

`WriteConfigVisual` takes both presence states and the already allocated appearance ID. It admits the witnessed profile with both inline objects present. The same composable writers take the material locator for the target installation as input. Another locator length changes the record width and the enclosing split calculation.

## Replay

```sh
python re/solidworks/WriterResearch/VerifyConfigVisual.py --read-only
```

The six P01 and eight P03 pinned saves each contain an 817-byte visual body. Each body matches that file's independently parsed CMgr visual object exactly, including appearance ID and the entire DSPBR record. The saved ID frequencies are 4 in five saves, 5 in five, and 6 in four. The replay SHA-256 is `4fa9ad81435c8a0231ce0f280e62b29648dffa409d9be17e621bc73584aec82b`. Its digest covers compact JSON rows of native file hash, visual tag offset, visual body start and end, PW appearance ID, next index and body SHA-256, in receipt order.

Hosted `CheckConfigVis` composes the named part root and the visual object through that same allocator, then compares their exact saved bytes. The hosted run and native acceptance remain pending. The next unconstructed record is the typed units table.
