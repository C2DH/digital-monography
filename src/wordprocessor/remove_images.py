import docx.document
import docx.oxml.drawing
import docx.oxml.text.paragraph
import docx.oxml.text.run


def remove_images(doc: docx.document.Document) -> None:
    """
    Find "drawing" objects and remove the whole paragraph if it contains only one
    run. Else, remove the run containing the drawing object.
    ```
    <w:p>
        <w:pPr>
            <w:pStyle w:val="BodyText"/>
            <w:jc w:val="both"/>
        </w:pPr>
        <w:r>
            <w:rPr>
                <w:noProof/>
            </w:rPr>
            <w:drawing>
                ...
            </w:drawing>
        </w:r>
    </w:p>
    ```
    """
    for drawing in doc.element.xpath(".//w:drawing"):
        # TODO
        print("Why drawing doesn't have getparent() method?")
        print("type(drawing)", type(drawing))
        assert isinstance(drawing, docx.oxml.drawing.CT_Drawing)
        r_elem = drawing.getparent()
        assert isinstance(r_elem, docx.oxml.text.run.CT_R)
        p_elem = r_elem.getparent()
        assert isinstance(p_elem, docx.oxml.text.paragraph.CT_P)
        if len(p_elem.r_lst) == 1:
            p_parent = p_elem.getparent()
            # TODO
            print("TODO: CHeck type of p_parent")
            print("type(p_parent)", type(p_parent))
            p_parent.remove(p_elem)
            p_elem._p = None
            p_elem._element = None
        else:
            p_elem.remove(r_elem)
            r_elem._element = None
