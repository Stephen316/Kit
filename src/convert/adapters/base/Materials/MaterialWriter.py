from typing import Protocol, runtime_checkable as RuntimeCheck


@RuntimeCheck
class MaterialWriter(Protocol):
    @property
    def TypedMaterials(self) -> bool:
        raise TypeError("a writer must explicitly implement typed material support")
