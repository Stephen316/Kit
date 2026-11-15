from interchange.document.models.DocumentModel import CadDocument


# assembly exports require qualified placements and constraints throughout the component tree
def AssemblyIssues(Document: CadDocument) -> tuple[str, ...]:
    Assembly = Document.assembly
    if Assembly is None:
        return ()
    Findings = [
        f"{Document.source.path}: assembly {Assembly.root_definition_id} {FieldName} (native-only)"
        for FieldName in ("transform_status", "constraint_status")
        if Assembly.attributes.get(FieldName) == "native-only"
    ]
    Findings.extend(
        f"{Document.source.path}: instance {Instance.id} has an unresolved native transform"
        for Instance in Assembly.instances
        if Instance.attributes.get("transform_resolved") is False
    )
    return tuple(Findings)
