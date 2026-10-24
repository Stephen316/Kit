"""Execute actual witness AST with synthetic handles; never import/run the SDK."""
import argparse
import ast
import gc
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import weakref

ROOT = Path(__file__).resolve().parent
SOURCE = 'GenerateRuleFilletSurfaceContrasts.py'
HELPERS = ('quarantine_witness', 'same_api_entity', 'resolve_single', 'create_witness',
           'read_rolled_witness', 'restore_after_witness', 'finalize')
SCENARIOS = ('two_witness_success', 'ambiguous_token', 'zero_offset_add_failure',
             'rolled_entity_mismatch', 'rollback_failure', 'restoration_failure',
             'equality_not_implemented', 'equality_non_boolean')


def validate():
    source = (ROOT/SOURCE).read_text()
    parsed = ast.parse(source)
    run = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
    helpers = [n for n in run.body if isinstance(n, ast.FunctionDef) and n.name in HELPERS]
    if {n.name for n in helpers} != set(HELPERS):
        raise AssertionError('Actual witness helper extraction differs')
    index = next(i for i, n in enumerate(run.body) if isinstance(n, ast.For)
        and isinstance(n.target, ast.Tuple) and [e.id for e in n.target.elts] == ['case', 'offset'])
    exercise = ast.FunctionDef(name='exercise_orchestration',
        args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=run.body[index:], decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=helpers+[exercise], type_ignores=[]))
    compiled = compile(module, SOURCE+' [actual witness AST, synthetic SDK]', 'exec')
    results, checks = [], []

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    for scenario in SCENARIOS:
        live = weakref.WeakValueDictionary()
        state = dict(scenario=scenario, before=False, features={}, next_feature=1,
            create_input_calls=0, add_calls=0, equality_calls=0, base_equality_calls=0,
            equality_boolean_coercions=0, close_calls=0,
            restoration_calls=0, events=[], documents=[])

        class Native:
            def __init__(self, kind, identity=0):
                self.kind, self.identity = kind, identity
                live[id(self)] = self

            @property
            def isValid(self):
                return True

            @property
            def objectType(self):
                return 'Synthetic::'+self.kind

            def __eq__(self, other):
                # Model the cross-module Base binding that caused the live
                # failure. A concrete Fusion comparison must bypass this.
                state['base_equality_calls'] += 1
                return NotImplemented

        class NonBooleanEquality:
            def __bool__(self):
                state['equality_boolean_coercions'] += 1
                raise AssertionError('Nonboolean SDK equality was coerced')

        def concrete_equal(left, right):
            state['equality_calls'] += 1
            if scenario == 'equality_not_implemented':
                return NotImplemented
            if scenario == 'equality_non_boolean':
                return NonBooleanEquality()
            return (type(left) is type(right) and left.kind == right.kind
                and left.identity == right.identity)

        class Face(Native):
            def __init__(self, identity):
                super().__init__('BRepFace', identity)

            def __eq__(self, other):
                return concrete_equal(self, other)

            @staticmethod
            def cast(value):
                return value if isinstance(value, Face) else None

            @property
            def body(self):
                return Body()

            @property
            def tempId(self):
                return self.identity*10

        class Body(Native):
            def __init__(self):
                super().__init__('BRepBody', 1)

            name = 'SyntheticRuleBody'
            entityToken = 'body-token'

        class Collection(Native):
            def __init__(self, identities=()):
                super().__init__('ObjectCollection')
                self.identities = list(identities)

            @staticmethod
            def create():
                return Collection()

            @property
            def count(self):
                return len(self.identities)

            def add(self, face):
                self.identities.append(face.identity)
                return True

            def item(self, index):
                return Face(self.identities[index])

        class Value(Native):
            def __init__(self, number):
                super().__init__('ValueInput')
                self.realValue = number

            @staticmethod
            def createByReal(number):
                return Value(number)

        class Inputs(Native):
            def __init__(self, identities, distance, operation, chain):
                super().__init__('OffsetFeatureInput')
                self.identities = identities[:]
                self.number = distance
                self.operation, self.isChainSelection = operation, chain
                self.offsetType = 0

            @property
            def entities(self):
                return Collection(self.identities)

            @property
            def distance(self):
                return Value(self.number)

        class Parameter(Native):
            def __init__(self):
                super().__init__('ModelParameter')
                self.value = 0.

        class TimelineObject(Native):
            def __init__(self, feature_id):
                super().__init__('TimelineObject', feature_id)

            def rollTo(self, before):
                state['events'].append(dict(event='rollback', before=before))
                if scenario == 'rollback_failure':
                    return False
                state['before'] = before
                return True

        class Feature(Native):
            def __init__(self, identity):
                super().__init__('OffsetFeature', identity)

            def __eq__(self, other):
                return concrete_equal(self, other)

            @property
            def name(self):
                return state['features'][self.identity]['name']

            @name.setter
            def name(self, value):
                state['features'][self.identity]['name'] = value

            @property
            def entityToken(self):
                return 'feature:'+str(self.identity)

            healthState = 0
            errorOrWarningMessage = ''
            isChainSelection = False
            operation = 4
            offsetType = 0

            @property
            def distance(self):
                return Parameter()

            @property
            def timelineObject(self):
                return TimelineObject(self.identity)

            @property
            def entities(self):
                if not state['before']:
                    raise AssertionError('Actual helper called rolled getter outside pre-node state')
                identities = state['features'][self.identity]['identities']
                if scenario == 'rolled_entity_mismatch':
                    identities = [999]
                return Collection(identities)

        class Offsets(Native):
            def __init__(self):
                super().__init__('OffsetFeatures')

            def createInput(self, entities, distance, operation, chain):
                state['create_input_calls'] += 1
                return Inputs(entities.identities, distance.realValue, operation, chain)

            def add(self, inputs):
                state['add_calls'] += 1
                if scenario == 'zero_offset_add_failure':
                    raise RuntimeError('Synthetic zero-offset add rejected')
                identity = state['next_feature']
                state['next_feature'] += 1
                state['features'][identity] = dict(name='', identities=inputs.identities[:])
                return Feature(identity)

            def itemByName(self, name):
                found = [i for i, row in state['features'].items() if row['name'] == name]
                return Feature(found[0]) if len(found) == 1 else None

        class Features(Native):
            def __init__(self):
                super().__init__('Features')

            @property
            def offsetFeatures(self):
                return Offsets()

        class Root(Native):
            def __init__(self):
                super().__init__('Component')

            @property
            def features(self):
                return Features()

        class Timeline(Native):
            def __init__(self):
                super().__init__('Timeline')

            markerPosition = 100

            def moveToEnd(self):
                kinds = sorted(h.kind for h in live.values())
                state['restoration_calls'] += 1
                state['events'].append(dict(event='restore', live_kinds=kinds))
                if kinds != ['Design', 'Timeline']:
                    raise AssertionError('Rolled getter/native feature aliases survived into restoration')
                if scenario == 'restoration_failure':
                    return False
                state['before'] = False
                return True

        class Options(Native):
            def __init__(self, path):
                super().__init__('ExportOptions')
                self.path = Path(path)

        class Export(Native):
            def __init__(self):
                super().__init__('ExportManager')

            def createFusionArchiveExportOptions(self, path):
                return Options(path)

            def execute(self, options):
                options.path.write_bytes(('Synthetic archive; consumers='+str(len(state['features']))).encode())
                state['events'].append(dict(event='export', file=options.path.name,
                    consumers=len(state['features'])))
                return True

        class Design(Native):
            def __init__(self):
                super().__init__('Design')

            @staticmethod
            def cast(value):
                return value

            @property
            def rootComponent(self):
                return Root()

            @property
            def timeline(self):
                return Timeline()

            @property
            def exportManager(self):
                return Export()

            def computeAll(self):
                return True

            def findEntityByToken(self, token):
                kind, identity = token.split(':')
                identity = int(identity)
                if kind == 'feature':
                    return [Feature(identity)]
                if scenario == 'ambiguous_token':
                    return [Face(identity), Face(identity+100)]
                return [Face(identity)]

        class Products:
            def itemByProductType(self, _kind):
                return Design()

        class Document:
            products = Products()

            def close(self, save):
                state['close_calls'] += 1
                kinds = sorted(h.kind for h in live.values())
                state['events'].append(dict(event='close', live_kinds=kinds, save=save))
                if kinds or state['before'] or save:
                    raise AssertionError('Native aliases/model rollback survived to owned close(False)')
                return True

        class Documents:
            def add(self, _kind):
                doc = Document()
                state['documents'].append(doc)
                return doc

        class Collector:
            @staticmethod
            def collect():
                collected = gc.collect()
                kinds = sorted(h.kind for h in live.values())
                state['events'].append(dict(event='gc', before=state['before'], live_kinds=kinds))
                if kinds:
                    raise AssertionError('Successful actual helper frame leaked native wrappers into outer GC')
                return collected

        fusion = SimpleNamespace(Design=Design, BRepFace=Face, OffsetFeature=Feature,
            FeatureOperations=SimpleNamespace(NewBodyFeatureOperation=4))
        adsk = SimpleNamespace(fusion=fusion, core=SimpleNamespace(Base=Native,
            ObjectCollection=Collection, ValueInput=Value,
            DocumentTypes=SimpleNamespace(FusionDesignDocumentType=1)))
        truth = dict(samples=[], errors=[])
        with tempfile.TemporaryDirectory(prefix='fusion-rule-witness-synthetic-') as directory:
            folder = Path(directory)

            def populate(_doc, case, _offset):
                return dict(file=case+'.f3d', result_bodies=[dict(deep_face_temp_ids=[10, 20],
                    faces=[dict(entity_token='face:1', temp_id=10), dict(entity_token='face:2', temp_id=20)])])

            def journal(phase, case=None, **fields):
                state['events'].append(dict(event='journal', phase=phase, case=case, **fields))

            env = dict(adsk=adsk, app=SimpleNamespace(documents=Documents()), truth=truth,
                folder=folder, populate=populate, journal=journal, gc=Collector, hashlib=hashlib,
                MAX_WITNESSES_PER_CASE=8, CASES=(('synthetic_case', '2 mm'),),
                HALTED_ATTRIBUTE='_fusion_study_rule_surface_halted_documents',
                WITNESS_HALTED_ATTRIBUTE='_fusion_study_rule_surface_witness_halted_native_handles')
            exec(compiled, env)
            env['exercise_orchestration']()
            baseline = folder/'synthetic_case.f3d'
            check(scenario+' baseline exported before any consumers', baseline.is_file()
                and baseline.read_bytes() == b'Synthetic archive; consumers=0')
            check(scenario+' native equality was called', state['equality_calls'] > 0 or scenario == 'ambiguous_token')
            check(scenario+' concrete dispatch bypassed core Base equality', state['base_equality_calls'] == 0)
            check(scenario+' equality result never coerced to bool', state['equality_boolean_coercions'] == 0)
            aliases = getattr(fusion, env['WITNESS_HALTED_ATTRIBUTE'], [])
            if scenario == 'two_witness_success':
                check(scenario+' two actual AST witnesses completed', len(truth['samples'][0]['witnesses']) == 2
                    and not truth['errors'] and state['add_calls'] == 2)
                check(scenario+' each restoration saw no getter aliases', state['restoration_calls'] == 2
                    and all(e['live_kinds'] == ['Design', 'Timeline'] for e in state['events'] if e['event'] == 'restore'))
                check(scenario+' GC ran while before each restored node',
                    sum(e['event'] == 'gc' and e['before'] and not e['live_kinds'] for e in state['events']) == 2)
                check(scenario+' separate witness export and baseline hash exact',
                    (folder/'synthetic_case_witnesses.f3d').read_bytes() == b'Synthetic archive; consumers=2'
                    and truth['samples'][0]['pre_witness_archive_hash_unchanged'])
                check(scenario+' close only after all aliases released', state['close_calls'] == 1 and not aliases
                    and not live and (folder/'complete.txt').is_file())
            else:
                check(scenario+' failure retained without next witness/close', len(truth['errors']) == 1
                    and state['create_input_calls'] <= 1 and state['add_calls'] <= 1 and state['close_calls'] == 0)
                check(scenario+' stable native/document quarantine populated', bool(aliases)
                    and getattr(fusion, env['HALTED_ATTRIBUTE'], []) == state['documents'])
                check(scenario+' no witness archive or completion on failure',
                    not (folder/'synthetic_case_witnesses.f3d').exists()
                    and not (folder/'complete.txt').exists() and (folder/'halted.txt').is_file())
                check(scenario+' no automatic restore after rollback/getter failure',
                    state['restoration_calls'] == (1 if scenario == 'restoration_failure' else 0))
                if scenario in ('equality_not_implemented', 'equality_non_boolean'):
                    expected = ('Concrete SDK entity equality returned NotImplemented'
                        if scenario == 'equality_not_implemented'
                        else 'Concrete SDK entity equality did not return bool')
                    check(scenario+' explicit equality rejection before add without fallback',
                        state['create_input_calls'] == 1 and state['add_calls'] == 0
                        and truth['errors'][0]['error'] == expected)
            results.append(dict(scenario=scenario, passed=True,
                create_input_calls=state['create_input_calls'], add_calls=state['add_calls'],
                native_equality_calls=state['equality_calls'], restoration_calls=state['restoration_calls'],
                base_equality_calls=state['base_equality_calls'],
                equality_boolean_coercions=state['equality_boolean_coercions'],
                close_calls=state['close_calls'], actual_orchestration_errors=truth['errors'],
                quarantine_phases=[row['phase'] for row in aliases], events=state['events']))
        # These are synthetic objects only. Drop their test quarantine after the
        # scenario so no test-owned handles affect subsequent checks.
        aliases.clear()
        env.clear()
        gc.collect()
    return dict(status='Offline synthetic lifecycle checks passed; revised concrete-equality capture UNEXECUTED',
        source=SOURCE, source_sha256=hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest(),
        validator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Actual generator helper/orchestration AST executed against synthetic API handles and temporary fake archive bytes; no adsk import, Fusion API execution, offset acceptance, real native release behavior or native selection/VBL binding is proved',
        extracted_helpers=list(HELPERS), scenarios=results, checks=checks,
        validation=dict(scenarios=len(results), focused_checks=len(checks),
            successful_witnesses=2, failure_scenarios=len(SCENARIOS)-1, live_API_calls=0, main_reader_calls=0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='rule-fillet-surface-witness-lifecycle.json')
    args = parser.parse_args()
    report = validate()
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], sort_keys=True))


if __name__ == '__main__':
    main()
