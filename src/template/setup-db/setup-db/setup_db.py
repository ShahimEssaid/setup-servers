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

        if self.info.info_status == setupservers.SetupInfo.STATUS_CREATED:
            if self.info.dbs_name != dbs_name or self.info.dbs_version != dbs_version:
                raise Exception(f"SetupInfo dbs name and version didn't match")

        self.dbs_actions: list[str] = dbs_action

    def run(self):
        provider_name = None
        provider_relative_path = None
        if self.provider_name is not None and self.provider_name in self.provider_name_relative_path_map:
            provider_name = self.provider_name
            provider_relative_path = self.provider_name_relative_path_map[self.provider_name]
        module = setupservers.load_module(self.command_home_path / provider_relative_path, self.info.setup_name,
                                          str(provider_relative_path))
        can_provide = getattr(module, 'can_provide_db')
        if can_provide(self):
            getattr(module, 'provide_db')(self)
        self.info.info_status = setupservers.SetupInfo.STATUS_CURRENT


setup_db: typing.Optional[SetupDb] = None


@click.command()
@click.option("--dbs-name")
@click.option("--dbs-version")
@click.option("--dbs-action", multiple=True, help="db actions in desired order: run, stop, destroy.")
@click.option("--dbs-user")
@click.option("--dbs-pass")
@click.option("--dbs-uid")
@click.option("--dbs-host")
@click.option("--dbs-port")
@click.option("--setup-directory-name", required=True)
@click.option("--dbs-provider",
              help="This can be the full provider directory name, the part after any -- or more dashes, or the "
                   "normalized name. It will be normalized before being used.")
def setup_db_command(dbs_name,
                     dbs_version,
                     dbs_action: list[str],
                     dbs_user,
                     dbs_pass,
                     dbs_uid,
                     dbs_host,
                     dbs_port,
                     setup_directory_name: str,
                     dbs_provider=None):
    info = setupservers.servers_setup.get_setup_info(setup_directory_name)
    if info.info_status == setupservers.SetupInfo.STATUS_NEW:
        info.dbs_name = dbs_name
        info.dbs_version = dbs_version
        info.dbs_user = dbs_user
        info.dbs_pass = dbs_pass
        info.dbs_uid = dbs_uid
    info.dbs_host = dbs_host
    info.dbs_port = dbs_port

    dbs_provider_name_clean = setupservers.provider_name_from_dir(dbs_provider)
    setup_home_path = pathlib.Path(__file__).parent.parent

    global setup_db
    setup_db = SetupDb(dbs_name,
                       dbs_version,
                       dbs_action,
                       info,
                       setup_home_path,
                       dbs_provider_name_clean)
    setup_db.run()
    setup_db.save()
