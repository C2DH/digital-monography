import nbformat

from src.preparer.ipynb_prep import tags_to_myst_crossref_targets


class TestTagsToMySTtargets:
    @classmethod
    def setup_class(cls):
        cls.nbnode = nbformat.from_dict(
            {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "id": "8731951e",
                        "metadata": {
                            "editable": True,
                            "slideshow": {"slide_type": ""},
                            "tags": ["heading-title"],
                        },
                        "source": ["# Chapter title"],
                    },
                ],
                "metadata": {
                    "celltoolbar": "Tags",
                    "kernelspec": {
                        "display_name": "Python 3 (ipykernel)",
                        "language": "python",
                        "name": "python3",
                    },
                    "language_info": {
                        "codemirror_mode": {"name": "ipython", "version": 3},
                        "file_extension": ".py",
                        "mimetype": "text/x-python",
                        "name": "python",
                        "nbconvert_exporter": "python",
                        "pygments_lexer": "ipython3",
                        "version": "3.10.12",
                    },
                },
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        tags_to_myst_crossref_targets(cls.nbnode)

    def test_heading_crossref_target(self):
        assert len(self.nbnode.cells[0]["source"]) == 2
        assert self.nbnode.cells[0]["source"][0] == "(heading-title)=\n"
        assert self.nbnode.cells[0]["source"][1] == "# Chapter title"
