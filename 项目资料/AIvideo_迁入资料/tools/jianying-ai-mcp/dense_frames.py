import subprocess,io,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
BASE=Path(__file__).resolve().parent;OUT=BASE/"work/media";idx=json.loads((OUT/"index.json").read_text(encoding="utf-8"));ff=imageio_ffmpeg.get_ffmpeg_exe();font=ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",18)
for n in [0,5,12,17,18]:
 ts=[float(t) for t in range(int(idx[n]["duration"]))];sheet=Image.new("RGB",(320*5,206*3),"white");d=ImageDraw.Draw(sheet)
 for j,t in enumerate(ts):
  p=subprocess.run([ff,"-v","error","-ss",str(t),"-i",idx[n]["path"],"-frames:v","1","-vf","scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2","-f","image2pipe","-vcodec","png","-"],capture_output=True,creationflags=0x08000000)
  im=Image.open(io.BytesIO(p.stdout));x=(j%5)*320;y=(j//5)*206;sheet.paste(im,(x,y+26));d.text((x+4,y),f"{n:02} | {t:.1f}s",font=font,fill="black")
 sheet.save(OUT/f"dense_{n:02}.jpg",quality=90)
 print(n,flush=True)

