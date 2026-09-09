import bpy, math, os, json
from mathutils import Vector, Matrix

s = bpy.context.scene
out = os.path.join(os.path.dirname(bpy.data.filepath), '冲锋预演')
os.makedirs(out, exist_ok=True)
fps, end = 24, 192
s.frame_start, s.frame_end, s.render.fps = 1, end, fps
s.render.resolution_x, s.render.resolution_y = 1280, 720
s.render.resolution_percentage = 100
for name, y in [('左侧机械蛛_整体移动',15.2),('右侧机械蛛_整体移动',15.8)]:
    obj = bpy.data.objects[name]
    obj.scale = (1.5,)*3
    obj.location.y = y

def smooth(t):
    t = max(0., min(1., t))
    return t*t*(3-2*t)

def motion(t):
    # Acceleration, constant speed, deceleration; continuous velocity.
    u = max(0.,min(1.,(t-.65)/6.25))
    a = .12
    if u < a: return u*u/(2*a*(1-a))
    if u > 1-a: return 1-(1-u)**2/(2*a*(1-a))
    return (u-a/2)/(1-a)

def key(o,f):
    o.keyframe_insert('location',frame=f)
    o.keyframe_insert('rotation_euler',frame=f)
    o.keyframe_insert('scale',frame=f)

def segment(o,a,b):
    v=b-a
    o.location=(a+b)/2
    o.rotation_euler=v.to_track_quat('Z','Y').to_euler()
    o.scale.z=v.length/o['rest_length']

def init_seg(o):
    o['rest_length'] = max(v.co.z for v in o.data.vertices)-min(v.co.z for v in o.data.vertices)

for prefix,rootname,start,finish in [
    ('A','人物A_持长剑_整体移动',(-1.05,-3.25,0),(-6.3,11.25,0)),
    ('B','人物B_双束发_整体移动',(1.62,-2.85,0),(6.65,11.85,0))]:
    root=bpy.data.objects[rootname]
    parts=list(root.children)
    original={o.name:(o.location.copy(),o.rotation_euler.copy(),o.scale.copy()) for o in parts}
    start,finish=Vector(start),Vector(finish)
    delta=finish-start
    distance=delta.length
    heading=-math.atan2(delta.x,delta.y)
    def obj(suffix): return bpy.data.objects[prefix+'_'+suffix]
    thigh0=.65 if prefix=='A' else .61
    shinz=.59 if prefix=='A' else .56
    hipheight=1.05 if prefix=='A' else .96
    shoulders={'左':Vector((-.49,.05,2.02)),'右':Vector((.23,.13,2.01))} if prefix=='A' else {'左':Vector((-.27,.1,1.78)),'右':Vector((.30,.12,1.78))}
    origlegs={
       '左':(Vector((-.27,0,1.03)),Vector((-.48,.16,.59)),Vector((-.68,-.22,.15))),
       '右':(Vector((.17,0,1.03)),Vector((.52,.17,.57)),Vector((.63,-.27,.14)))
    } if prefix=='A' else {
       '左':(Vector((-.21,0,.96)),Vector((-.51,.08,.55)),Vector((-.74,-.10,.12))),
       '右':(Vector((.20,0,.96)),Vector((.65,.06,.52)),Vector((.87,-.22,.12)))
    }
    origarms={
       '左':(Vector((-.66,.12,1.55)),Vector((-.32,.42,1.28))),
       '右':(Vector((.50,0,1.65)),Vector((.67,.10,1.30)))
    } if prefix=='A' else {
       '左':(Vector((-.44,.13,1.40)),Vector((-.14,.43,1.30))),
       '右':(Vector((.69,.16,1.87)),Vector((.65,.52,1.60)))
    }
    for side in ['左','右']:
        for limb in ['大腿','小腿','上臂', '护臂' if prefix=='A' else '前臂']:
            init_seg(obj(side+limb))
    weapons=[o for o in parts if any(w in o.name for w in ['剑柄','剑格','长剑白模','短兵器柄'])]
    limbparts=[o for o in parts if any(w in o.name for w in ['大腿','小腿','靴','膝','髋','上臂','护臂','前臂','手','肘','肩'])]
    upper=[o for o in parts if o not in weapons and o not in limbparts]
    for f in range(1,end+1):
        t=(f-1)/fps
        travel=motion(t)
        d=travel*distance
        run=smooth((t-.55)/.4)*(1-smooth((t-6.55)/.55))
        phase=d/2.0*math.tau
        bob=.055*(1-math.cos(2*phase))*run
        crouch=-.11*math.sin(math.pi*smooth(t/.65)) if t<.65 else 0
        root.location=start+delta*travel
        root.rotation_euler.z=heading*smooth(t/.85)
        key(root,f)
        pivot=Vector((0,0,hipheight))
        lean=Matrix.Rotation(-.17*run,3,'X')
        for o in upper:
            p,r,sc=original[o.name]
            o.location=pivot+lean@(p-pivot)+Vector((0,0,bob+crouch))
            o.rotation_euler=r.copy()
            o.rotation_euler.x-=.17*run
            if any(w in o.name for w in ['下摆','衣摆','挂件']): o.rotation_euler.x+=.12*math.sin(phase)*run
            key(o,f)
        for side,sign,offset in [('左',-1,0),('右',1,.5)]:
            hip,knee,ankle=origlegs[side]
            q=d/2.+offset
            frac=q%1
            if frac<.5:
                fy=.5-2*frac; fz=.13
            else:
                u=(frac-.5)*2
                fy=-.5+smooth(u)
                fz=.13+.40*math.sin(math.pi*u)
            h=Vector((sign*.23,0,hipheight+bob))
            foot=Vector((sign*.25,fy,fz))
            v=foot-h; mid=(h+foot)/2
            bend=Vector((0,1,0)); bend-=v.normalized()*bend.dot(v.normalized()); bend.normalize()
            k=mid+bend*math.sqrt(max(.02,((thigh0+shinz)/2)**2-v.length_squared/4))
            h=hip.lerp(h,run)+Vector((0,0,crouch))
            k=knee.lerp(k,run)+Vector((0,0,crouch*.4))
            foot=ankle.lerp(foot,run)
            segment(obj(side+'大腿'),h,k); key(obj(side+'大腿'),f)
            segment(obj(side+'小腿'),k,foot); key(obj(side+'小腿'),f)
            obj(side+'膝').location=k; key(obj(side+'膝'),f)
            boot=obj(side+'靴'); boot.location=foot+Vector((0,.11,-.02)); boot.rotation_euler.x=-.22*math.sin(phase+offset*math.tau)*run; key(boot,f)
            if prefix=='A': obj(side+'髋').location=h; key(obj(side+'髋'),f)
            sh=shoulders[side]+Vector((0,.06*run,bob+crouch))
            wave=math.sin(phase+offset*math.tau)
            elbow=sh+Vector((sign*.07,.27*wave,-.34))
            hand=elbow+Vector((0,.30,-.12+.08*wave))
            oldel,oldhand=origarms[side]
            elbow=oldel.lerp(elbow,run); hand=oldhand.lerp(hand,run)
            shoulder=obj(side+('肩甲' if prefix=='A' else '肩'))
            shoulder.location=sh; key(shoulder,f)
            segment(obj(side+'上臂'),sh,elbow); key(obj(side+'上臂'),f)
            fore=obj(side+('护臂' if prefix=='A' else '前臂'))
            segment(fore,elbow,hand); key(fore,f)
            obj(side+'肘').location=elbow; key(obj(side+'肘'),f)
            obj(side+'手').location=hand; key(obj(side+'手'),f)
            if side=='右':
                # Rigid weapon assembly follows the right hand throughout.
                rot=Matrix.Rotation(.50*run+.09*wave*run,3,'X')
                for w in weapons:
                    p,r,sc=original[w.name]
                    w.location=hand+rot@(p-oldhand)
                    w.rotation_euler=(rot@r.to_matrix()).to_euler()
                    key(w,f)

