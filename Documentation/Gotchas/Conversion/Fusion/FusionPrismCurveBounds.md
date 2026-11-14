# Prism carrier bounds differ from edge intervals

A bounded rectangular edge does not imply that its `straight-curve` carrier stores bounds. In the qualified 40 × 30 × 25 mm Fusion control, all twelve edges have finite endpoint parameters. However, only the four bottom carriers store lower and upper bounds. The four top carriers and four vertical carriers are unbounded.

The complete field evidence is [ControlledHistory.json](../../../../re/Fusion/Reconstruction/CuboidHistory/ControlledHistory.json), from source history SHA-256 `aa25da5b0c1bf72d5ea53cacea4ec09854a0395ebfcfd46786f32480403d0cf2`. A bounded straight carrier has nine fields; an unbounded one has seven. Each bound flag controls whether its following numeric value exists.

Keep carrier bounds separate from edge endpoint parameters. The prism history reader preserves both qualified forms and validates `origin + parameter × direction` against the edge's vertices. Its writer derives a complete finite solid even when all carrier lines are unbounded. Do not infer carrier bounds from an edge's geometric role or use a fixed nine-field decoder for every line.
