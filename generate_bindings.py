import subprocess
import os
import os.path
import shutil
import pathlib

from cffi import FFI


def split_paths(paths: str) -> list[str]:
    """Split a colon-separated list of paths into an actual list."""
    return paths.split(':')


def standardize_paths(paths: set[str]) -> set[str]:
    """Standardize a set of paths.

    This will convert them all to absolute paths and resolve any
    symbolic links that may be present.
    """
    # Resolve all symlinks and convert to absolute paths:
    resolved_paths: set[str] = set()
    for path in paths:
        path = pathlib.Path(path)
        try:
            path = path.resolve(strict=True)
        except FileNotFoundError:
            continue
        resolved_paths.add(path.as_posix())
    return resolved_paths


def get_env_include_paths() -> set[str]:
    """Check environment variables to identify include paths.

    This will check the following environment variables:
    - YOGRT_INCLUDE_PATH
    - CPATH
    - C_INCLUDE_PATH
    """
    paths: set[str] = set()
    def _get_from_env(name: str) -> None:
        env = os.environ.get(name, None)
        if env:
            paths.update(split_paths(env))

    _get_from_env('YOGRT_INCLUDE_PATH')
    _get_from_env('CPATH')
    _get_from_env('C_INCLUDE_PATH')

    return paths


def get_env_library_paths() -> set[str]:
    """Check environment variables to identify library paths.

    This will check the following environment variables:
    - YOGRT_LIB_PATH
    - LIBRARY_PATH
    """
    paths: set[str] = set()

    def _get_from_env(name: str) -> None:
        env = os.environ.get(name, None)
        if env:
            paths.update(split_paths(env))

    _get_from_env('YOGRT_LIBRARY_PATH')
    _get_from_env('LIBRARY_PATH')

    return paths


# TODO: Maybe support pkg-config --cflags-only-I in the future?


def determine_compiler() -> str | None:
    """Attempt to determine a compiler.

    This checks for a compiler as follows (in this order):
    - The value of the `CC` environment variable.
    - The `cc` command.
    - `gcc`.
    - `clang`.
    """
    compiler = os.environ.get('CC', None)
    if compiler:
        return compiler

    compiler = shutil.which('cc')
    if compiler:
        return compiler

    compiler = shutil.which('gcc')
    if compiler:
        return compiler

    compiler = shutil.which('clang')
    if compiler:
        return compiler

    return None


def determine_preprocessor(compiler: str) -> str | None:
    """Attempt to determine the C preprocessor given a compiler.

    This essentially runs `compiler -print-prog-name=cpp`.
    """
    try:
        cpp = subprocess.check_output([compiler, '-print-prog-name=cpp'],
                                      text=True)
    except subprocess.CalledProcessError:
        return None

    return cpp.strip()


def get_compiler_include_paths() -> set[str]:
    """Attempt to determine the compiler's default include paths.

    This does so by determining a compiler, running
    `COMPILER -print-prog-name=cpp`
    to determine the C preprocessor, then running
    `CPP -v < /dev/null`
    to determine the include paths.
    """
    paths: set[str] = set()
    compiler = determine_compiler()
    if not compiler:
        return paths

    cpp = determine_preprocessor(compiler)
    if not cpp:
        return paths

    try:
        output = subprocess.check_output([cpp, '-v'],
                                         stdin=subprocess.DEVNULL,
                                         stderr=subprocess.STDOUT,
                                         text=True)
    except subprocess.CalledProcessError:
        return paths

    # Attempt to parse the output:
    output = output.split('\n')
    try:
        include_start = output.index('#include <...> search starts here:') + 1
    except ValueError:
        return paths
    try:
        include_end = output.index('End of search list.')
    except ValueError:
        return paths
    raw_paths = output[include_start:include_end]
    raw_paths = [path.strip() for path in raw_paths]
    paths.update(raw_paths)
    return paths


def get_compiler_library_paths() -> set[str]:
    """Attempt to determine the compiler's default library paths.

    This operates the same way as get_compiler_include_paths.
    """
    paths: set[str] = set()
    compiler = determine_compiler()
    if not compiler:
        return paths

    cpp = determine_preprocessor(compiler)
    if not cpp:
        return paths

    try:
        output = subprocess.check_output([cpp, '-v'],
                                         stdin=subprocess.DEVNULL,
                                         stderr=subprocess.STDOUT,
                                         text=True)
    except subprocess.CalledProcessError:
        return paths

    # Attempt to parse the output:
    output = output.split('\n')
    for line in output:
        if line.startswith('LIBRARY_PATH='):
            paths.update(split_paths(line[len('LIBRARY_PATH='):]))
    return paths


def get_ldconfig_library_paths() -> set[str]:
    """Use ldconfig to attempt to locate libyogrt.

    This essentially runs `ldconfig -p` and searches for libyogrt.so.
    """
    paths: set[str] = set()
    try:
        output = subprocess.check_output(['ldconfig', '-p'], text=True)
    except subprocess.CalledProcessError:
        return paths

    output = output.split('\n')
    for line in output:
        line = line.strip()
        # Space at end to distinguish between e.g. libyogrt.so.1
        if line.startswith('libyogrt.so '):
            path = line.split(' => ')[1]
            paths.add(path)

    return paths


def find_yogrt_h() -> str:
    """Attempt to locate yogrt.h."""
    paths = get_env_include_paths() | get_compiler_include_paths()
    # Ensure standard include paths are always present:
    paths.add('/usr/include')
    paths.add('/usr/local/include')

    paths = standardize_paths(paths)

    for path in paths:
        header_path = os.path.join(path, 'yogrt.h')
        if os.path.exists(header_path):
            return header_path

    # Failed to find yogrt.h.
    raise RuntimeError('Could not find yogrt.h')


def preprocess_header(header_path: str) -> str:
    """Preprocess the given header with a compiler."""
    cc = determine_compiler()
    if not cc:
        raise RuntimeError('Could not determine a compiler')
    return subprocess.check_output([cc, '-E', '-P', header_path], text=True)


def find_yogrt_lib() -> set[str]:
    """Attempt to find all library directories containing libyogrt."""
    paths = (get_env_library_paths()
             | get_compiler_library_paths()
             | get_ldconfig_library_paths())
    # Ensure standard library paths are always present:
    paths.add('/lib')
    paths.add('/lib64')
    paths.add('/usr/lib')
    paths.add('/usr/lib64')
    paths.add('/usr/local/lib')
    paths.add('/usr/local/lib64')

    paths = standardize_paths(paths)

    paths_with_libyogrt: set[str] = set()
    for path in paths:
        if os.path.exists(os.path.join(path, 'libyogrt.so')):
            paths_with_libyogrt.add(path)

    if not paths_with_libyogrt:
        raise RuntimeError('Could not find libyogrt.so')

    return paths_with_libyogrt


ffibuilder = FFI()
yogrt_h_path = find_yogrt_h()
lib_paths = list(find_yogrt_lib())
header = preprocess_header(yogrt_h_path)
ffibuilder.cdef(header)
ffibuilder.set_source('yogrt._yogrt_c',
                      """
                      #include <yogrt.h>
                      """,
                      libraries=['yogrt'],
                      library_dirs=lib_paths,
                      runtime_library_dirs=lib_paths)


if __name__ == '__main__':
    _ = ffibuilder.compile()
