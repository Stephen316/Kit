# Calculated initial extrusion shapes

Independent inline Create extrusions can now carry a calculated initial `Shape.brp` on the actual editable `Part::Extrusion` owner.
The writer uses the existing pure-Python prism/circular geometry builders and BREP serializer.
No CAD runtime, captured native shape, donor template or extra visible substitute solid supplies the cache.
Driver expressions, native direction/reversal properties and feature dependencies remain intact.

The supported cache family is a millimetre document with a rigid support frame and one simple closed 3–64-line ring or circle covering every nonconstruction sketch entity.
Feature selections, attached/offset support, unsupported extent controls, offsets and tapers acquire no new cache.
Direction must be exactly collinear with the profile normal; conservative floating-point refusals remain unqualified rather than approximating an oblique extrusion.
The already resolved native-mm end values determine the stations: `[-reverse, forward]`, or `[-forward/2, forward/2]` for symmetric total thickness.
Direction orientation and reversal determine the sign before station ordering.
Parameter units may differ from document coordinates; the cache consumes the same resolved distances as native XML emission.

Other document units and unsupported cache families retain their existing unqualified paths.
Boolean result caches remain unfinished: a tool's shape cannot substitute for its Boolean result.
Final cache metadata is cleared unless the current feature or existing representation actually owns that shape member.
See the [whole-sketch boundary](../../Gotchas/Conversion/FreeCad/WholeSketchExtrusionCache.md) and [direction precision boundary](../../Gotchas/Conversion/FreeCad/NearParallelExtrusionDirections.md).

Cache presence does not establish native acceptance or promote result flags.
The [initial-open witness](FreeCadEndNativeWitness.md) applies to the preceding source, which had no cache and failed C5.
The new implementation still requires an independent fresh initial-open check before explicit recompute, followed by driving edits, restoration, rebuild, save and fresh reopen with healthy controls.
Broader A16, A13 and A15 requirements remain open.

New public process coverage authors varied polygon/circle profiles, rigid frames, direction/reversal combinations, symmetric/two-ended controls and mixed cm/mm drivers.
It inspects native XML and shape ownership, then strips only the neutral manifests and reads the BREP through the public native reader.
Additional controls retain unsupported units/oblique directions/extra sketch geometry without a cache and prevent stale cache ownership after a Boolean.
Research output uses explicit `AllowCarrier=True` with unqualified flags; strict output refusal remains governed by the separate attestation repair.
Static source, type, format, steering and policy checks were performed; local tests, collection, SDK/generator and native execution were not run.
Hosted process and installed-native verification remain required.

[Cache implementation](../../../src/convert/adapters/freecad/ExtrusionCache/InlineShape.py), [profile guard](../../../src/convert/adapters/freecad/ExtrusionCache/InlineProfile.py), [process coverage](../../../tests/Research/Archives/FreeCadInitialShapeTests.py)
