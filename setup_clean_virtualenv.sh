#!/bin/sh
mkdir -p ~/env
pushd ~/env
curl -O  https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.10.1.tar.gz
tar -xvzf virtualenv-1.10.1.tar.gz
python virtualenv-1.10.1/virtualenv.py ~/env/clean --no-setuptools --no-pip --no-site-packages
popd
