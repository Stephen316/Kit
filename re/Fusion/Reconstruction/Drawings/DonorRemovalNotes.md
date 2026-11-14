# Donor removal notes (working state)

Branch: local `drawings-native` (worktree agent-ae1eac21c45d002d9). Commit only here. No push, no PR.

## Commits so far

- f1516ec99 feat(fusion): derive drawing view, text and sheet rules from the format
  (audit rows 1, 2, 3, 4, 6, 7, 8 and row 13 code).
- 88f20a547 feat(fusion): generate ISO sheet borders from the paper size (row 10 border).
- 72283f49b feat(fusion): build drawing header variables from rules (row 10 header; re/ scripts; G2 evidence).
- f359e4042 feat(fusion): generate the drawing standard objects from vocabulary (row 10 tables/NOD/classes/title).
- f35c399c0 feat(fusion): derive drawing sheet members from the paper and verify by graft (KSheetSizes, D3 thumbs,
  KCycleColor gone; exact dashes; T3/T4 graft evidence: T1Tables T2Standard T3Sheet C0 C1 C2 all open).

## Rules and evidence

- Border (Sheet/BorderPlan.py, PlaceBorder.py). ISO 5457. Frame left 20, other sides FrameMargin. Trim marks 15 mm
  on Defpoints. Centring marks band edge to 5 inside. Zones per side 2*round(len/100). Pitch (span + 10)/count, no
  rounding. Labels digits left to right, letters top to bottom, plain alphabet (Fusion uses I and O).
  Matches Fusion A3 36/28, A1 64/56, A0 88/80 lines/labels, max error 1.4e-5 mm. Fitted on A3 only.
- Header (Standard/HeaderPlan.py, HeaderDefaults.py, DimensionVars.py). 310 vars in spec order, equal to the
  captured header except DimTm (0.1 vs 0.1000000001) and paper extents (exact paper vs float noise).
  PLimMax/PExtMax from paper (Fusion leaves A3 values in A1/A0 saves: template residue).
  Dim gaps 0.6h/0.4h/3h (exact tenths), DimTFac = next smaller ISO 3098 size / h.
  UnknownLongC..H are ASCII-like words ("0000", "095M"...), same in all recent saves.
  InsUnits stays mm for all sheets (ISO drawing standard); ASME B unverified.
- Graft round G2 (Rules/GraftRoundG2.json): L1Lean, L2Rules, L3LeanRules, L4Core open (views 5/4/4 curves,
  1 dimension, 420x297). L0Base stalled at 420 s (cold open; rerun). Z1EmptyDwg: dialog "Drawing file is not
  valid" -> route (b) closed, Fusion does not regenerate an empty DWG member.
- L4Core keeps for the standard: layers FD_Dimensions Hidden "Smart Centers" Visible 0 Defpoints BORDER
  TITLEBLOCK; ltypes ByBlock ByLayer Continuous CENTER2 HIDDEN2 ACAD_VIEWBORDER_LINETYPE; styles Standard
  FusionTitle; DIMSTYLE Dim-ISO-25; VPORT *Active; MATERIAL ByLayer ByBlock; MLINESTYLE; one SCALE; NOD dicts.

## Graft tools (re/)

- Rules/BuildTransplant.py: T1Tables/T2Standard/T3Sheet on L4Core, header untouched, new entities on freed handles.
- Rules/BuildContainer.py: typed re-emission of control with one container rule (C0..C2). Plans registered in
  Native/BeginUploads.PLAN_FILES. Run: BisectRound.py <tag> <labels> --stall 420. Evidence: scratch evidence_t.py.
- Kit vs control standard objects: 19/22 equal; differ by design: ACAD_VIEWBORDER_LINETYPE, DimTolMinus, VPORT.

## Corrections (2026-11-13 02:00)

- A1Control/A0Control are acceptance labels; both saves are A3 paper (layout 420x297, manifest A3). There is NO
  template residue. Every Fusion save holds 10 template border blocks (ISO_A0..A3, (P) variants, A4(L), A4(P)).
  Border rule matches landscape A0-A3 (<=2e-4 mm). Portrait: Fusion divides frame span (not band span), MTEXT
  labels. A4: no zones, A4(L) side marks at y=100. Kept Kit ISO 5457 rule (ISO field table 24x16..6x4).
  Gotcha FusionDrawingTemplateBorders.md.
