# 生图模型规格说明

## GPT Image 系列

### 特性
- 最佳输入：自然语言描述
- 支持长度：最多 ~400 tokens
- 优势：理解复杂语义、场景还原强
- 劣势：风格化可控性较弱

### 提示词建议
```
1. 用完整句子描述，而非关键词堆砌
2. 优先描述主体，再展开细节
3. 避免过多技术参数
4. 使用"high quality""detailed"等简单质量词
```

**模板格式**:
```
A [age] [gender] who is [appearance details]. 
They are wearing [clothing description]. 
The setting is [scene description]. 
[Lighting and atmosphere]. High quality, detailed artwork.
```

---

## Seedream 系列

### 特性
- 最佳输入：关键词 + 自然语言混合
- 支持长度：~600 tokens
- 优势：亚洲人脸优化、风格多样
- 劣势：英文理解略逊

### 提示词建议
```
1. 关键特征用英文关键词
2. 复杂描述用自然语言
3. 可以加入中文注释（部分支持）
4. 明确指定风格标签
```

**模板格式**:
```
[keyword1], [keyword2], [keyword3], 
[detailed description in sentences], 
style: [style_tag], quality: [quality_tag]
```

### 常用风格标签
```
photorealistic      # 写实
anime               # 动漫
watercolor          # 水彩
oil painting        # 油画
digital art         # 数字艺术
illustration        # 插画
```

---

## 通用参数建议

### 分辨率
- 人设图推荐：1024x1024 或 768x1024 (竖版更适合人物)

### 采样步数
- SDXL 系：30-40 steps
- DALL·E 3：自动
- Midjourney: --s 250-500 (stylize)

### CFG Scale
- 写实风格：5-7
- 艺术风格：7-10

---

## 负面提示词

默认不输出。只有用户明确要求且目标平台支持时，才根据当前主体提供简短、针对性的规避项；不得把 `3d`、`cgi` 或 `render` 列为负面词。
