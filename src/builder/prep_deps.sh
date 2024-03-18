#!/usr/bin/bash
rm ./src/builder/builder.zip
mkdir ./src/builder/package
python -m pip install --target ./src/builder/package/ -r ./src/builder/requirements.txt
cd src/builder/package/
zip -r ../builder.zip .
cd ..
zip builder.zip main.py
rm -r package
cd ../..
