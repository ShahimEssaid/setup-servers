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
        fn = os.path.join(SETUP_SERVER_HOME, name, "setup-db", name + '.py')
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
            command_name = name.replace("-", "_")
            command = ns[command_name]
        return command


class ServerSetup:
    def run(self):
        print( "Running from the ServerSetup")


server_setup = None


@click.command(cls=RunCli)
def run():
    print("Running")
    global server_setup
    server_setup = ServerSetup()
    server_setup.run()


@click.command()
def install():
    print("Installing")
    shutil.copytree(TEMPLATE, SETUP_SERVER_HOME, dirs_exist_ok=True)
