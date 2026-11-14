# External instances add graphics links

## Expectation

The saved graphics scene of an assembly uses the same frame and attribute layout as a part.

## Actual behavior

Two graphics structures differ after a cloud save of a root with an as-built joint.
The controls `R5_saved` to `R9_archive` contain both structures.
Each of these controls has two frames with the flag set and two qualifiers.
The unsaved control `R4_joint` has the same joint but neither structure.
The saved subassembly `S1_saved` has a reference but no joint, and it has neither structure.

| Structure | Change | Typed model |
| --- | --- | --- |
| Render frame | A third link flag follows the two empty links | `RenderFrame.HasEmptyLink` |
| `SelectabilityAttribute` | The field links an `AlphaImageSelectionQualifier` object | `QualifierValue.ImagePath` |

The qualifier holds an absolute image path in the Fusion installation.
The observed paths end in `Server/Component/Resources/JointOccurrence/rigid1.png` and `rigid2.png`.
The installation folder is under the home folder of the user.

The previous reader raised `Unsupported linked graphics callback payload` for these controls.

## Workaround

Read the third frame flag and the qualifier as typed values.
Replace the home folder in the image path before you commit a control.
A set frame flag that a callback payload follows still raises `ValueError`.

## Evidence

- [Frame transfer](../../../../../src/convert/formats/Fusion/GraphicsCodec/Nodes/XferFrameMut.py)
- [Qualifier transfer](../../../../../src/convert/formats/Fusion/GraphicsCodec/Values/XferQualifier.py)
- [Scene trace script](../../../../../re/Fusion/Reconstruction/LinksConfigs/TraceScene.py)
- [External references change](../../../../Changes/Fusion/Assembly/FusionExternalReferences.md)
