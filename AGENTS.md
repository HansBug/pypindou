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

## Python Pydoc / Docstring 规范

本仓库的 Python docstring 规范沿用 `pyfcstm` 的写法：只使用 reStructuredText (reST) 格式，并面向 Sphinx
生成 API 文档。不要使用 Google style、NumPy style 或 Markdown 风格 docstring。

### 核心原则

1. **格式**：统一使用 reST markup。
2. **完整性**：所有公开模块、类、函数、方法都应有 docstring。
3. **清晰性**：解释对象的用途、约束和返回语义；不要只复述实现步骤。
4. **交叉引用**：使用 `:class:`、`:func:`、`:mod:`、`:meth:` 等 reST roles。
5. **示例**：公开 API 优先提供可运行的 Python 交互示例。
6. **语气**：专业、清楚、技术准确，避免营销化描述。

### Docstring 模板

**Module**:

```python
"""
Brief one-line description.

Longer description of purpose, main capabilities, and fit in the larger system.

The module contains:
* :class:`ClassName` - Brief description
* :func:`function_name` - Brief description

.. note::
   Important caveats about usage or requirements.

Example::

    >>> from pypindou.color import rgb_to_hex
    >>> rgb_to_hex((255, 128, 0))
    '#FF8000'
"""
```

**Class**:

```python
class ClassName:
    """
    Brief one-line description.

    Longer explanation of purpose, responsibilities, and usage patterns.

    :param param_name: Description of constructor parameter.
    :type param_name: ParamType
    :param optional_param: Description, defaults to ``default_value``.
    :type optional_param: ParamType, optional

    :ivar instance_var: Description of instance variable.
    :vartype instance_var: VarType
    :cvar class_var: Description of class variable.
    :type class_var: ClassVarType

    Example::

        >>> obj = ClassName(param_name=value)
        >>> obj.method()
        expected_result
    """
```

**Function / Method**:

```python
def function_name(param1: Type1, param2: Type2 = default) -> ReturnType:
    """
    Brief one-line description.

    Longer explanation of behavior, algorithm, or important details.

    :param param1: Description of the first parameter.
    :type param1: Type1
    :param param2: Description, defaults to ``default``.
    :type param2: Type2, optional
    :return: Description of what is returned.
    :rtype: ReturnType
    :raises ValueError: If the input shape or option value is invalid.

    Example::

        >>> result = function_name(arg1, arg2)
        >>> result
        expected_output
    """
```

**Dataclass**:

```python
@dataclass
class DataClassName:
    """
    Brief description of what this dataclass represents.

    :param field1: Description of the first field.
    :type field1: Type1
    :param field2: Description of the second field.
    :type field2: Type2

    Example::

        >>> obj = DataClassName(field1=value1, field2=value2)
        >>> obj.field1
        value1
    """
    field1: Type1
    field2: Type2
```

### 参数、返回值和异常写法

```python
:param param_name: Description.
:type param_name: type_annotation
:param param_name: Description, defaults to ``value``.
:type param_name: type_annotation, optional
:return: Description of what is returned.
:rtype: ReturnType
:return: ``None``.
:rtype: None
:raises ValueError: When this exception is raised.
:raises FileNotFoundError: If the source image file does not exist.
```

所有带类型标注的公开参数仍要写 `:type:`；返回值仍要写 `:rtype:`。可选参数在 `:type:` 后加 `, optional`，
默认值写在 `:param:` 描述里，使用双反引号标记字面值。

### 交叉引用和内联标记

- 类、函数、方法、模块、异常分别使用 `:class:`、`:func:`、`:meth:`、`:mod:`、`:exc:`。
- 数据和属性使用 `:data:`、`:attr:`；实例变量使用 `:ivar:` / `:vartype:`；类变量使用 `:cvar:` / `:type:`。
- 内联代码只使用双反引号，例如 reST 源码中的 ` ``nearest`` `；不要使用单反引号。
- 引用本项目 API 时写全限定路径更稳，例如 `` :class:`pypindou.pattern.Pattern` ``。

### Inline Markup 边界规则

在 reST/Sphinx 中，内联加粗 `**bold**` 和内联字面量 ` ``literal`` ` 的左右两侧都需要合法边界。如果普通文本紧贴
开头或结尾标记，Sphinx 可能把标记原样渲染出来。

**错误示例**：

- `prefix**text**`
- `**text**suffix`
- `建模**层次状态机**。`
- `前文``code``后文`
- ``code``suffix
- `中文**加粗**文本`
- `中文``code``文本`

**正确示例**：

