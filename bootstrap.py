"""
:Version: 1.1
"""
import argparse
import logging
import os
import platform
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen


BUILDOUT_VERSION = '3.0rc2'
PIP_VERSION = '22.0.4'
SETUPTOOLS_VERSION = '59.6.0'
WHEEL_VERSION = '0.37.1'

GET_PIP_URL = 'https://bootstrap.pypa.io/get-pip.py'


def main():
    parser = argparse.ArgumentParser(description='Bootstrap zc.buildout')
    parser.add_argument(
        '-r, --recreate', dest='recreate', action='store_true',
        help='Recreate virtual python if it exists.',
    )
    parser.add_argument(
        '--buildout_version', default=BUILDOUT_VERSION,
        help='Version of zc.buildout (default: %(default)).',
    )
    parser.add_argument(
        '--pip_version', default=PIP_VERSION,
        help='Version of pip (default: %(default)).',
    )
    parser.add_argument(
        '--setuptools_version', default=SETUPTOOLS_VERSION,
        help='Version of setuptools (default: %(default)).',
    )
    parser.add_argument(
        '--wheel_version', default=WHEEL_VERSION,
        help='Version of wheel (default: %(default)).',
    )

    args = parser.parse_args(sys.argv[1:])
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(levelname)s: %(message)s'
    )
    logger = logging.getLogger('buildout.bootstrap')

    project_dir = Path(os.getcwd()).absolute()
    venv_dir = project_dir / '.venv'
    if args.recreate and venv_dir.is_dir():
        logger.info('Delete exists virtual python')
        shutil.rmtree(venv_dir)

    is_win = platform.system() == 'Windows'
    if is_win:
        venv_python_path = venv_dir / 'Scripts' / 'python.exe'
    else:
        venv_python_path = venv_dir / 'bin' / 'python'

    if venv_python_path.is_file():
        logger.debug('Checking version of exists virtual python...')
        proc = subprocess.Popen(
            [
                str(venv_python_path),
                '-c',
                'import sys;print(sys.version)',
            ],
            stdout=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()
        env_version = stdout.strip().decode()
        if env_version != sys.version:
            logger.info(
                'Removing exists virtual python environment '
                'due to incorrect version of Python in it...'
            )
            shutil.rmtree(venv_dir)

    if not venv_python_path.is_file():
        logger.info(f'Installing virtual python environment in directory {venv_dir}')
        venv.create(
            venv_dir,
            symlinks=not is_win,
            system_site_packages=False,
            with_pip=False,
        )
        logger.info('Virtual python environment has installed.')

    logger.info('Installing pip...')
    with TemporaryDirectory() as tmp_dir:
        get_pip_path = Path(tmp_dir) / 'get_pip.py'
        with urlopen(GET_PIP_URL) as get_pip:
            content: bytes = get_pip.read()
            get_pip_path.write_bytes(content)
        cmd = [
            str(venv_python_path),
            str(get_pip_path),
            '--no-setuptools',
            '--no-wheel',
        ]
        if args.pip_version:
            cmd.append(f'pip=={args.pip_version}')
        _run_cmd(cmd)

    logger.info(f'Installing setuptools=={args.setuptools_version} and wheel=={args.wheel_version}')
    _run_cmd([
        str(venv_python_path),
        '-m', 'pip',
        'install',
        f'setuptools=={args.setuptools_version}',
        f'wheel=={args.wheel_version}',
    ])

    logger.info(f'Installing zc.buildout == {args.buildout_version}')
    _run_cmd([
        str(venv_python_path),
        '-m', 'pip',
        'install',
        f'zc.buildout=={args.buildout_version}'
    ])

    logger.info(f'Bootstrap zc.buildout')
    is_win = platform.system() == 'Windows'
    if is_win:
        buildout_path = venv_dir / 'Scripts' / 'buildout.exe'
    else:
        buildout_path = venv_dir / 'bin' / 'buildout'
    _run_cmd([
        str(buildout_path),
        'bootstrap',
    ])

    # Delete zc.buildout.egg-link from list of develop eggs
    buildout_link = project_dir / 'develop-eggs' / 'zc.buildout.egg-link'
    if buildout_link.is_file():
        os.remove(buildout_link)

    # Fix buildout script
    buildout_script_path = project_dir / 'bin' / 'buildout'
    buildout_script = buildout_script_path.read_text()
    buildout_script = buildout_script.replace(
        'import zc.buildout.buildout',
        'try:\n'
        '    from _distutils_hack import DistutilsMetaFinder\n'
        '    DistutilsMetaFinder.pip_imported_during_build = lambda cls: True\n'
        'except ImportError:\n'
        '    pass\n\n'
        'import zc.buildout.buildout\n'
        'import warnings\n'
        'from pkg_resources import PkgResourcesDeprecationWarning\n\n'
        'warnings.filterwarnings("ignore", category=PkgResourcesDeprecationWarning)'
    )
    buildout_script_path.write_text(buildout_script)


def _run_cmd(cmd):
    if subprocess.call(cmd) != 0:
        raise Exception(f'Failed to execute command:\n {" ".join(cmd)}')


if __name__ == '__main__':
    main()
