from collections.abc import Callable

from convert.adapters.Fusion.Writer import FusionWriter
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.catia.Adapter import CatiaAdapter
from convert.adapters.freecad.Adapter import FreeCadAdapter
from convert.adapters.json.Adapter import JsonAdapter
from interchange.document.models.DocumentModel import CadDocument

KDirectWriters: tuple[
    tuple[str, Callable[[CadDocument, KTargetType, WriteOptions], WriteResult]], ...
] = (
    ("json-write", JsonAdapter().write),
    ("json-Write", JsonAdapter().Write),
    ("json-EmitTarget", JsonAdapter().EmitTarget),
    ("fusion-write", FusionWriter().write),
    ("fusion-Write", FusionWriter().Write),
    ("catia-write", CatiaAdapter().write),
    ("freecad-write", FreeCadAdapter().write),
)
