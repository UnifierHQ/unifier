#!/bin/bash

FILEPATH="$(which python3)"

if [[ -z $FILEPATH ]]; then
  echo "Could not find a Python 3 installation."
  exit 1
fi

python3 ./boot/bootloader.py "$@"
