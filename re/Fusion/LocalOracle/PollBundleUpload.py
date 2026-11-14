import builtins
import json
from pathlib import Path
import traceback

import adsk.core

root = Path(__file__).resolve().parent / 'Bundles'
state = builtins._kit_bundle_acceptance
report = state.report
try:
    future = state.future
    report['upload_state'] = int(future.uploadState)
    if future.uploadState == adsk.core.UploadStates.UploadFailed:
        raise RuntimeError('Native bundle upload failed')
    if future.uploadState == adsk.core.UploadStates.UploadFinished:
        state.data_file = future.dataFile
        if state.data_file is None:
            raise RuntimeError('Completed upload has no data file')
        report['stage'] = 'uploaded'
        report['data_file'] = {'name': state.data_file.name, 'extension': state.data_file.fileExtension, 'complete': state.data_file.isComplete}
        if state.data_file.isComplete:
            children = state.data_file.childReferences
            report['child_references'] = [{'name': children.item(i).name, 'extension': children.item(i).fileExtension, 'complete': children.item(i).isComplete} for i in range(children.count)]
            report['stage'] = 'cloud_processing_complete'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
    raise
finally:
    (root / 'UploadStatus.json').write_text(json.dumps(report, indent=2) + '\n')
