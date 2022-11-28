import pathlib
import shutil

import click
from clickactions import Command


@click.command(name='init', cls=Command)
def command():
    template_dir = pathlib.Path(__file__).parent.parent / 'template'
    target_dir = pathlib.Path.cwd()

    shutil.copytree(template_dir, target_dir, dirs_exist_ok=True)
