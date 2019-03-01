import logging
import sys

__version__ = "0.1.0"

if sys.version_info[0] == 2:
    print("Python v3 is needed!")
    sys.exit(-1)

logging.basicConfig(level=logging.DEBUG)
