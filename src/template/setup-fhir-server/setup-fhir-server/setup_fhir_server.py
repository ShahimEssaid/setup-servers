import pathlib

import click
import setupservers


class SetupFhirServer(setupservers.SetupBase):
    def __init__(self, info, setup_home_path, provider_name):
        super().__init__('setup-fhir-server',
                         info,
                         setup_home_path,
                         provider_name)


@click.command()
@click.option("--implementation-version")
@click.option("--setup-directory-name", required=True)
@click.option("--fhir-server-provider")
@click.option("--dbs-type", required=True)
@click.option("--dbs-setup-name", required=True)
@click.option("--db-user", required=True)
@click.option("--db-pass", required=True)
def setup_fhir_server_command(**kwargs):
    setupservers.console_info("Setting up FHIR server")
    info = setupservers.servers_setup.get_setup_info(kwargs['setup_directory_name'])
    info.params = kwargs
    setup_home_path = pathlib.Path(__file__).parent.parent
