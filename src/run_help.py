import re
import sys

from setupservers.setup_servers import run, install


if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

    # sys.argv = ("setup-servers", "--help")
    sys.exit(run())