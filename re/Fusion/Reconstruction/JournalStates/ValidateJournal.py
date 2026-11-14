import math


def validate_journal(model):
    stream=model['stream'];states=model['states'];entities=model['entities'];active=model['activeCount']
    for key in ('currentStateId','maxStateId','maxStatesToKeep','nextEntityTag'):
        if type(stream[key]) is not int or not 0<=stream[key]<1<<31:raise ValueError('Invalid stream integer')
    if stream['currentStateId']>stream['maxStateId']:raise ValueError('Invalid maximum state')
    if stream['maxStatesToKeep']!=0 or stream['workingNode']!=-1 or stream['ownerEntity']!=-1:raise ValueError('Unsupported history stream variant')
    if not 1<=active<=len(entities)<=100000 or not 2<=len(states)<=10000:raise ValueError('Invalid history bounds')
    if entities[0]['kind']!='asmheader':raise ValueError('Missing ASM header entity')
    if len({state['stateId'] for state in states})!=len(states):raise ValueError('Duplicate state identity')
    heads=[index for index,state in enumerate(states) if state['previousNode']==-1]
    if heads!=[stream['activeNode']]:raise ValueError('Inconsistent active state')
    current=heads[0]
    if states[current]['stateId']!=stream['currentStateId']:raise ValueError('Current state mismatch')
    versions={index:index for index in range(active)};seen=set();old_ids=set();aliases={}
    for state in states:
        for board in state['boards']:
            for change in board['changes']:
                old,new=change['old'],change['new']
                if old>=0:
                    if not active<=old<len(entities) or old in old_ids:raise ValueError('Invalid archived entity reference')
                    old_ids.add(old)
                if new<-1 or new>=len(entities) or old<-1 or old==new:raise ValueError('Invalid bulletin')
                if old>=0 and new>=0:aliases[old]=new
    if old_ids!=set(range(active,len(entities))):raise ValueError('Unreferenced archived geometry')
    def resolve(value):
        visited=set()
        while value in aliases:
            if value in visited:raise ValueError('Cyclic revision aliases')
            visited.add(value);value=aliases[value]
        return value
    while current!=-1:
        if current in seen or not 0<=current<len(states):raise ValueError('Cyclic or invalid state chain')
        seen.add(current);state=states[current]
        if not 0<=state['stateId']<=stream['maxStateId']:raise ValueError('Invalid state ID')
        if (state['backward'],state['hidden'],state['partnerNode'],state['mergedWithNode'],state['ownerStream'])!=(1,0,current,-1,0) or state['name'] is not None or state['stateList48']:raise ValueError('Unsupported branching/merged/named state profile')
        validate_live(entities,versions,resolve)
        for board in state['boards']:
            if board['ownerNode']!=current or board['status']!=2:raise ValueError('Unsupported bulletin board profile')
            for change in board['changes']:
                old,new=change['old'],change['new']
                if old==-1:
                    if new not in versions:raise ValueError('Absent insertion target')
                    del versions[new]
                elif new==-1:
                    if old in versions:raise ValueError('Live deletion target')
                    versions[old]=old
                else:
                    if new not in versions:raise ValueError('Absent replacement target')
                    versions[new]=old
        following=state['nextNode']
        if following!=-1 and (not 0<=following<len(states) or states[following]['previousNode']!=current):raise ValueError('Broken reciprocal state link')
        if following==-1 and current!=stream['initialNode']:raise ValueError('Wrong initial state')
        current=following
    if len(seen)!=len(states) or versions!={0:0}:raise ValueError('Incomplete state chain')


def validate_live(entities,versions,resolve):
    common={'attribute':('ATTRIB_CUSTOM-attrib',),'reservedRef':()}
    mapping={
        'asmheader':{'attribute':('ATTRIB_CUSTOM-attrib',)},
        'body':{'firstLump':('lump',),'firstWire':(),'transform':()},
        'lump':{'nextLump':('lump',),'firstShell':('shell',),'ownerBody':('body',)},
        'shell':{'nextShell':('shell',),'firstSubshell':(),'firstFace':('face',),'wire':(),'ownerLump':('lump',)},
        'face':{'nextFace':('face',),'firstLoop':('loop',),'ownerShell':('shell',),'reservedFaceRef':(),'surface':('plane-surface','cone-surface')},
        'loop':{'nextLoop':('loop',),'firstCoedge':('coedge',),'ownerFace':('face',)},
        'coedge':{'nextCoedge':('coedge',),'previousCoedge':('coedge',),'partnerCoedge':('coedge',),'edge':('edge',),'ownerLoop':('loop',),'pcurve':()},
        'edge':{'startVertex':('vertex',),'endVertex':('vertex',),'ownerCoedge':('coedge',),'curve':('ellipse-curve',)},
        'vertex':{'ownerEdge':('edge',),'point':('point',)},
        'ATTRIB_CUSTOM-attrib':{'reserved':(),'next':('ATTRIB_CUSTOM-attrib',),'previous':('ATTRIB_CUSTOM-attrib',),'owner':('body','face','edge','coedge')},
    }
    for slot,revision in versions.items():
        record=entities[revision];fields=record['fields'];kind=record['kind']
        refs=dict(mapping.get(kind,{}))
        if kind not in ('asmheader','ATTRIB_CUSTOM-attrib'):refs.update(common)
        for key,allowed in refs.items():
            value=fields[key]
            if type(value) is not int or value<-1:raise ValueError('Invalid semantic entity reference')
            if value==-1:continue
            target=resolve(value)
            if target not in versions or entities[versions[target]]['kind'] not in allowed:raise ValueError(f'Invalid live {kind}.{key} reference at slot {slot}')
        if kind=='ATTRIB_CUSTOM-attrib' and fields['family']=='generic_tag_attrib_def':
            for group in fields['groups']:
                for value in (group['secondaryId'],group['approachId'],*group['operationIds']):
                    if type(value) is not int or not -(1<<31)<=value<1<<31:raise ValueError('Invalid generic-tag native integer')
        if kind=='cone-surface' and not math.isclose(fields['sineAngle']**2+fields['cosineAngle']**2,1.0,abs_tol=1e-12):raise ValueError('Invalid cone angle')
