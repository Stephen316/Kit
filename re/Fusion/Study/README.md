<!--
This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion native-file study

The experimental reader exports observed native records and bounded geometry
derivations to JSON. See the [Fusion feature index](../README.md) for SDK
coverage and the [corpus notes](../Notes/Corpus.md) for the scope of saved audits.

## What is currently recovered

Each note records the observed layouts, compared cases and open work for that
topic. Report and capture paths in those notes are relative to this directory.

| Area                             | Notes                                                                                                                                                                               | Focused study check                                                                                     |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Streams, parameters and timeline | [Archive](../Notes/Archive.md), [parameters](../Notes/Parameters.md), [timeline](../Notes/Timeline.md)                                                                              | [Parameter identities](validate_parameter_identity_contrasts.py)                                        |
| Construction and sketch geometry | [Construction](../Notes/ConstructionPlanes.md), [sketches](../Notes/Sketches.md)                                                                                                    | [Saved-file workflow](../Notes/Workflow.md#validate-saved-examples)                                     |
| Solid features                   | [Extrude](../Notes/Extrude.md), [Revolve](../Notes/Revolve.md), [body tools](../Notes/BodyTools.md), [other solid tools](../Notes/ModelingTools.md)                                 | [Shell reconstruction](validate_shell_reconstruction_integration.py)                                    |
| Components and ASM bodies        | [Assemblies](../Notes/Assemblies.md), [topology](../Notes/BodyTopology.md), [naming and identity](../Notes/NativeNaming.md), [ASM caches](../Notes/AsmCaches.md)                    | [ASM body identifiers](validate_body_asm_identifiers.py)                                                |
| Sweeps and surfaces              | [Sweep, Loft and Pipe](../Notes/SweepsLofts.md), [sheet tools](../Notes/SurfaceTools.md), [Split and Trim](../Notes/SplitTrim.md), [boundary caches](../Notes/SurfaceBoundaries.md) | [Sweep spline paths](validate_sweep_nurbs_integration.py), [Trim](validate_surface_trim_integration.py) |
| Patterns                         | [Rectangular, Circular and Path](../Notes/Patterns.md)                                                                                                                              | [Circular placement caches](validate_circular_feature_caches.py)                                        |
| Mesh                             | [Geometry and sources](../Notes/Mesh.md), [operations](../Notes/MeshTools.md)                                                                                                       | [Mesh contents](validate_mesh_contents.py), [mesh operations](validate_mesh_operation_integration.py)   |

## Run the reader

Use the [saved-file commands](../Notes/Workflow.md#run-the-reader) from the
repository root. For the original library path and Python entry points, see the
[study reader notes](../Notes/StudyWorkflow.md#run-the-reader).

## Evidence and navigation

Use the [evidence guide](../Notes/StudyWorkflow.md#evidence-and-navigation) to
distinguish observed, derived and unresolved data. It also records the
[live capture protocol](../Notes/StudyWorkflow.md#live-capture-protocol).
