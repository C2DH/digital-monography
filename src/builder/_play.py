import json
import pathlib
import typing as t
from metadata import DocumentMetadata, RefDatapoint, TargetDatapoint


with open("/tmp/efs/small-links/_metadata/file_ref.json", "r") as f:
    md_r = DocumentMetadata()
    md_r.from_json(json.load(f))
    # fn = "./file_target.md"  # note "./" and ".md"
    # f2f_r = next(r for r in md_r.refs if r.href == fn + "#f-file-target-heading-t")
    # inf_r = next(r for r in md_r.refs if r.href == "#f-file-ref-heading-within-this")
    # inf_t = next(t for t in md_r.targets if t.pk == "f-file-ref-heading-within-this")


with open("/tmp/efs/small-links/_metadata/file_target.json", "r") as f:
    md_t = DocumentMetadata()
    md_t.from_json(json.load(f))
    # f2f_t = next(t for t in md_t.targets if t.pk == "f-file-target-heading-t")


# book_path = pathlib.Path("/tmp/efs/small-links")
book_path = pathlib.Path("/tmp/efs/hermeneutics-of-practice")
multidocs_meta: dict[pathlib.PurePath, DocumentMetadata] = {}
targets: dict[str, tuple[pathlib.PurePath, TargetDatapoint]] = {}
# for fp in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
for fp in (book_path / "_metadata").glob("**/*.json"):
    fn = fp.relative_to(fp.parent).with_suffix(".md")
    multidocs_meta[fn] = DocumentMetadata(fn)
    with open(fp, "r") as f:
        multidocs_meta[fn].from_json(json.load(f))
    for target in multidocs_meta[fn].targets:
        target: TargetDatapoint
        targets[target.pk] = (fn, target)

i = 0
for fn, md in multidocs_meta.items():
    for ref in md.refs:
        i += 1
        ref: RefDatapoint
        # 1. if href is external, perform verification
        if ref.href.startswith("http"):
            print(i, "External link:", ref.href)
        # 2. if href points to the same doc, check targets of this file
        elif ref.href.startswith("#"):
            t = targets.get(ref.href[1:])
            print(i, "In-file link:", ref.href, t)
        # 3. if href points to another doc, check targets of that file
        elif "#" in ref.href:
            target_fn, fragment = ref.href.split("#")
            t = targets.get(fragment)
            print(i, "Cross-file link:", ref.href, t)
        else:
            print(i, "Unknown link:", ref.href)
        # print(ref)


# TODO: add filename in RefDatapoint and TargetDatapoint cls
