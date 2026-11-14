from tests.Research.MiniClaims import MiniClaims
from tests.Research.MiniLeases import MiniLeases
from tests.Research.MiniQueue import MiniQueue
from tests.Research.MiniResources import MiniResources


class MiniController(MiniResources, MiniQueue, MiniClaims, MiniLeases):
    pass
