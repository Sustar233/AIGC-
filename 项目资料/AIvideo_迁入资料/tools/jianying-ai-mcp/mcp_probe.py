import asyncio, json, os, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
BASE=Path(__file__).resolve().parent
OUT=BASE/"work";OUT.mkdir(exist_ok=True)
async def main():
 env=dict(os.environ)
 for key in ["OPENAI_API_KEY","GROQ_API_KEY"]:env.pop(key,None)
 env.update(JIANYING_DRAFT_ROOT="F:/JianyingPro Drafts",JIANYING_MCP_WORK_ROOT=str(OUT),JIANYING_EXE="C:/Users/浮白文化/AppData/Local/JianyingPro/Apps/11.5.0.14471/JianyingPro.exe",JIANYING_DRAFT_CRYPTO=str(BASE/"native/jy-draftc.exe"),PYTHONIOENCODING="utf-8")
 cfg=StdioServerParameters(command=sys.executable,args=["-m","jianying_ai_mcp"],env=env)
 async with stdio_client(cfg) as (reader,writer):
  async with ClientSession(reader,writer) as session:
   init=await session.initialize()
   print("MCP_CONNECTED",init.serverInfo.model_dump(),flush=True)
   listed=await session.list_tools()
   (OUT/"tools.json").write_text(json.dumps(listed.model_dump(),ensure_ascii=False,indent=2),encoding="utf-8")
   print("TOOLS",[t.name for t in listed.tools],flush=True)
   cap=await session.call_tool("get_jianying_capabilities",{})
   (OUT/"capabilities.json").write_text(cap.model_dump_json(indent=2),encoding="utf-8")
   print("CAPABILITIES_SAVED",flush=True)
   result=await session.call_tool("analyze_reference_draft",{"draft_name":"codex剪映测试","include_text":True})
   (OUT/"reference_analysis.json").write_text(result.model_dump_json(indent=2),encoding="utf-8")
   print("ANALYSIS",result.model_dump_json()[:9000],flush=True)
asyncio.run(main())

