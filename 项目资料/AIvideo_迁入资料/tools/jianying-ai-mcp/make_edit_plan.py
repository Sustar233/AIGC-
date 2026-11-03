import json, math, hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[1]/"AIvideo-codex-"/"鹿城"
OUT=PROJECT/"剪辑成片"/"停车场85秒_v001";OUT.mkdir(parents=True,exist_ok=True)
items=json.loads((BASE/"work/media/index.json").read_text(encoding="utf-8"))
# 30fps edit-frame ranges; audio dialog kept complete, silence cuts at confirmed gaps.
groups=[
(5,18,50,"柱后警惕"),
(5,96,179,"离柱出画"),
(0,6,148,"走向车、开门放袋、田静小姐"),
(5,195,450,"敌意回望与二人走近介绍"),
(4,0,110,"我听说过你，易容仍被认出"),
(7,0,447,"社交账号与玩偶线索完整解释"),
(8,0,88,"油条内心吐槽"),
(8,102,450,"问来意、三千万、田静反讽"),
(9,0,191,"何出此言、合同赔款"),
(9,205,315,"三千万彩礼是假的"),
(12,0,365,"Q版解释骗局与十倍赔款"),
(12,377,442,"只能躲起来"),
(18,0,315,"真实目的与卖人吃瓜反应")]
cursor=0
for i,(n,st,en,label) in enumerate(groups):cursor+=en-st
# exactly 2550 frames / 85s, adjustment only on silent eating tail.
delta=cursor-2550
n,st,en,label=groups[-1];groups[-1]=(n,st,en-delta,label)
# Additional composition boundaries only where source already cuts, except selected reaction punch-in.
bounds={5:[71,252,369],0:[67,102],4:[95],7:[82,147,257,403],8:[101,162,242,323],9:[52,122],12:[54,224,246,318,380],18:[67,180,229]}
segments=[];audio=[];cursor=0
for gi,(n,st,en,label) in enumerate(groups):
 cuts=[st]+[x for x in bounds.get(n,[]) if st<x<en]+[en]
 for a,b in zip(cuts,cuts[1:]):
  z0=z1=1.;cx=cy=.5
  if n==5 and a<180:z0=z1=1.035
  elif n==5 and a>=369:z0=1.03;z1=1.10;cx=.48;cy=.47
  elif n==5 and 195<=a<252:z0=1.;z1=1.06;cx=.47
  elif n==4:z0=z1=1.04 if a<95 else 1.10
  elif n==7:
   if a<82:z0=1.02;z1=1.07
   elif a>=147 and a<257:z0=1.02;z1=1.07
   elif a>=257 and a<403:z0=1.05;z1=1.1;cx=.44
   elif a>=403:z0=z1=1.045
  elif n==8:
   if a<101:z0=z1=1.08;cx=.43
   elif a>=242:z0=1.04;z1=1.10;cx=.58
  elif n==9:
   if a<52:z0=z1=1.04
   elif a>=122 and a<191:z0=1.02;z1=1.07;cx=.52
  elif n==18:
   if a<67:z0=z1=1.04
   elif a<180:z0=1.0;z1=1.10
   elif a<229:z0=z1=1.065
   else:z0=1.04;z1=1.08;cx=.48
  segments.append(dict(index=len(segments),clip=n,source=items[n]["path"],source_start_frame=a,frames=b-a,start_frame=cursor+a-st,zoom_start=z0,zoom_end=z1,center_x=cx,center_y=cy,label=label))
 audio.append(dict(clip=n,source=str(BASE/f"work/media/clip_{n:02}.wav"),source_start_frame=st,frames=en-st,start_frame=cursor,label=label))
 cursor+=en-st
assert cursor==2550
plan={"name":"codex剪映测试_鹿城停车场85秒_v001","fps":30,"width":1920,"height":1080,"duration_frames":cursor,"video":segments,"audio":audio}
(OUT/"剪辑计划.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
(BASE/"work/output_path.txt").write_text(str(OUT),encoding="utf-8")
# Native draft references original videos; fit/fill conversion matches ffmpeg crop and zoom.
video=[]
for s in segments:
 info=items[s["clip"]]
 base=max(1., (info["duration"]*0+ 1470/630)/(16/9)) if s["clip"]==0 else 1.
 z0=s["zoom_start"]*base;z1=s["zoom_end"]*base
 # Use centered cropping for draft/render consistency.
 item={"source":s["source"],"start":s["start_frame"]*1000000//30,"duration":s["frames"]*1000000//30,
 "source_start":s["source_start_frame"]*1000000//30,"source_duration":s["frames"]*1000000//30,"volume":0,
 "clip":{"scale_x":z0,"scale_y":z0,"transform_x":(.5-s['center_x'])*2*(z0-1),"transform_y":(s['center_y']-.5)*2*(z0-1)}}
 if abs(z1-z0)>1e-5:
  last=(s["frames"]-1)*1000000//30
  item["keyframes"]=[{"property":"uniform_scale","time":0,"value":z0},{"property":"uniform_scale","time":last,"value":z1}]
  for prop,fac in [('position_x',(.5-s['center_x'])*2),('position_y',(s['center_y']-.5)*2)]:
   if fac: item["keyframes"] += [{"property":prop,"time":0,"value":fac*(z0-1)},{"property":prop,"time":last,"value":fac*(z1-1)}]
 video.append(item)
audio_segs=[]
for a in audio:
 audio_segs.append({"source":a["source"],"start":a["start_frame"]*1000000//30,"duration":a["frames"]*1000000//30,
 "source_start":a["source_start_frame"]*1000000//30,"source_duration":a["frames"]*1000000//30,"volume":1,
 "fade":{"in":"0.004s","out":"0.006s"}})
manifest={"draft":{"name":plan["name"],"width":1920,"height":1080,"fps":30},"tracks":[{"type":"video","name":"画面剪辑与运镜","segments":video},{"type":"audio","name":"对白与原场景声","segments":audio_segs}]}
(OUT/"剪映MCP清单.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
rows=["# 鹿城停车场｜85秒剪辑","", "状态：待验收。日期：2026-10-12。","", "MCP：本地 JianyingAIEditor，已成功握手并读取源工程。源工程素材库20段视频，时间线为空。", "", "目标：1920×1080、30fps、85秒；保留完整对白内容，缩短无对白间隔，以硬切、反应镜和轻微推近组织节奏。","", "| 成片时间 | 素材 | 内容 |","| --- | --- | --- |"]
for a in audio: rows.append(f"| {a['start_frame']/30:.2f}—{(a['start_frame']+a['frames'])/30:.2f}s | {items[a['clip']]['name']} | {a['label']} |")
rows+=["","人物和台词使用原视频及原声；语音识别用于核对定位，未用合成语音替换。纯白Q版只用于田静解释骗局，末尾保留卖人反应及吃瓜反差。","", "剪映原工程保留；新工程独立命名。原素材中的口型、道具、车门状态等生成连续性问题可能仍存在；适度取近景减少暴露，不声称已逐帧修复。","", "草稿使用原素材链接，移动原素材会导致离线。最终MP4由同一剪辑计划本地渲染，不依赖剪映界面导出。"]
(OUT/"剪辑说明.md").write_text("\n".join(rows),encoding="utf-8")
print(json.dumps({"duration":cursor/30,"video_segments":len(video),"audio_segments":len(audio),"output":str(OUT)},ensure_ascii=True))

