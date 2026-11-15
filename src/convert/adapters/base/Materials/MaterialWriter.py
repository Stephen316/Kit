from typing import Protocol, runtime_checkable as RuntimeCheck


# the material writer contract needs a dedicated boundary so format boundaries expose consistent document behavior
@RuntimeCheck
class MaterialWriter(Protocol):

    # typed materials needs an explicit validity boundary so format boundaries expose consistent document behavior
    @property
    def TypedMaterials(self) -> bool:
        raise TypeError("a writer must explicitly implement typed material support")
