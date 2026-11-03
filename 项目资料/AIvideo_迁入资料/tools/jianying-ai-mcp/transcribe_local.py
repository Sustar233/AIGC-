import json,os,wave
import numpy as np
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE/"work/media"
os.environ["HF_HOME"]=str(BASE/"work/hf");os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"]="1"
from faster_whisper import WhisperModel
print("Loading local ASR model",flush=True)
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=8,download_root=str(BASE/"work/models"))
index=json.loads((OUT/"index.json").read_text(encoding="utf-8"))
# Primary story and likely alternatives first.
order=[5,19,0,1,6,4,3,2,7,8,11,9,10,15,16,12,13,14,18,17]
for n in order:
 dst=OUT/f"transcript_{n:02}.json"
 if dst.exists():continue
 with wave.open(str(OUT/f"clip_{n:02}.wav"),'rb') as w: samples=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
 segs,info=model.transcribe(samples,language="zh",beam_size=5,word_timestamps=True,vad_filter=True,initial_prompt="田静、方向、油条。水鱼街恩怨事务所。拉裤裤玩偶。万鹿城。")
 rows=[{"start":s.start,"end":s.end,"text":s.text,"words":[{"s":w.start,"e":w.end,"t":w.word} for w in (s.words or [])]} for s in segs]
 dst.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps({"index":n,"name":index[n]["name"],"segments":[{k:v for k,v in row.items() if k!="words"} for row in rows]},ensure_ascii=True),flush=True)

