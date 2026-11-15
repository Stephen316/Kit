# Closed-profile IDs do not prove a closed contour

`Sketch.closed_profile_entity_ids` declares member identities.
Neutral definition validation checks the creator's sketch and controls but does not prove that those members form a finite, nondegenerate contour.
A single `LineGeometry` can therefore remain neutral-valid while its closed-profile declaration is geometrically false.
An entity's kind tag can also disagree with its actual geometry class.

The CLI checks actual supported geometry classes and matching tags, then reuses the SDK's circle and straight-ring validators.
It currently accepts one complete circle or a simple source-ordered three/four-sided line ring.
Longer, curved, mixed, or multiple-loop paths remain available for inspection without being promoted to conversion-ready profiles.
The four-side bound keeps the reused pairwise simplicity check constant per profile; entity/member indexing is linear.

See [the contour guard change](../../../Changes/Commands/ProfileContourGuard.md).
