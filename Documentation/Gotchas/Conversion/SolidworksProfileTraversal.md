# Repeated component scans grow with disconnected profiles

A connected-component routine can look bounded because each rectangle has only four edges.
Scanning the complete remaining edge collection for each disconnected rectangle still adds quadratic work.
Searching the complete marker list for every rectangle header adds another quadratic scan, including when no header exists.

Build marker positions and vertex adjacency once for each candidate collection.
Then traverse incident edges and look up the first owned marker directly.
Retain native marker positions for adjacency references and physical offsets for source provenance.
Those two identities must not be substituted for each other.

The [A04c change](../../Changes/Research/IndexedSolidworksProfileTraversal.md) records the source review and remote integration boundary.
