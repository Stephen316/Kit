# Independent rectangle and cuboid document authoring

## Evidence and qualified behavior

The next document profiles are an unconstrained closed rectangle sketch and an ordinary positive-Z solid extrusion of that sketch. Width and depth are authoring inputs. Extrusion height remains a driving user parameter connected to `AlongDistance`. This scope does not claim that width/depth are native driving sketch dimensions.

The source control is `re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d`, SHA-256 `09980af5a2c9e03e0fc9246ed0b20e796c8f5574c8838d255c85bdd08ea1aa9c`. The research decoder consumes all 303 Design records, including 269 primaries, totaling 29,133 payload bytes. [ControlGraph.json.xz](ControlGraph.json.xz) retains every named decoded field; [ControlSummary.json](ControlSummary.json) records the digest and counts. [InspectRectangle.py](InspectRectangle.py) regenerates these research artifacts without importing production codecs or calling Fusion.

`MSketch` entity 202 has empty `constraints` and `dimensions`; `DcSketch` 207 has empty `dcParameters`. The only two numeric parameters are extrusion distance and taper. There are no horizontal, vertical, perpendicular, coincident or dimensional constraint entities. The four line endpoints share point entities, which establishes closure without separate coincidence objects.

The existing independently authored circle document already establishes the minimal roots, units, ACT/Browser links, sketch plane tracking, feature timeline, numeric parameter binding, material defaults and envelope. The source control's cameras, views, render settings, saved topology caches and material packages are not required additions to the new writer. They are source-instance state, not a template.

## Exact sketch model

Let `W=WidthMm/10`, `D=DepthMm/10`; all Design coordinates are centimetres. The rectangle lies in the origin XY plane. Its corner roles are A=(0,0,0), B=(W,0,0), C=(W,D,0), D=(0,D,0). The fixed sketch origin is a separate Point3D, even when corner A shares its coordinates.

| Role | Control entity | Named point tag | CurveUses geometries |
| --- | ---: | ---: | --- |
| Fixed sketch origin | 205 | 100 | Empty |
| A | 228 | 101 | AB, DA |
| B | 230 | 102 | AB, BC |
| C | 232 | 103 | BC, CD |
| D | 234 | 104 | CD, DA |

Each point owns a `CurveUses` child; the four corner points have `isFixed=false`, `isFullyConstrained=false`, `isOrigin=false`, and the existing Point3D defaults. The origin retains the accepted fixed/origin flags and empty uses. Every point is a child of the sketch, while its CurveUses is its own child. No subject callbacks are present on these source records.

| Line | Control entity | Curve tag | Start/end | `lineDirection` |
| --- | ---: | ---: | --- | --- |
| AB / Y minimum | 236 | 105 | A→B | (1,0,0) |
| BC / X maximum | 237 | 106 | B→C | (0,1,0) |
| CD / Y maximum | 238 | 107 | C→D | (-1,0,0) |
| DA / X minimum | 239 | 108 | D→A | (0,-1,0) |

`Line3D` is GUID `DCA267ED-D615-4934-B64F-AD805E8003E2`, schema version 2, namespace `Geometry`, base `Curve3D` (`9FF71F46-205F-484B-A2B5-A245D0D8FE33`). Its exact five persisted fields are `lineCurve`, `lineDirection`, `planeNormal`, `rEndPoint`, and `rStartPoint`. `lineCurve` uses the recovered `AcGeLineSeg3d` callback: startPoint followed by displacement. Displacement is end minus start, not the normalized direction. The control has `planeNormal=(0,0,-1)` for all four lines. The source marks all four curves unfixed, unconstrained, unprojected, and non-reference.

Each line receives named uint64 metadata `EntityGenesis`, `crv_primary_id` and `crv_secondary_id=0`. Allocate these identities from the author's tag policy: origin=T, corners=T+1..T+4, curves=T+5..T+8, then `Sketches.crv_tag_id_idx=T+9`. They are separate from fresh entity IDs. Rooted sketch membership, sketch group highWaterMark=1 and the existing plane/UCS/compute-node graph remain unchanged.

## Extrusion and profile recipe

Reuse the accepted `DcExtrudeFeature`, `ModelDataRef`, `SketchRegionRef`, parameter/binding pairs, tool body, `DcBody`, and their status/dynamic nodes. Scope `profile_region` to the freshly allocated sketch ID as a string, the new asset UUID and Design segment 0. Keep profile tracking type 65 and the same feature parent joins.

The region recipe is an optional list of `SkRegionRecipeDataValue`, with one `faceRecipe` pair containing four sketch tags and Boolean true. `originalFaceRecipes` is empty. The tags use version 3, secondary 0, direction 0, split `(1,1)` and zero topology role flags.

The native type is `list<pair<list<sketch_tag_id>,bool>>`, not a set. The control saves tags 107,106,108,105, which is not perimeter order. This observation does not prove order independence. An independent author should choose an explicit stable perimeter order AB,BC,CD,DA; native rebuild acceptance must establish that this generated order is admitted. Do not copy the control's arbitrary entity-specific list as an unexplained constant.

Create four `SketchCurveProgenitor`/`SketchCurveRecipe` pairs. The profile-edge callback's two uint64 sets are named `startAdjacentPrimaryTagIds` and `endAdjacentPrimaryTagIds`; see [SketchTagSemantics.md](../EntityGraph/SketchTagSemantics.md). That naming is not confirmed by a black-box experiment. Their adjacency follows the source line direction, even though the recipe tag itself has direction one:

| Side role | Progenitor tag / face primary | Source line | Start-adjacent | End-adjacent |
| --- | ---: | --- | --- | --- |
| X minimum | 3 | DA | CD | AB |
| Y minimum | 4 | AB | DA | BC |
| X maximum | 5 | BC | AB | CD |
| Y maximum | 6 | CD | BC | DA |

