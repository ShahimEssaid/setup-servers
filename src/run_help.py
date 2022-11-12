import re
import sys

from setupservers.setup_server import run, install
import setupservers.setup_server

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

    sys.argv = ['--help']
    sys.exit(run(), standalone_mode=False)
