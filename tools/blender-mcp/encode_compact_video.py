import bpy,pathlib,json
root=pathlib.Path(__file__).resolve().parents[2]
out=root/'项目资料/outputs/白模/仓库对峙/调度精简版'
frames=sorted((out/'视频帧').glob('frame_*.png'))
assert len(frames)==384, len(frames)
s=bpy.context.scene;s.render.fps=24;s.frame_start=1;s.frame_end=384
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
seq=s.sequence_editor_create()
strip=seq.strips.new_image('白模预演帧',str(frames[0]),channel=1,frame_start=1)
for f in frames[1:]:strip.elements.append(f.name)
strip.frame_final_duration=384
s.view_settings.view_transform='Standard'
s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG'
s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.ffmpeg.audio_codec='NONE'
s.render.filepath=str(out/'仓库对峙_16秒调度预演.mp4')
bpy.ops.render.render(animation=True)
print('ENCODED',s.render.filepath)
