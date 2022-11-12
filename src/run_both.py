import re
import sys

from setupservers.setup_server import run, install
import setupservers.setup_server

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

    # sys.argv = ['setup-server-install', "--working-dir", working_dir]
    sys.argv = ['setup-server-install']
    install(standalone_mode=False)

    sys.argv = ["setup-server", "setup-db", "--db-type", "db-type", "--db-provider", "db-provider"]
    run1 = run()
    sys.exit()
