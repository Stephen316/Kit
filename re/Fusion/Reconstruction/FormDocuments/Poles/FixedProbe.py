"""Research (runs inside Fusion through re/Fusion/LocalOracle/RunLocked.mjs): import, convert and
save the FixedCages.py cages with the crease-round driver, without touching its shared Plan.txt.

Saves land in the ignored Crease/tmp/FixedRound/, the report in Crease/FixedRound/Probe.json.
"""

from pathlib import Path

crease = Path(__file__).resolve().parents[3] / 'LocalOracle/FormDocuments/Crease'
driver = crease / 'ProbeCrease.py'
source = driver.read_text().split('\nfor plan in pointer.read_text().split():')[0]
namespace = {'__file__': str(driver), '__name__': 'fixed_probe'}
exec(compile(source, str(driver), 'exec'), namespace)
namespace['probe']('FixedRound/Preparation.json')
