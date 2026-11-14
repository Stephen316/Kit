# Body LOD display items replace the render geometry link

## Expectation

A body LOD node with a nonzero `HasLODs` mask holds a `DisplayItemType` word of 0. A `RenderGeom` link to an `OgsSimpleMesh` or `FatPointMesh` follows the word.

## Actual behavior

A body LOD node writes the display item type of its render geometry. Type 0 is followed by a `RenderGeom` link. Other types are followed by the data of the display item.

| Type | Item | Data after the type word |
| --- | --- | --- |
| 6 | Edge | `Props` u32[4]: stream, offset, position floats, normal floats |
| 7 | Face | `Props` u32[6], `EdgeNum` u32, edge ordinals u32[`EdgeNum`] |

The six face `Props` words are stream, offset, position floats, normal floats, texture floats and index count.

An edge item writes six floats for each vertex in `Fusion_mesh_NNN`. The floats are the position and then the normal. A face item writes eight floats for each vertex: position, normal and texture coordinates. The 32-bit triangle indices follow the vertex data.

A face edge ordinal is the serialization position of an earlier type 6 item in the same body.

Kit raised `ValueError("Unsupported graphics display item or LOD set")` when it found type 6.

## Workaround

Decode types 0, 6 and 7. Raise `ValueError` for any other type. Require equal position and normal counts. Require two texture floats for each face vertex. Require each face edge ordinal to refer to a type 6 item of the same body.

## Evidence

- [Scene stream evidence](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/SceneStreams.json)
- [LOD trace script](../../../../../re/Fusion/Reconstruction/ReaderCoverage/SceneStreams/TraceLods.py)
