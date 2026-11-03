import asyncio,json,os,sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
BASE=Path(__file__).resolve().parent
OUT=Path((BASE/"work/output_path.txt").read_text(encoding="utf-8"))
async def main():
 env=dict(os.environ)
 for key in ["OPENAI_API_KEY","GROQ_API_KEY"]:env.pop(key,None)
 env.update(JIANYING_DRAFT_ROOT="F:/JianyingPro Drafts",JIANYING_MCP_WORK_ROOT=str(BASE/"work"),JIANYING_EXE="C:/Users/浮白文化/AppData/Local/JianyingPro/Apps/11.5.0.14471/JianyingPro.exe",PYTHONIOENCODING="utf-8")
 manifest=json.loads((OUT/"剪映MCP清单.json").read_text(encoding="utf-8"))
 publish="--publish" in sys.argv
 async with stdio_client(StdioServerParameters(command=sys.executable,args=["-m","jianying_ai_mcp"],env=env)) as (rd,wr):
  async with ClientSession(rd,wr) as session:
   await session.initialize()
   res=await session.call_tool("build_draft",{"manifest":manifest,"dry_run":not publish})
   (OUT/("MCP发布结果.json" if publish else "MCP试运行结果.json")).write_text(res.model_dump_json(indent=2),encoding="utf-8")
   data=res.structuredContent or {}
   print(json.dumps(data,ensure_ascii=True),flush=True)
   if not data.get("success"):raise SystemExit(1)
asyncio.run(main())

