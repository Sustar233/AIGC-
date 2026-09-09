import bpy,json,pathlib
s=bpy.context.scene;out=pathlib.Path(bpy.data.filepath).parent
manifest=json.loads((out/'shot_manifest.json').read_text(encoding='utf-8'))
folder=out/'核验帧';folder.mkdir(exist_ok=True)
s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
s.render.resolution_percentage=75
for f in sorted({f for shot in manifest['shots'] for f in shot['review_frames']}):
    s.frame_set(f);s.render.filepath=str(folder/f'frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
