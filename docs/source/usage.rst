使用
====

生成偏实操的干净图纸：

.. code-block:: python

    from pypindou import generate_pattern

    pattern = generate_pattern(
        "input.png",
        palette="mard-221-alfonse-doudou",
        width=58,
        height=58,
        fit="cover",
        max_colors=32,
        prefilter="smooth",
        cleanup="majority",
        cleanup_passes=2,
        min_region_size=3,
    )

    print(pattern.color_counts())
    pattern.to_image(scale=12).save("preview.png")
    pattern.to_symbol_image(cell_size=24).save("symbols.png")

照片输入建议先控制颜色数量，再用清理参数减少孤立色块。`prefilter="smooth"` 会先弱化照片噪声，
`cleanup="majority"` 和 `min_region_size` 会让输出更接近可手工摆豆的大色块图纸。

如果更重视照片纹理，可以显式启用 Floyd-Steinberg 抖动：

.. code-block:: python

    pattern = generate_pattern(
        "input.png",
        width=58,
        height=58,
        max_colors=48,
        quantize="floyd-steinberg",
        dither_strength=0.5,
    )

抖动会增加细碎色块，适合保留渐变和阴影纹理，不建议作为默认实操图纸参数。

色卡资源由 git submodule 生成：

.. code-block:: bash

    git submodule update --init --recursive
    make resource
