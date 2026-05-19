# 拼豆图纸生成调研与实现计划

日期：2026-05-19

## 背景

当前 `pypindou` 已经具备从图像生成拼豆图纸的核心链路：缩放、按真实色卡最近色匹配、限色、图纸网格、颜色统计、预览图和符号图。README 示例之前默认启用 Floyd-Steinberg 抖动，照片类输入会产生大量棋盘式纹理和孤立噪点；这对屏幕预览可能更接近原图，但对真人按色号摆豆并不友好。

本调研目标是参考现有拼豆/像素图纸工具，确定 `pypindou` 的默认生成策略和近期算法参数。

## 参考来源

| 来源 | 类型 | 观察到的能力 | 对 `pypindou` 的启发 |
| --- | --- | --- | --- |
| `codex resume 019e3ef9-8543-7f31-992b-8abd6bf8e5d5` | 本地调研会话 | PyPI 上没有成熟、完整的 image -> bead pattern -> 色号统计 -> 打印输出纯库；成熟能力多在 Web/桌面工具。 | `pypindou` 应先提供稳定核心库，不强塞 CLI/GUI；算法、数据、渲染输出要可复用。 |
| `codex resume 019e3ee1-e919-7fe3-91c9-dec2b3b3a191` | 本地色卡调研会话 | 国内色卡交付以每系列 `colors.json`、`colors.xlsx`、`legend.pdf`、`README.md` 的结构整理，强调 RGB 来源、缺失 RGB 和特殊材质。 | 本库资源生成必须保留国内数据质量字段，默认过滤 `unidentified`，并把国内外数据统一进同一套 dataclass/schema。 |
| `glasnt/ih` / PyPI `ih` | Python CLI，十字绣/拼豆相关 | 支持 palette、scale、colors 限制、HTML/终端输出、print-ready guidelines；内部先把图片压到有限颜色，再映射到目标 palette。 | 限色、图例、打印友好图纸是主流需求；图纸生成不应只追求像素级误差。 |
| `BrechtBa/beadalize` / PyPI `beadalize` | Python 包 | 包很小，sdist 缺失 readme 导致构建失败，实际没有可复用算法主体。 | 不作为算法参考；也说明 PyPI 生态空缺明显。 |
| `maxcleme/beadifier` | Web/Angular 工具 | 目标功能包括图片转图纸、选择多个品牌、Mini/Midi 珠、拼板数量、用量统计、PDF 导出；有亮度/对比度/饱和度/灰度滤镜，支持多种颜色距离和可调硬度的 Floyd-Steinberg 抖动。 | 抖动应是显式参数；用户需要预处理调节、颜色距离选项、板格/用量/导出。 |
| `sucpyy/perler-pattern` | 单文件 Python 脚本 | Pillow 缩放、加权 RGB 距离、透明阈值、Artkal/Perler/Hama 色卡、自定义颜色、颜色数、颜色预览/编号图/图例/板格覆盖。 | 最小可用工具会提供透明处理、色卡匹配、编号图和图例；距离可比纯 RGB 更偏感知。 |
| `KafukaTree/pindou-generator` | Web/Next 工具 | 使用 median-cut 风格 quantize 抽样得到主色，再按国内品牌色卡 Euclidean RGB 最近色匹配；跳过 alpha < 128 的透明像素；canvas 渲染色号格。 | 限制主色数量再映射到真实色卡是常见做法；国内品牌色号图是关键输出。 |
| `VB6Hobbyst7/pixie_stitch` | 桌面/Rust 工具 | 面向小尺寸 pixel-art，最多约 20 色，输出完整预览和真实感预览；README 明确适合少色透明像素图。 | 人工图纸更适合低色数、清晰区域、透明背景；照片输入需要转成更像 pixel-art 的结果。 |
| MakeBead 等在线工具 | Web 工具 | 典型流程是上传图片、选择拼板/尺寸/色卡/颜色数量、预览图纸和色号统计。 | `pypindou` 应把这些 UI 层能力拆成库参数，供后续 Web/GUI/PDF 层调用。 |

## 算法结论

1. **默认不应启用全强度抖动。** Floyd-Steinberg 会改善屏幕色调连续性，但会把照片阴影和皮肤纹理打散成大量交错小色块。对手工拼豆来说，这会增加选豆和摆豆负担。
2. **先压缩视觉信息，再映射真实色卡。** 输入照片应先经过亮度/对比度/饱和度/锐化或平滑等可控预处理，再缩放到拼豆网格，之后限制总颜色数。
3. **量化后需要清理孤立色块。** 人工图纸不宜包含大量 1 到 2 个豆的孤岛。应提供邻域多数清理和小连通域合并参数。
4. **抖动仍应保留，但作为纹理/detail 选项。** 用户需要时可设置 `quantize="floyd-steinberg"` 和较低 `dither_strength`。
5. **输出图纸要服务操作。** 色号统计、符号图、可选板格、限制颜色总数、限定/排除色号比单纯相似度更重要。

## 本次实现计划

- 在 `pypindou.image.preprocess` 增加：
  - `enhance_image`：亮度、对比度、饱和度、锐度、灰度混合。
  - `prefilter_image`：`none`、`smooth`、`median`、`edge` 预滤波。
- 在 `pypindou.image.quantize` 增加：
  - `dither_strength`：控制 Floyd-Steinberg 扩散强度。
  - `cleanup_quantization`：量化后邻域多数清理。
  - `min_region_size`：合并小连通域，减少孤立色块。
- 在 `generate_pattern` / `PatternOptions` 暴露这些参数，并记录到 metadata。
- README 示例改用干净图纸默认：
  - `quantize="nearest"`
  - `prefilter="smooth"` 或 `median`
  - 低于原先的 `max_colors`
  - `cleanup="majority"`、`cleanup_passes=2`、`min_region_size` 合并小块
- 文档中明确：
  - 干净图纸适合实际摆豆。
  - 抖动适合追求照片纹理，但会增加操作复杂度。
  - 大图、低色数和小连通域清理之间需要权衡。

## 后续方向

- PDF/分页/板格坐标导出应放在独立输出层，核心库继续返回结构化 `Pattern`。
- 可增加更多颜色距离，如 CIE94/CIEDE2000，但需要先确认性能和 Python 3.8-3.14 依赖稳定性。
- SAM、去背景、主体裁剪等深度学习能力适合作为可选插件或下游应用层，不宜进入默认运行时依赖。
- Benchmark 应覆盖：图像尺寸、色卡大小、限色数量、抖动强度、清理强度、输出色数和平均误差。
