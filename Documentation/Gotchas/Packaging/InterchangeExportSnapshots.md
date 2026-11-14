# Interchange exports register serialization types

A new name in `interchange.__all__` might appear to change only the import surface.
Every dataclass or enum in that tuple is also added to `KTypeRegistry`.
`CheckRegistry` accepts a registered type only when a facade module in `PythonCompatFacades.py` exports it.
`CheckTopLevel` and `CheckClasses` compare the top-level names and the `CadDocument` fields with their snapshots.

When you add a public model, add a facade module whose `__all__` exports it.
Update `PythonCompatFacades.py`, `PythonCompatTopNames.py` and the field snapshot of each changed model in `tests/interchange/compatibility/`.
`MaterialRecord` uses the `interchange.materials` facade.
