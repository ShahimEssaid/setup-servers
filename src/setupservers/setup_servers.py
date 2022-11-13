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
        home_dir = pathlib.Path(os.curdir).absolute()
        work_dir = pathlib.Path(os.curdir).absolute() / "working-directory"

        if len(ctx.help_option_names) > 0 and not servers_setup.home_directory.exists():
            raise Exception("You need to be in installation directory to get help output.")
        rv = []
        for setup_dir in next(os.walk(home_dir))[1]:
            if setup_dir == "setup-servers":
                continue
            if setup_dir.startswith("setup-"):
                rv.append(setup_dir)
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        command_path = servers_setup.home_directory / name / name / (name + ".py")
        with open(command_path) as f:
            code = compile(f.read(), name + ".py", 'exec')
            eval(code, ns, ns)
            command = ns[name.replace("-", "_")]
        return command


class ServersSetup:
    def __init__(self):
        self.home_directory = pathlib.Path(os.curdir).absolute()
        self.working_directory = pathlib.Path(os.curdir).absolute() / "working-directory"

    def run(self):
        print("Running from ServersSetup")
        print("Home directory: " + str(self.home_directory))
        print("Working directory: " + str(self.working_directory))
        print()


servers_setup = ServersSetup()


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
