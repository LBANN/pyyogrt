from setuptools import setup

# Not currently supported via pyproject.toml, though
# [tool.cffi]
# modules = ["generate_bindings.py:ffibuilder"]
# should eventually work.

setup(cffi_modules='generate_bindings.py:ffibuilder')
