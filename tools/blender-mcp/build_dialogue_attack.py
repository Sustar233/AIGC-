import bpy, math, pathlib, json
from mathutils import Vector, Matrix, Quaternion

s=bpy.context.scene
base=pathlib.Path(bpy.data.filepath).parents[1]
out=base/'对白与火淬刀预演'
out.mkdir(exist_ok=True)
roots={p:bpy.data.objects[n] for p,n in [('A','人物A_持长剑_整体移动'),('B','人物B_双束发_整体移动')]}
parts={p:[r]+list(r.children) for p,r in roots.items()}
samples={p:[] for p in roots}
# Reuse the checked running poses from the previous editable animation.
for f in range(1,193):
    s.frame_set(f)
    for p,obs in parts.items():
        samples[p].append({o.name:(o.location.copy(),o.rotation_euler.copy(),o.scale.copy()) for o in obs})
s.frame_set(1)
for o in s.objects:
    if o.animation_data: o.animation_data_clear()
    if o.type=='CAMERA' and o.data.animation_data: o.data.animation_data_clear()
for n in ['A_剑柄','A_剑格','A_长剑白模','B_短兵器柄']:
    bpy.data.objects[n].hide_render=True
    bpy.data.objects[n].hide_set(True)
coll=bpy.data.collections.new('06_匕首与火淬刀动作资产');s.collection.children.link(coll)

def material(n,c):
    m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
white=material('新武器_白模',(.82,.82,.82))
dark=material('把手_深灰',(.22,.22,.22))
firemat=material('火淬_附着刀刃示意',(1,.20,.015))
blue=material('腥月蛛_蓝色识别',(.03,.28,.9))
red=material('腥日蛛_红色识别',(.9,.055,.025))
for prefix,mat in [('左侧机械蛛',blue),('右侧机械蛛',red)]:
    for o in s.objects:
        if o.name.startswith(prefix) and ('眼部' in o.name or '壳刺' in o.name):
            o.data.materials.clear();o.data.materials.append(mat)

def objmesh(n,verts,faces,par,mat):
    mesh=bpy.data.meshes.new(n);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(n,mesh);coll.objects.link(o);o.parent=par;o.data.materials.append(mat);return o
def empty(n,par):
    o=bpy.data.objects.new(n,None);coll.objects.link(o);o.parent=par;return o
def cube(n,pos,dim,par,mat):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=bpy.context.object;o.name=n;o.location=pos;o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    coll.objects.link(o);o.parent=par;o.data.materials.append(mat);return o

