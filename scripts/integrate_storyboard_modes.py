"""Apply the authorized AIvideo multi-panel workflow to the current skill."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
backup = root / 'memory/workspace-merges/AIvideo_2026-11-03/当前工作区修改前'
files = [
    '.agents/skills/storyboard-director/SKILL.md',
    '.agents/skills/storyboard-director/references/storyboard-preview.md',
    '.agents/skills/storyboard-director/scripts/build_storyboard_context.py',
]
for name in files:
    p = root / name
    saved = backup / name
    if not saved.exists():
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, saved)

p = root / files[0]
t = p.read_text(encoding='utf-8-sig')
t = t.replace('文字版只生成文字，带图版在文字完成后生成每单元 1 张预览图。', '文字版只生成文字；带图版在文字完成后生成每单元1张代表图；多格预览版先展示文字脚本，再按配置生成同脚本的完整N格预览，默认A/B两张。用户指定张数优先。')
t = t.replace('通过后，若为带图版再执行预览流程', '通过后，若为带图版或多格预览版再执行对应预览流程')
t = t.replace('上限超过 15 秒时继续拆分，表演已完整时不为凑满 15 秒继续细拆。', '用户贴出的单个片段优先一个完整单元；上限超过15秒时先说明原因并提出压缩或拆分选项，等待用户决定，不擅改台词或自动拆分。用户已授权多单元范围时按该范围拆分，表演完整时不为凑满15秒继续细拆。')
t = t.replace('- 用户选择带图版：`references/storyboard-preview.md`', '- 用户选择带图版或多格预览版：`references/storyboard-preview.md`')
t = t.replace('目标：忠于剧本', '目标：忠于剧本', 1)
if '## 项目覆盖与迁入规则' not in t:
    t += '\n\n## 项目覆盖与迁入规则\n\n根目录AGENTS、project.json及当前项目专属规则覆盖本文通用模板。正式正文是否输出时长、镜头时间轴、音效要求等以项目配置为准，不把下方通用示例的固定白噪音或时间轴强加到所有项目。旧AIvideo规则原件只按当前任务定向参考，不恢复另一套默认画风或缓存。\n'
p.write_text(t, encoding='utf-8')

p = root / files[1]
t = p.read_text(encoding='utf-8-sig')
t = t.replace('只在用户选择“带图版”时读取。', '只在用户选择“带图版”或“多格预览版”时读取。')
t = t.replace('每单元只选 1 个单帧画面', '普通带图版每单元只选1个单帧画面')
t = t.replace('不要制作多格拼贴，也不要为每个镜头各生一张图。', '普通带图版不制作多格拼贴，也不为每个镜头各生一张图；多格预览版按下方专用流程执行。')
if '## 多格预览版' not in t:
    t += '''

## 多格预览版

用户明确要求完整故事板、多格预览或A/B预览时，使用 `workflow.storyboard_generation.multi_panel_preview`；默认文字版与普通带图版不自动升级。

1. 先完成、校验并展示同一份文字分镜，再生成图片，不以等待生图阻塞脚本交付。
2. 默认两张A/B完整预览，每张覆盖本次脚本全部N镜，同镜号、同布局、同对白与动作边界；A/B为视觉备选，不是两条剧情。张数按用户或配置指定。
3. 采用规整等尺寸矩形网格，每格优先16:9，统一边距和分隔，镜号在画外标识带；格内不加对白字幕或说明文字，剧情必要标识按脚本保留。
4. 逐镜选一个最可读瞬间，明确景别、机位、构图、可见人数、站位和道具状态。不要把单格不同时间点叠在一起；全图角色外观和尺度保持一致。
5. 复用当前已读取的最小参考集合；不重新扫描全剧、不逐像素验收。集中检查镜数、镜序、关键人物与动作连续性，有实质错误才定向修正。
6. 图片保存到配置的 `multi_panel_preview.output_path`。无此字段时使用普通预览目录的“多格预览”子目录。只在交付记录或末尾链接记录图片路径，不写入供视频模型使用的逐镜正文。
7. 调用当前可用的生图工具；需要计费确认时按工具要求执行。不得因历史规则写了“自动”就绕过计费确认。

多格预览用于核对镜头设计，不代表完整动态运镜，也不保证独立视频素材自动帧级匹配。
'''
p.write_text(t, encoding='utf-8')

p = root / files[2]
t = p.read_text(encoding='utf-8-sig')
t = t.replace('choices=("文字版", "带图版")', 'choices=("文字版", "带图版", "多格预览版")')
t = t.replace('cache_path = root / "memory" / "storyboard-cache" / f"第{args.episode}集.md"', 'cache_root = project.get("paths", {}).get("storyboard_cache", "memory/storyboard-cache")\n    cache_path = root / cache_root / f"第{args.episode}集.md"')
p.write_text(t, encoding='utf-8')
print('Integrated multi-panel mode, excerpt boundary policy and configured cache path.')
