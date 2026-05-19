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

## Quick Start

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

## Palettes

The packaged palette resource is generated from:

- `HansBug/pindou-color-data`: 国内常用拼豆色卡数据，含 MARD、盼盼、COCO、漫漫、咪小窝、优肯等。
- `maxcleme/beadcolors`: Hama、Perler、Artkal、Nabbi 等国际色卡数据。

Regenerate packaged resources after updating submodules:

```bash
git submodule update --init --recursive
make resource
```

List palettes:

```python
from pypindou import list_palettes

for item in list_palettes():
    print(item["id"], item["title"], item["count"])
```

## Data Quality

Domestic palette data may contain upstream-unidentified colors marked with `unidentified: true` in the source data. `pypindou` excludes these by default. Set `allow_unidentified=True` only when you explicitly want those placeholder colors in downstream patterns.

## Development

```bash
git submodule update --init --recursive
python -m pip install -r requirements-test.txt
make test
make docs
make package
```

There is intentionally no CLI in this repository. Application-facing CLIs, web UIs, manual editing workflows, PDF exports, and deep-learning-assisted segmentation should be built as downstream layers on top of this library.
