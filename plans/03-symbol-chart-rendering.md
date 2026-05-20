# 符号图导出与文字约束实现记录

日期：2026-05-20

## 背景

拼豆图纸的色号文字必须严格位于各自 cell 内，不能跨格污染邻近格子。同时图纸需要支持位图和矢量两种交付格式，便于 README 预览、打印和下游编辑。

## 实现结论

- PNG 继续基于 Pillow 输出，不引入系统级图形依赖。
- SVG 使用标准库字符串生成，不依赖 cairo、浏览器或 JavaScript runtime。
- PNG 和 SVG 共用同一套 label 策略和 cell padding 约束。
- `to_symbol_image` 输出 PNG 兼容的 `PIL.Image.Image`，保持旧调用方式可用。
- `to_symbol_svg` 返回 SVG 文本。
- `save_symbol_chart` 根据 `.png` 或 `.svg` 后缀保存对应格式。

## 文字约束策略

PNG 路径先把色号文字渲染到透明临时图，再按 cell 内框缩放并粘贴。这样即使色号很长，也只会缩小，不会画出 cell 内框。

SVG 路径为每个活跃 cell 生成独立 `clipPath`，并给 `<text>` 添加 `textLength` 和 `lengthAdjust="spacingAndGlyphs"`。即使不同 SVG 查看器的字体度量不同，文字也会被限制在对应 cell 内。

## 验证

新增单元测试使用超长色号放在右侧 cell，左侧 cell 保持空白；如果文字向左溢出，左侧内部像素会被污染。该测试覆盖了 PNG 的严格 cell 边界行为。SVG 测试覆盖 `clipPath`、`textLength` 和保存路径。