# Clear only the narrow running lanes of loose rubble, not structural columns.
for o in bpy.data.collections['04_碎石残骸'].objects:
    if not o.name.startswith('散落瓦砾'): continue
    p=o.location.copy()
    for st,en in [(Vector((-1.05,-3.25,0)),Vector((-6.3,11.25,0))),(Vector((1.62,-2.85,0)),Vector((6.65,11.85,0)))]:
        v=en-st; t=max(0,min(1,(p-st).dot(v)/v.length_squared))
        near=st+t*v
        if (Vector((p.x,p.y,0))-near).length<.9:
            o.location.x += -1.5 if p.x<0 else 1.5

cam=s.camera
for f in range(1,end+1):
    t=(f-1)/fps
    u=smooth((t-.3)/4.7)
    cam.location=(0,-8.2+2.2*u,2.2+3.2*u)
    target=Vector((0,13.0,1.65))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=28-3*u
    cam.keyframe_insert('location',frame=f); cam.keyframe_insert('rotation_euler',frame=f); cam.data.keyframe_insert('lens',frame=f)

s['预演动作']='8秒：准备→男女主分别冲向左右蜘蛛→减速停稳。无攻击接触。'
s['蜘蛛调整']='相对原白模放大至1.5倍，向仓库深处后移8米。'
s.render.engine='BLENDER_WORKBENCH'
sh=s.display.shading
sh.light='STUDIO'; sh.studiolight_rotate_z=.35
sh.color_type='MATERIAL'; sh.show_shadows=True; sh.show_cavity=True
sh.cavity_type='BOTH'; sh.curvature_ridge_factor=1.25; sh.curvature_valley_factor=1.1
sh.show_specular_highlight=False
sh.background_type='WORLD'; s.world.color=(.18,.18,.18)
s.display.render_aa='8'
s.render.image_settings.file_format='PNG'
s.render.filepath=out+'/frames/frame_'
os.makedirs(out+'/frames',exist_ok=True)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out+'/仓库对峙_双人冲锋预演.blend')
print(json.dumps({'saved':bpy.data.filepath,'frames':end,'fps':fps,'duration':end/fps,'objects':len(s.objects)},ensure_ascii=False))
