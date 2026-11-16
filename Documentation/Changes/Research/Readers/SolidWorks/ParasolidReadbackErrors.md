# Report failures from generated Parasolid readback

The Parasolid writer reports the first rejected readback boundary when it cannot verify generated geometry. It uses the same header, partition scan, topology reconstruction and model validation as the ordinary reader. The diagnostic includes the reason for a topology exception. The writer still refuses to return an unverified payload.

The archived P04 through-all case passed source archive decoding and failed verification of the generated partition. The first run reported only that the partition could not be decoded. The next run reported a disconnected coedge ring during topology reconstruction. The existing through-all export assertion exercises that path. [First Linux run](https://github.com/TryUniCAD/Kit/actions/runs/43791586077/job/133051099512) · [Linux run with diagnostics](https://github.com/TryUniCAD/Kit/actions/runs/43793274991/job/133056295549) · [Planar loop roles](ParasolidLoopRoles.md)
