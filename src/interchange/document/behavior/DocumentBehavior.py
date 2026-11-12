from interchange.document.behavior.DocumentIoBehavior import DocumentIo
from interchange.document.behavior.DocumentLookupBehavior import DocumentLookup
from interchange.document.behavior.DocumentValidBehavior import DocumentValid


# focused method contracts keep the immutable document schema independently reviewable
class DocumentApi(DocumentIo, DocumentValid, DocumentLookup):
    KSlotsValue = ()

    locals()["__slots__"] = KSlotsValue