- `prefix **text**`
- `**text** suffix`
- `prefix ``code`` suffix`
- `建模\ **层次状态机**。`
- `**text**.`
- `前文 **加粗** 后文`
- `前文 ``code`` 后文`
- `**加粗**\ 后文`
- ``code``\ 后文

中文文档或紧凑中文句子里，优先使用安全写法：

- `前文\ **加粗**\ 后文`
- `前文\ ``code``\ 后文`

不要假设中文全角标点天然是安全边界。尤其是 ` ``literal`` ` 后面直接跟全角括号 `（` 时，很容易在 HTML 中产生
`class="problematic"` 或直接漏出反引号。

常见问题模式：

- `**普通详细级别**（默认）`
- `**1. pip 安装**（推荐）：`
- `执行 ``A.enter``（未定义）`
- `检查转换：``A -> B :: Go``（事件匹配！）`
- `- ``variable_display_mode`` (str)：显示模式 - ``'note'``（默认：``'legend'``）`

安全修复：

- `**普通详细级别**\ （默认）`
- `**1. pip 安装**\ （推荐）：`
- `执行 ``A.enter``\ （未定义）`
- `检查转换：``A -> B :: Go``\ （事件匹配！）`
- `- ``variable_display_mode`` (str)：显示模式 - ``'note'``\ （默认：``'legend'``）`

批量清理 `.rst` 或 docstring 时，不要只相信源文件正则检查；应重建 Sphinx HTML，并检查生成 HTML 是否仍有
`class="problematic"`、泄漏的 `**` 或泄漏的成对反引号。

### Docstring 示例

公开 API 示例使用 Python doctest 风格，优先选择稳定、轻量、无需外部文件的输入。

```python
Example::

    >>> from pypindou.color import hex_to_rgb, rgb_to_hex
    >>> hex_to_rgb("#FF8000")
    (255, 128, 0)
    >>> rgb_to_hex((255, 128, 0))
    '#FF8000'
```

本仓库是纯 Python 库，不要在 docstring 中添加命令行调用示例，除非项目方向明确增加 CLI。需要展示图像到图纸
流程时，使用 Python 代码示例。

**项目语境示例**：

```python
def generate_pattern_with_options(image: str | Path | Image.Image, options: PatternOptions) -> Pattern:
    """
    Generate a fuse-bead pattern from an image and a reusable options object.

    This helper keeps user-facing image conversion settings in
    :class:`pypindou.pattern.PatternOptions` and delegates the actual conversion
    to :func:`pypindou.pattern.generate_pattern`.

    :param image: Image path or already loaded PIL image.
    :type image: str | pathlib.Path | PIL.Image.Image
    :param options: Pattern generation options.
    :type options: pypindou.pattern.PatternOptions
    :return: Generated bead pattern.
    :rtype: pypindou.pattern.Pattern
    :raises FileNotFoundError: If ``image`` is a path that does not exist.
    :raises ValueError: If image sizing, palette, or quantization options are invalid.

    Example::

        >>> from PIL import Image
        >>> from pypindou.pattern import PatternOptions, generate_pattern_with_options
        >>> image = Image.new("RGB", (2, 2), "#ffffff")
        >>> pattern = generate_pattern_with_options(image, PatternOptions(width=2, height=2))
        >>> pattern.width, pattern.height
        (2, 2)
    """
```

### 特殊指令

```python
.. note::
   Important information or caveats about usage.

.. warning::
   Critical warnings about potential issues or dangers.
```

### Checklist

- [ ] 顶部有一句简短 summary。
- [ ] 非平凡函数/类有更长说明。
- [ ] 所有参数都有 `:param:` 和 `:type:`。
- [ ] 返回值有 `:return:` 和 `:rtype:`。
- [ ] 公开抛出的异常有 `:raises:`。
- [ ] 交叉引用使用 reST roles。
- [ ] 公开 API 有实用示例。
- [ ] 内联代码使用双反引号。
- [ ] `**strong**` 和 ` ``literal`` ` 两侧有合法边界；中文紧凑文本优先使用 `\ `。
- [ ] 不要让 closing `**` 或 closing double-backtick 直接贴全角 `（`；不确定时加 `\ `。
- [ ] 大规模标记清理后，以 Sphinx HTML 的渲染结果为准。
- [ ] 可选参数标记 `, optional`，默认值写在描述里。

### Anti-Patterns

**不要**：使用 Google/NumPy style；省略 `:type:` / `:rtype:`；使用单反引号；把 `**strong**` 或 ` ``literal`` `
紧贴中文或英文文本；只写模糊描述如 "Does something"；裸写类名/函数名而不用 reST roles；在 docstring 中记录
易过期的内部实现细节。

