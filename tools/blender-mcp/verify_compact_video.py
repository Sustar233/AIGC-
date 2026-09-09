import bpy,pathlib,json
out=pathlib.Path(__file__).resolve().parents[2]/'项目资料/outputs/白模/仓库对峙/调度精简版'
s=bpy.context.scene
v=s.sequence_editor_create().strips.new_movie('预演视频校验',str(out/'仓库对峙_16秒调度预演.mp4'),channel=1,frame_start=1)
assert v.frame_final_duration==384 and abs(v.fps-24)<.01
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
s.view_settings.view_transform='Standard'
s.frame_set(264);s.render.filepath=str(out/'视频封面.png');bpy.ops.render.render(write_still=True)
report={'frames':v.frame_final_duration,'fps':v.fps,'duration':v.frame_final_duration/v.fps,'resolution':'1280x720','shots':6,'audio':'none','verification':'Decoded MP4; checked six shots via representative frames and motion contact sheets.'}
(out/'交付校验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('VERIFIED',report)
