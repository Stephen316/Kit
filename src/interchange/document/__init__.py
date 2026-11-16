from interchange.document.Models.DocumentCaps import GetRetainedCaps, InferCaps
from interchange.document.Models.DocumentError import DocumentError
from interchange.document.Models.DocumentFilter import FilterDocument
from interchange.document.Models.DocumentMetadata import AddWrapperMeta, GetSemanticMeta
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentPayload import GetPayloadIds
from interchange.document.Behavior.DocumentMethods import BindDocumentMut
from interchange.Compatibility.PythonCompat import BindCompatMut
from interchange.Compatibility.PublicMetadata import BindFunctionMut, BindNameMut
from inspect import Signature as FuncSig
from inspect import Parameter as FuncParam

BindCompatMut((CadDocument,), {__name__: globals()})
BindDocumentMut(CadDocument)

BindNameMut(
    DocumentError,
    __name__,
    "CadDocumentValidationError",
    globals(),
)

BindFunctionMut(
    FilterDocument,
    __name__,
    "filter_document",
    {
        "document": "CadDocument",
        "include_brep": "bool",
        "include_tessellation": "bool",
        "keep_payload_records": "bool",
        "return": "CadDocument",
    },
    FuncSig(
        (
            FuncParam(
                "document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"
            ),
            FuncParam("include_brep", FuncParam.KEYWORD_ONLY, annotation="bool"),
            FuncParam(
                "include_tessellation", FuncParam.KEYWORD_ONLY, annotation="bool"
            ),
            FuncParam(
                "keep_payload_records", FuncParam.KEYWORD_ONLY, annotation="bool"
            ),
        ),
        return_annotation="CadDocument",
    ),
    globals(),
)
BindFunctionMut(
    InferCaps,
    __name__,
    "infer_capabilities",
    {
        "document": "CadDocument",
        "roundtrip_metadata": "bool",
        "return": "frozenset[Capability]",
    },
    FuncSig(
        (
            FuncParam(
                "document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"
            ),
            FuncParam(
                "roundtrip_metadata",
                FuncParam.KEYWORD_ONLY,
                default=False,
                annotation="bool",
            ),
        ),
        return_annotation="frozenset[Capability]",
    ),
    globals(),
)
BindFunctionMut(
    GetRetainedCaps,
    __name__,
    "retained_capabilities",
    {
        "document": "CadDocument",
        "capabilities": "frozenset[Capability]",
        "include_brep": "bool",
        "include_tessellation": "bool",
        "return": "frozenset[Capability]",
    },
    FuncSig(
        (
            FuncParam(
                "document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"
            ),
            FuncParam(
                "capabilities",
                FuncParam.POSITIONAL_OR_KEYWORD,
                annotation="frozenset[Capability]",
            ),
            FuncParam("include_brep", FuncParam.KEYWORD_ONLY, annotation="bool"),
            FuncParam(
                "include_tessellation", FuncParam.KEYWORD_ONLY, annotation="bool"
            ),
        ),
        return_annotation="frozenset[Capability]",
    ),
    globals(),
)
BindFunctionMut(
    GetSemanticMeta,
    __name__,
    "semantic_metadata",
    {
        "metadata": "Mapping[str, Any]",
        "return": "Mapping[str, Any]",
    },
    FuncSig(
        (
            FuncParam(
                "metadata",
                FuncParam.POSITIONAL_OR_KEYWORD,
                annotation="Mapping[str, Any]",
            ),
        ),
        return_annotation="Mapping[str, Any]",
    ),
    globals(),
)
BindFunctionMut(
    GetPayloadIds,
    __name__,
    "source_payload_indexes",
    {
        "document": "CadDocument",
        "return": "frozenset[int]",
    },
    FuncSig(
        (
            FuncParam(
                "document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"
            ),
        ),
        return_annotation="frozenset[int]",
    ),
    globals(),
)
BindFunctionMut(
    AddWrapperMeta,
    __name__,
    "with_wrapper_metadata",
    {
        "metadata": "Mapping[str, Any]",
        "keys": "Iterable[str]",
        "return": "Mapping[str, Any]",
    },
    FuncSig(
        (
            FuncParam(
                "metadata",
                FuncParam.POSITIONAL_OR_KEYWORD,
                annotation="Mapping[str, Any]",
            ),
            FuncParam(
                "keys",
                FuncParam.POSITIONAL_OR_KEYWORD,
                annotation="Iterable[str]",
            ),
        ),
        return_annotation="Mapping[str, Any]",
    ),
    globals(),
)

# the public cad document validation error name must remain available so existing integrations keep resolving the canonical implementation
CadDocumentValidationError = DocumentError

# the public filter document name must remain available so existing integrations keep resolving the canonical implementation
filter_document = FilterDocument

# the public infer capabilities name must remain available so existing integrations keep resolving the canonical implementation
infer_capabilities = InferCaps

# the public retained capabilities name must remain available so existing integrations keep resolving the canonical implementation
retained_capabilities = GetRetainedCaps

# the public semantic metadata name must remain available so existing integrations keep resolving the canonical implementation
semantic_metadata = GetSemanticMeta

# the public source payload indexes name must remain available so existing integrations keep resolving the canonical implementation
source_payload_indexes = GetPayloadIds

# the public with wrapper metadata name must remain available so existing integrations keep resolving the canonical implementation
with_wrapper_metadata = AddWrapperMeta


# document consumers need one intentional facade while implementations remain independently reviewable
__all__ = (
    "CadDocument",
    "CadDocumentValidationError",
    "filter_document",
    "infer_capabilities",
    "retained_capabilities",
    "semantic_metadata",
    "source_payload_indexes",
    "with_wrapper_metadata",
)
