import json,subprocess,io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
BASE=Path(__file__).resolve().parent; OUT=BASE/"work"/"media";OUT.mkdir(exist_ok=True)
inventory=json.loads((BASE/"work/source_inventory.json").read_text(encoding="utf-8"))
clips=inventory["draft_meta_info.json"]["draft_materials"][0]["value"]
ff=imageio_ffmpeg.get_ffmpeg_exe()
font=ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",16)
def process(item):
 name=item["extra_info"];src=Path(item["file_Path"]);idx=clips.index(item)
 length=item["duration"]/1000000
 times=[round(min(length-.25,x),2) for x in [.4,length*.25,length*.5,length*.75,length-.4]]
 frames=[]
 for t in times:
  p=subprocess.run([ff,"-v","error","-ss",str(t),"-i",str(src),"-frames:v","1","-vf","scale=384:216:force_original_aspect_ratio=decrease,pad=384:216:(ow-iw)/2:(oh-ih)/2","-f","image2pipe","-vcodec","png","-"],capture_output=True,creationflags=0x08000000)
  if p.returncode==0:
   im=Image.open(io.BytesIO(p.stdout)).convert("RGB");frames.append((t,im))
 sheet=Image.new("RGB",(384*5,250),"#eeeeee");d=ImageDraw.Draw(sheet)
 for j,(t,im) in enumerate(frames):sheet.paste(im,(j*384,30));d.text((j*384+4,5),f"{idx:02} {name} | {t:.2f}s",font=font,fill="black")
 path=OUT/f"clip_{idx:02}.jpg";sheet.save(path,quality=88)
 subprocess.run([ff,"-v","error","-i",str(src),"-vn","-ac","1","-ar","16000","-y",str(OUT/f"clip_{idx:02}.wav")],capture_output=True,creationflags=0x08000000)
 print(json.dumps({"index":idx,"name":name,"duration":length,"sheet":str(path)},ensure_ascii=True),flush=True)
 return {"index":idx,"name":name,"path":str(src),"duration":length,"sheet":str(path),"times":times}
with ThreadPoolExecutor(max_workers=4) as pool: result=list(pool.map(process,clips))
(OUT/"index.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")

