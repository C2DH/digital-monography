# Software composition analysis

## Generating Software Bill of Materials

Below are the instructions used to generate Software Bill of Materials (SBOM). The commands start from the project root.

### Python

```sh
python --version # 3.12.1
python -m venv .sbom
source .sbom/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt 
python -m pip freeze > sbom-req.txt
python -m pip install sbom4python
sbom4python -r sbom-req.txt -o sbom-out.tags
```

See [`sbom-out.tags`](./sbom-out.tags) for Python SBOM.

### JS/TS

Dashboard was written in JavaScript/TypeScript. Two experimental versions exist, among which the final dashboard will be selected:
* [React + Bootstrap + Next.js](../../staticws/dashboard/)
* [Flask html templates + Tailwindcss + htmx](../../src/dashboard/)

#### React + Bootstrap + Next.js

```sh
cd staticws/dashboard/
npm install
cp package.json ../../docs/06_soft-composition/package.json
cp package-lock.json ../../docs/06_soft-composition/package-lock.json
```

See [`package.json`](./package.json) and [`package-lock.json`](./package-lock.json) for JavaScript SBOM.

#### Flask html templates + Tailwindcss + htmx

The dependencies are fetched from jsdelivr CDN server. 

```sh
grep -R '<script' src/dashboard/_templates/*.html
```

* tailwindcss@4.1.18
    - https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.1.18/dist/index.global.js
    - [MIT](https://github.com/tailwindlabs/tailwindcss/blob/v4.1.18/LICENSE)
    - [No dependencies found other than dev dependencies](https://github.com/tailwindlabs/tailwindcss/blob/v4.1.18/package.json):
* htmx@2.0.7
    - https://cdn.jsdelivr.net/npm/htmx.org@2.0.7/dist/htmx.min.js
    - [Zero-Clause BSD](https://github.com/bigskysoftware/htmx/blob/v2.0.7/LICENSE)
    - [No dependencies found other than dev dependencies](https://github.com/bigskysoftware/htmx/blob/v2.0.7/package.json)
