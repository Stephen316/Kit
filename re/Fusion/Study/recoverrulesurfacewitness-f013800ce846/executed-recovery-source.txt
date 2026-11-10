"""Bounded v2 prepared recovery for the exact pre-add 9dd46198ca8a witness failure.

No feature creation, cancellation, timeline movement, recompute, export, global
UI action or unrelated document access. Root reviews and dispatches explicitly.
"""
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import uuid

import adsk.core
import adsk.fusion

CAPTURE = 'rulefilletsurfaces-9dd46198ca8a'
SOURCE_SHA256 = '6acfc86ee89a9d811959db7218509dadc295b5f28f944e38a0587460da5eb305'
ARCHIVE_SHA256 = 'e4920ced5f952f99fe0bed8eda71ead47098afa4d26308fdd53dc3141f35fd52'
WITNESS = '_fusion_study_rule_surface_witness_halted_native_handles'
DOCUMENTS = '_fusion_study_rule_surface_halted_documents'
RECOVERY = '_fusion_study_rule_surface_recovery_halted_native_handles'
HANDLE_KEYS = frozenset(('design','root','offsets','source_face','source_body','entities','distance',
                        'inputs','input_entities','input_face','input_distance','parameter','previous',
                        'feature','looked_up_feature'))

V1_CAPTURE = 'recoverrulesurfacewitness-b0a35766ba60'
V1_SOURCE_SHA256 = '6d8b0963db1caa7ac2050152b1ebd27528ed82b40a5201b3964ae7216491272a'
V1_REPORT_SHA256 = 'df282bfea4fc22061c24ea77fb1ae8b77d7a83c45d5e56d18967969657bf0dc9'
INSPECTION = 'inspectrulewitnessquarantine-151086054fb5'
INSPECTION_SHA256 = '6ae9f013c5b410200aa4ca7d3ae173e4b179375514121065a8f19c10c07e8899'
OWNERSHIP_INSPECTION = 'inspectrulewitnessquarantine-2a852f50f1a0'
OWNERSHIP_INSPECTION_SHA256 = '0e76bb722ce8223726f24b9cf9ea1f36cb9931d7208abda6e58fc5f76743dc78'
RECOVERY_HANDLE_KEYS = frozenset(('design','root','offsets','resolved','input_faces',
                                'quarantine_rows','quarantine_entry','native_handles'))


