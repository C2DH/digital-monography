# References and Targets

This document explains references and targets 
as produced in docx 

There are two types of references in Microsoft Word, which we use:
* cross-references,
* links.

Certain elements can be standalone targets of references, while others must have
a bookmark that will be referenced. The self-referable elements include, among others:
* headings,
* equations,
* figures,
* tables.

compliant with
Jupyter Book v2 (mystmd) specification.
See: https://mystmd.org/guide/cross-references


# Refs in docx/html




# Refs in MyST docs

## Links
### Default links
[My text](#target)

### Using myst autonumbering and names
[Sec. %s](#targeting-headers)
[Section "{name}"](#targeting-headers)

### Links to files
[](./citations.md)

### External refs to other
[Admonition](xref:spec#admonition)

## MyST roles
https://mystmd.org/guide/cross-references#reference-roles

# Targets in MyST docs
To be targeted the content must have a label.

## Directive Targets
Not implemented.

## Header Targets
```
(my-section)=
#### Header _Targets_
```

## Label Anything
```
(my-paragraph)=
This is just a paragraph!
Please see [this paragraph](#my-paragraph) and [these points](#my-points).
```

## Notebook Cell Targets
Not implemented yet.



PRE_REFS_HTML
```html
<p>In the same file: Link to <a href="#_Heading">direct heading</a> and to <a href="#a_heading">bookmark heading</a>.
    Cross-reference to <strong><a href="#_Ref177042490">Figure 1</a></strong> and to <a href="#_Ref177044323">Table
        1</a>.</p>
<p>In a separate file: Links to <a href="02_b.docx#h2Subheading">Heading</a>, <a href="02_b.docx#figRedSquare">Figure
        [auto]</a>, and to <a href="02_b.docx#tblSimpleTable">Table [auto]</a>.</p>
<p>Footnote<sup><a href="#footnote-1" id="footnote-ref-1">[1]</a></sup> without links. Start footnote<sup><a
            href="#footnote-2" id="footnote-ref-2">[2]</a></sup>. Middle footnote<sup><a href="#footnote-3"
            id="footnote-ref-3">[3]</a></sup>. End footnote<sup><a href="#footnote-4" id="footnote-ref-4">[4]</a></sup>.
```

POST_REFS
```md
In the same file: Link to [direct heading](#f-01-a-heading) and 
to [bookmark heading](#f-01-a-a-heading). 
Cross-reference to **[Figure {{ f01aref177042490 }}](#f-01-a-ref177042490)** and 
to [Table {{ f01aref177044323 }}](#f-01-a-ref177044323).

In a separate file: Links to [Heading](./02_b.md#f-02-b-h2subheading), 
[Figure {{ 02bdocxf02bfigredsquare }}](./02_b.md#f-02-b-figredsquare), and to 
[Table {{ 02bdocxf02btblsimpletable }}](./02_b.md#f-02-b-tblsimpletable).

Footnote[^footnote-ref-fn-01-a-1] without links. 
Start footnote[^footnote-ref-fn-01-a-2]. 
Middle footnote[^footnote-ref-fn-01-a-3]. 
End footnote[^footnote-ref-fn-01-a-4].
```

PRE_TARGETS
```html
<h1>Hyperlinks A</h1>
<h2>
    <a id="_Heading"></a>
    <a id="a_heading"></a>
    Heading
</h2>
<p class="dgt-mon-caption">
    <a id="_Ref177042490"></a>
    <strong>Figure <data value=" SEQ Figure \* ARABIC ">1</data>:</strong> Image.
</p>
<p><img alt="The Alt Text"
    src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAAXNSR0IArs4c6QAAAAlwSFlzAAAOvgAADr4B6kKxwAAAABNJREFUKFNj/M+ADzDhlWUYqdIAQSwBE8U+X40AAAAASUVORK5CYII=" />
</p>
<ol>
    <li id="footnote-1">
        <p> Standard footnote without links. <a href="#footnote-ref-1">↑</a></p>
    </li>
    <li id="footnote-2">
        <p> <a href="https://web.archive.org/web/20250101004557/http:/example.com/">Footnote link to an external
                website</a> <a href="#footnote-ref-2">↑</a></p>
    </li>
    <li id="footnote-3">
        <p> There is a <a href="https://web.archive.org/web/20250101004557/http:/example.com/">footnote link</a> in the
            middle. <a href="#footnote-ref-3">↑</a></p>
    </li>
    <li id="footnote-4">
        <p> Link at the <a href="https://web.archive.org/web/20250101004557/http:/example.com/">end of the footnote.</a>
            <a href="#footnote-ref-4">↑</a>
        </p>
    </li>
</ol>
```

POST_TARGETS
```md
# Hyperlinks A

(f-01-a-heading)=
(f-01-a-a-heading)=
## Heading

(f-01-a-ref177042490)=
**Figure {{ f01aref177042490 }}:** Image.
![The Alt Text](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAAXNSR0IArs4c6QAAAAlwSFlzAAAOvgAADr4B6kKxwAAAABNJREFUKFNj/M+ADzDhlWUYqdIAQSwBE8U+X40AAAAASUVORK5CYII=)

[^footnote-ref-fn-01-a-1]:  Standard footnote without links. 
[^footnote-ref-fn-01-a-2]:  [Footnote link to an external website](https://web.archive.org/web/20250101004557/http:/example.com/) 
[^footnote-ref-fn-01-a-3]:  There is a [footnote link](https://web.archive.org/web/20250101004557/http:/example.com/) in the middle. 
[^footnote-ref-fn-01-a-4]:  Link at the [end of the footnote.](https://web.archive.org/web/20250101004557/http:/example.com/) 
```
