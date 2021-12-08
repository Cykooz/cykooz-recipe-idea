

def runtests():
    import sys
    import pytest
    from os import environ
    from pathlib import Path
    root_dir_path = Path(__file__).parent / '..' / '..' / '..' / '..'
    cfg_path = root_dir_path / 'src' / 'setup.cfg'

    args = sys.argv[1:]
    if not args or args[0].startswith('-'):
        args += ['--pyargs', 'cykooz.recipe.idea']
    args = [
        '-c', str(cfg_path),
        '--rootdir', str(root_dir_path),
    ] + args
    environ['IS_TESTING'] = 'true'

    return pytest.main(args)