sword=empty('陈默_双手火淬刀控制',roots['A'])
cube('火淬刀_刀柄',(0,0,-.12),(.09,.09,.48),sword,dark)
cube('火淬刀_刀格',(0,0,.15),(.38,.12,.08),sword,white)
knob=empty('火淬刀_旋转把手',sword)
cube('把手_旋转段',(0,0,-.045),(.12,.12,.18),knob,white)
cube('把手_可视方向标',(0,.075,-.045),(.035,.05,.14),knob,dark)
verts=[(-.095,-.025,.19),(.095,-.025,.19),(.095,.025,.19),(-.095,.025,.19),(-.075,-.025,1.40),(.075,-.025,1.40),(.075,.025,1.40),(-.075,.025,1.40),(0,0,1.65)]
blade=objmesh('火淬刀_刀刃',verts,[(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(4,8,5),(5,8,6),(6,8,7),(7,8,4)],sword,white)
fire=[]
for i in range(8):
    z=.3+i*.155
    sign=1 if i%2 else -1
    o=objmesh('火淬_焰片'+str(i),[(sign*.065,0,z),(sign*.095,0,z+.20),(sign*.22,.035,z+.32),(sign*.16,-.025,z+.10)],[(0,1,2),(0,2,3)],sword,firemat)
    fire.append(o)
dagger=empty('月织_匕首控制',roots['B'])
cube('月织_匕首柄',(0,0,-.06),(.065,.07,.19),dagger,dark)
cube('月织_匕首护手',(0,0,.055),(.18,.085,.035),dagger,white)
objmesh('月织_匕首刀刃',[(-.06,-.016,.07),(.06,-.016,.07),(.06,.016,.07),(-.06,.016,.07),(0,0,.47)],[(0,1,2,3),(0,4,1),(1,4,2),(2,4,3),(3,4,0)],dagger,white)

def sm(v):
    v=max(0,min(1,v));return v*v*(3-2*v)
def key(o,f):
    for p in ['location','rotation_euler','scale']:o.keyframe_insert(p,frame=f)
def pose(o,data):
    o.location,o.rotation_euler,o.scale=data
def seg(o,a,b):
    if 'rest_length' not in o:o['rest_length']=max(v.co.z for v in o.data.vertices)-min(v.co.z for v in o.data.vertices)
    d=b-a;o.location=(a+b)/2;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.scale.z=d.length/o['rest_length']
def arm(p,side,hand,elbow,frame):
    sh=bpy.data.objects[p+'_'+side+('肩甲' if p=='A' else '肩')].location.copy()
    upper=bpy.data.objects[p+'_'+side+'上臂'];lower=bpy.data.objects[p+'_'+side+('护臂' if p=='A' else '前臂')]
    seg(upper,sh,elbow);seg(lower,elbow,hand)
    bpy.data.objects[p+'_'+side+'肘'].location=elbow
    bpy.data.objects[p+'_'+side+'手'].location=hand
    for o in [upper,lower,bpy.data.objects[p+'_'+side+'肘'],bpy.data.objects[p+'_'+side+'手']]:key(o,frame)

headparts={p:[o for o in parts[p] if any(x in o.name for x in ['头部','后脑','发型','发髻','束发','发顶']) and o!=roots[p]] for p in roots}
start={p:samples[p][0][roots[p].name][0] for p in roots}
oldend={p:samples[p][-1][roots[p].name][0] for p in roots}
ends={'A':Vector((-7.67284,12.0,0)),'B':Vector((6.65,11.85,0))}
reach=Vector((0,2.0,1.55))
allnew=[sword,knob,dagger]+fire
for f in range(1,505):
    t=(f-1)/24
    for p,launch,finish in [('A',12.15,18.15),('B',11.6,17.5)]:
        u=max(0,min(1,(t-launch)/(finish-launch)))
        source_t=.65+6.25*u if t>=launch else 0
        ix=max(0,min(191,round(source_t*24)))
        src=samples[p][ix]
        for o in parts[p]:pose(o,src[o.name])
        root=roots[p]
        progress=(root.location.y-start[p].y)/(oldend[p].y-start[p].y)
        root.location=start[p].lerp(ends[p],progress)
        yaw=-math.atan2(ends[p].x-start[p].x,ends[p].y-start[p].y)
        root.rotation_euler.z=yaw*sm((t-launch)/.5)
        if p=='A': root.rotation_euler.z*=1-sm((t-17.4)/.8)
        # Modest head turns for speech, and a readable nod before Yue Zhi starts.
        turn=(.16*math.sin(math.pi*t/2.5) if t<5 else 0) if p=='A' else 0
        nod=(.24*math.sin(math.pi*sm((t-11.05)/.42)) if 11.05<=t<=11.47 else 0) if p=='B' else 0
        for h in headparts[p]:
            h.rotation_euler.z+=turn;h.rotation_euler.x+=nod
            if nod:
                pivot=Vector((.02,.26,2.0));h.location=pivot+Matrix.Rotation(nod,3,'X')@(h.location-pivot)
        for o in parts[p]:key(o,f)

    # Yue Zhi visibly reaches to her waist, draws and retains a real short blade.
    bh=bpy.data.objects['B_右手'].location.copy()
    if t<5:
        bh=Vector((.65,.52,1.60))
    elif t<5.55:
        bh=Vector((.65,.52,1.60)).lerp(Vector((.34,.02,1.05)),sm((t-5)/.55))
    elif t<6.5:
        bh=Vector((.34,.02,1.05)).lerp(Vector((.5,.43,1.43)),sm((t-5.55)/.95))
    elif t<11.6:bh=Vector((.5,.43,1.43))
    if t<11.6:arm('B','右',bh,Vector((.48,.04,1.50)),f)
    dagger.location=bh
    direction=Vector((.14,.36,.92))
    dagger.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    dagger.scale=(1,1,1) if t>=5.55 else (.0001,)*3
    key(dagger,f)

    # One rigid sword and two attached hands. The right hand rotates the grip.
    grip=Vector((.67,.1,1.30));direction=Vector((.55,-.2,-.81)).normalized()
    ready=sm((t-8.05)/.95)
    grip=grip.lerp(Vector((.02,.36,1.48)),ready)
    direction=direction.lerp(Vector((0,.45,.893)),ready).normalized()
    if t>=12.15:
        grip=Vector((.05,.40,1.50+bpy.data.objects['A_胸背'].location.z-1.73))
        direction=Vector((0,.62,.785)).normalized()
    if 18<=t<18.6:
        u=sm((t-18)/.6)
        grip=grip.lerp(Vector((0,.15,2.25)),u)
        direction=direction.lerp(Vector((0,-.15,.989)),u).normalized()
    finaldir=Vector((0,.985,-.17)).normalized()
    finalgrip=reach-finaldir*1.65
    if t>=18.6:
        u=sm((t-18.6)/1.10)
        grip=Vector((0,.15,2.25)).lerp(finalgrip,u)
        q0=Vector((0,-.15,.989)).to_track_quat('Z','Y')
        q1=finaldir.to_track_quat('Z','Y')
        rot=q0.slerp(q1,u)
        direction=rot@Vector((0,0,1))
    sword.location=grip;sword.rotation_euler=direction.to_track_quat('Z','Y').to_euler();key(sword,f)
    twist=sm((t-16.25)/.75)*math.pi*.5
    knob.rotation_euler.z=twist;key(knob,f)
    rhand=grip
    lhand=grip-direction*.23
    elr=Vector((.43,.0,1.66)).lerp(Vector((.40,.02,2.08)),sm((grip.z-1.5)/.7))
    ell=Vector((-.37,.03,1.65)).lerp(Vector((-.35,.02,2.08)),sm((grip.z-1.5)/.7))
    arm('A','右',rhand,elr,f)
    oldleft=bpy.data.objects['A_左手'].location.copy()
    arm('A','左',oldleft.lerp(lhand,ready),Vector((-.66,.12,1.55)).lerp(ell,ready),f)
    rh=bpy.data.objects['A_右手'];rh.rotation_euler=(sword.rotation_euler.to_matrix()@Matrix.Rotation(twist,3,'Z')).to_euler();key(rh,f)
    for i,fl in enumerate(fire):
        amount=sm((t-17)/.3)
        fl.scale=(amount*(1+.13*math.sin(t*25+i)),amount,amount)
        key(fl,f)

def camera(name,position,target,lens):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o)
    o.location=position;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=200
    return o
