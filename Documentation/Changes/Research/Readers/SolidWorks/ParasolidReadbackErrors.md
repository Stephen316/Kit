# Report failures from generated Parasolid readback

The Parasolid writer reports the first rejected readback boundary when it cannot verify generated geometry. It uses the same header, partition scan, topology reconstruction and model validation as the ordinary reader. Reconstruction errors retain the original cause. Readers still return no model for rejected data, and the writer still refuses to return an unverified payload.

The archived P04 through-all case on [Linux job 133051099512](https://github.com/TryUniCAD/Kit/actions/runs/43791586077/job/133051099512) passed source archive decoding and failed verification of the generated partition. The earlier failure reported only that the partition could not be decoded. The existing through-all export assertion is the hosted verification for the diagnosed path. [Planar loop roles](ParasolidLoopRoles.md)
