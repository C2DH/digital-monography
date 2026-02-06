python --version # 3.12.1
python -m venv .sbom
source .sbom/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt 
python -m pip freeze > sbom-req.txt
python -m pip install sbom4python
sbom4python -r sbom-req.txt -o sbom-out.tags
