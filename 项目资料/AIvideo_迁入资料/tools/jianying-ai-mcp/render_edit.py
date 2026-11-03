import json,subprocess,math,io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import imageio_ffmpeg
BASE=Path(__file__).resolve().parent;OUT=Path((BASE/"work/output_path.txt").read_text(encoding="utf-8"));RENDER=OUT/"渲染缓存";RENDER.mkdir(exist_ok=True)
plan=json.loads((OUT/"剪辑计划.json").read_text(encoding="utf-8"));ff=imageio_ffmpeg.get_ffmpeg_exe()
def run(cmd):
 r=subprocess.run(cmd,capture_output=True,encoding="utf-8",errors="replace",creationflags=0x08000000)
 if r.returncode:raise RuntimeError(r.stderr[-3000:])
 return r
def render(s):
 i=s["index"];dest=RENDER/f"v_{i:03}.mp4";frames=s["frames"]
 z=f"({s['zoom_start']}+({s['zoom_end']}-{s['zoom_start']})*on/{max(1,frames-1)})"
 # Fit-fill crop without distortion, then optional gentle anime push.
 vf="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30"
 if s["zoom_start"]!=1 or s["zoom_end"]!=1:
  vf+=f",zoompan=z='{z}':x='(iw-iw/zoom)*{s['center_x']}':y='(ih-ih/zoom)*{s['center_y']}':d=1:s=1920x1080:fps=30"
 cmd=[ff,"-v","error","-ss",f"{s['source_start_frame']/30:.8f}","-i",s["source"],"-an","-vf",vf,"-frames:v",str(frames),"-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p","-threads","3","-y",str(dest)]
 run(cmd);print(f"VIDEO {i+1}/{len(plan['video'])}",flush=True);return dest
with ThreadPoolExecutor(max_workers=3) as pool:videos=list(pool.map(render,plan["video"]))
concat=RENDER/"video_concat.txt";concat.write_text("".join("file '"+x.as_posix().replace("'","'\\''")+"'\n" for x in videos),encoding="utf-8")
run([ff,"-v","error","-f","concat","-safe","0","-i",str(concat),"-c","copy","-y",str(RENDER/"video.mp4")])
audio_parts=[]
for i,a in enumerate(plan["audio"]):
 dest=RENDER/f"a_{i:03}.wav";duration=a["frames"]/30
 # 4ms/6ms fades protect cut boundaries without cutting intelligible syllables.
 af=f"atrim=start={a['source_start_frame']/30:.8f}:duration={duration:.8f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.004,afade=t=out:st={duration-.006:.8f}:d=0.006,aresample=48000"
 run([ff,"-v","error","-i",a["source"],"-af",af,"-ac","2","-c:a","pcm_s16le","-y",str(dest)]);audio_parts.append(dest)
aconcat=RENDER/"audio_concat.txt";aconcat.write_text("".join("file '"+x.as_posix().replace("'","'\\''")+"'\n" for x in audio_parts),encoding="utf-8")
run([ff,"-v","error","-f","concat","-safe","0","-i",str(aconcat),"-af","loudnorm=I=-16:TP=-1.5:LRA=9","-ar","48000","-c:a","pcm_s16le","-y",str(OUT/"对白混音_85秒.wav")])
final=OUT/"鹿城_停车场_85秒_v001.mp4"
run([ff,"-v","error","-i",str(RENDER/"video.mp4"),"-i",str(OUT/"对白混音_85秒.wav"),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","256k","-t","85","-movflags","+faststart","-y",str(final)])
print("FINAL "+str(final),flush=True)

