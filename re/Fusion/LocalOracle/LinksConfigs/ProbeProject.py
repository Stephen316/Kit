import sys
from pathlib import Path
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
import adsk.fusion
from LinkCommon import acceptance_folder, private, write

app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'offline': app.isOffLine, 'documents_before': app.documents.count}
try:
    project, folder = acceptance_folder(app, create=True)
    report['project_name'] = project.name
    report['folder_name'] = folder.name
    report['folder_files'] = [folder.dataFiles.item(i).name for i in range(folder.dataFiles.count)]
    report['folder_children'] = [folder.dataFolders.item(i).name for i in range(folder.dataFolders.count)]
    report['configuration_api'] = {name: hasattr(adsk.fusion.Design, name) for name in ('createConfiguredDesign', 'configurationTopTable', 'configurationRulesManager')}
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
    raise
finally:
    report['documents_after'] = app.documents.count
    write(private / 'ProbeProject.json', report)
