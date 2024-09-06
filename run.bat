py -3 -V >nul 2>&1 && (
    py -3 ./boot/bootloader.py
) || (
    echo Could not find a Python 3 installation.
)