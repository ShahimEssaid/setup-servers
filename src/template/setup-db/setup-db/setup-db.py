import click
import setupservers.api as api
from setupservers import servers_setup


class DbSetup:
    def __init__(self):
        self.module_name = None
        self.module = None
        self.module_path = None


class SetupDb(api.SetupBase):
    pass

"""

provider directory names are: LOCAL-PREFIX_PY-PROVIDER-FILE-NAME_LOCAL-SUFFIX

* LOCAL-PREFIX: is for local use and can help with directory sorting if 
    and when it matters. It has no special meaning.
* PY-PROVIDER-FILE-NAME: is the provider's file name without the .py that will be used and called as the provider.
    If there is no provider file match, a file named setup-*  will be looked for.
* LOCAL-SUFFIX: a local hint to the specifics of the provider. For example, the same git submodule checked out at
    a different revision/version. The suffix can be a clear hint for this checkout.
     
"""


@click.command()
@click.option("--db-type")
@click.option("--db-provider")
def setup_db(db_type=None, db_provider=None):
    print("Setting up db...: " + db_type, db_provider)
