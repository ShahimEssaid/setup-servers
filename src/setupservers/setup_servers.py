import os
import pathlib
import shutil
import sys
import click

import setupservers
from setupservers import servers_setup
import setupservers

TEMPLATE = os.path.join(os.path.dirname(__file__), "../template/")


orig_init = click.core.Option.__init__


def _new_init(self, *args, **kwargs):
    orig_init(self, *args, **kwargs)
    self.show_default = True


click.core.Option.__init__ = _new_init


class RunCli(click.MultiCommand):
    def __init__(self, name, **kwargs):
        super().__init__(name, chain=True, **kwargs)

    def list_commands(self, ctx):

        if not (servers_setup.home_directory / "setup-servers").exists():
            print("You need to be in an installation/home directory. \nCurrent home directory doesn't seem to be an "
                  "installation:\n\t" + str(servers_setup.home_directory))
            sys.exit(10)
        rv = []
        for setup_dir in next(os.walk(servers_setup.home_directory))[1]:
            if setup_dir == "setup-servers":
                continue
            if setup_dir.startswith("setup-"):
                rv.append(setup_dir)
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        name_part = name.replace("-", "_")
        command_path = servers_setup.home_directory / name / name / (name_part + ".py")
        command_module = setupservers.load_module(name_part, command_path)
        command = getattr(command_module, name_part + '_command')
        return command


@click.command(cls=RunCli)
@click.option("--home-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True, exists=True),
              default=pathlib.Path(os.curdir).absolute())
@click.option("--work-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True, exists=True),
              default=pathlib.Path(os.curdir).absolute() / setupservers.WORK_DIRECTORY_NAME)
@click.option('--remote-pycharm-debug', is_flag=True)
@click.option('--pycharm-host')
@click.option('--pycharm-port', type=int)
def run(home_dir, work_dir, remote_pycharm_debug, pycharm_host=None, pycharm_port=None):
    if remote_pycharm_debug:
        import pydevd_pycharm
        pydevd_pycharm.settrace(pycharm_host, port=pycharm_port, stdoutToServer=True, stderrToServer=True,
                                suspend=False)
    servers_setup.home_directory = home_dir;
    servers_setup.work_directory = work_dir;
    servers_setup.initialize()
    servers_setup.run()


@click.command()
@click.option("--home-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True),
              default=pathlib.Path(os.curdir).absolute())
@click.option("--work-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True),
              default=pathlib.Path(os.curdir).absolute() / setupservers.WORK_DIRECTORY_NAME)
def install(home_dir, work_dir):
    print("Installing")
    servers_setup.home_directory = home_dir;
    servers_setup.work_directory = work_dir;
    os.makedirs(home_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)
    shutil.copytree(TEMPLATE, home_dir, dirs_exist_ok=True)
