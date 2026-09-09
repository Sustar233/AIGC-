import bpy,pathlib
s=bpy.context.scene
out=pathlib.Path(bpy.data.filepath).parent/'关键帧'
out.mkdir(exist_ok=True)
s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
for f in [48,145,230,280,360,408,446,472,494]:
    s.frame_set(f);s.render.filepath=str(out/f'镜头核验_{f:04d}.png')
    bpy.ops.render.render(write_still=True)
