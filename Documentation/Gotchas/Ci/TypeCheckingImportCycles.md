# CodeQL counts type-checking imports in cycles

An import under `if TYPE_CHECKING:` might appear to remove a runtime import cycle.
CodeQL still reports `py/unsafe-cyclic-import` for it.
When the name is used only in a string such as `cast("CadDocument", self)`, CodeQL also reports `py/unused-import`.
An import moved into a function body is also counted.

Make the dependency one-way.
For a mixin that reads fields of its composing class, declare a `Protocol` with those fields in the mixin module.
Cast `self` to that `Protocol`.
The mixin module then imports only leaf types.
Keep a member whose type is defined in the composing module, such as `CadDocument.Assembly`, in that class.
See the `RootAccess`, `FeatureAccess` and `GeometryAccess` mixins under `src/interchange/document/models/Access/`.