**应该**：稳定使用 reST；说明 API 的用途和约束；使用交叉引用；包含可运行示例；代码变化时同步更新 docstring。

### pypindou 常见写法

**颜色模型和色卡过滤**：

```python
def by_code(self, code: str) -> BeadColor:
    """
    Get a bead color by its palette code.

    :param code: Palette-local color code.
    :type code: str
    :return: Matching bead color.
    :rtype: pypindou.color.BeadColor
    :raises KeyError: If the code is not present in this palette.
    """
```

**图像量化和矩阵输入**：

```python
def quantize_image(
    rgb: np.ndarray,
    active_mask: np.ndarray,
    palette: Palette,
    *,
    method: QuantizeMethod = "nearest",
    color_space: ColorSpace = "lab",
) -> QuantizationResult:
    """
    Quantize an RGB image to bead palette indices.

    :param rgb: RGB image array with shape ``(height, width, 3)``.
    :type rgb: numpy.ndarray
    :param active_mask: Boolean mask marking pixels that should become beads.
    :type active_mask: numpy.ndarray
    :param palette: Palette used for color matching.
    :type palette: pypindou.color.Palette
    :param method: Quantization method, defaults to ``"nearest"``.
    :type method: pypindou.image.QuantizeMethod, optional
    :param color_space: Color space used for distance calculation, defaults to ``"lab"``.
    :type color_space: pypindou.color.ColorSpace, optional
    :return: Quantized indices, rendered RGB preview, active mask, and error map.
    :rtype: pypindou.image.QuantizationResult
    :raises ValueError: If array shapes or method values are invalid.
    """
```

## LLM 文档生成和 RST

```bash
make rst_auto      # 从 Python 源文件生成 docs/source/api_doc/*.rst
make docs_auto     # 生成或补全 Python docstring，需要 hbllmutils 和本地 .llmconfig.yaml
make todos_auto    # 补 TODO 注释，需要 hbllmutils
make tests_auto    # 生成单元测试，需要 hbllmutils
make docs_auto RANGE_DIR=color AUTO_OPTIONS="--model-name deepseek-V3 --param max_tokens=200000"
```

常用 `AUTO_OPTIONS` 包括 `--param max_tokens=N`、`--model-name MODEL`、`--no-ignore-module pypindou`。
`.llmconfig.yaml` 必须保持本地 gitignored 状态，不能提交。

最佳实践：

1. 先运行 `make rst_auto` 建立 API 文档结构。
2. 审核 LLM 生成的 docstring 和代码后再提交。
3. 用 `RANGE_DIR` 对 `docs_auto`、`todos_auto`、`tests_auto` 做增量更新。
4. 生成文档和行为代码尽量分开提交。
5. 修改 public API docstring 后运行 `make docs`。

## Commit Message 规范

新增提交使用 `pyfcstm` 的 conventional commit 风格。早期中文提交属于初始化历史，不作为后续新增提交的格式参考。

- 普通提交优先使用 `type(scope): imperative summary`，例如
  `feat(pattern): add board pagination estimator`、`fix(color): preserve unidentified flags in palette filters`、
  `test(image): cover transparent alpha threshold handling`。
- `type` 使用简短小写词：`feat`、`fix`、`docs`、`test`、`refactor`、`chore`。有 scope 时也保持小写，
  例如 `pattern`、`color`、`image`、`benchmark`、`docs`、`makefile`、`ci`。
- summary 写成简洁祈使句，以小写动词开头，例如 `add`、`update`、`improve`、`align`、`clean up`；
  不要加句号。
- 只有当变更确实跨越整个仓库时才省略 scope。
- 非平凡提交添加空行和正文。正文先写一个简短概述，再用 `-` bullets 列具体行为、测试、兼容性、文档变化。
- bullet 换行时缩进续行，不要拆成新的 bullet。
- 保留标准 trailers，特别是 `Co-Authored-By: Name <email>`。
- merge commit 保持 Git/GitHub 生成风格，例如 `Merge branch 'main' into dev/...` 或
  `Merge pull request #52 from HansBug/dev/fixed`。

示例：

```text
docs(agents): add pydoc and commit guidance

Document the reST docstring style used by the project and align commit
messages with the existing HansBug Python repositories.

- add function, class, dataclass, and module docstring templates
- document inline markup boundary rules for Chinese Sphinx docs
- add conventional commit examples for pattern and color changes
```

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
