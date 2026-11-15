from tests.Research.MiniAdapter.MiniClaims import MiniClaims
from tests.Research.MiniAdapter.MiniLeases import MiniLeases
from tests.Research.MiniAdapter.MiniQueue import MiniQueue
from tests.Research.MiniAdapter.MiniResources import MiniResources


# supervisor tests need a substitute controller without copying its durable store implementation
class MiniController(MiniResources, MiniQueue, MiniClaims, MiniLeases):
    pass
