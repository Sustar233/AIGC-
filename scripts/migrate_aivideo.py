"""Preserve and import the explicitly authorized AIvideo workspace (no deletion)."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Users\浮白文化\Documents\ChatGPT\AIvideo")
DEST = ROOT / "项目资料/AIvideo_迁入资料"
AUDIT = ROOT / "memory/workspace-merges/AIvideo_2026-11-03"
BACKUP = AUDIT / "AIvideo_完整工作区.zip"
SKIP_ACTIVE = {".git", ".venv", "venv", "node_modules", "__pycache__", "渲染缓存"}

def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def mapping(rel):
    if any(p in SKIP_ACTIVE for p in rel.parts):
        return None
    if "models" in rel.parts and rel.parts[0] == "tools":
        return None
    parts = list(rel.parts)
    if ".agents" in parts:
        i = parts.index(".agents")
        parts[i] = "规则原件"
    if parts[-1] == "AGENTS.md":
        parts[-1] = "AGENTS.source.md"
    return Path(*parts)

def main():
    assert ROOT.resolve() != SOURCE.resolve()
    if DEST.exists() or BACKUP.exists():
        raise RuntimeError("Import or backup already exists; inspect it instead of overwriting")
    files = sorted(p for p in SOURCE.rglob("*") if p.is_file())
    if any(p.is_symlink() or p.is_junction() for p in SOURCE.rglob("*")):
        raise RuntimeError("Source contains links; inspect before import")
    AUDIT.mkdir(parents=True, exist_ok=True)
    before = AUDIT / "当前工作区修改前"
    for name in ["project.json", "AGENTS.md", "README.md", "memory/MEMORY.md", "memory/新剧_方向与油条_项目状态.md", "项目资料/新剧_方向与油条/分镜编写规则.md"]:
        target = before / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    rows = []
    print(f"Backing up {len(files)} files", flush=True)
    with zipfile.ZipFile(BACKUP, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
        for p in files:
            rel = p.relative_to(SOURCE)
            row = {"source": rel.as_posix(), "bytes": p.stat().st_size, "sha256": digest(p)}
            z.write(p, rel.as_posix())
            mapped = mapping(rel)
            if mapped is not None:
                target = DEST / mapped
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
                if digest(target) != row["sha256"]:
                    raise RuntimeError(f"Copy verification failed: {rel}")
                row["destination"] = target.relative_to(ROOT).as_posix()
            else:
                row["destination"] = None
                row["preserved_in"] = "完整工作区备份"
            rows.append(row)
    print("Verifying every backup entry by SHA-256", flush=True)
    with zipfile.ZipFile(BACKUP) as z:
        assert len(z.infolist()) == len(rows)
        for row in rows:
            with z.open(row["source"]) as f:
                if hashlib.file_digest(f, "sha256").hexdigest() != row["sha256"]:
                    raise RuntimeError(f"Backup verification failed: {row['source']}")
    manifest = {"source_root": str(SOURCE), "destination_root": str(DEST), "backup": str(BACKUP.relative_to(ROOT)), "backup_sha256": digest(BACKUP), "source_files": len(rows), "copied_files": sum(r["destination"] is not None for r in rows), "source_bytes": sum(r["bytes"] for r in rows), "backup_verified": True, "source_deleted": False, "files": rows}
    (AUDIT / "迁移清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in manifest.items() if k != "files"}, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