- Row 12 code (committed a703bb1cd after T5): Records/RecordIds.PlanIds (sources 2 ids each, sheets 1 each, tracked 6
  each, from 1+max skeleton id = 39); SourcesRecord/SheetsRecord/SourceParts/SheetRecord built from ids;
  KFirstTracked/KTrackedSpan/KActNextId gone. Grafts C3Renumbered (gapless ids on control) and C4KitMembers
  (all Kit members around control DWG; ids 39,40,41 next 42) built, to run as T5.

- 218488636 HoleData generator (identical text), border gotcha, acceptance evidence section.
- KStateMark 2184de7b09: once after each body bounds in all 9 FDOC_VIEW_STATE_CAPTURE xrecords (4 saves, 3
  designs, Wheel has 2 bodies) -> documented constant (FusionDataModel 'Drawing authoring rules').
- Skeleton ids 0..38 identical (34 records) in Wheel/A1/A0. Wheel tracked 45..56 contiguous; A1 has gaps.
- CaptureEdit dry run: views created for all orientations; vertical+aligned dims OK; radial/diameter only where
  circles; ASME B fails: "Sheet size is not valid for the active drawing standard" (needs ASME document).
  Script hung in sheet_info after build; CaptureEdit now saves before sheet_info.
- Account editable docs 10/10, none older than 7 days -> may not delete; new documents impossible now.

## Update (2026-11-13 later)

- a703bb1cd feat(fusion): number drawing records from one counter. T5: C3Renumbered and C4KitMembers both opened
  (views 5/4/4, 1 dim, 420x297); evidence Rules/GraftRoundT5.json. sheetOrder now = layout TabOrder rule
  (SheetKeys.KFirstSheetTab = 2, TabOrder removed from SheetDefaults.json; authored DWG bytes unchanged).
- Tab orders in saves: modern Wheel/A1/A0 have Model 0 + one sheet at 2; older Boxes save has 2 sheets at 1 and 2.
  Multi-sheet modern order comes from the CaptureEdit save (running as CaptureEditSave).
- SheetDefaults.json audit (scratch defaultscheck.py): 75,669 default field values equal the 4 readable saves;
  differences are Kit's neutral choices (no plot device, zero margins, PlotFlags 688, MTEXT middle attachment).
  DIMENSION_ALIGNED/DIAMETER/RADIUS defaults appear in no save yet (CaptureEdit save will have them).
- Scrubber: the PR worktree ScrubSaved.py gained a rule. This branch commits no Fusion saves, only normalized JSON
  checked by grep, so it does not run the scrubber. Pull it from the PR worktree before scrubbing any save.
- Public API: drawing standard is set only at creation (CreateDrawingInput.standard); DocumentSettings.standard is
  read-only, so ASME needs a new document. Only base views can be added; projected views come only from the
  automatic creation mode (CaptureAutoRules).

## Next steps

1. Analyse the CaptureEdit save (editcap.py): sheetOrder/TabOrder for 5 sheets, ids per sheet, base view shapes per
   orientation (row 11), Fusion vertical/aligned/radial/diameter DIMENSION objects vs Kit PlaceDimension (row 13),
   borders for A4P/A2/A1/A4L. Record normalized JSON in Rules/.
2. Try CaptureAutoRules (AutoIsoA4, AutoAsmeB) for projected children and ASME; record refusal if the limit hits.
3. Docs for findings; finalgrep.sh; final report.

## CaptureEdit save (Edit2, Wheel drawing v2, 5 sheets)

- Layout TabOrder: Model 0, sheets 2, 3, 4, 5, 6 in creation order; each sheet record's sheetOrder equals its
  layout TabOrder. Confirms: first sheet tab 2, +1 per sheet.
- Each new sheet's base views added model sources n_Component (index n, designId 1); sources take 2 ids (source +
  parts), sheets 1 id; folder 25: lastUsedModelSource = last source, modelSourceNextId = count + 1. Matches PlanIds.
