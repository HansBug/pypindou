pypindou.color.model
========================================================

.. currentmodule:: pypindou.color.model

.. automodule:: pypindou.color.model


RGB
-----------------------------------------------------

.. autodata:: RGB


BeadColor
-----------------------------------------------------

.. autoclass:: BeadColor
    :members: __post_init__,to_dict,code,rgb,name,hex,group,source,unidentified,original_code,metadata


Palette
-----------------------------------------------------

.. autoclass:: Palette
    :members: __post_init__,size,by_code,filter,to_dict,id,title,colors,description,source,metadata


rgb\_to\_hex
-----------------------------------------------------

.. autofunction:: rgb_to_hex


hex\_to\_rgb
-----------------------------------------------------

.. autofunction:: hex_to_rgb


