import click
from setupservers import server_setup


class DbSetup:
    def __init__(self):
        self.module_name = None
        self.module = None
        self.module_path = None




"""

provider directory names are:   LOCAL-PREFIX_PY-PROVIDER-FILE-NAME_LOCAL-SUFFIX
    LOCAL-PREFIX is for local use and can help with directory sorting if and when it matters
    PY-PROVIDER-FILE-NAME is the provider py file that will be used and called as the provider
    LOCAL-SUFFIX

provider_type: this is confirmed by the provider but its directory can hint in it with 
"""


@click.command()
@click.option("--db-type")
@click.option("--db-provider")
def setup_db(db_type=None, db_provider=None):
    print("Setting up db...: " + db_type, db_provider)
