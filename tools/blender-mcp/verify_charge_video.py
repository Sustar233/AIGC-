import bpy, pathlib, json
out=pathlib.Path(__file__).resolve().parents[2]/'项目资料/outputs/白模/仓库对峙/冲锋预演'
video=out/'双人冲锋_白模预演.mp4'
s=bpy.context.scene
seq=s.sequence_editor_create()
strip=seq.strips.new_movie('MP4校验',str(video),channel=1,frame_start=1)
print('VIDEO_VERIFY',json.dumps({'bytes':video.stat().st_size,'frames':strip.frame_final_duration,'fps':strip.fps},ensure_ascii=False))
assert strip.frame_final_duration==192
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
s.render.use_sequencer=True
s.view_settings.view_transform='Standard'
for f in [1,72,168]:
    s.frame_set(f)
    s.render.filepath=str(out/f'视频核验_{f:04d}.png')
    bpy.ops.render.render(write_still=True)
