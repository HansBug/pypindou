# AGENTS.md

本仓库是一个纯 Python 拼豆图纸计算库，用于把图片转换成拼豆图纸数据。

## 范围

- `pypindou` 必须保持纯库形态。除非项目方向明确改变，不要添加 CLI。
- 核心输入是图像；核心输出是 `Pattern`，包含网格、图例/数量统计、预览渲染和元数据。
- 色卡数据必须通过 `make resource` 从 submodule 生成；不要手工编辑 `pypindou/resources/palettes.json`。

## 数据来源

- `data/pindou-color-data` 是国内色卡数据来源，对应 `HansBug/pindou-color-data`。
- `data/beadcolors` 是国际色卡数据来源，对应 `maxcleme/beadcolors`。
- 修改 submodule 或资源生成逻辑后，运行 `make resource`，并提交生成的 `pypindou/resources/palettes.json`。
- 标记为 `unidentified: true` 的颜色默认应被过滤。转换数据时不要丢掉这个标记。

## 代码风格

- 遵循当前模块结构：`color`、`image`、`pattern`、`benchmark`。
- 测试路径在 `test/` 下镜像模块路径。
- 只有足够稳定、适合用户直接使用的 API 才从 `pypindou.__init__` 暴露。
- 公开返回对象优先使用清晰的 dataclass。

## 验证

推送实质性改动前运行：

```bash
make resource
make test
make docs
make package
```

如果只修改文档或 CI，可以运行更窄的相关命令，并在交付说明中说明跳过了什么。

## 后续方向

计划方向包括：

- 更好的调色板压缩指标与 benchmark；
- 拼豆板分页、摆放约束和跨板布局；
- 作为下游 helper 的 PDF/XLSX 导出；
- 通过 extras 接入可选的去背景 / SAM 分割能力；
- 面向人工操作友好性的换色和操作成本启发式。
