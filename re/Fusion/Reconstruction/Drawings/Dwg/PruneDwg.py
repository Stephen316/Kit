"""Research helpers that remove DWG objects from a typed DwgFile.

The native experiments use them to learn which objects Fusion requires.
Removal follows ownership, then repairs typed lists that point at removed objects.
Any other reference to a removed object is replaced by a null handle and counted.
"""

import collections
from dataclasses import replace

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField, DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.NameObject import NameObject

RELATIVE = {6: 1, 8: -1}


def target(own, ref):
    if ref.RefCode == 6:
        return own + 1
    if ref.RefCode == 8:
        return own - 1
    if ref.RefCode == 0xA:
        return own + ref.RefValue
    if ref.RefCode == 0xC:
        return own - ref.RefValue
    return ref.RefValue


def field(record, name, default=None):
    for item in record.RecordFields:
        if item.FieldName == name:
            return item.FieldValue
    return default


def with_fields(record, **values):
    names = {item.FieldName for item in record.RecordFields}
    missing = set(values) - names
    if missing:
        raise ValueError(f'fields not present: {sorted(missing)}')
    return DwgRecord(tuple(DwgField(item.FieldName, values.get(item.FieldName, item.FieldValue)) for item in record.RecordFields))


def without_fields(record, *names):
    return DwgRecord(tuple(item for item in record.RecordFields if item.FieldName not in names))


def refs_in(value):
    if isinstance(value, DwgHandleRef):
        yield value
    elif isinstance(value, DwgRecord):
        for item in value.RecordFields:
            yield from refs_in(item.FieldValue)
    elif isinstance(value, tuple):
        for item in value:
            if isinstance(item, (DwgHandleRef, DwgRecord)):
                yield from refs_in(item)


def object_targets(obj):
    own = obj.ObjectHandle
    for ref in refs_in(obj.CommonData):
        yield 'common', target(own, ref)
    for ref in refs_in(obj.ClassData):
        yield 'class', target(own, ref)
    for ref in obj.HandleRefs:
        yield 'tail', target(own, ref)


def owner_of(obj):
    ref = field(obj.CommonData, 'Owner')
    return None if ref is None else target(obj.ObjectHandle, ref)


class Graph:
    def __init__(self, dwg):
        self.dwg = dwg
        self.objects = {obj.ObjectHandle: obj for obj in dwg.DwgObjects}
        self.names = {handle: NameObject(obj.TypeNumber, dwg.ClassTable)[0] for handle, obj in self.objects.items()}
        self.children = collections.defaultdict(set)
        self.incoming = collections.defaultdict(set)
        for handle, obj in self.objects.items():
            owner = owner_of(obj)
            if owner is not None:
                self.children[owner].add(handle)
            for _where, other in object_targets(obj):
                if other and other != handle:
                    self.incoming[other].add(handle)
            if self.names[handle] == 'BLOCK_HEADER':
                for name in ('BlockEntity', 'EndBlock'):
                    ref = field(obj.ClassData, name)
                    if ref is not None:
                        self.children[handle].add(target(handle, ref))
                for ref in field(obj.ClassData, 'Owned', ()):
                    self.children[handle].add(target(handle, ref))

    def closure(self, kill):
        result = set(kill)
        queue = list(kill)
        while queue:
            handle = queue.pop()
            for child in self.children.get(handle, ()):
                if child not in result and child in self.objects:
                    result.add(child)
                    queue.append(child)
            obj = self.objects.get(handle)
            if obj is not None:
                xdic = field(obj.CommonData, 'Xdic')
                if xdic is not None:
                    other = target(handle, xdic)
                    if other in self.objects and other not in result:
                        result.add(other)
                        queue.append(other)
        for handle, obj in self.objects.items():
            if self.names[handle] == 'SORTENTSTABLE' and handle not in result:
                if any(other in result for _w, other in object_targets(obj)):
                    result.add(handle)
        return result


def filter_pairs(own, record, list_name, count_name, partner=None, dead=frozenset()):
    refs = field(record, list_name, ())
    keep = [index for index, ref in enumerate(refs) if target(own, ref) not in dead]
    if len(keep) == len(refs):
        return record
    values = {list_name: tuple(refs[index] for index in keep)}
    if count_name:
        values[count_name] = len(keep)
    if partner:
        others = field(record, partner)
        values[partner] = type(others)(others[index] for index in keep) if not isinstance(others, bytes) else bytes(others[index] for index in keep)
    return with_fields(record, **values)


def null_dead(own, value, dead, counter, label):
    if isinstance(value, DwgHandleRef):
        if value.RefValue and target(own, value) in dead:
            counter[label] += 1
            return DwgHandleRef(value.RefCode if value.RefCode in (2, 3, 4, 5) else 4, 0)
        return value
    if isinstance(value, DwgRecord):
        return DwgRecord(tuple(DwgField(item.FieldName, null_dead(own, item.FieldValue, dead, counter, label)) for item in value.RecordFields))
    if isinstance(value, tuple) and value and isinstance(value[0], (DwgHandleRef, DwgRecord)):
        return tuple(null_dead(own, item, dead, counter, label) for item in value)
    return value


LISTS = {
    'DICTIONARY': [('Items', 'ItemCount', 'Entries')],
    'ACDBDICTIONARYWDFLT': [('Items', 'ItemCount', 'Entries')],
    'BLOCK_HEADER': [('Owned', 'OwnedCount', None), ('Inserts', None, 'InsertCounts')],
    'LAYOUT': [('Viewports', 'ViewportCount', None)],
}


def repair(graph, obj, dead, counter):
    own = obj.ObjectHandle
    name = graph.names[own]
    common = filter_pairs(own, obj.CommonData, 'Reactors', 'ReactorCount', None, dead)
    xdic = field(common, 'Xdic')
    if xdic is not None and target(own, xdic) in dead:
        common = with_fields(without_fields(common, 'Xdic'), NoXdic=1)
    data = obj.ClassData
    for list_name, count_name, partner in LISTS.get(name, []):
        if field(data, list_name) is not None:
            data = filter_pairs(own, data, list_name, count_name, partner, dead)
    if name.endswith('_CONTROL') and field(data, 'Entries') is not None:
        data = filter_pairs(own, data, 'Entries', 'EntryCount', None, dead)
    common = null_dead(own, common, dead, counter, name + ' common')
    data = null_dead(own, data, dead, counter, name + ' class')
    tail = tuple(null_dead(own, ref, dead, counter, name + ' tail') for ref in obj.HandleRefs)
    return replace(obj, CommonData=common, ClassData=data, HandleRefs=tail)


def prune(dwg, kill):
    graph = Graph(dwg)
    dead = graph.closure(kill)
    counter = collections.Counter()
    kept = tuple(repair(graph, obj, dead, counter) for obj in dwg.DwgObjects if obj.ObjectHandle not in dead)
    removed = collections.Counter(graph.names[handle] for handle in dead if handle in graph.objects)
    return replace(dwg, DwgObjects=kept), removed, counter