def saved_evidence(root):
    folder = root / CAPTURE
    truth = json.loads((folder/'ground_truth.json').read_text())
    events = [json.loads(line) for line in (folder/'journal.jsonl').read_text().splitlines() if line]
    source = folder/'executed-generator-source.txt'
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256 or truth['executed_generator_sha256'] != SOURCE_SHA256:
        raise RuntimeError('Known executed generator snapshot differs; recovery refused')
    if len(truth['samples']) != 1 or len(truth['errors']) != 1:
        raise RuntimeError('Expected exactly one saved sample and one error')
    sample, error = truth['samples'][0], truth['errors'][0]
    if (sample['file'] != 'offsets_one_two.f3d' or sample['witnesses'] != []
            or sample['feature_health_state'] != 0 or sample['getter_errors']
            or error != dict(case='offsets_one_two',error_type='TypeError',
                error='NotImplemented should not be used in a boolean context',
                owned_document_retained=True,automatic_retry=False,
                pre_witness_archive_preserved=True,native_witness_handles_quarantined=True)):
        raise RuntimeError('Known pre-add sample/error differs; recovery refused')
    if (events[-2].get('phase') != 'creating_face_witness' or events[-2].get('witness_ordinal') != 0
            or events[-1].get('phase') != 'batch_halted' or events[-1].get('error_count') != 1
            or any(e['phase'] in ('witness_create_wrappers_released','witness_export_complete','owned_document_closed','batch_complete') for e in events)):
        raise RuntimeError('Known pre-add journal differs; recovery refused')
    archive = folder/sample['file']
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256 or sample['archive_sha256'] != ARCHIVE_SHA256:
        raise RuntimeError('Original pre-witness archive differs; recovery refused')
    requests = [f['entity_token'] for b in sample['result_bodies'] for f in b['faces']
                if f['temp_id'] in b['deep_face_temp_ids']]
    if len(requests) != 8 or not all(isinstance(t,str) and t for t in requests):
        raise RuntimeError('Known first source token request is unavailable')
    v1folder=root/V1_CAPTURE
    v1path=v1folder/'recovery.json'
    if (hashlib.sha256((v1folder/'executed-recovery-source.txt').read_bytes()).hexdigest()!=V1_SOURCE_SHA256
            or hashlib.sha256(v1path.read_bytes()).hexdigest()!=V1_REPORT_SHA256):
        raise RuntimeError('Known first recovery evidence differs')
    v1=json.loads(v1path.read_text())
    if (v1['status']!='HaltedRetained' or v1['release']!=dict(status='HaltedRetained',
            phase='release_known_handles',error_type='RuntimeError',error='Concrete native wrappers refer to different objects')
            or [e['phase'] for e in v1['events']]!=['saved_evidence_verified','recovery_halted']):
        raise RuntimeError('First recovery did not halt before release as expected')
    inspection_path=root/INSPECTION/'inspection.json'
    if hashlib.sha256(inspection_path.read_bytes()).hexdigest()!=INSPECTION_SHA256:
        raise RuntimeError('Known read-only equality inspection differs')
    inspection=json.loads(inspection_path.read_text());observed=inspection['inspection']
    comparisons={r['label']:r for r in observed['comparisons']}
    if (inspection['status']!='InspectionComplete' or observed['read_errors']
            or observed['counts']!=dict(witness=1,documents=1,recovery=1)
            or observed['fresh_offset_count']!=0 or observed['fresh_input_entity_count']!=1
            or any(r['result_kind']!='bool' or r['boolean_value'] is not (label!='fresh_vs_retained_OffsetFeatures')
                   for label,r in comparisons.items())):
        raise RuntimeError('Read-only inspection does not establish the expected collection-only inequality')
    ownership_path=root/OWNERSHIP_INSPECTION/'inspection.json'
    if hashlib.sha256(ownership_path.read_bytes()).hexdigest()!=OWNERSHIP_INSPECTION_SHA256:
        raise RuntimeError('Known read-only ownership inspection differs')
    ownership=json.loads(ownership_path.read_text());owned=ownership['inspection']
    owned_comparisons={r['label']:r for r in owned['comparisons']}
    required=('fresh_vs_retained_rootComponent','resolved_source_body_vs_retained_sourceBody',
              'resolved_source_body_component_vs_fresh_root')
    if (ownership['status']!='InspectionComplete' or owned['read_errors']
            or owned['counts']!=dict(witness=1,documents=1,recovery=1)
            or owned['fresh_offset_count']!=0 or owned['retained_offset_count']!=0
            or owned['fresh_input_entity_count']!=1
            or any(owned_comparisons[k]['result_kind']!='bool' or owned_comparisons[k]['boolean_value'] is not True for k in required)):
        raise RuntimeError('Known owned root/body/component corroboration is incomplete')
    return dict(capture=CAPTURE,executed_generator_sha256=SOURCE_SHA256,
        original_archive_sha256=ARCHIVE_SHA256,source_token=requests[0],
        journal_sha256=hashlib.sha256((folder/'journal.jsonl').read_bytes()).hexdigest(),
        truth_sha256=hashlib.sha256((folder/'ground_truth.json').read_bytes()).hexdigest(),
        observed_error=error,observed_final_journal=events[-1],
        previous_recovery_capture=V1_CAPTURE,previous_recovery_source_sha256=V1_SOURCE_SHA256,
        previous_recovery_report_sha256=V1_REPORT_SHA256,
        read_only_inspection=INSPECTION,read_only_inspection_sha256=INSPECTION_SHA256,
        ownership_inspection=OWNERSHIP_INSPECTION,ownership_inspection_sha256=OWNERSHIP_INSPECTION_SHA256,
        collection_equality_observation=comparisons['fresh_vs_retained_OffsetFeatures'],
        collection_equality_is_not_entity_identity=True)


def concrete_equal(left, right, cls):
    if not isinstance(left,cls) or not isinstance(right,cls) or not left.isValid or not right.isValid:
        raise RuntimeError('Required valid concrete native wrapper types differ')
    result = cls.__eq__(left,right)
    if type(result) is not bool:
        raise RuntimeError('Concrete native equality did not return a Boolean')
    if result is not True:
        raise RuntimeError('Concrete native wrappers refer to different objects')
    return result


def retain_failure(doc, phase, handles):
    rows = list(getattr(adsk.fusion,RECOVERY,[]))
    rows.append(dict(document=doc,phase=phase,native_handles=handles))
    setattr(adsk.fusion,RECOVERY,rows)


