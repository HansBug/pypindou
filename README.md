# pypindou

`pypindou` 是一个纯 Python 拼豆图纸计算库，目标是把输入图像转换成真实拼豆色卡上的图纸、色号统计和可渲染预览。

当前阶段重点放在可复用库能力，而不是 CLI 或 GUI：

- 图片缩放到指定拼豆格数。
- 基于真实色卡做最近色匹配。
- 支持 RGB / Lab 距离空间。
- 支持 Floyd-Steinberg 抖动。
- 支持限制可用颜色列表、排除颜色、限制总颜色数。
- 默认过滤不可辨认色号，避免下游误用 `UNKNOWN-*`。
- 输出图纸网格、色号用量、预览图和符号图。
- 内置色卡资源由 submodule 生成并随 PyPI 包发布。

## 快速开始

```python
from pypindou import generate_pattern

pattern = generate_pattern(
    "input.png",
    palette="mard-221-alfonse-doudou",
    width=58,
    height=58,
    max_colors=48,
    quantize="floyd-steinberg",
)

print(pattern.color_counts())
pattern.to_image(scale=12).save("preview.png")
pattern.to_symbol_image(cell_size=24).save("symbols.png")
```

## 色卡数据

包内静态色卡资源由以下 submodule 生成：

- `HansBug/pindou-color-data`：国内常用拼豆色卡数据，含 MARD、盼盼、COCO、漫漫、咪小窝、优肯等。
- `maxcleme/beadcolors`：Hama、Perler、Artkal、Nabbi 等国际色卡数据。

更新 submodule 后重新生成包内资源：

```bash
git submodule update --init --recursive
make resource
```

列出可用色卡：

```python
from pypindou import list_palettes

for item in list_palettes():
    print(item["id"], item["title"], item["count"])
```

## 数据质量

国内色卡数据里可能存在上游无法确认真实色号的颜色。这类颜色会在源数据中标记为 `unidentified: true`。`pypindou` 默认过滤它们，只有显式设置 `allow_unidentified=True` 时才会参与图纸生成。

## 开发

```bash
git submodule update --init --recursive
python -m pip install -r requirements-test.txt
make test
make docs
make package
```

本仓库刻意不提供 CLI。面向用户的 CLI、Web UI、人工改色流程、PDF 导出、深度学习辅助抠图/分割等，都应该作为下游应用层基于这个库继续构建。
