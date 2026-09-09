import bpy, pathlib, json, math
from mathutils import Vector
s=bpy.context.scene
out=pathlib.Path(bpy.data.filepath).parents[1]/'调度精简版'
out.mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'仓库对峙_调度精简版.blend'))
try:bpy.ops.ed.undo_push(message='Deepwhite compact staging version')
except RuntimeError:pass
s.name='仓库对峙_16秒调度精简版'
segments=[(0,4,0,5),(4,7,5,8),(7,9,8,11),(9,13,11,16),(13,14,16,18),(14,16,18,20)]
def source_time(t):
    for lo,hi,a,b in segments:
        if t<=hi:return a+(b-a)*(t-lo)/(hi-lo)
    return 20
animated=[o for o in s.objects if o.type!='CAMERA' and o.animation_data and o.animation_data.action]
snapshots=[]
for f in range(1,385):
    sf=1+24*source_time((f-1)/24)
    s.frame_set(math.floor(sf),subframe=sf%1)
    snapshots.append([(o.location.copy(),o.rotation_euler.copy(),o.scale.copy()) for o in animated])
for o in animated:o.animation_data_clear()
for f,poses in enumerate(snapshots,1):
    for o,(loc,rot,scale) in zip(animated,poses):
        o.location=loc;o.rotation_euler=rot;o.scale=scale
        for prop in ['location','rotation_euler','scale']:o.keyframe_insert(prop,frame=f)
rigs=bpy.data.collections.new('07_精简版摄影机与注视目标');s.collection.children.link(rigs)
def cam(n,pos,target,lens):
    root=bpy.data.objects.new(n+'_移动控制',None);rigs.objects.link(root);root.location=pos
    aim=bpy.data.objects.new(n+'_注视目标',None);rigs.objects.link(aim);aim.location=target;aim.empty_display_type='SPHERE';aim.empty_display_size=.12
    data=bpy.data.cameras.new(n);ob=bpy.data.objects.new(n,data);rigs.objects.link(ob);ob.parent=root;data.lens=lens
    c=ob.constraints.new('TRACK_TO');c.target=aim;c.track_axis='TRACK_NEGATIVE_Z';c.up_axis='UP_Y'
    data.clip_start=.05;data.clip_end=200
    return ob,root,aim
c1=cam('C01_识敌全景',(0,-8.2,2.25),(0,12,1.8),28)
c2=cam('C02_月织取刀',(4.8,-1.4,2.2),(1.85,-2.55,1.65),43)
c3=cam('C03_双手持刀',(1.7,-1.6,2.25),(-1.03,-2.92,1.6),38)
c4=cam('C04_先后分向冲锋',(0,-8,3.3),(0,11,1.3),26)
c5=cam('C05_扭柄启动',(0,0,0),(0,1,1),43)
c6=cam('C06_头部下劈',(-1.4,11.4,3.3),(-7.6,13.1,1.85),32)
for f in range(217,313):
    t=(f-217)/95;u=t*t*(3-2*t)
    c4[1].location=(0,-8+7.0*u,3.3+1.2*u)
    c4[2].location=(0,11+2*u,1.3)
    c4[1].keyframe_insert('location',frame=f);c4[2].keyframe_insert('location',frame=f)
for f in range(313,337):
    s.frame_set(f)
    h=bpy.data.objects['陈默_双手火淬刀控制'].matrix_world.translation.copy()
    c5[1].location=h+Vector((1.60,.95,.48));c5[2].location=h+Vector((0,0,.04))
    c5[1].keyframe_insert('location',frame=f);c5[2].keyframe_insert('location',frame=f)
for mark in list(s.timeline_markers):s.timeline_markers.remove(mark)
shots=[('C01',1,96,c1,'辨认左右目标',28,'固定'),('C02',97,168,c2,'月织取刀并回应',43,'固定'),('C03',169,216,c3,'双手持刀作决定',38,'固定'),('C04',217,312,c4,'月织先冲、陈默随后分向',26,'后方前推'),('C05',313,336,c5,'扭柄后启动火淬',43,'同侧跟移'),('C06',337,384,c6,'进入刀长并向头部下劈',32,'固定')]
manifest=[]
review=[]
for n,start,end,rig,purpose,lens,move in shots:
    m=s.timeline_markers.new(n+'_'+purpose,frame=start);m.camera=rig[0]
    frames=sorted(set([start,min(start+6,end),(start+end)//2,end]))
    if n=='C04':frames+= [228,240]
    if n=='C05':frames += [325,332]
    if n=='C06':frames += [351,365,377]
    frames=sorted(set(frames));review+=frames
    manifest.append(dict(name=n,start=start,end=end,purpose=purpose,lens_mm=lens,camera_move=move,camera=rig[0].name,target=rig[2].name,review_frames=frames))
for o in rigs.objects:
    if o.animation_data and o.animation_data.action:
        action=o.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for k in fc.keyframe_points:k.interpolation='LINEAR'
s.camera=c1[0];s.frame_start=1;s.frame_end=384;s.render.fps=24
s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=False
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG'
s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.ffmpeg.audio_codec='NONE'
s.render.filepath=str(out/'仓库对峙_16秒调度预演.mp4')
s['预演说明']='16秒6镜，原台词保留，月织先冲、陈默分向左蓝蛛、扭柄后火淬下劈。无声白模，外置对白字幕。'
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
(out/'shot_manifest.json').write_text(json.dumps({'fps':24,'frames':384,'duration_seconds':16,'shots':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'saved':bpy.data.filepath,'shots':6,'duration':16,'review_frames':review},ensure_ascii=False))
