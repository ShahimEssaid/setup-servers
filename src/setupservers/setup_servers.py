import os
import pathlib
import shutil
import sys
import click

from setupservers import servers_setup
from setupservers import api

TEMPLATE = os.path.join(os.path.dirname(__file__), "../template/")

orig_init = click.core.Option.__init__


def _new_init(self, *args, **kwargs):
    orig_init(self, *args, **kwargs)
    self.show_default = True


click.core.Option.__init__ = _new_init


class RunCli(click.MultiCommand):
    def __init__(self, name, **kwargs):
        super().__init__(self, name, chain=True, **kwargs)

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
        command_path = servers_setup.home_directory / name / name / (name + ".py")
        command_module = api.load_module(name, command_path)
        command = getattr(command_module, name.replace("-", "_"))
        # with open(command_path) as f:
        #     code = compile(f.read(), name + ".py", 'exec')
        #     eval(code, ns, ns)
        #     command = ns[name.replace("-", "_")]
        return command


@click.command(cls=RunCli)
@click.option("--home-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True, exists=True),
              default=pathlib.Path(os.curdir).absolute())
@click.option("--working-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True, exists=True),
              default=pathlib.Path(os.curdir).absolute() / "working-directory")
def run(home_dir, working_dir):
    servers_setup.home_directory = home_dir;
    servers_setup.working_directory = working_dir;
    print("Running")
    servers_setup.run()


@click.command()
@click.option("--home-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True),
              default=pathlib.Path(os.curdir).absolute())
@click.option("--working-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True),
              default=pathlib.Path(os.curdir).absolute() / "working-directory")
def install(home_dir, working_dir):
    print("Installing")
    servers_setup.home_directory = home_dir;
    servers_setup.working_directory = working_dir;
    os.makedirs(home_dir, exist_ok=True)
    os.makedirs(working_dir, exist_ok=True)
    shutil.copytree(TEMPLATE, home_dir, dirs_exist_ok=True)
