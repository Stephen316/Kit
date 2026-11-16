# Configuration material and density

`WriteConfigMaterial` resumes the [section hatch](ConfigModelBody.md) and allocates a `moMaterial_c` and its one `moDensityParameter_c` child. It takes physical part density in kg/m³ from the document caller. The supported standalone path uses the initial unnamed density node and has no second density value. It stops before the following `uoModelData_c` tag.

## Native field authority

These are preferred addresses in the [pinned SOLIDWORKS 34.4.1.1011 sldmodu image](ConfigRoot.md#native-field-authority).

| Owner | Filed data and source |
| --- | --- |
| Part material | The part archives `+0x1420` through the `moMaterial_c` descriptor at `0x4daed8f8`, calling the typed binary writer at `0x4c22e5d3`. The factory `0x4c20ce00` selects `0x4bccc020` and supplies a null density placeholder. The same constructor takes an actual density child for a newly authored part. Material virtual table `0x4cfe6870` slot 5 calls `0x4c222460`, whose storing branch at `0x4c22249d` files only `+0x8` through the typed `moDensityParameter_c` writer. `moMaterial_c::getDensity` at `0x4b285170` reads that member. |
| Initial density node | Density descriptor `0x4daebd10` selects factory `0x4c174320`. Its constructor `0x4c1996b0` sets virtual table `0x4d121630`. The base constructor `0x4c1996e0` invokes the node constructor `0x4c03a5c0`, which supplies the unset signed node ID `-1`, null node name, empty auxiliary text, primary flags `0x40000000` and zero secondary flags. It clears the initial update state through `0x4c03d100` and the store at `0x4c03d209`. Node stores `0x4c178b11..0x4c178b47`, `0x4c178d6a` and `0x4c178df6` file the first null name, update, primary flags, ID, secondary flags and wide empty text. The base parameter initializes `+0x48` to null and files it at `0x4c178022` using the `moNodeName_c` descriptor. |
| Density value | The density serializer jumps from `0x4c175bc0` to `0x4c175bd0`. It calls the base serializer and files `+0x58` as a double at `0x4c175c42`, with the native archive key `Value`. The factory placeholder is `-1.0`. For a newly authored part, the constructor obtains a separate double from environment option `0xe4` at `0x4c19d518`, passes it into the density constructor at `0x4c19d54f` and assigns the owning part material at `0x4c19d569`. The constructor files the caller's actual density here rather than using the loader placeholder. |
| Second value | The parameter constructor zeros `+0x60` and `+0x68` at `0x4c199737` and `0x4c19973b`. With archive condition `0x80` clear, `0x4c175c7f` files the `+0x68` byte. A nonzero value would add the separate double at `+0x60`. The loader can replace the primary value with that double at `0x4c175d48`. The measured standalone branch has only the zero selector. |

## Replay

```sh
python re/solidworks/WriterResearch/VerifyConfigMat.py --read-only
```

All six P01 and eight P03 receipt-pinned saves contain the same 77-byte material span, including the two compact schema-1 definitions. The density is 1000 kg/m³ in each save and agrees exactly with the separate [Definition record](DefinitionJournal.md). The two null names use no archive slots. P01 advances from next index 49 to 53 and P03 from 51 to 55. The independent packaged walker agrees on the `uoModelData_c` tag and the inherited class and object maps. The material digest is `b374ed9b882980262445026060e9caecfb5f354b2e3dae9adfbe9ddde9dd4ad1`. The receipt-order replay digest is `f7f43f4bbee7452e83d0fd271eaf6143b49bc9453556310cc4bb1119aa7f09ce`.

Hosted `CheckConfigMat` constructs from the independent Definition density and compares exact bytes and allocation state. The current result is a read-only archive replay. The model data owner and native acceptance remain open.
