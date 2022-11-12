import os
import pathlib
import shutil

import click

TEMPLATE = os.path.join(os.path.dirname(__file__), "../template/")
SETUP_SERVER_HOME = pathlib.Path().absolute()


class RunCli(click.MultiCommand):
    def __init__(self, name, **kwargs):
        super().__init__(self, name, chain=True, **kwargs)

    def list_commands(self, ctx):
        raise Exception("Didn't expect to have to list commands")
        rv = []
        for setup_dir in next(os.walk(SETUP_SERVER_HOME))[1]:
            if setup_dir == "setup-server":
                continue
            if setup_dir.startswith("setup-"):
                rv.append(setup_dir)
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        with open(home_directory / name / name / (name + ".py")) as f:
            code = compile(f.read(), name + ".py", 'exec')
            eval(code, ns, ns)
            command_name = name.replace("-", "_")
            command = ns[command_name]
        return command


class ServerSetup:
    def __init__(self):
        self.working_dir = None

    def run(self):
        print("Running from the ServerSetup")


server_setup = ServerSetup()

home_directory = None
working_directory = None


@click.command(cls=RunCli)
@click.option("--home-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True, exists=True),
              default=pathlib.Path(os.curdir).absolute())
@click.option("--working-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True, exists=True),
              default=pathlib.Path(os.curdir).absolute() / "working-directory")
def run(home_dir, working_dir):
    global working_directory, home_directory
    working_directory = working_dir
    home_directory = home_dir
    os.makedirs(home_directory, exist_ok=True)
    os.makedirs(working_directory, exist_ok=True)

    if working_dir is not None:
        if working_directory is not None and working_directory != working_dir:
            raise Exception(
                "Working directory is not the same. Have:" + working_directory + " but got:" + working_dir)
        else:
            working_directory = working_dir
    print("Running")

    server_setup.run()


@click.command()
@click.option("--home-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True),
              default=pathlib.Path(os.curdir).absolute())
@click.option("--working-dir", type=click.Path(path_type=pathlib.Path, resolve_path=True),
              default=pathlib.Path(os.curdir).absolute() / "working-directory")
def install(home_dir, working_dir):
    print("Installing")
    global working_directory, home_directory
    working_directory = working_dir
    home_directory = home_dir
    os.makedirs(home_directory, exist_ok=True)
    os.makedirs(working_directory, exist_ok=True)
    shutil.copytree(TEMPLATE, home_directory, dirs_exist_ok=True)
