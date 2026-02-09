# Digital monography

Platform for scholars of digital humanities to publish their digital work.

The platform facilitates preparation of books. It aids in generating both traditional outcome of scholarly work (i.e. research presented in printed monographs) but also digital components unsupported by the EPUB format: data sets, multimedia contents (for example videos and photos), etc. Key elements of the publishing platform will be long-term sustainability and accessibility of the digitally published monographs. Digital books prepared with our platform are expected to stand out through integration of rich media elements, including embedded audio and visual materials. In addition, one of the core innovations of the project lies in making available tools for preparing manuscripts for publishing, including facilitating collaboration and editorial processes, automatic verification, archival, etc.

## Value proposition

What this project offers which other solutions do not provide?
* Jupyter Book does not handle manuscripts written in `.docx` files (MS Word, LibreOffice).
* EPUB and other e-book formats do not support videos, interactive maps, interactive visualisations, etc.
* Paper books can be extended with digital specific features - multimedia, code execution, etc.

## CI pipeline status

| Branch  | Status                                                                                                                                                                                                                     |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| main    | [![pipeline status](https://gitlab.com/uniluxembourg/c2dh/private/degruyter/digital-monography/badges/main/pipeline.svg)](https://gitlab.com/uniluxembourg/c2dh/private/degruyter/digital-monography/-/commits/main)       |
| develop | [![pipeline status](https://gitlab.com/uniluxembourg/c2dh/private/degruyter/digital-monography/badges/develop/pipeline.svg)](https://gitlab.com/uniluxembourg/c2dh/private/degruyter/digital-monography/-/commits/develop) |

## Materials

[Notes and materials related with the project](https://uniluxembourg-my.sharepoint.com/:f:/r/personal/pawel_kaminski_uni_lu/Documents/Digital%20Monography%20Documents?csf=1&web=1&e=YYBKgk) can be found on the University's OneDrive shared directory. Access to the directory is given upon request. Some of other important project documents include:
* [Jira board](https://degruyter.atlassian.net/jira/software/projects/TNB/boards/59);
* [concept document](https://docs.google.com/document/d/1-iBdDUBQe8O8vU5hF83HuAKAacU7xEpgUfpdi975-CM/edit?exids=71471482,71471477&tab=t.0);
* [notes from meetings related to the project](https://uniluxembourg-my.sharepoint.com/:f:/r/personal/pawel_kaminski_uni_lu/Documents/Digital%20Monography%20Documents/Meeting%20Notes?csf=1&web=1&e=Mbc9E9);
* [notes from workshop of 7th December 2023](https://docs.google.com/document/d/1DniLbpg7pNBygPI1s-L6i6DjEW4tjvXVBhYtyFm1wyg/edit?tab=t.0);
* [author's guidelines for drafting manuscripts](https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com/read/guidelines-for-drafting-manuscripts/index.html).

The development cycle is based on release cycles 4 months each. The direction of development is coordinated with project's partners during monthly meetings.

## Technical documentation

- [Architecture](./docs/01_architecture/index.md)
- [Pipeline details](./docs/02_pipeline-details/index.md)
- [Development](./docs/03_development/index.md)
- [Infrastracture setup](./docs/04_infra-setup/index.md)
- [Jupyter Book](./docs/05_jupyter-book/index.md)
- [Software composition analysis](./docs/06_audit/index.md)
