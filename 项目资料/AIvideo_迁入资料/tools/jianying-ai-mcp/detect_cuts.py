import json, subprocess,re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import imageio_ffmpeg
BASE=Path(__file__).resolve().parent;OUT=BASE/"work/media"
items=json.loads((OUT/"index.json").read_text(encoding="utf-8"));ff=imageio_ffmpeg.get_ffmpeg_exe()
def inspect(it):
 cmd=[ff,"-hide_banner","-i",it["path"],"-vf","select='gt(scene,0.25)',showinfo","-an","-f","null","-"]
 r=subprocess.run(cmd,capture_output=True,encoding="utf-8",errors="replace",creationflags=0x08000000)
 cuts=[float(x) for x in re.findall(r"pts_time:([0-9.]+)",r.stderr)]
 return {"index":it["index"],"name":it["name"],"cuts":cuts}
with ThreadPoolExecutor(max_workers=3) as pool:rs=list(pool.map(inspect,items))
(OUT/"cuts.json").write_text(json.dumps(rs,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(rs,ensure_ascii=True),flush=True)