- Dimensions saved: LINEAR 6, ALIGNED 6, RADIUS 2, DIAMETER 1 (compare with scratch dimcompare.py/dimdiff.py).
- Base views in Left/Back/Bottom/Right/Top/Front: identical field shape, (11, 1, 0, 8224, 100, 0); the original
  Wheel base view (single view, no children) stays (11, 2, 0, 3104, 100, 0). Orientation does not change the shape.
  Open question: (1, 8224) vs (2, 3104) = not yet computed vs computed? Test: recompute views and resave.
- Iso base views (IsoTopRight, IsoBottomLeft) use another ACDBVIEWREP layout; Kit's reader leaves them unparsed
  (9375-bit tail). Kit must not write iso eye directions with the orthographic layout until this is decoded.

## Dimensions (row 13) and later steps

- Edit2 dims vs Kit (scratch dimcompare.py/dimdiff.py): vertical and aligned layout identical to Kit's rule
  (ext offset/extend 2.1, arrows 3.5 x 1/6, text 1.4 + h/2 off the line). Short Fusion aligned dims put arrows
  outside (5 lines); Kit refuses dims shorter than two arrows. All 15 texts: Kit TextExtent within 4e-7 mm.
- Round dims: Fusion flags 10 + DSTYLE overrides (radius 75=1, 288=1; diameter 288=1); diameter text U+2205
  measured with Arial Ø box. Kit now writes these (PlaceDimension KStyleOverrides, KPlacedText; DimensionPlan;
  TextMetrics). Kit keeps its leader-and-shelf layout (Fusion puts text on the radial line).
- Grafts D0Plain..D4Diameter (Rules/BuildDims.py, PlanDims.json) swap the control's plain dimension for Kit's
  dimension of each kind; T6 round running.
- Evidence Rules/CaptureEdit2.json (normalized). SourceRecord now takes the source index (n_Component).
- CaptureEdit.py: plan FirstFront (base view on first sheet) and existing_info/after_info switches. Next run:
  FirstFront save to test whether view shape (1, 8224) changes on resave or by sheet; then CaptureAutoRules.
- ab73beb59: round dimension rules (flags 10, DIMUPT/DIMSE1, U+2205) and source index; T6 D0..D4 all opened
  (views 5/4/4, 1 dim). Evidence Rules/GraftRoundT6.json, Rules/CaptureEdit2.json.
- Scrubber: still not run by this branch. If ever needed, first copy the PR worktree's newer ScrubSaved.py
  (fragment search confined to AssetData members) and compare ReadDocument models before and after scrubbing.
- Running: CaptureFirstFront (Wheel drawing v3 with a Front base view on sheet 1). Then CaptureAutoRules.
- Edit3 (FirstFront resave): v2 API views stay (1, 8224) after resave; new Front view on sheet 1 is (1, 8224);
  original Wheel view stays (2, 3104). So the shape is not age or sheet. The (2, 3104) views (Wheel, A1, A0
  bases) show no hidden lines; the API views show hidden lines -> display options. StyleGrid plan (8 base views,
  one option changed each: style x4, tangent off/full, threads, interference) queued to map the fields.
