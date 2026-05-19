"""
Auto-generate RST documentation top index for Python projects.

This module provides functionality to automatically create top-level index files
in reStructuredText format for a Python project's API documentation. It scans a
project directory for Python modules and packages, then generates toctree
directives that can be used in Sphinx documentation.

The generated index includes all Python packages (directories with __init__.py)
and standalone Python modules (excluding __init__.py and other dunder files).

Supports generating both English and Chinese versions of the API documentation index.
"""

import argparse
import os

from natsort import natsorted


def generate_rst_index(input_dir, output_file, title):
    """
    Generate a single RST index file with a titled toctree.

    :param input_dir: Input Python project directory to scan
    :type input_dir: str
    :param output_file: Output RST documentation index file path
    :type output_file: str
    :param title: Section title shown before the toctree
    :type title: str
    """
    rel_names = []
    for name in os.listdir(input_dir):
        item_path = os.path.join(input_dir, name)
        # Check if it's a package (directory with __init__.py) or a standalone module
        if (os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, '__init__.py'))) or \
                (os.path.isfile(item_path) and name.endswith('.py') and not name.startswith('__')):
            if name.endswith('.py'):
                # Remove .py extension for modules
                rel_names.append(os.path.splitext(name)[0])
            else:
                # Keep directory name for packages
                rel_names.append(name)

    # Sort names naturally (e.g., module1, module2, module10)
    rel_names = natsorted(rel_names)

    # Write the titled RST toctree to output file
    with open(output_file, 'w') as f:
        print(f'{title}', file=f)
        print(f'-------------------------', file=f)
        print(f'', file=f)
        print(f'.. toctree::', file=f)
        print(f'    :maxdepth: 2', file=f)
        print(f'    :caption: {title}', file=f)
        print(f'    :hidden:', file=f)
        print(f'', file=f)
        for name in rel_names:
            # Packages get /index suffix, modules don't
            if os.path.exists(os.path.join(input_dir, name, '__init__.py')):
                print(f'    api_doc/{name}/index', file=f)
            else:
                print(f'    api_doc/{name}', file=f)
        print(f'', file=f)
        for name in rel_names:
            if os.path.exists(os.path.join(input_dir, name, '__init__.py')):
                print(f'* :doc:`api_doc/{name}/index`', file=f)
            else:
                print(f'* :doc:`api_doc/{name}`', file=f)
        print(f'', file=f)


def main():
    """
    Main entry point for the RST documentation index generator.

    This function parses command-line arguments, scans the input directory for
    Python modules and packages, and generates RST files with toctree directives
    containing all discovered items in natural sorted order.

    The function identifies:
    - Python packages: directories containing __init__.py
    - Python modules: .py files that don't start with '__'

    Command-line arguments:
        -i, --input_dir: Input Python project directory to scan
        -o, --output_dir: Output directory for RST documentation index files

    Example::
        >>> # Command line usage
        >>> python script.py -i ./my_project -o ./docs/source
        # Generates api_doc_en.rst and api_doc_zh.rst files
    """
    parser = argparse.ArgumentParser(description='Auto create rst docs top index for project')
    parser.add_argument('-i', '--input_dir', required=True, help='Input python project directory')
    parser.add_argument('-o', '--output_dir', required=True, help='Output directory for rst doc index files')
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate English version
    output_en = os.path.join(args.output_dir, 'api_doc_en.rst')
    generate_rst_index(args.input_dir, output_en, 'API Documentation')
    print(f'Generated: {output_en}')

    # Generate Chinese version
    output_zh = os.path.join(args.output_dir, 'api_doc_zh.rst')
    generate_rst_index(args.input_dir, output_zh, 'API 文档')
    print(f'Generated: {output_zh}')


if __name__ == '__main__':
    main()
