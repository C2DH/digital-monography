#!/usr/bin/bash
rm ./src/preparer/preparer.zip
mkdir ./src/preparer/package
python -m pip install --target ./src/preparer/package/ -r ./src/preparer/requirements.txt
cd src/preparer/package/
zip -r ../preparer.zip .
cd ..
zip preparer.zip main.py constants.py citations.py metadata_extraction.py md_extraction.py html2md.py keys.py 
rm -r package
cd ../..
