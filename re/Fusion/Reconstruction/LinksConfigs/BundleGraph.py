import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.ContainerCodec.Wire.EmitRedirects import EmitRedirects
from convert.formats.Fusion.ContainerCodec.Wire.ReadDocProps import ReadDocProps
from convert.formats.Fusion.ContainerCodec.Wire.ReadRedirects import ReadRedirects
from convert.formats.Fusion.ContainerCodec.Wire.ReadAssetHeader import ReadAssetHeader
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootWire import ReadRootWire

bundle = ReadBundle(Path(sys.argv[1]).read_bytes())
owners = {entry.ObjectId: entry for entry in bundle.Description.Graph.Objects}
documents = {entry.FileName: entry.DataValue for entry in bundle.Documents}
for entry in bundle.Description.Graph.Objects:
    data = documents[entry.MemberPath]
    with OpenFusionZip(data) as archive:
        names = archive.Names if hasattr(archive, 'Names') else None
        redirects_bytes = archive.ReadMember('RedirectionsStream.dat', 4 << 20)
        props_bytes = archive.ReadMember('Properties.dat', 1 << 16)
        root_bytes = archive.ReadMember('Manifest.dat', 1 << 20)
    redirects = ReadRedirects(redirects_bytes)
    assert EmitRedirects(redirects) == redirects_bytes
    props = ReadDocProps(props_bytes)
    root = ReadRootWire(root_bytes)
    roles = {(ref.TargetName, dict(ref.Properties).get('neutronRole')) for ref in redirects.References}
    graph = {
        (owners[relation.TargetId].MemberPath, field.TextValue)
        for group in entry.References
        for relation in group.Relations
        for field in relation.Metadata
        if field.FieldName == 'neutronRole'
    }
    link_ids = {link.LinkId for link in root.Links}
    print(entry.ObjectId, entry.MemberPath[:12], 'designs', len(redirects.Designs), 'refs', len(redirects.References), 'graph==redirects', graph == roles, 'roles==links', {role for _, role in roles} == link_ids, 'props', props.Structure.TypeName if props and props.Structure else props, 'lineage', root.Lineage[0] if root.Lineage else None)
    for design in redirects.Designs:
        print('    design', design.TargetName[:12], design.FileVersion, design.DisplayName, design.LineageUrn == entry.LineageUrn or None)
