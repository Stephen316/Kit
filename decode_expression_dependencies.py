"""Syntactically derive numeric arithmetic references from owned parameter names.

This is an explicit derived view, not a native dependency-table decoder or an
expression evaluator. Only the bounded arithmetic grammar is admitted; function,
Text, comparison and other syntax stays unresolved rather than losing references.
"""

import re


NUMBER = re.compile(r'(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')
NAME = re.compile(r'[A-Za-z_][A-Za-z_0-9]*')
UNITS = frozenset(('mm', 'cm', 'm', 'in', 'ft', 'deg', 'rad'))


class ArithmeticReferences:
    def __init__(self, expression, names):
        if not expression or len(expression) > 1024:
            raise ValueError('Empty or overlong stored expression')
        self.expression, self.names = expression, names
        self.tokens, self.occurrences = [], []
        position = 0
        while position < len(expression):
            if expression[position].isspace():
                position += 1
                continue
            start = position
            match = NUMBER.match(expression, position)
            if match:
                kind, value, position = 'number', match.group(), match.end()
            else:
                match = NAME.match(expression, position)
                if match:
                    kind, value, position = 'name', match.group(), match.end()
                elif expression[position] in '+-*/()':
                    kind, value, position = 'operator', expression[position], position+1
                else:
                    raise ValueError('Unsupported expression token at offset '+str(position))
            self.tokens.append((kind, value, start, position))
            if len(self.tokens) > 512:
                raise ValueError('Expression token limit exceeded')
        self.tokens.append(('end', '', len(expression), len(expression)))
        self.position = 0

    def current(self):
        return self.tokens[self.position]

    def binary(self, operators, child, depth):
        node = child(depth+1)
        while self.current()[1] in operators:
            operator = self.current()[1]
            self.position += 1
            right = child(depth+1)
            node = {'kind': 'Binary', 'operator': operator, 'left': node, 'right': right}
        return node

    def expression_node(self, depth=0):
        if depth > 64:
            raise ValueError('Expression nesting limit exceeded')
        return self.binary(('+', '-'), self.term, depth)

    def term(self, depth):
        return self.binary(('*', '/'), self.unary, depth)

    def unary(self, depth):
        if depth > 64:
            raise ValueError('Expression nesting limit exceeded')
        if self.current()[1] in ('+', '-'):
            operator = self.current()[1]
            self.position += 1
            return {'kind': 'Unary', 'operator': operator, 'operand': self.unary(depth+1)}
        return self.primary(depth+1)

    def primary(self, depth):
        if depth > 64:
            raise ValueError('Expression nesting limit exceeded')
        kind, text, start, end = self.current()
        self.position += 1
        if kind == 'number':
            unit = None
            if self.current()[0] == 'name' and self.current()[1] in UNITS:
                unit = self.current()[1]
                self.position += 1
            return {'kind': 'NumericLiteral', 'spelling': text, 'unit_spelling': unit}
        if kind == 'name':
            if self.current()[1] == '(':
                raise ValueError('Function syntax is outside the supported arithmetic subset')
            parameter = self.names.get(text)
            if parameter is None:
                raise ValueError('Name is not a unique parameter in the owned collection: '+text)
            if parameter.get('value_type') == 'Text':
                raise ValueError('Text parameter references are outside the numeric arithmetic subset')
            identity = parameter['parameter_object_id']
            self.occurrences.append({'parameter_object_id': identity, 'parameter_name': text,
                                     'expression_start': start, 'expression_end': end})
            return {'kind': 'ParameterReference', 'parameter_object_id': identity, 'parameter_name': text}
        if text == '(':
            node = self.expression_node(depth+1)
            if self.current()[1] != ')':
                raise ValueError('Missing closing expression parenthesis')
            self.position += 1
            return {'kind': 'Parenthesized', 'expression': node}
        raise ValueError('Expected numeric literal, parameter name or parenthesized expression at offset '+str(start))

    def parse(self):
        tree = self.expression_node()
        if self.current()[0] != 'end':
            raise ValueError('Unconsumed expression syntax at offset '+str(self.current()[2]))
        return tree


def derive_expression_dependencies(parameters, parameter_tables):
    by_id = {}
    for parameter in parameters:
        by_id.setdefault(parameter['parameter_object_id'], []).append(parameter)
    scopes = {}
    for table in parameter_tables['decoded']:
        names = {}
        for member in table['named_members']:
            candidates = by_id.get(member['parameter_object_id'], [])
            if (member['parameter_name'] in names or len(candidates) != 1
                    or candidates[0]['parameter_name'] != member['parameter_name']):
                names = None
                break
            names[member['parameter_name']] = candidates[0]
        if names is not None:
            for member in table['named_members']:
                scopes.setdefault(member['parameter_object_id'], []).append((table, names))
    decoded, unresolved = [], []
    for parameter in parameters:
        identity = parameter['parameter_object_id']
        expressions = parameter.get('expression_candidates', [])
        try:
            if parameter.get('value_type') == 'Text':
                raise ValueError('Text expression analysis is outside the numeric arithmetic subset')
            if len(expressions) != 1:
                raise ValueError('Expected one explicit stored expression')
            candidates = scopes.get(identity, [])
            if len(candidates) != 1:
                raise ValueError('Unique reciprocal parameter-name collection is unavailable')
            table, names = candidates[0]
            parser = ArithmeticReferences(expressions[0], names)
            tree = parser.parse()
            unique = list(dict.fromkeys(item['parameter_object_id'] for item in parser.occurrences))
            decoded.append({'parameter_object_id': identity, 'parameter_name': parameter['parameter_name'],
                            'collection_object_id': table['collection_object_id'],
                            'name_registry_object_id': table['name_registry_object_id'],
                            'stored_expression': expressions[0], 'syntax_tree': tree,
                            'reference_occurrences': parser.occurrences,
                            'referenced_parameter_object_ids': unique,
                            'referenced_parameter_names': [by_id[i][0]['parameter_name'] for i in unique],
                            'source': 'Syntactically derived from completely parsed stored arithmetic and reciprocal owned names; not an explicit native dependency table'})
        except (ValueError, KeyError, IndexError) as error:
            unresolved.append({'parameter_object_id': identity, 'parameter_name': parameter['parameter_name'],
                               'stored_expressions': expressions, 'reason': str(error)})
    return {'derived': decoded, 'unresolved': unresolved,
            'scope': 'Derived numeric arithmetic references only; + - * /, unary signs, parentheses and bounded numeric unit spellings',
            'limitations': ['No expression evaluation, dimensional validation, native dependency-edge interpretation or dependency ordering is implemented.',
                            'Functions, comparisons, Text, exponentiation, compound units and external/scoped names remain unresolved.']}
