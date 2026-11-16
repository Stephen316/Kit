# Standalone P03 visual-state component records

The eight receipt-pinned P03 saves at `466dcb172dfa3803463e07ccde963ba01671d200` contain six component-owner rows each. The physical member ends at byte 1789. A typed read consumed all 48 component records and the two terminal counts. An independent raw-DEFLATE expansion reached the exact compressed end and matched each declared size and CRC. Native addresses below are RVAs in the installed SOLIDWORKS 34.4.1.1011 libraries pinned with the preceding ownership work. [P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json) [Native module pins](VisualStateOwners.md#evidence-pins)

## Two component collections

The first two unsigned counts after the representation scalars end at byte 137. Byte 129 holds zero for the filtered component vector written at `sldvisualstateu` RVA `0x407f0`. The native reader consumes this count at `0x412ee` and skips its row loop at `0x41307` when empty. Byte 133 holds six for the separate component-owner map at root `+0x78`, whose `+0x80` count is stored at `0x40bfe`. This resolves the earlier attribution of the six rows to the first vector. The six object links described in the earlier checkpoint are from the second map. [Saved object links](VisualStateOwners.md#component-and-attribute-references)

The second map writes the owner pointer at `0x40c35`, the filtered representation count at `0x40d03`, each representation ID at `0x40d61`, and the attached-attribute count and pointers at `0x40e0f` and `0x40e48`. The load version gate at `0x41668` admits this map from generation `0xf34`. Its reader takes the count at `0x4167a`, the next representation count at `0x41bf4`, and the representation ID and attribute count at `0x41c17` and `0x41c25`. All six saved rows carry one representation with ID 1 and two attributes. The map size comes from the selected owner collection at save time. The prior note traces the configured representation and the live model's self component and feature selection.

## Component owner and reference fields

The `moCompHolder_c` and `moCompFeature_c` routes share `sldmodu!moCompRef_c::Serialize` at `0xa66160`. The component-taking base constructor at `0x6a7940` gets a component through the input component's virtual `+0x158` method and installs it at reference member `+0x58` at `0x6a7a09`. That pointer owns a fresh `moUnitComponent_c` in every saved row. The first row registers the class and each of the next five rows opens a new occurrence through the class slot.

With the standalone visual-state archive condition `0x20004000`, the `0x6000` test at `0xa662bd` selects the temporary filed-owner path. The helper's native `hasCondition` intersects the masks at `sldmfcu` RVA `0x8c03c`. The reference serializer saves the component's existing filed owner, clears it at `0xa662e3`, writes the component pointer at `0xa662ef` and restores the owner at `0xa66314`. The unit component serializer calls `moComponent_c::Serialize` at `0x10e99af`. On the standalone route the base's `0x82006000` condition test reaches the null filed-concept pointer write at `0x10da401`. The derived serializer adds a zero external-object byte at `0x10e9cd0`. These three body bytes exactly terminate the unit child in all 48 records. The live caller supplies the model self component. The archive stores its owner through the ordinary standalone branch, with the external object absent.

The enclosing `moCompRef_c` immediately resumes from the child return. Relative offsets below start at that return and use the signed Windows `long` width unless specified. The component-taking constructor initializes the default members at `0x6a7975–0x6a79e6` and the four unset selectors at `0x6a7a11` and `0x6a7a1c`. The saver independently clears the optional `+0x84` record. The existing component-reference evidence records the same primitive sequence in another archive context. [Existing reference framing](DisplayHandle.md#empty-component-reference)

| Offset | Native source | Saved field |
| ---: | --- | --- |
| 0–24 | `+0x68,+0x18,+0x1c,+0x20,+0x30,+0x70`, `0xa66340–0xa663b2` | Six zero words. `+0x20` is the ghost body ID and remains zero for these self-component references. |
| 24–28 | Setter and write at `0xa663b8–0xa663c4` | Zero optional record presence. |
| 28–40 | `+0xa0,+0x34,+0x48`, `0xa6642c–0xa66444` | Zero signed word, zero unsigned word and zero signed word. |
| 40–56 | Four words from `+0x90`, loop at `0xa66460–0xa66474` | Four signed unset values `-1`. |
| 56–76 | `+0xb0,+0xb8,+0xc0,+0xc8,+0xd0`, `0xa66476–0xa6653b` | Five zero presence words for absent children. |
| 76–80 | `+0x4c`, initialized from the native file version at `0x6a7a54–0x6a7a60`, emitted at `0xa66586` | Unsigned generation 19000. |

For a feature row, `moCompFeature_c` constructs an owned `moFRData_c` from the selected feature at `0x6d499e`. Its constructor obtains the feature ID by virtual call at `0x9f3676` and calls `moLoggedNode_c::getCreationTime` at `0x9f3685`. After the shared reference returns the feature serializer passes that owned object to `0x9f3e50` at `0xa658ca`. The helper stores a signed feature ID at `0x9f3e87` and a `su_CTime` at `0x9f3e9c`. The eight approved saves use the four-byte time form. The earlier ModelHeader join found the same native feature ID and creation clock for every row, including the different clocks when the YZ and reverse-direction sketches were reauthored. [Independent feature-log join](VisualStates.md#typed-appearance-and-feature-evidence)

| Owner | Unit body start | Unit return | Reference return | Feature return |
| --- | ---: | ---: | ---: | ---: |
| Self holder | 180 | 183 | 263 | — |
| RectangleSketch | 1204 | 1207 | 1287 | 1295 |
| Origin | 1321 | 1324 | 1404 | 1412 |
| Right Plane | 1432 | 1435 | 1515 | 1523 |
| Top Plane | 1563 | 1566 | 1646 | 1654 |
| Front Plane | 1674 | 1677 | 1757 | 1765 |

Each row next writes its representation count, representation ID and attribute count before the two attribute pointers. The final attribute reference ends at 1781. The component unit, base and feature-reference fields are constructible for this bounded standalone branch from their typed defaults, the authored model and the feature's actual ID and creation time. The root still needs the independent appearance allocation chronology and complete policy for the selected representation and state-attribute scalars. [Unresolved visual-state inputs](VisualStateOwners.md)

## Terminal representation attributes and tracker

Byte 1781 is the unsigned count of a separate root map at `+0x88` with count `+0x90`. The store calls helper `0x43c30` at `0x40f80`. Its first archive write is the count at `0x43c5b`. Populated entries would carry a signed representation key and a counted attribute collection. The loader calls `0x42de0` at `0x41db6` and reads its count at `0x42e3c` from generation `0xf50`. The root constructor initializes the map and count at `0x72d4f–0x72d7d`. All eight streams store zero and have no members in this map.

Byte 1785 is the signed entry count of the root's `moDisplayedEntityTracker_c` at `+0x98`. The parent calls the tracker at `0x40f9b`. In `sldmodu`, the tracker constructor creates its empty map at `0xd2e800–0xd2e82d` and the store writes the `+0x10` count at `0xd2f52f`. A populated map would write a wide name and typed object pointer for every entry. The parent read at `0x41e02` is gated to generation `0x1101` or higher, and the tracker reads the count at `0xd2f5f6`. It skips its entry loop at zero. All eight captures reach exact EOF at 1789 after these two counts. These are independently owned empty collections for the observed standalone default state. Parts with representation-wide attributes or explicitly tracked entities need separate population evidence.
