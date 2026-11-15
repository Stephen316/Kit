# Native Form area caches have their own precision

## Expectation

A difference between an independently integrated area and Fusion's stored area cache must mean that the quadrature order is insufficient.
Raising that order should move the integrated value toward the native one.
Alternatively, a precision explanation could justify a looser equality assertion.

## Actual behavior

Eight-point and sixteen-point spans produced the same Box3 area within `1e-13 cm²` and the same HeldPrism5 area within `3.21e-13 cm²`.
Box3 changed from `28.196624686525613` to `28.196624686525713 cm²`.
HeldPrism5 changed from `14.69314686718681` to `14.693146867187131 cm²`.
The measured convergence disproves the quadrature explanation.

The independent integral and native cache come from different numerical estimators.
Their relative area differences are about `3.991e-5` for Box3 and `7.008e-6` for HeldPrism5.
Fusion nevertheless evaluates the expected BRep area and geometry during load, edit, rebuild, export, and reopen.
The [convergence record](../../../../../../re/Fusion/Reconstruction/FormDocuments/General/AreaConvergence.json) binds both remote runs and their exact values.
The [eight-point run](https://github.com/TryUniCAD/Kit/actions/runs/43583291958) and [sixteen-point run](https://github.com/TryUniCAD/Kit/actions/runs/43584701390) both failed an incorrect exact-area assumption.

## Workaround

Do not loosen an existing tolerance to accommodate different numerical estimators.
Use an exact planar fixture where geometry and cached area have the same measured meaning and compare area at `1e-8` absolute and relative tolerance.
`TestPlanarArea` supplies this check through the current writer and the untouched native `Grid/Primitives/Plane3x2.f3d` control.
It reuses that control's typed cage directly, so it cannot select an edited-area archive by mistake.
Keep curved BRep geometry and all other mass fields at `1e-8` absolute and relative tolerance.
Preserve the convergence record as evidence about the estimator, not as a cross-kernel equality assertion or a production correction value.
The [mass-cache change](../../../../../Changes/Fusion/TSpline/FusionFormMassCache.md) distinguishes cache validation from native approximation and exact geometry acceptance.