- KBodyBits 0x8000000001: all 70 body/holder keys in 5 saves (3 designs); KeyFlag = body index. Documented.
- 4d17ec0ec: authored base views must look along a model axis (iso layout unparsed). Tests TestViewAxes.
- CaptureAutoRules (AutoAsmeBmm, AutoIsoA4) started 02:50; createDrawing has not returned (stage "creating
  AutoAsmeBmm"). Account: Personal tier, 10/10 editable documents, none older than 7 days, so no deletion allowed.
  RunGuarded's stall check only watches "opening drawing" stages; this run ends at its 1800 s timeout.
- ASME: ISO saves carry ANSI_TITLEBLOCK but no ASME border blocks; an ISO drawing refuses ASME sheet sizes. Kit's
  current ASME output mixes inch paper numbers into a mm drawing (border 17 x 11 units). Next: express ASME paper
  in mm and derive the border from ASME Y14.1 (zones half an A-size side), verify acceptance by graft.

## ASME sheets and short dimensions (03:10-03:30)

- ASME paper now in mm (inch sizes x 25.4); PlotWidth/PlotHeight removed (paper = plot size). ISO DWG bytes unchanged
  (A0-A4 hashes equal before/after). ASME border (BorderPlan FrameRule): 0.5 in margins, no filing margin, quarter-A
  zones over the whole sheet (A 2x2, B 4x2, C 4x4, D 8x4, E 8x8), numbers from right, letters from bottom, 0.12 in
  labels in a 0.25 in band, no trim/centring marks. Manifest zones from ZoneCounts(Paper). Gotcha
  FusionDrawingAsmeSheets.md. Graft round T7 (Rules/BuildAsme.py: S1AsmeB, S2AsmeD, S3AsmeA) queued.
- CaptureAutoRules createDrawing hung (Fusion idle, no dialog); account at 10/10 editable documents.
- Short dimensions (Edit2): Fusion keeps arrows and text inside when span >= 2 arrows + text width (16.33 inside
  with 16.09 needed; 7.07 and 4.08 outside). Outside: arrows point in from outside, 3.5 stub beyond the first
  arrow, line beyond the second arrow of 3.5 + 1.4 + text + 1.4 with the text over it, dimension line between the
  feet. Dimension line through the points: no extension lines. FitGrid plan (Front views at scales 3-4.6) queued to
  pin the threshold. Kit DimensionPlan change in progress.
- Queue: StyleGrid save (row 11), T7 ASME round, FitGrid save.
- d4062e8e4 ASME sheets in mm with ASME border; 3c7c9dd47 short dimension layout (Kit matches all 12 saved linear
  and aligned dims to 3e-6 mm; long dims byte-identical). Grafts D5Short/D6OnLine queued as T8.
- CaptureAutoRules: timeout at 1800 s inside createDrawing (AutoAsmeBmm), Fusion restarted by the guard. Fusion was
  idle (~4% CPU) with no dialog window. No ASME or automatic-projection save is possible while the account holds
  10/10 editable documents that are all younger than 7 days.
- View refs: top-level ACDBVIEWREPBLOCKREFERENCEs sit in *Model_Space at (0,0); each follows its ACDBVIEWREP handle.
  Original Wheel view draws 5 visible circles (looks along the wheel axis); API Front views draw arcs, visible and
  hidden lines. Scratch stylegrid.py pairs views with their layer counts.
- T7 (GraftRoundT7.json): S1AsmeB, S2AsmeD, S3AsmeA all opened (views 5/4/4, 1 dim); Fusion reports sheets
  431.8x279.4, 863.6x558.8, 215.9x279.4 mm, so it takes the sheet size from the DWG layout.
- StyleGrid (Edit4, CaptureStyleGrid.json): all 8 views report style 1 (visible and hidden) after creation, whatever
  style the input asked; all saved (11, 1, 0, 8224, 100, 0) with 6 hidden lines. The input style is ignored.
  StyleSet plan sets view.style after creation (queued after T8) to tie the shape to the style.
- T8 (GraftRoundT8.json): D5Short and D6OnLine opened (views 5/4/4, 1 dim).
- FitGrid (Edit5): input scales ignored; all six Front views at 5:1 on A1, so all aligned dims were 17.678 mm
  (inside). Kit matches those 12 dims too (<=8e-7 mm). Fit limit still bounded only by (7.07, 16.33].
- StyleSet + FitSet (set view.style and view scale after creation) queued as CaptureStyleSet.
- StyleSet (Edit6, CaptureStyleSet.json): view.style set after creation works. Visible (11,2,..,8224), visible+hidden
  (11,1,..,8224), shaded+hidden (11,1,..,8225), shaded visible (11,2,..,8225). So ViewLongB 2 = no hidden edges,
  1 = hidden edges; flag bit 0 = shaded. Original UI views (2, 3104) = visible-edge style; 3104 vs 8224 differ in
  0x400|0x800 vs 0x2000 (ToggleSet queued: tangent, threads, interference).
- FitSet (Edit6): view scaleValue set after creation works. Aligned 3.54 dims: 10.607 arrows inside + text outside
  (text line from the second tip, 3.5 + 1.4 + W + 1.4); 14.142..16.263 all inside (text above the line).
  So Kit's single limit (2 arrows + text) is wrong for 10.6..16.07. FitSteps queued (scales 2.75..3.9).
- FitSteps (Edit7, CaptureDimensionFit.json): arrows inside from 9.899 (9.723 out) -> limit 2a + 2g = 9.8; text inside
  from 11.985 (11.773 out) -> limit W + 2g = 11.875. Kit now has three layouts (inside, split, outside); arrow
  corners ordered by the reading-direction normal (aligned dims pointing left). Kit matches all 56 saved linear
  and aligned dims to 2.9e-6 mm. Open: text fits but arrows do not (short text): FitShort queued with ToggleSet.
- ToggleSet (Edit8, CaptureToggleSet.json): thread edges on -> flags +0x800, interference on -> +0x400; tangent Off and
  FullLength leave 8224. UI base views 3104 = 0x20|0x400|0x800 (visible style, threads and interference on); API
  views 8224 = 0x20|0x2000 (0x2000 unexplained, only API-created). Kit's (11, 2, 3104) = UI form, now explained
  except bit 0x20. Child (15, 6, 40032 = 0x9C60) shares 0x400|0x800; not testable (API makes no projected views).
- FitShort (Edit8): text "10" (4.672 wide): 6.0 both out; 7.5/8.5/9.5 text inside above the line with arrows outside
  and a 3.5 stub past each arrow (flank layout); 11 and 13 inside. Text limit W + 2g confirmed on a second width.
  Kit now has four layouts; matches all 68 saved linear/aligned dims (<=5.1e-6 mm).
- T9 (GraftRoundT9.json): D7Split (aligned 10.607 at 3:1, split layout) and D8Flank (vertical 7.5 at 0.75:1, flank
  layout) opened (views 5/4/4, 1 dim). All four short layouts now have a Kit graft that Fusion opened.
- c31ccbd96: T9 docs and evidence committed.
- Child directions (row 11): Rules/BuildChildren.py grafts left/below (V1LeftBelow), right+back (V2RightBack) and
  above+below (V3AboveBelow) children onto the control by copying only the leaves that differ between Kit builds
  A (right+above) and B. The control equals Kit A on every such leaf (32/45/27 leaves, 0 mismatches), including the
  back view parent relink. Found: Fusion ACDBVIEWREP.Viewport points to the view's paper viewport (first of the
  pair, view direction 0,0,1); Kit points to the second (model) viewport. Fix in ViewRepData next, then run T10.
