import re
import sys

from setupservers.setup_servers import run, install

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

    # sys.argv = ['setup-servers-install', "--working-dir", working_dir]
    sys.argv = ['setup-servers-install']
    install(standalone_mode=False)

    sys.argv = ["setup-servers", "setup-db", "--db-type", "db-type", "--db-provider", "db-provider"]
    run1 = run()
    sys.exit()
