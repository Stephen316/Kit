"""Compare derived unary-function references with captured dependency getters."""

import argparse
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_parameters import decode_file
from decode_expression_dependencies import ArithmeticReferences


def validate(root, zstd_library):
    captures = [('parameterfunctions-bc10224394fe', None),
                ('parameterexpressions-3ddbef2b20bd',
                 {'function_outside_subset.f3d', 'product_sum.f3d', 'text_name_literal.f3d'})]
    report = {'scope': 'Derived references only; no native dependency graph or expression evaluation',
              'samples': [], 'negative_checks': []}
    names = None
    for folder, selected in captures:
        truth = json.loads((root/folder/'ground_truth.json').read_text())
        assert (root/folder/'complete.txt').exists() and not truth['errors']
        for sample in truth['samples']:
            if selected is not None and sample['file'] not in selected:
                continue
            path = root/folder/sample['file']
            main = decode_basics(path, zstd_library)['streams'][0]
            derived = main['derived_expression_dependencies']
            parameter_only = decode_file(path, zstd_library)['streams'][0]
            assert parameter_only['derived_expression_dependencies'] == derived
            numeric = {p['parameter_name']: p for p in derived['derived']}
            unresolved = {p['parameter_name']: p for p in derived['unresolved']}
            checks = []
            for actual in sample['parameters']:
                if actual['unit'].lower() == 'text':
                    assert actual['name'] in unresolved
                    continue
                parsed = numeric[actual['name']]
                assert set(parsed['referenced_parameter_names']) == set(actual['dependency_names'])
                assert parsed['stored_expression'] == actual['expression']
                checks.append({'name': actual['name'], 'reference_names_match_api': True,
                               'stored_expression_matches_api': True})
            report['samples'].append({'file': str(path.relative_to(root)), 'checks': checks,
                                      'derived': derived['derived'], 'unresolved': derived['unresolved'],
                                      'both_entrypoints_equal': True})
            if names is None:
                parameters = main['unbound_parameters']
                names = {p['parameter_name']: p for p in parameters}
    for label, expression in (
        ('Unknown function', 'sin(probeScale)'),
        ('Extra function argument', 'abs(probeScale, probeWidth)'),
        ('Missing function argument', 'sqrt()'),
        ('Trailing syntax', 'sqrt(probeScale) probeWidth'),
        ('Excessive call nesting', 'sqrt('*70+'probeScale'+')'*70),
    ):
        try:
            ArithmeticReferences(expression, names).parse()
        except (ValueError, IndexError) as error:
            report['negative_checks'].append({'check': label, 'passed': True, 'reason': str(error)})
        else:
            raise AssertionError(label)
    report['summary'] = {'new_archives': 4, 'prior_archives': 3,
                         'api_parameter_checks': sum(len(s['checks']) for s in report['samples']),
                         'unresolved_text_expressions': sum(len(s['unresolved']) for s in report['samples']),
                         'negative_checks': len(report['negative_checks']), 'all_passed': True}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    report = validate(root, args.zstd_library)
    (root/'parameter-function-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary']))
