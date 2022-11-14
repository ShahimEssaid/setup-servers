import os
import pathlib
import re
import sys
import types
import typing
from importlib.machinery import SourceFileLoader

import click
import yaml


class BaseInfo(yaml.YAMLObject):
    NEW = 'New'
    CURRENT = 'Current'
    CLOSED = 'Closed'

    def __init__(self):
        self.info_status: str = BaseInfo.NEW
        self.setup_name: typing.Optional[str] = None


class DbInfo(BaseInfo):
    def __init__(self):
        super().__init__()
        self.dbs_name: typing.Optional[str] = None
        self.dbs_version: typing.Optional[str] = None


class SetupBase:

    def __init__(self, setup_name: str, setup_home_path: pathlib.Path, setup_provider_name: str,
                 setup_working_directory_name: str,
                 info_typing: typing.Type[BaseInfo]):
        self.setup_name: str = setup_name
        self.setup_home_path = setup_home_path
        self.setup_provider_name = setup_provider_name
        self.setup_working_path: pathlib.Path = servers_setup.working_directory / setup_working_directory_name
        self.info_typing: typing.Type[BaseInfo] = info_typing

        # setup info
        self.setup_working_path.mkdir(exist_ok=True)
        self.info_path = self.setup_working_path / (self.setup_name + ".yaml")
        self._info = load_info(self.info_path, self.info_typing)
        if self._info.info_status == BaseInfo.CLOSED:
            console_error("Setup {}")
        if self._info.info_status == BaseInfo.NEW:
            self._info.setup_name = self.setup_name

        self.provider_names = provider_names(self.setup_home_path, self.setup_name)

    def save_setup(self):
        self._info.info_status = BaseInfo.CURRENT
        save_info(self.info_path, self._info)


class SetupProviderBase:
    def __init__(self, setup: SetupBase):
        self.setup = setup

    def find_provider_module(self) -> types.ModuleType:
        dir_parts = str(self.provider_directory.name).split("--")
        if len(dir_parts) > 3:
            print("Setup provider directory has too many underscores: " + str(self.provider_directory))
            sys.exit(11)
        if len(dir_parts) == 3:
            provider_file_name = dir_parts[1]
        else:
            provider_file_name = dir_parts[0]
        provider_file_name = provider_file_name + ".py"
        self.provider_path = self.provider_directory / provider_file_name
        if not self.provider_path.exists():
            self.provider_path = self.provider_directory / (self.setup.setup_name + ".py")
        if not self.provider_path.exists():
            raise Exception("Failed to find provider path for provider directory {dir} and setup name {name}".format(
                dir=self.provider_directory, name=self.setup.setup_name))
        # we have the provider path. Build a module name to load it
        provider_module_name = self.setup.setup_name + "_"
        if len(dir_parts) == 3:
            provider_module_name += dir_parts[1] + "_" + dir_parts[2]
        else:
            provider_module_name += "_".join(dir_parts)

        self.provider_module = load_module(provider_module_name, self.provider_path)

        return self.provider_module


class ServersSetup:
    def __init__(self):
        self.home_directory: pathlib.Path = pathlib.Path(os.curdir).absolute()
        self.working_directory: pathlib.Path = pathlib.Path(os.curdir).absolute() / "working-directory"

    def run(self):
        pass


servers_setup = ServersSetup()

loaded_modules = {}


def provider_names(providers_dir_path: pathlib.Path, setup_name: str) -> dict:
    provider_dirs = next(os.walk(providers_dir_path))[1]
    provider_dirs.sort()
    providers = {}
    for provider_dir in provider_dirs:
        if provider_dir == setup_name:
            continue
        name = provider_name(provider_dir)
        if name in providers:
            console_error(
                f"Found duplicate provider name: {name}"
                f"\n\tin directory {provider_dir}"
                f"\n\twith existing directory: {providers[name]}."
                f"\n\tPlease make provider name unique and try again.", 10)
        providers[name] = provider_dir
    return providers


def provider_name(directory_name: str):
    if directory_name is None:
        return None
    provider_dir_clean = re.sub('-{2,}', '--', directory_name)
    parts = provider_dir_clean.split('--', 1)
    prefix = None
    if len(parts) == 2:
        prefix = parts[0]
        name = parts[1]
    else:
        name = parts[0]
    name = re.sub('[^a-zA-Z0-9]', '_', name)
    name = re.sub('_{1,}', '_', name)
    name = name.lower()
    return name


def load_module(module_name: str, module_path: pathlib.Path) -> types.ModuleType:
    module: types.ModuleType = SourceFileLoader("setupservers." + module_name, str(module_path)).load_module()
    loaded_modules[module.__name__] = module
    return module


def load_info(info_path: pathlib.Path, info_type: typing.Type[BaseInfo]) -> BaseInfo:
    if info_path.exists():
        with open(info_path) as f:
            info = yaml.unsafe_load(f)
    else:
        info = info_type()
        with open(info_path, 'w') as f:
            f.write(yaml.dump(info))
    return info


def save_info(info_path: pathlib.Path, info: BaseInfo) -> None:
    with open(info_path, 'w') as f:
        f.write(yaml.dump(info))


def console_info(message: str, exit_code: int = None):
    console_message(message, 'green', exit_code)


def console_warn(message: str, exit_code: int = None):
    console_message(message, 'yellow', exit_code)


def console_error(message: str, exit_code: int = None):
    console_message(message, 'red', exit_code)


def console_message(message: str, color: str, exit_code: int = None):
    click.secho(message, fg=color)
    if exit_code is not None:
        click.secho(f"Exising code: {exit_code}", fg=color)
        sys.exit(exit_code)  #
# def save_info(info, setup_name, setup_directory_name):
#     infos = load_infos(setup_name)
#     if hasattr(infos, setup_directory_name):
#         if not infos[setup_directory_name] is info:
#             raise Exception(
#                 "Saving info object while already have a different object for same name: {name} "
#                 "and setup directory: {directory}".format(
#                     name=setup_name, directory=setup_directory_name))
#     else:
#         infos[setup_directory_name] = info
#
#     info_path = servers_setup.working_directory / setup_directory_name / (setup_name + '.yaml')
#     with open(info_path, 'w') as f:
#         f.write(yaml.dump(info))
#
#
# def load_infos(setup_name) -> dict:
#     if not hasattr(setup_infos, setup_name):
#         setup_infos[setup_name] = {}
#         for setup_dir in next(os.walk(servers_setup.working_directory))[1]:
#             info_path = servers_setup.working_directory / setup_dir / (setup_name + ".yaml")
#             if info_path.exists():
#                 with open(info_path) as f:
#                     info = yaml.safe_load(f)
#                     if hasattr(info, 'setup_directory'):
#                         info_setup_dir = info.setup_directory
#                         if info_setup_dir != setup_dir:
#                             raise Exception(
#                                 "Info directory: {dir} does not match setup directory: {setup}".format(
#                                     dir=info_setup_dir,
#                                     setup=setup_dir))
#                     setup_infos[setup_name][setup_dir] = info
#     return setup_infos[setup_name]
#
#
# setup_infos = {}
