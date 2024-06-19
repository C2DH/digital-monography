import markdown_it
import markdown_it.tree
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.myst_blocks import myst_block_plugin
from mdit_py_plugins.myst_role import myst_role_plugin

import typing as t

text = "# Book Title\n\n## Heading 2\n\nThis is an index of the book.\n\n:::{important}   \nAdmonition example.  \n:::\n\n### Heading 3\n\nMore content.\n\n> Block quote example.\n#### Heading 4\n\nEven more content. An example ofan image is placed below.\n"


def parse():
    parser = (
        markdown_it.MarkdownIt("commonmark")
        .enable("table")
        .use(front_matter_plugin)
        .use(myst_block_plugin)
        .use(myst_role_plugin)
        # we only need to parse block level components (for efficiency)
        .disable("inline", True)
    )
    tokens = parser.parse(text)
    tree = markdown_it.tree.SyntaxTreeNode(tokens)
    _recurse(tree)


def _recurse(node: t.Optional[markdown_it.tree.SyntaxTreeNode]) -> None:
    if node is None:
        return
    for child in node.children:
        if _is_heading(child):
            _verif_atomic_heading(child)
        else:
            print("child.attrs", child.attrs)
            print("child.content", child.content)
            print("child.markup", child.markup)
            print("child.meta", child.meta)
            print("child.tag", child.tag)
            print("child.type", child.type)
        _recurse(child)


def _is_heading(node: markdown_it.tree.SyntaxTreeNode) -> bool:
    pass


def _verif_atomic_heading(node):
    pass
