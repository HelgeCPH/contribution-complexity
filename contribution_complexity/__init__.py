import toml

with open("pyproject.toml") as fp:
    contents = toml.load(fp)


__version__ = contents["tool"]["poetry"]["version"]
__version__ = "0.1.0"
