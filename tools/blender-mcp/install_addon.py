import bpy
import pathlib
import shutil

root = pathlib.Path(__file__).resolve().parent
source = root / '.venv/Lib/site-packages/blender_mcp/bundled/addon.py'
destination = pathlib.Path(bpy.utils.user_resource('SCRIPTS', path='addons', create=True)) / 'blender_mcp.py'
if destination.exists():
    shutil.copy2(destination, destination.with_suffix('.py.bak'))
code = source.read_text(encoding='utf-8')
# Local-only deployment: do not opt this user into prompt/screenshot collection.
code = code.replace('default=True,\n        update=_on_telemetry_consent_changed', 'default=False,\n        update=_on_telemetry_consent_changed')
destination.write_text(code, encoding='utf-8')
bpy.utils.refresh_script_paths()
bpy.ops.preferences.addon_enable(module='blender_mcp')
bpy.context.preferences.addons['blender_mcp'].preferences.telemetry_consent = False
bpy.ops.wm.save_userpref()
print('INSTALLED_ADDON', destination)
