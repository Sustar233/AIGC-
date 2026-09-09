import bpy,pathlib
s=bpy.context.scene;out=pathlib.Path(bpy.data.filepath).parent
folder=out/'视频帧';folder.mkdir(exist_ok=True)
s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
s.render.resolution_percentage=100;s.render.filepath=str(folder/'frame_')
s.render.use_overwrite=False;s.render.use_placeholder=False
bpy.ops.render.render(animation=True)
