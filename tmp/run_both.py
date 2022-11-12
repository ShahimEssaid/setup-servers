import re
import sys

from setupserver.cli import run, install

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    install(standalone_mode=False)

    sys.argv.append("setup-db")
    sys.argv.append("setup-db")
    sys.exit(run(), standalone_mode=False)
