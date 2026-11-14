"""Research: half-edge view of a Form cage for the face-block study.

Links are TSM half-edges. Boundary links of an open cage carry FaceIndex -1.
"""


class CageGraph:
    def __init__(self, surface):
        topo = surface.Topology
        self.surface = surface
        self.links = topo.Links
        self.faces = topo.Faces
        self.nverts = len(topo.Vertices)
        links = self.links
        self.head = [links[link.NextLink].VertexIndex for link in links]
        self.fans = []
        for index, vertex in enumerate(topo.Vertices):
            fan, link = [], vertex.OriginLink
            while True:
                fan.append(link)
                link = links[links[link].Previous].Opposite
                if link == vertex.OriginLink:
                    break
            self.fans.append(fan)
        self.valence = [len(fan) for fan in self.fans]
        self.boundary_link = [link.FaceIndex < 0 or links[link.Opposite].FaceIndex < 0 for link in links]
        creased = set(surface.Creases.EdgeIndices) if surface.Creases else set()
        self.crease_vertices = set(surface.Creases.VertexIndices) if surface.Creases else set()
        self.creased_link = [link.EdgeIndex in creased for link in links]
        self.on_boundary = [any(self.boundary_link[link] for link in fan) for fan in self.fans]

    def loop(self, face):
        out, link = [], self.faces[face].OriginLink
        while True:
            out.append(link)
            link = self.links[link].NextLink
            if link == self.faces[face].OriginLink:
                return out

    def loop_vertices(self, face):
        return [self.links[link].VertexIndex for link in self.loop(face)]

    def sharp(self, link):
        return self.boundary_link[link] or self.creased_link[link]

    def is_regular(self, vertex):
        """Interior valence-4 vertex with no sharp edge through it."""
        if self.on_boundary[vertex] or vertex in self.crease_vertices:
            return False
        return self.valence[vertex] == 4

    def straight(self, link):
        """Outgoing link at the head vertex continuing `link` straight, or None."""
        head = self.head[link]
        fan = self.fans[head]
        back = self.links[link].Opposite
        position = fan.index(back)
        if self.valence[head] == 4 and not self.on_boundary[head]:
            return fan[(position + 2) % 4]
        return None

    def edge_key(self, link):
        return self.links[link].EdgeIndex
