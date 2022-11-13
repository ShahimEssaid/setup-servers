import os
import pathlib

parent = pathlib.Path(os.curdir).absolute().parent

print(str(parent))

directories = next(os.walk(parent))[1]
directories.sort()
for subdir in directories:
    print(str(subdir))
