import json, subprocess, os
from pathlib import Path
import numpy as np
import imageio_ffmpeg
from faster_whisper import WhisperModel
BASE=Path(__file__).resolve().parent
OUT=Path((BASE/'work/output_path.txt').read_text(encoding='utf-8'))
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
pcm=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(OUT/'鹿城_停车场_85秒_v001.mp4'),'-vn','-ac','1','-ar','16000','-f','f32le','-'],capture_output=True,check=True,creationflags=0x08000000).stdout
model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=8,download_root=str(BASE/'work/models'),local_files_only=True)
segs,info=model.transcribe(np.frombuffer(pcm,dtype=np.float32),language='zh',beam_size=5,word_timestamps=True,vad_filter=True,initial_prompt='田静、方向、油条。水鱼街恩怨事务所。拉裤裤玩偶。万鹿城。')
rows=[dict(start=s.start,end=s.end,text=s.text) for s in segs]
(OUT/'成片对白核对.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=True),flush=True)
