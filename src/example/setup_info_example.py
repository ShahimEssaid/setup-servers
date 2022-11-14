import setupservers.api as api
import pathlib

info = api.SetupInfo(pathlib.Path(__file__).parent / 'setup_path')

name = info.name
print(str(name))

info.name = 'Shahim'

name = info.name
print(str(name))


print(info.dict)

print(info.name)
print(str(info.url))
info.dict = {'one': 1}

info.save()
