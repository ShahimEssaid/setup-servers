import os
import pathlib
import re
import sys
import types
import typing
from importlib.machinery import SourceFileLoader

import click
import yaml

import docker

SETUP_INFO_YAML = 'setup-info.yaml'
WORK_DIRECTORY_NAME = 'work-directory'

docker_client = docker.from_env()


#
# class BaseInfo(yaml.YAMLObject):
#     NEW = 'New'
#     CURRENT = 'Current'
#     CLOSED = 'Closed'
#
#     def __init__(self):
#         self.info_status: str = BaseInfo.NEW
#         self.setup_name: typing.Optional[str] = None
#
#
# class DbInfo(BaseInfo):
#     def __init__(self):
#         super().__init__()
#         self.dbs_name: typing.Optional[str] = None
#         self.dbs_version: typing.Optional[str] = None


class SetupInfo:
    STATUS_NEW = 'New'
    STATUS_CREATED = 'Created'
    STATUS_CURRENT = 'Current'
    STATUS_CLOSED = 'Closed'

    INFO_STATUS = 'info_status'

    def __init__(self, setup_directory_path: typing.Union[str, pathlib.Path]):
        setup_path = pathlib.Path(str(setup_directory_path))
        setup_info_path = setup_path / SETUP_INFO_YAML

        if setup_info_path.exists():
            with open(setup_info_path) as f:
                self.__dict__ = yaml.unsafe_load(f)
        else:
            self.info_status = SetupInfo.STATUS_NEW

        self.setup_path: str = str(setup_path)
        self.setup_info_path: str = str(setup_info_path)

    def __getattr__(self, item):
        return None

    def save(self):
        setup_info_path = pathlib.Path(self.setup_info_path)
        setup_info_path.parent.mkdir(parents=True, exist_ok=True)
        with open(setup_info_path, 'w') as f:
            f.write(yaml.dump(self.__dict__))


class SetupBase:

    def __init__(self, setup_name: str, setup_info: SetupInfo, setup_home_path: pathlib.Path, setup_provider_name: str):
        if setup_info.info_status == SetupInfo.STATUS_CLOSED:
            raise Exception("SetupInfo already closed")

        if setup_info.info_status == SetupInfo.STATUS_NEW:
            setup_info.setup_name = setup_name
        else:
            if setup_info.setup_name != setup_name:
                raise Exception(f"Setup name {setup_name} did not match setup info name {setup_info.setup_name}")

        self.setup_info = setup_info
        self.setup_home_path = setup_home_path
        self.setup_provider_name = setup_provider_name
        self.provider_name_relative_path_map = provider_name_dir_map(self.setup_home_path, self.setup_info.setup_name)

    def save(self):
        # self.setup_info.info_status = SetupInfo.STATUS_CURRENT
        self.setup_info.save()


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

        self.provider_module = load_module(self.provider_path, provider_module_name)

        return self.provider_module


class ServersSetup:
    def __init__(self):
        self.home_directory: pathlib.Path = pathlib.Path(os.curdir).absolute()
        self.work_directory: pathlib.Path = pathlib.Path(os.curdir).absolute() / WORK_DIRECTORY_NAME
        self.setups = {}

    def initialize(self):
        work_dirs = next(os.walk(self.work_directory))[1]
        for work_dir in work_dirs:
            work_dir_path = self.work_directory / work_dir
            if (work_dir_path / SETUP_INFO_YAML).exists():
                self.setups[work_dir] = SetupInfo(work_dir_path)

    def get_setup_info(self, setup_directory_name: str) -> SetupInfo:
        if setup_directory_name in self.setups:
            return self.setups[setup_directory_name]
        else:
            console_warn(f"Creating new setup at: {setup_directory_name}")
            setup_info = SetupInfo(self.work_directory / setup_directory_name)
            self.setups[setup_directory_name] = setup_info
            return setup_info

    def run(self):
        pass


servers_setup = ServersSetup()

loaded_modules = {}


def provider_name_dir_map(providers_dir_path: pathlib.Path, setup_name: str) -> dict:
    provider_dirs = next(os.walk(providers_dir_path))[1]
    provider_dirs.sort()
    providers = {}
    for provider_dir in provider_dirs:
        if provider_dir == setup_name:
            continue
        provider_relative = pathlib.Path(provider_dir) / (setup_name.replace('-', '_') + '.py')
        provider_path = providers_dir_path / provider_relative
        if not provider_path.exists():
            continue
        name = provider_name(provider_dir)
        if name in providers:
            console_error(
                f"Found duplicate provider name: {name}"
                f"\n\tin directory {provider_dir}"
                f"\n\twith existing directory: {providers[name]}."
                f"\n\tPlease make provider name unique and try again.", 10)
        providers[name] = provider_relative
    return providers


def provider_name(directory_name: str):
    if directory_name is None:
        return None
    provider_dir_clean = re.sub('--+', '--', directory_name)
    parts = provider_dir_clean.split('--', 1)
    prefix = None
    if len(parts) == 2:
        prefix = parts[0]
        name = parts[1]
    else:
        name = parts[0]
    name = re.sub('[^a-zA-Z0-9]', '_', name)
    name = re.sub('_+', '_', name)
    name = name.lower()
    return name


def load_module(module_path: pathlib.Path, *name_parts) -> types.ModuleType:
    module_name = build_module_name(*name_parts)
    module: types.ModuleType = SourceFileLoader(module_name, str(module_path)).load_module()
    loaded_modules[module.__name__] = module
    return module


def build_module_name(*parts):
    name = 'setupservers.'
    clean_parts = []
    for part in parts:
        part = re.sub('[^a-zA-Z0-9]', '_', part)
        part = re.sub('_+', '_', part)
        clean_parts.append(part)

    name += '_'.join(clean_parts)
    return name;


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


def docker_container_name(module_name: str, work_dir_name):
    split = module_name.split('.')
    name = split[0]

    work_path_string = str(servers_setup.work_directory)
    pattern = re.compile(r'([a-zA-Z]+)')
    for (letters) in re.findall(pattern, work_path_string):
        name += "." + letters[0]

    name += '_' + work_dir_name + '_' + split[1]
    name = re.sub('[^a-zA-Z0-9_.-]', '_', name)
    name = re.sub('__+', '_', name)
    return name


def is_port_in_use(host: str, port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0