c1=camera('S01_辨认双蛛',(0,-8.2,2.25),(0,12,1.8),28)
c2=camera('S02_月织取匕首',(3.65,-5.5,2.05),(1.8,-2.5,1.6),47)
c3=camera('S03_陈默双手持刀',(1.0,-5.8,2.1),(-1.0,-2.9,1.65),43)
c4=camera('S04_月织先起跑',(0,-7.8,2.6),(0,9,1.5),29)
c5=camera('S05_分向冲锋',(0,-7.8,3.5),(0,12,1.5),27)
c6=camera('S06_扭动刀柄',(0,0,0),(0,1,1),52)
c7=camera('S07_踏步下劈',(-3.8,9.5,3.0),(-7.6,13.4,2),32)
c8=camera('S08_头部落点',(-4.8,11.0,2.65),(-7.6,13.5,1.7),43)
for f in range(289,385):
    t=(f-1)/24;u=sm((t-12)/4)
    c5.location=(0,-7.8+5*u,3.5+1*u);c5.rotation_euler=(Vector((0,13,1.4))-c5.location).to_track_quat('-Z','Y').to_euler();key(c5,f)
for f in range(385,433):
    s.frame_set(f)
    h=roots['A'].matrix_world@sword.location
    c6.location=h+Vector((1.30,-1.65,.65));c6.rotation_euler=(h-c6.location).to_track_quat('-Z','Y').to_euler();key(c6,f)
for m in list(s.timeline_markers):s.timeline_markers.remove(m)
for f,c in [(1,c1),(121,c2),(193,c3),(265,c4),(289,c5),(385,c6),(433,c7),(481,c8)]:
    marker=s.timeline_markers.new(c.name,frame=f);marker.camera=c
s.camera=c1;s.frame_start=1;s.frame_end=504;s.render.fps=24
s.render.engine='BLENDER_WORKBENCH'
s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=False
s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG'
s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.ffmpeg.audio_codec='NONE'
s.render.filepath=str(out/'仓库对峙_对白与火淬刀_白模预演.mp4')
s['当前人物对应']='A=陈默；B=月织；左蓝=腥月蛛；右红=腥日蛛（台词原文猩日蛛）'
s['当前预演']='21秒8镜；月织先冲，陈默随后冲左，双手持刀扭柄启动火淬，刀刃到达头部，无伤势胜负。'
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'仓库对峙_对白与火淬刀.blend'))
print(json.dumps({'saved':bpy.data.filepath,'frames':504,'shots':len(s.timeline_markers)},ensure_ascii=False))
