from tests.Research.MiniAdapter.MiniClaims import MiniClaims
from tests.Research.MiniAdapter.MiniLeases import MiniLeases
from tests.Research.MiniAdapter.MiniQueue import MiniQueue
from tests.Research.MiniAdapter.MiniResources import MiniResources


class MiniController(MiniResources, MiniQueue, MiniClaims, MiniLeases):
    pass
