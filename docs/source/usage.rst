Usage
=====

Generate a pattern:

.. code-block:: python

    from pypindou import generate_pattern

    pattern = generate_pattern(
        "input.png",
        palette="mard-221-alfonse-doudou",
        width=58,
        height=58,
        max_colors=48,
    )

    print(pattern.color_counts())
    pattern.to_image(scale=12).save("preview.png")

Palette resources are generated from git submodules:

.. code-block:: bash

    git submodule update --init --recursive
    make resource