def release_known_handles(doc, evidence):
    """Validate the exact pre-add state, then release aliases while doc is open."""
    handles = entry = rows = outer = design = root = offsets = resolved = input_faces = None
    recovery_rows = recovery_entry = recovery_handles = source_body = source_component = None
    try:
        rows = getattr(adsk.fusion,WITNESS,None)
        outer = getattr(adsk.fusion,DOCUMENTS,None)
        recovery_rows=getattr(adsk.fusion,RECOVERY,None)
        if (not isinstance(rows,list) or len(rows)!=1 or not isinstance(outer,list) or len(outer)!=1
                or not isinstance(recovery_rows,list) or len(recovery_rows)!=1):
            raise RuntimeError('V2 requires exactly one known witness, document and first-recovery quarantine')
        entry=rows[0]
        if not isinstance(entry,dict) or set(entry)!= {'phase','document','native_handles'} or entry['phase']!='create_witness':
            raise RuntimeError('Only exact create_witness pre-add quarantine is recoverable')
        concrete_equal(doc,outer[0],adsk.core.Document)
        concrete_equal(doc,entry['document'],adsk.core.Document)
        handles=entry['native_handles']
        if not isinstance(handles,dict) or set(handles)!=HANDLE_KEYS:
            raise RuntimeError('Known quarantined handle layout differs')
        if any(handles[k] is not None for k in ('feature','looked_up_feature','parameter','previous')):
            raise RuntimeError('Witness may have been added or unrelated resolution retained; recovery refused')
        recovery_entry=recovery_rows[0]
        if (type(recovery_entry) is not dict or set(recovery_entry)!={'phase','document','native_handles'}
                or recovery_entry['phase']!='release_known_handles'):
            raise RuntimeError('First-recovery quarantine phase/schema differs')
        concrete_equal(doc,recovery_entry['document'],adsk.core.Document)
        recovery_handles=recovery_entry['native_handles']
        if (type(recovery_handles) is not dict or set(recovery_handles)!=RECOVERY_HANDLE_KEYS
                or recovery_handles['resolved'] is not None or recovery_handles['input_faces'] is not None
                or any(recovery_handles[k] is None for k in ('design','root','offsets'))):
            raise RuntimeError('First-recovery local checkpoint differs from known collection-equality failure')
        # Python identity proves aliases of the exact built-in containers only.
        # Native wrapper ownership is always checked by concrete native equality.
        if (recovery_handles['quarantine_rows'] is not rows
                or recovery_handles['quarantine_entry'] is not entry
                or recovery_handles['native_handles'] is not handles):
            raise RuntimeError('First recovery does not alias the exact original quarantine containers')
        design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        concrete_equal(design,handles['design'],adsk.fusion.Design)
        concrete_equal(design,recovery_handles['design'],adsk.fusion.Design)
        concrete_equal(doc,design.parentDocument,adsk.core.Document)
        root=design.rootComponent;offsets=root.features.offsetFeatures
        concrete_equal(root,handles['root'],adsk.fusion.Component)
        concrete_equal(root,recovery_handles['root'],adsk.fusion.Component)
        # OffsetFeatures collection wrappers compared False in the actual probe.
        # Counts/type are checked; their equality is never asserted as ownership.
        for collection in (offsets,handles['offsets'],recovery_handles['offsets']):
            if not isinstance(collection,adsk.fusion.OffsetFeatures) or not collection.isValid or collection.count!=0:
                raise RuntimeError('An expected valid empty OffsetFeatures collection changed')
        collection=None
        source_body=handles['source_face'].body
        concrete_equal(source_body,handles['source_body'],adsk.fusion.BRepBody)
        source_component=source_body.parentComponent
        concrete_equal(source_component,root,adsk.fusion.Component)
        concrete_equal(source_component.parentDesign,design,adsk.fusion.Design)
        if offsets.count!=0 or any(root.features.item(i).name.startswith('WitnessRuleSurface_') for i in range(root.features.count)):
            raise RuntimeError('An added witness feature is present; recovery refused')
        if handles['inputs'] is None or not isinstance(handles['inputs'],adsk.fusion.OffsetFeatureInput) or not handles['inputs'].isValid:
            raise RuntimeError('Expected unadded OffsetFeatureInput is unavailable')
        resolved=design.findEntityByToken(evidence['source_token'])
        if len(resolved)!=1:
            raise RuntimeError('Saved first source token does not resolve uniquely')
        source_equal=concrete_equal(resolved[0],handles['source_face'],adsk.fusion.BRepFace)
        input_faces=handles['inputs'].entities
        if input_faces.count!=1:
            raise RuntimeError('Known singleton OffsetFeatureInput changed')
        input_equal=concrete_equal(input_faces.item(0),handles['input_face'],adsk.fusion.BRepFace)
        concrete_equal(handles['input_face'],handles['source_face'],adsk.fusion.BRepFace)
        if (handles['inputs'].isChainSelection or handles['inputs'].operation!=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
                or float(handles['inputs'].distance.realValue)!=0.):
            raise RuntimeError('Known unadded zero-offset NewBody input controls differ')
        result=dict(status='KnownPreAddAliasesReleased',recovery_version=2,
            first_recovery_container_aliases_verified=True,owned_root_component_equality=True,
            source_body_and_component_ownership_verified=True,all_three_offset_collection_counts=0,
            offset_collection_equality_observation=evidence['collection_equality_observation'],
            offset_collection_equality_asserted_as_identity=False,concrete_Document_equality=True,
            concrete_Design_equality=True,concrete_source_face_equality=source_equal,
            concrete_input_face_equality=input_equal,offset_feature_count=0,witness_feature_is_None=True,
            source_input_equality_scope='Concrete BRepFace native equality; no token-string or temporary-ID identity test',
            cleared_handle_names=sorted(handles),document_open_during_release=True)
        # Clear the original stable containers, including their document aliases.
        # DOCUMENTS deliberately retains the owned document until close succeeds.
        handles.clear();recovery_handles.clear();entry.clear();recovery_entry.clear()
        rows.clear();recovery_rows.clear()
        setattr(adsk.fusion,WITNESS,[]);setattr(adsk.fusion,RECOVERY,[])
        return result
    except Exception as error:
        retain_failure(doc,'release_known_handles',dict(design=design,root=root,offsets=offsets,
            resolved=resolved,input_faces=input_faces,quarantine_rows=rows,quarantine_entry=entry,native_handles=handles,
            original_recovery_rows=recovery_rows,original_recovery_entry=recovery_entry,
            original_recovery_handles=recovery_handles,source_body=source_body,source_component=source_component))
        return dict(status='HaltedRetained',phase='release_known_handles',error_type=type(error).__name__,error=str(error))


