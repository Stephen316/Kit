# Native circular mass caches are numerically integrated

Analytically identical circular geometry can have slightly unequal cached transverse moments in a native Fusion save. The 12 mm radius, 21 mm height cylinder control stores `moi.x = 17.385321755015763` and `moi.y = 17.38532263840058` in centimetre-based volume-inertia units. Its cached center also contains a small nonzero X component. Requiring exact analytic symmetry for this numerical cache rejects the valid saved model.

The circular projector checks the full tensor, volume, area and center against independent analytic formulas with relative tolerance `1e-6` and absolute tolerance `1e-8`. This tolerance applies only to the persisted numeric mass cache. Radius, height, placement, conical carriers, recipes and native topology retain their separate tight geometric checks. The complete original floating-point cache remains in typed state and is re-emitted unchanged.

The source reports integration precision approximately `0.00048340252544976824`. The observed transverse discrepancy is approximately `8.83e-7`, far smaller than that reported precision. The independent strict prism comparison remains unchanged.

See the [research evidence](../../../../../re/Fusion/Reconstruction/PublicRotational/ProjectionModel.md) and [qualified circular adapter](../../../../Changes/Fusion/Adapter/FusionNativeCircularProjection.md).
