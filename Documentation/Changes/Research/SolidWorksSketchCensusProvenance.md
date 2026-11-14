# SOLIDWORKS sketch census provenance

The [A04c discovery census](SolidWorksDiscoveryCensus.md) now records the native sketch stream range and marker offsets, types, roles and endpoint indices. Profile records identify their marker offsets. Rule records retain their native codes and references. Neutral entities and rules include provenance spans so an emitted segment can be traced to the marker or entire sketch it came from.

The evidence helps distinguish a captured sketch with no recognized profile from a projection that emitted an extra line. Native geometry and rule records still represent decoder observations. Horizontal and vertical rules reconstructed without a native rule code are identified as inferred in the report and do not count as native-bound constraint matches.

Download `SolidworksDiscoveryCensus-<attempt>` from a completed **Workflow quality** run. Compare a sketch's `stream_span`, `markers` and `profile_records` with the matching neutral sketch's `entities` and `closed_profile_entity_ids`. A zero marker count identifies the absence of recognized markers in the inspected span. The capture can still contain authored geometry outside that reader grammar.

The existing capture pins restrict this diagnostic to P01, P03 and P04. It reports structural evidence and does not change production reader semantics or qualification status. Static syntax and whitespace checks ran on this change. Runtime verification belongs to the existing remote discovery census.