def final_open_check(doc):
    """Fresh short frame after release/GC; no timeline/recompute/export mutation."""
    design=root=offsets=None
    try:
        if getattr(adsk.fusion,WITNESS,None) or getattr(adsk.fusion,RECOVERY,None):
            raise RuntimeError('Native handle quarantine remains; close refused')
        outer=getattr(adsk.fusion,DOCUMENTS,None)
        if not isinstance(outer,list) or len(outer)!=1:
            raise RuntimeError('Owned document quarantine changed; close refused')
        concrete_equal(doc,outer[0],adsk.core.Document)
        design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        concrete_equal(doc,design.parentDocument,adsk.core.Document)
        root=design.rootComponent;offsets=root.features.offsetFeatures
        if offsets.count!=0 or any(root.features.item(i).name.startswith('WitnessRuleSurface_') for i in range(root.features.count)):
            raise RuntimeError('Witness count changed after release; close refused')
        return dict(status='OpenDocumentChecked',document_valid=True,offset_feature_count=0,
                    recompute_called=False,export_called=False,timeline_mutated=False)
    except Exception as error:
        retain_failure(doc,'final_open_check',dict(design=design,root=root,offsets=offsets))
        return dict(status='HaltedRetained',phase='final_open_check',error_type=type(error).__name__,error=str(error))


def run(context):
    root=Path(__file__).resolve().parent
    output=root/('recoverrulesurfacewitness-'+uuid.uuid4().hex[:12]);output.mkdir()
    report=dict(status='Started',recovery_version=2,scope='One exact known pre-add owned witness quarantine; no feature/timeline mutation or unrelated document cleanup',
        executed_recovery_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),events=[])
    def journal(phase,**fields):
        report['events'].append(dict(phase=phase,time_utc=datetime.now(timezone.utc).isoformat(),**fields))
        (output/'recovery.json').write_text(json.dumps(report,indent=2)+'\n')
    doc=None
    try:
        report['saved_evidence']=saved_evidence(root)
        (output/'executed-recovery-source.txt').write_bytes(Path(__file__).read_bytes())
        journal('saved_evidence_verified')
        owned=getattr(adsk.fusion,DOCUMENTS,None)
        if not isinstance(owned,list) or len(owned)!=1:
            raise RuntimeError('Exactly one retained owned document required')
        doc=owned[0];owned=None
        report['release']=release_known_handles(doc,report['saved_evidence'])
        if report['release']['status']!='KnownPreAddAliasesReleased':
            report['status']='HaltedRetained';journal('recovery_halted');return
        journal('release_frame_returned_JSON')
        journal('release_frame_gc_document_open',collected=gc.collect())
        report['final_open_check']=final_open_check(doc)
        if report['final_open_check']['status']!='OpenDocumentChecked':
            report['status']='HaltedRetained';journal('recovery_halted');return
        journal('final_check_frame_returned_JSON')
        journal('final_check_frame_gc_document_open',collected=gc.collect())
        returned=doc.close(False)
        if returned is not True:
            raise RuntimeError('Owned close(False) did not return True; document remains retained')
        # The strong document quarantine is cleared only after successful close.
        setattr(adsk.fusion,DOCUMENTS,[]);doc=None
        report['status']='RecoveredClosed';journal('owned_close_returned',returned=True,save=False)
        (output/'complete.txt').write_text('RecoveredClosed; inspect recovery.json.\n')
    except Exception as error:
        if doc is not None:retain_failure(doc,'run',{})
        report['status']='HaltedRetained';report['error']=dict(error_type=type(error).__name__,error=str(error))
        journal('recovery_halted')
