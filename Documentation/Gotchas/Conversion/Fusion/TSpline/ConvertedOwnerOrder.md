# Converted Form owners follow face creation order

## Expectation

The owner coedge of an edge is the coedge of the first face in the shell chain. The owner edge of a vertex is the first edge that names the vertex.

## Actual behavior

Fusion selects owners in face creation order. Faces are created in patch program order. The shell chain lists them in the reverse order. Coedges are created in loop order inside each face.

Kit reproduces the native owners of nine local archives with these rules.

| Owner | Rule |
| --- | --- |
| Edge owner coedge | The first coedge in creation order that uses the edge |
| Vertex owner edge | The first edge end in creation order that touches the vertex |
| Vertex end index | 0 when the vertex is the edge start, 1 when the vertex is the edge end |
| Split edge start | A split piece that starts after its curve start owns its start vertex, with end index 0 |

The split rule changes one owner in the local archives. In `vendor_BoxCreasedControl`, edge 6 has bounds (−1, 0) on a curve with range (−2, 0). The first-touch rule selects the end of edge 7. Fusion stores edge 6 with end index 0.

## Workaround

Give each face its patch program index in `FormSurface.Region`. `MakeFormLinks` sorts the faces by this index and then applies the rules in the table. Give a split edge its parameter interval in `FormEdge.Bounds`.

## Evidence

- [BRep rebuild comparison](../../../../../re/Fusion/Reconstruction/FormDocuments/Sourceless/BrepRebuild.json)
- [Rebuild script](../../../../../re/Fusion/Reconstruction/FormDocuments/Sourceless/CompareBrep.py)
- [Record order](ConvertedRecordOrder.md)