The callback has version 0, one sketch tag, and one primary ID in each endpoint set. All source line tags in these four recipes have direction 1, split `(1,1)`, secondary 0 and role flags 0. The source's actual progenitor entities are 301/303/305/307 and recipes 302/304/306/308; these numeric entity IDs must not enter the writer.

The body progenitor uses the same fresh body UUID as `Body.persistentId` and `DcBody.bodyUuid`. Its `FeatureTagInfoValue.facePrimIdData` is the concatenation of the four generated ASCII side names; offsets derive from encoded string lengths. For the explicit policy above this is `3456` with offsets `[0,1,2,3,4]`, operation E, primary=false and occurrence=1. Body progenitor tag is 7, and `ProgenitorTable.tagId` is 8. Generate these from allocation policy and role assignments, not from a source record.

## History joins and carrier direction

The [cuboid history model](../CuboidHistory/CuboidHistoryModel.md) and [native acceptance](../../LocalOracle/PrismHistory/NativeAcceptance.json) establish the independently emitted prism history profile.

| Design role | Shared semantic identity |
| --- | --- |
| Sketch feature | Operation S |
| Extrusion feature | Operations E=S+1 and S+2 |
| Component operation seed | S+3 |
| Extrusion start/endModelHS | History initial/current IDs |
| BRepHistorySerializer.mapBodyId | Explicit body key→fresh Body entity ID |
| Serializer partName | Fresh BRep part filename |
| Body generic primary | ASCII decimal E |
| Body generic secondary | Body-progenitor tag 7 |
| Bottom/top cap generic primary | Reserved names `1`,`2` |
| Side generic primary | Corresponding four curve-progenitor names |
| Every face operation list | `[E]` |
| Bottom coedge sketch links | The four independently allocated line tags |

`PrismTags.Faces` order is bottom, top, Y minimum, Y maximum, X minimum, X maximum, giving `1,2,4,6,3,5` for this named policy. `PrismTags.Sketches` order is Y minimum, X maximum, Y maximum, X minimum, giving AB,BC,CD,DA.

The proven history construction uses source-CCW bottom carrier directions and zero sketch-link direction. `FreshPrism` starts with lower-to-higher-corner edges; reverse the two bottom carriers whose endpoint order opposes CD or DA, including start/end corner roles and the line origin/displacement. Derive this from corner-role pairs rather than copying native edge ordinals. The current topology happens to use edge indices 1 and 4. Its coedge uses and vertex owner indices are rebuilt from the explicit frame.

## Mass cache from dimensions

For H=LengthMm/10, V=W·D·H, the origin-based unit-density cache is:

| Field | Formula |
| --- | --- |
| volume | V |
| area | 2(WD+WH+DH) |
| cog | (W/2,D/2,H/2) |
| moi | V/3 · (D²+H²,W²+H²,W²+D²) |
| moiOffDiag | -V/4 · (WD,WH,DH) |

The 4×3×2.5 cm source gives volume30, area59, cog(2,1.5,1.25), moi(152.5,222.5,250), off-diagonal(-90,-75,-56.25), exactly as the decoded cache. Precision fields remain the already accepted zero defaults; revisionGuid is a fresh author revision UUID. The cache is derived from the same input dimensions as the history.

## Production integration partition

1. Extend the immutable `DocumentSpec` with `rectangle` and `cuboid` profiles and positive finite WidthMm/DepthMm. Existing parameter/circle/extrusion behavior and declarations remain unchanged. Rectangle emits a sketch only; cuboid adds the ordinary height-driven feature/body.
2. Factor existing common sketch-root/plane/compute setup into focused constructors, retaining the old circle allocation order. Add four-point/four-line construction as a separate rectangle geometry builder. Use a selected semantic sketch role instead of assuming every sketch is a circle.
3. Add Line3D v2 as schema vocabulary and select the qualified typed profile-edge callback for rectangle. The frozen circle author vocabulary currently treats endpoint sets as `set<unsupported>`; copying that declaration would reject valid rectangle adjacency. Either use a per-profile schema overlay with canonical field names or the full native catalog, without introducing source-instance values.
4. Keep the shared extrusion feature and numeric binding constructors. Select rectangle region/curve recipes and four progenitor pairs. Factor body-side tag data so the body builder consumes semantic side roles rather than one circle-only label.
5. Add an analytic cuboid mass-cache builder and a cuboid `BuildBodyPart` branch using `EmitPrismHist`. The surrounding accepted minimal container/ACT/Browser builders require no source archive or extra material/OGS/snapshot parts.
6. Native metadata-selected Design reading and typed cylinder/prism history dispatch are owned separately. Keep `DocumentBody`, `EmitBodyPart` and read dispatch changes coordinated with that work.

Relative to the minimal circle extrusion, rectangle geometry adds nine primary records and the extra three progenitor/recipe pairs add six. No new managed continuation boundary is introduced by these additions. The expected delta is fifteen primary/physical Design records, subject to the final shared constructor refactoring.

## Acceptance and remaining limits

Generate fresh 17×23×31 mm geometry at the origin, then drive height to37 mm. Acceptance must inspect initial shape before recomputation, confirm six faces/twelve edges/eight vertices, roll back to sketch-only, restore, rebuild, edit the driving height, save and reopen. A separate rectangle-sketch document should expose four shared-corner lines and one closed profile. These are future checks, not claims established by decoding this control.

The only unresolved construction choice in this minimal profile is native acceptance of the independently ordered four-tag region list. Width/depth driving dimensions remain out of scope. Existing dimension reports cover radius, diameter, angle and tangent modes; they do not establish a complete rectangular width/depth constraint constructor. No dimension entities or speculative constraints are added to bridge that gap.
