#!/usr/bin/bash
rm ./src/preparer/preparer.zip
mkdir ./src/preparer/package
pip install --target ./src/preparer/package/ boto3
cd src/preparer/package/
zip -r ../preparer.zip .
cd ..
zip preparer.zip main.py
rm -r package
cd ../..
