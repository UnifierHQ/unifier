@echo off
py -3 -V >nul 2>&1

if NOT ERRORLEVEL 0 (
  echo on
  echo Could not find a Python 3 installation.
) else (
  py -3 boot/bootloader.py
)
