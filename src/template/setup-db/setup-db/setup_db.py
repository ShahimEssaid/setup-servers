import pathlib

import click
import typing

import setupservers


class SetupDb(setupservers.SetupBase):
    def __init__(self,
                 dbs_name: str,
                 dbs_version: str,
                 dbs_action: list[str],
                 setup_info: setupservers.SetupInfo,
                 setup_home_path: pathlib.Path,
                 provider_name: str):

        super().__init__('setup-db',
                         setup_info,
                         setup_home_path,
                         provider_name)

        if self.setup_info.info_status == setupservers.SetupInfo.STATUS_NEW:
            self.setup_info.dbs_name = dbs_name
            self.setup_info.dbs_version = dbs_version
        elif self.setup_info.info_status == setupservers.SetupInfo.STATUS_CURRENT:
            if self.setup_info.dbs_name != dbs_name or self.setup_info.dbs_version != dbs_version:
                raise Exception(f"SetupInfo dbs name and version didn't match")

        self.dbs_actions: list[str] = dbs_action

    def run(self):
        self.setup_info.info_status = setupservers.SetupInfo.STATUS_CREATED


setup_db: typing.Optional[SetupDb] = None

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
@click.option("--dbs-name")
@click.option("--dbs-version")
@click.option("--dbs-action", multiple=True, help="db actions in desired order: create, start, stop, remove")
@click.option("--setup-directory-name", required=True)
@click.option("--dbs-provider",
              help="This can be the full provider directory name, the part after any -- or more dashes, or the "
                   "normalized name. It will be normalized before being used.")
def setup_db_command(dbs_name, dbs_version, dbs_action: list[str], setup_directory_name: str, dbs_provider=None):
    setup_info = setupservers.servers_setup.get_setup_info(setup_directory_name)
    dbs_provider_name_clean = setupservers.provider_name(dbs_provider)
    setup_home_path = pathlib.Path(__file__).parent.parent

    global setup_db
    setup_db = SetupDb(dbs_name, dbs_version, dbs_action, setup_info, setup_home_path, dbs_provider_name_clean)
    setup_db.save()
    print('Hello')
