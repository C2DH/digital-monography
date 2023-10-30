# Markdown guidelines

## Introduction

### What is Markdown

> Markdown is a plain text format for writing structured documents [...] The overriding design goal for Markdown’s formatting syntax is to make it as readable as possible. The idea is that a Markdown-formatted document should be publishable as-is, as plain text, without looking like it’s been marked up with tags or formatting instructions.

### Markdown's variant

The project supports MyST markdown, which is a superset of the CommonMark, a variant of the Markdown markup language. 

### This document

This document is meant as guidelines of features supported by our tool. It mostly repeats after the original specifiactions for [CommonMark](https://spec.commonmark.org/) and [MyST](https://github.com/executablebooks/myst-spec). Please treat the original specifications as an ultimate source of truth and this document as a way of facilitating user experience with our tool.

## Main features

### Headers

```
# Chapter 1 title
## Chapter 1 second header
### Chapter 1 third header
#### Chapter 1 section title
##### Chapter 1 section second header
```

# Chapter 1 title
## Chapter 1 second header
### Chapter 1 third header
#### Chapter 1 section title
##### Chapter 1 section second header

More than six `#` characters is not a heading.

For more details please read [the specification](https://spec.commonmark.org/0.30/#atx-heading). It might be also useful to read ["how headers and sections map onto to book structure"](https://jupyterbook.org/en/stable/structure/sections-headers.html#how-headers-and-sections-map-onto-to-book-structure).

### Emphasis

#### Italics

```
To write in italics, use single *asterisks* or _underscores_.
```

To write in italics, use single *asterisks* or _underscores_.

#### Bold

```
You can make text bold with double **asterisks** or __underscores__.
```

You can make text bold with **asterisks** or __underscores__.

#### Strikethrough

```
Strikethrough with ~~two tildes~~.
```

Strikethrough with ~~two tildes~~.

#### Escaping symbols

```
Sometimes you might want to use \*asterisks\*, \_\_underscores\_\_, \~\~tildes\~\~, etc. without special formatting. To do this, place the backslash (`\`) before a special character.
```

Sometimes you might want to use \*asterisks\*, \_\_underscores\_\_, \~\~tildes\~\~, etc. without special formatting. To do this, place the backslash (`\`) before a special character.

#### Subscript

```
H{sub}`2`O
```

H{sub}`2`O

#### Superscript

```
11{sup}`th` of November
```

11{sup}`th` of November

### Lists

# TODO

### Links

#### Links to external resources

```
You can just paste a link to an external resource, e.g. to https://spec.commonmark.org/0.30/#links
```

You can just paste a link to an external resource, e.g. to https://spec.commonmark.org/0.30/#links

```
You can include a link with a [link text](https://spec.commonmark.org/0.30/#link-text) and a hidden link destination
```

You can include a link with a [link text](https://spec.commonmark.org/0.30/#link-text) and a hidden link destination

#### Links to internal resources

You can also have a link to a specified part of your work.

For example, let us assume that your book comprises of two chapters that are located on the same level of a directory:

```
/contents/
├── chapter_1.md
└── chapter_2.md
```

Then in your `chapter_1.md` file you can include a [link](./chapter_2.md) to a `chapter_2.md`.

### Multimedia

#### Images

You can embed an image by linking to an image file.

```
![Logo of the University](./img/university_of_luxembourg_logo_fr.svg)
```

![Logo of the University](./img/university_of_luxembourg_logo_fr.svg)

A common use case is to add a caption under an image. You can even include a hyperlink to better describe the cited resource. Note that we can use the [cross-reference syntax]() to have an auto-incremented figure number.

```
![Logo of the University](./img/university_of_luxembourg_logo_fr.svg)Figure 1: logo of the University from the [wikipedia page](https://en.wikipedia.org/wiki/File:University_of_Luxembourg_logo_(fr).svg).
```

![Logo of the University](./img/university_of_luxembourg_logo_fr.svg)Figure 1: logo of the University from the [wikipedia page](https://en.wikipedia.org/wiki/File:University_of_Luxembourg_logo_(fr).svg).

#### Using directives to format your image <sup>(MyST feature)</sup>

The `image` directive allows you to customize:
* `width`
* `alignment`
* `classes` to add to the image

What is important, using MyST directives allows us to cross-reference our images within the content. This feature ensures that we won't have to manually increment references - the software will do that for us automatically. To enable cross-referencing, add a `label` attribute to a `{image}` directive with a name that you will use to reference the image (here: myst-img-example).

```{image} https://source.unsplash.com/random/500x150?sunset
:label: myst-img-example
:width: 500px
:align: center
```

To reference this image [](#myst-img-example), use `[](#myst-img-example)` syntax.

See the [MyST guide](https://mystmd.org/guide/figures#image-directive) for the implementation details.

#### Videos

# TODO
<!-- [![Alternate Text]({image-url})]({video-url} "Link Title") -->

#### YouTube/Vimeo videos <sup>(MyST feature)</sup>

If your video is hosted on one of supported platforms (at the time of writing of this document: on YouTube and on Vimeo) you can embed the video using the url. Please read the [MyST guide](https://mystmd.org/guide/figures#youtube-videos) for more details.

### Footnotes <sup>(MyST feature)</sup>

```
Using MyST[^ref-to-footnotes] variant enables us to use footnotes in our markdown files.

[^ref-to-footnotes]: Please note the syntax of the footnotes. `My content.[^some-text]` in your content's body and `[^some-text]: Footnote.` after it.
```

Using MyST[^ref-to-footnotes] variant enables us to use footnotes in our markdown files.

[^ref-to-footnotes]: Please note the syntax of the footnotes. `My content.[^some-text]` in your content's body and `[^some-text]: Footnote.` after it.

See the [the MyST guide](https://mystmd.org/guide/typography#footnotes) for more details.

### Tables <sup>(MyST feature)</sup>

#### Markdown tables <sup>(MyST feature)</sup>

For tables, MyST uses the [GitHub Markdown syntax](https://github.github.com/gfm/#tables-extension-).

To add a table, use three or more hyphens (`---`) to create each column’s header, and use pipe characters (`|`) to separate each column. You should also add a pipe character on the start and the end of each row.

```
| Header 1        | Header 2        |
| --------------- | --------------- |
| Row 1, Column 1 | Row 1, Column 2 |
| Row 2, Column 1 | Row 2, Column 2 |
```

| Header 1        | Header 2        |
| --------------- | --------------- |
| Row 1, Column 1 | Row 1, Column 2 |
| Row 2, Column 1 | Row 2, Column 2 |

You don't have to be strict with formatting the table, as long as you use the proper syntax. For example, the following table will be rendered the same as the one above.

```
| Header 1| Header 2 |
| --- | -------- |
| Row 1, Column 1 | Row 1, Column 2 |
| Row 2, Column 1 | Row 2, Column 2 |
```

| Header 1| Header 2 |
| --- | -------- |
| Row 1, Column 1 | Row 1, Column 2 |
| Row 2, Column 1 | Row 2, Column 2 |


You can also align text in the columns by adding a colon (`:`) to the hyphens:
* `:---` - align left
* `:---:` - center
* `---:` - align right

```
| Align left | Center | Align right |
| :---       | :---:  | ---:        |
| Text       | Text   | Text        |
```

| Align left | Center | Align right |
| :---       | :---:  | ---:        |
| Text       | Text   | Text        |

#### CSV tables <sup>(MyST feature)</sup>

```{csv-table} Example of a csv table
:widths: 5, 15, 5, 5, 5
:align: "center", "left", "right", "right", "right"
:header: 1
:file: ./csv/csv-example.csv
```

### Horizontal Rule

# TODO

### Line Breaks

# TODO

### Container blocks

#### Block quotes

```
> You can insert a block of text separate from the rest of the page with a use of the `> ` syntax.
```

> You can insert a block of text separate from the rest of the page with a use of the `> ` syntax.

```
> You **can** also use *markdown* in your block quotes.
> 
> In addition,
> > you can also nest your block.
> 
> use `-` character to specify the author of a given quote.
> - Author Unknown
```

> You **can** use *markdown* in your block quotes.
> 
> In addition,
> > you can nest your block.
> 
> use `-` character to specify the author of a given quote.
> - Author Unknown

See the details in the [CommonMark specification](https://spec.commonmark.org/0.30/#block-quotes).

#### Admonitions <sup>(MyST feature)</sup>

> Admonitions highlight a particular block of text that exists slightly apart from the narrative of your page, such as a note or a warning.

```
:::{tip} _Title_ of the block
Block of text that is separated from the rest of the page.
:::
```

See the [MyST guide](https://mystmd.org/guide/admonitions) for the implementation details.

### Math <sup>(MyST feature)</sup>

MyST syntax derives from the $\hologo{LaTeX}$. To get started with the math syntax, please see the [documentation](https://www.latex-project.org/help/documentation/).
See the [MyST guide](https://mystmd.org/guide/math) for more details on the MyST implementation.

#### Inline math <sup>(MyST feature)</sup>

The most famous equation is {math}`e=mc^2`.

#### Equation blocks <sup>(MyST feature)</sup>

```{math}
:label: euler-identity-equation
e^{i\pi}+1 =0
```

#### Dollar math equation <sup>(MyST feature)</sup>

$$
\label{maxwell}
\begin{aligned}
\nabla \times \vec{e}+\frac{\partial \vec{b}}{\partial t}&=0 \\
\nabla \times \vec{h}-\vec{j}&=\vec{s}\_{e}
\end{aligned}
$$

$$ \label{one-liner} Ax=b $$

#### Referencing equations <sup>(MyST feature)</sup>

Similarily to cross-referencing images, we can use `label` attribute to reference an equation and reference it [](#euler-identity-equation) in our book/article using the `[](#euler-identity-equation)` syntax.

We can even reference a specific equation [](#maxwell) (or [](#one-liner)) in a set of equations.

#### Proofs, Theorems and Algorithms <sup>(MyST feature)</sup>

Please see the [documentation](https://mystmd.org/guide/proofs-and-theorems) on the additional syntax for proofs, theorems and algorithms.

### Diagrams <sup>(MyST feature)</sup>

It is possible include [mermaid diagrams](https://mermaid.js.org/) in your book/article. For the time of writing this guidelines, the supported diagrams include
* flowcharts
* sequence diagrams
* class diagrams
* state diagrams
* entity relationship diagrams
* user journey diagrams
* Gantt
* pie charts
* quadrant charts
* requirement diagram
* Gitgraph (Git) diagrams
* C4 diagrams
* mindmaps
* timeline
* Zenuml
* Sankey
* XYCharts

To include the mermaid diagrams, use the `{mermaid}` directive.

Be sure to check the [mermaid documentation](https://mermaid.js.org/intro/getting-started.html) and the [MyST guide](https://mystmd.org/guide/diagrams) for the more information.

### Citations <sup>(MyST feature)</sup>

One of the requirements for a publication in this system is inclusion of a bibliography writen in the BibTeX syntax. We highly recommend managing your bibliographies using the [Zotero tool](https://www.zotero.org/), exporting `.bib` file and uploading this file alongside the rest of your book/article.

To cite your sources, use the syntax @author. Here are some ways in which you may want to format your citations (remember to follow the publisher guidelines and to stay consistent):

| Example | Render | Note |
|---|---|---|
| @Someone | @Someone | Citation without brackets |
| [@Someone] | [@Someone] | Citation with brackets (**recommended**) |
| [@Someone; @SthElse2020] | [@Someone; @SthElse2020] | Multiple citations |
| [@Someone, p. 100] | [@Someone, p. 100] | Page number as a suffix example |
| [@Someone, chap. 2] | [@Someone, chap. 2] | Chapter as a suffix example |
| [e.g. @Someone, p. 100; @SthElse2020] | [e.g. @Someone, p. 100; @SthElse2020] | Example of 'e.g.' prefix |

For more information, see the [MyST guide](https://mystmd.org/guide/citations).

### Glossaries, Terms and Abbreviations

:::{glossary}
Some term
: some term that need to be defined.

Definiendum
: an expression that is being defined.
:::

A use of glossaries enables us to reference certain terms in our books/articles.For example, we can now reference {term}`definiendum`.

Please see the [MyST guide](https://mystmd.org/guide/glossaries-and-terms) on how to create a glossary.

### Interactive notebooks (code blocks)

# TODO

https://mystmd.org/guide/interactive-notebooks
https://mystmd.org/guide/reuse-jupyter-outputs
https://mystmd.org/guide/integrating-jupyter

## Disclaimer

This guidelines were prepared in Q4 2023 for CommonMark v0.30 and MyST v0.0.4. and are up to date as of the date of writing of this document. The guidelines herein and the Markdown specification is provided "as is", without warranty of any kind, express or implied.