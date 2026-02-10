# Jupyter Book

## Jupyter Book v2

The project was written with Jupyter Book v1 in mind. However, on 3rd November 2025 Jupyter Book v2 was released. This was a complete re-write and move to mystmd ecosystem.

Jupyter Book is a series of open-source workflows and code that anyone can use to build a “living,” digital textbook. It is the software that we use for building a static website out of manuscripts.

Jupyter Book v1 (further refered to as "JB1" or "v1") was adding Jupyter Notebook integration to the [Sphinx documentation generator](https://github.com/sphinx-doc/sphinx). With time, the maintainers devoted more and more time to Jupyter Book v2 (further "JB2" or "v2"). JB2 is a complete re-write of the project, so migration from JB1 to JB2 is a non-trivial task.

## Clarification on the naming

It is difficult to express this issue in part due to unclear naming. Few definitions to clarify:

| Name | Description |
| ---- | ----------- |
| MyST | Extension of markdown syntax. Made by Executable Book Project, made for handling features useful for books, like references, footnotes, admonitions, glossaries, etc. |
| MyST.md (mystmd or myst.md) | Software of similar purpose as JupyterBook v1 (similar functionalities) but written in TypeScript. Works well with hosting services sold by Curvenote Inc. |
| myst-cli | npm package for MyST.md |
| mystjs | Development fork of MyST.md created by Curvenote Inc. |

Also, it is imporant to understand the difference between Jupyter Notebook and Jupyter Book.

| Name | Description |
| ---- | ----------- |
| Jupyter Notebook | Jupyter Notebook can colloquially refer to two different concepts, either the user-facing application to edit code and text (this is the editor you edit your code in), or the underlying file format which is interoperable across many implementations (".ipynb" files). |
| Jupyter Book | Open-source tool for building publication-quality books from MyST markdown files and .ipynb files. |

## Background

JB2 and mystmd are being developed mainly by contributors from two companies: [Curvenote](https://curvenote.com/) and [2i2c](https://2i2c.org/). To quote the [documentation](https://web.archive.org/web/20250219074454/https://mystmd.org/guide/deployment): “MyST was designed to be deployed as an application” with MyST server underneath and not as a static site with services underneath (which is how our book project is made). “At present, only Curvenote provides out-of-the-box support for deployment of MyST websites”. As a result, I found it difficult to use JB2 to build static websites that would work on AWS S3.

### Problems with migration to JB2

#### Python vs TypeScript

First, it is important to note the JB2 is just a thin wrapper around myst.md, which is written in TypeScript. I see 2 ways to use both Python and TypeScript in the `builder` service:
* use Python+TS Docker container,
* split the `builder` into multiple services, e.g. `pre-builder` (Python), `builder` (TS) and `post-builder` (Python).

#### Static websites with JB2

When built with `myst build --html` the output cannot be simply uploaded to S3 as a static website. This would result in `TypeError: Cannot read properties of undefined (reading 'handle')` error. Without deeper research this seems like a chunking error (JB2 uses [esbuild](https://esbuild.github.io/api/#splitting) for chunking), which could indicate some deeper issues.

To work properly, the build output needs to be served with [Vercel's serve repo](https://github.com/vercel/serve), e.g. `npx serve _build/html`. This creates a need of some compute capabilities behind static websites, which S3 does not have. A solution may be to use one of the providers that supports this solution, for example:
* [Netlify](https://mystmd.org/guide/deployment-netlify),
* [GitHub Pages](https://mystmd.org/guide/deployment-github-pages).

An alternative solution might be to fork myst.md and try to replace all features that require a server with neutral ones.

<!-- 1. install node.js v 20
1. npm install mystmd
1. myst build --html
1. create myst.yml config file (different from v1)
1. copy _build/html to s3 bucket -->
