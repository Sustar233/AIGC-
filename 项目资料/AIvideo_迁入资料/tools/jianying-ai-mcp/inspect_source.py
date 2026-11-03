import json, os
from pathlib import Path
from jianying_ai_mcp.config import Settings
from jianying_ai_mcp.draft_crypto import load_draft_json
BASE=Path(__file__).resolve().parent
os.environ.update(JIANYING_DRAFT_ROOT="F:/JianyingPro Drafts",JIANYING_MCP_WORK_ROOT=str(BASE/"work"),JIANYING_EXE="C:/Users/浮白文化/AppData/Local/JianyingPro/Apps/11.5.0.14471/JianyingPro.exe",JIANYING_DRAFT_CRYPTO=str(BASE/"native/jy-draftc.exe"))
settings=Settings.from_env()
folder=Path("F:/JianyingPro Drafts/codex剪映测试")
output={}
for name in ["draft_meta_info.json","Timelines/F6CC82EC-7503-4de3-BECA-268636F75C62/draft_content.json"]:
 data=load_draft_json(settings,folder/name).content
 output[name]=data
 print(name,"keys",list(data.keys()),flush=True)
 if name=="draft_meta_info.json":print(json.dumps(data,ensure_ascii=True)[:24000])
 else:print("duration",data.get("duration"),"tracks",len(data.get("tracks",[])))
(BASE/"work"/"source_inventory.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")

