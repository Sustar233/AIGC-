import json,subprocess,io
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from pymediainfo import MediaInfo
import imageio_ffmpeg
BASE=Path(__file__).resolve().parent;OUT=Path((BASE/"work/output_path.txt").read_text(encoding="utf-8"));path=OUT/"鹿城_停车场_85秒_v001.mp4";ff=imageio_ffmpeg.get_ffmpeg_exe()
media=MediaInfo.parse(str(path)).to_data()
(OUT/"成片媒体信息.json").write_text(json.dumps(media,ensure_ascii=False,indent=2),encoding="utf-8")
for t in media["tracks"]:
 if t.get("track_type") in ["General","Video","Audio"]:print(json.dumps({k:t.get(k) for k in ["track_type","duration","width","height","frame_rate","frame_count","format","channel_s","sampling_rate"]},ensure_ascii=True))
times=[.5,2.5,4.5,7.5,9.5,12,15,18,21,26,30,35,37,41,46,52,56,59,63,68,72,75.5,79,82.5,84.5]
font=ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",18);sheet=Image.new("RGB",(1600,1030),"#f0f0f0");d=ImageDraw.Draw(sheet)
for j,t in enumerate(times):
 r=subprocess.run([ff,"-v","error","-ss",str(t),"-i",str(path),"-frames:v","1","-vf","scale=320:180","-f","image2pipe","-vcodec","png","-"],capture_output=True,creationflags=0x08000000)
 im=Image.open(io.BytesIO(r.stdout));x=j%5*320;y=j//5*206;sheet.paste(im,(x,y+26));d.text((x+4,y),f"{t:.1f}s",fill="black",font=font)
sheet.save(OUT/"成片检查图.jpg",quality=90)
r=subprocess.run([ff,"-v","error","-i",str(path),"-f","null","-"],capture_output=True,encoding="utf-8",errors="replace",creationflags=0x08000000)
print("DECODE_CHECK",r.returncode,r.stderr[:500])
r=subprocess.run([ff,"-hide_banner","-i",str(path),"-af","ebur128=peak=true","-vn","-f","null","-"],capture_output=True,encoding="utf-8",errors="replace",creationflags=0x08000000)
(OUT/"音量检查.txt").write_text(r.stderr[-1200:],encoding="utf-8")
print(r.stderr[-500:])

