"""Derive empty references only for completely parsed observed Text literals.

Single-quote literal syntax is locally SDK documented and independently captured.
No Text concatenation, names, escape syntax, conditions or evaluation is added.
"""


def derive_text_literal_dependencies(parameters, parameter_tables):
    """Return derived/unresolved for Text parameters only; never mutate inputs."""
    by_id={}
    for p in parameters:
        by_id.setdefault(p['parameter_object_id'],[]).append(p)
    scopes={}
    for table in parameter_tables['decoded']:
        names={}
        valid=True
        for member in table['named_members']:
            candidates=by_id.get(member['parameter_object_id'],[])
            if (len(candidates)!=1 or candidates[0]['parameter_name']!=member['parameter_name']
                    or member['parameter_name'] in names):
                valid=False
                break
            names[member['parameter_name']]=candidates[0]
        if valid:
            for member in table['named_members']:
                scopes.setdefault(member['parameter_object_id'],[]).append(table)
    decoded,unresolved=[],[]
    for p in parameters:
        if p.get('value_type')!='Text':
            continue
        identity=p['parameter_object_id'];expressions=p.get('expression_candidates',[])
        try:
            if len(by_id.get(identity,[]))!=1 or len(scopes.get(identity,[]))!=1:
                raise ValueError('Unique reciprocal Text parameter-name collection unavailable')
            if len(expressions)!=1:
                raise ValueError('Expected one explicit stored Text expression')
            expression=expressions[0]
            if not 2<=len(expression)<=1024 or expression[:1]!="'" or expression[-1:]!="'":
                raise ValueError('Text expression is outside the observed complete single-quoted literal subset')
            literal=expression[1:-1]
            if "'" in literal or '\\' in literal or not all(c.isprintable() or c in '\r\n\t' for c in literal):
                raise ValueError('Text quote/escape/control syntax is outside the observed literal subset')
            if literal!=p.get('text_value') or p.get('display_units')!='Text':
                raise ValueError('Text literal spelling does not equal cached Text value')
            table=scopes[identity][0]
            decoded.append({'parameter_object_id':identity,'parameter_name':p['parameter_name'],
                'collection_object_id':table['collection_object_id'],'name_registry_object_id':table['name_registry_object_id'],
                'stored_expression':expression,'syntax_tree':{'kind':'TextLiteral','spelling':expression,'value':literal},
                'reference_occurrences':[],'referenced_parameter_object_ids':[],'referenced_parameter_names':[],
                'source':'Syntactically derived from a completely parsed SDK-documented Text literal, cached-value agreement and reciprocal owned name table; not a native dependency table'})
        except (ValueError,KeyError,IndexError) as error:
            unresolved.append({'parameter_object_id':identity,'parameter_name':p['parameter_name'],
                               'stored_expressions':expressions,'reason':str(error)})
    return {'derived':decoded,'unresolved':unresolved,
            'scope':'Observed complete single-quoted Text literals have no parameter references; multiline/Unicode literals retained',
            'limitations':['No Text expression evaluation, concatenation, references, conditions, quote escaping or general language grammar.',
                           'Numeric arithmetic dependencies remain with the existing reader.']}
