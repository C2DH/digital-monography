import pathlib

from src.preparer.state import DocumentState
from src.preparer.constants import MediumEnum
from src.preparer.keys import KeyPath
from src.preparer.models import Asset


class TestDocumentState:

    @classmethod
    def setup_class(cls):
        cls.doc_state = DocumentState(key=KeyPath("foo/bar/1.docx"))
        cls.asset1 = Asset(
            fp=pathlib.PosixPath("foo/bar/1.txt"),
            metadata_table="0a7bf8c-0a7b-4b8c-0a7b-f8c0a7bf8c0a",
            medium=MediumEnum.PAPER,
            slug="slug",
            author="author",
            source="source",
            location=KeyPath("foo/bar/1.docx"),
            alttext="alttext",
            caption="caption",
            comments="comments",
            target="target",
            is_color=True,
            is_ready=False,
        )
        cls.asset2 = Asset(
            fp=pathlib.PosixPath("foo/bar/2.txt"),
            metadata_table="",
            medium=MediumEnum.DIGITAL,
            slug="slug",
            author="author",
            source="source",
            location=KeyPath("foo/bar/2.docx"),
            alttext="alttext",
            caption="caption",
            comments="comments",
            target="target",
            is_color=True,
            is_ready=False,
        )
        cls.doc_state.add(cls.asset1)
        cls.doc_state.add(cls.asset2)

    def test_metadata(self):
        assert self.doc_state.metadata.key == KeyPath("foo/bar/1.docx")
        assert self.doc_state.metadata.slug == "foo"
        assert self.doc_state.metadata.word_count == 0
        assert self.doc_state.metadata.char_count == 0

    def test_to_json_from_json(self):
        data = self.doc_state.to_dict()
        new_state = DocumentState(key=KeyPath("foo/bar/1.docx"))
        new_state.from_dict(data)
        assert new_state.metadata.key == KeyPath("foo/bar/1.docx")
        assert new_state.metadata.slug == "foo"
        assert new_state.metadata.word_count == 0
        assert new_state.metadata.char_count == 0
        asset1: Asset = new_state.get("assets", self.asset1.pk)
        assert asset1.fp == pathlib.PosixPath("foo/bar/1.txt")
        assert asset1.metadata_table == "0a7bf8c-0a7b-4b8c-0a7b-f8c0a7bf8c0a"
        assert asset1.medium == MediumEnum.PAPER
        assert asset1.location == KeyPath("foo/bar/1.docx")
        assert asset1.alttext == "alttext"
        asset2: Asset = new_state.get("assets", self.asset2.pk)
        assert asset2.fp == self.asset2.fp
        assert asset2.metadata_table == self.asset2.metadata_table
        assert asset2.medium == self.asset2.medium
        assert asset2.location == self.asset2.location
