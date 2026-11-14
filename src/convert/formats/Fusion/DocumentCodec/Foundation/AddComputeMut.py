from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def AddComputeMut(Author: AuthorState) -> None:
    Author.Allocate("fragment", "DcDesignFragment", ParentRole="component")
    Author.Allocate("nodes", "DcNodes", ParentRole="fragment")
    for RoleName, NameValue in [
        ("compute", "DcComputeManager"),
        ("dependency", "DcDependencyManager"),
        ("association", "DcAssociationManager"),
        ("feature_ids", "DcFeatureIdManager"),
        ("xref", "DcXRefManager"),
    ]:
        Author.Allocate(RoleName, NameValue)
    Author.Allocate("dc_component", "DcComponent", ParentRole="nodes")
    Author.Allocate("dynamic", "DynamicUpdateData")
    Author.Allocate("creation_order", "DcCreationOrderFeatures")
    Author.Allocate("occurrence", "DcOccurrence")