- ViewRepData now links ACDBVIEWREP.Viewport to the frame viewport (all 63 view reps in 5 saves do; Kit linked the
  model viewport). Test TestViewPorts. Kit and control then agree on every paired view object except source ids,
  stored edges, model space places, base eye distance, null visual style (Kit writes none) and the layout viewport size.
- T10 (V1-V3) and T11 (V4-V6, Kit model places) all opened. Fusion re-projects each view's STORED edges on open:
  right->below and above->back views showed the old edges flattened to a line. T12 (V7-V9, no stored edges, Kit's
  form) opened with 0 curves in every view. T13 (--poke: base scale halved and restored) made Fusion find the edges:
  V7 back to 5/4/4, V3/V8 below view a proper 160x40 outline at Kit's planned place. Kit-authored views therefore
  stay empty until Fusion updates them. Gotcha FusionDrawingStoredEdges.md. T14 pokes V1/V2 (left, back).
- T14 (--poke V1, V2): left/below unchanged (already right by symmetry); back view after update 5 curves, 160x80 at
  Kit's planned place. T15 (V10-V13 on V7NoEdges: action/dependency/network status 1, view flag 0x2000): all opened,
  all views still 0 curves. No tested DWG field makes Fusion find edges on open. Evidence GraftRoundT10.json (T10-T15).

## Status at handoff (2026-11-13 04:50)

- 23 commits f1516ec99..HEAD. Fusion accepted G2 L1-L4, T3-T15 grafts (no failures since T3).
- finalgrep: only KStateMark (documented constant), KTrackedSpan = 6 (records per tracked edge), member file names,
  SheetDefaults.json and DrawingClasses.json (format vocabulary) remain.
- Open: Kit views carry no stored edges, so Fusion shows them empty until a view update; Kit would have to write
  the visible edge list (edge ids, cached curves, drawn entities). Iso base view layout undecoded. ASME template
  not captured (account at 10/10 documents, all younger than 7 days). Bits 0x20 and 0x2000 unexplained. Kit writes
  no visual style on viewports (Fusion links one).
