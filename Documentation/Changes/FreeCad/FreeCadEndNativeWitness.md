# Independent FreeCAD end-driver witness

Stephen316 [reported an isolated installed-native witness](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6929886318) of public SDK source `b32222b5f829198db3f2b4d2b75254b3c7d8f6d3`, tree `a25eae46d1c7b0661bbceffec7b39e7072e937bb`.
The target was FreeCAD 1.1.4 build `4fd3bf320d9566a27e60069fc8387448aaa3a094`.
The private witness retains two native process identities and loaded module hashes, four healthy independent box checks and six healthy native-authored extrusion controls.

Three caller-authored neutral documents produced editable `Part::Extrusion` histories with sketches and driver expressions.
The original generated archives have no cached BREP and returned zero solids before native recompute.
After recompute each returned one valid 12,432 mm³ solid.
Forward and reversed cases independently followed forward 11→14 mm and reverse 5→8 mm edits, preserving the other end and reaching 14,763 mm³.
Their world bounds and centres of mass mirrored correctly.
The symmetric case followed total thickness 16→20 mm, reaching 15,540 mm³.
All three restored, saved to new paths and reopened in a separate fresh native process with original geometry, properties and expressions present.
Original generated package bytes remained intact.

The witness seal is `64a6190dee34a2b4a3e682ea8ab65110e0804981de2b1f32b4dfcde54b376721`.
Preparation: `c4f97f5f4e619eefc55f982938815b01de46206e35eca240704e830c5a207296`.
Native edits: `3d9a3c61675ef0caa5178668b101611d249820242a2fa2454129169df8e5c7c0`.
Fresh reopen: `751a0799a69aa061df853b78b707d1a51da5398b74e49c2f3806e279a7d566c0`.
Original artifacts remain in the operator's private custody.

This establishes attributed scoped edit and reopen observations for that exact source and installed build.
It does not establish immediate geometry availability in the original packages: the [initial recompute limitation](../../Gotchas/Conversion/FreeCad/GeneratedExtrusionRequiresRecompute.md) remains explicit.
Broader A16 qualification remains `not_evaluated`; A13 and A15 gates remain open.
No local native application, SDK, generator, test or collection execution was performed while recording this evidence.
