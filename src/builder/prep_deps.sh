#!/usr/bin/bash
rm ./src/builder/builder.zip
mkdir ./src/builder/package
pip install --target ./src/builder/package/ boto3
cd src/builder/package/
zip -r ../builder.zip .
cd ..
zip builder.zip main.py
rm -r package
cd ../..
