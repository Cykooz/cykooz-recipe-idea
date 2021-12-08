"""
:Authors: cykooz
:Date: 03.12.2021
"""
import os
from pathlib import Path

import pytest
import zc.buildout
import zc.buildout.testing
from zc.buildout.buildout import Buildout
from zc.buildout.tests import create_sample_eggs

from cykooz.recipe.idea import Recipe


@pytest.fixture(name='build_env')
def build_env_fixture():
    env = Env()
    zc.buildout.testing.buildoutSetUp(env)

    # Create sample eggs
    sample_eggs = env.globs['tmpdir']('sample_eggs')
    env.globs['sample_eggs'] = sample_eggs
    os.mkdir(os.path.join(sample_eggs, 'index'))
    create_sample_eggs(env)
    env.globs['link_server'] = env.globs['start_server'](
        env.globs['sample_eggs']
    )

    yield env
    zc.buildout.testing.buildoutTearDown(env)


def test_recipe(build_env):
    build_env.write('setup.py', content='''
from setuptools import setup, find_packages
setup(
    name='test_develop',
    version='1.0.0',
    packages=find_packages(),
)
''')

    build_env.write('test_develop.py', content='')

    buildout = MockedBuildout(build_env.link_server)
    buildout._develop()

    eggs = '\n'.join((
        'test_develop',
        'demo',
        'setuptools',
    ))

    # The directory of Idea project is absent
    recipe = Recipe(
        buildout, 'test',
        {
            'eggs': eggs,
        }
    )
    recipe.install()
    assert not os.path.exists(recipe.result_path)

    # Create .idea dir
    build_env.mkdir('.idea')

    # .iml file is absent
    recipe.install()
    assert not os.path.exists(recipe.result_path)

    # Create .iml file
    build_env.write('.idea', 'project.iml', content=PROJECT_IML)

    # Only eggs
    recipe = Recipe(
        buildout, 'test',
        {
            'eggs': eggs,
        }
    )
    recipe.install()
    result_path = recipe.result_path
    assert os.path.exists(result_path)
    paths = get_result_paths(recipe.result_path)
    eggs_dir = Path(build_env.buildout_dir) / 'eggs'
    for i, egg_name in enumerate(('demo-0.3', 'demoneeded-1.1')):
        path = paths[i]
        expected_path = eggs_dir / egg_name
        assert path.startswith(f'file://{expected_path}')
        assert path.endswith('.egg')
    iml_content = Path('.idea', 'project.iml').open('rt').read()
    assert '<orderEntry type="library" name="Buildout Eggs" level="project" />' in iml_content

    # With develop packages
    build_env.write('.idea', 'project.iml', content=PROJECT_IML)
    Recipe(
        buildout, 'test',
        {
            'eggs': eggs,
            'include_develop': 'true',
        }
    ).install()
    paths = get_result_paths(result_path)
    assert len(paths) == 3
    assert paths[0] == f'file://{build_env.buildout_dir}'
    for i, egg_name in enumerate(('demo-0.3', 'demoneeded-1.1')):
        path = paths[i + 1]
        expected_path = eggs_dir / egg_name
        assert path.startswith(f'file://{expected_path}')
        assert path.endswith('.egg')

    # With other paths
    build_env.write('.idea', 'project.iml', content=PROJECT_IML)
    Recipe(
        buildout, 'test',
        {
            'eggs': eggs,
            'include_other': 'true',
        }
    ).install()
    paths = get_result_paths(result_path)
    assert len(paths) == 3
    assert any(path.endswith('site-packages') for path in paths)

    # Extra path and XML-encoding
    build_env.write('.idea', 'project.iml', content=PROJECT_IML)
    Recipe(
        buildout, 'test',
        {
            'eggs': eggs,
            'extra-paths': r'/home/user/My\Documents\pack&age',
        }
    ).install()
    paths = get_result_paths(result_path)
    paths = [path for path in paths if 'egg' not in path]
    assert paths == [
        r'file:///home/user/My\\Documents\\pack&amp;age'
    ]


def test_integration(build_env):
    build_env.write('setup.py', content='''
from setuptools import setup, find_packages
setup(
    name='test_develop',
    version='1.0.0',
    packages=find_packages(),
)
''')
    build_env.write('test_develop.py', content='')

    build_env.install('cykooz.recipe.idea')
    build_env.mkdir('.idea')
    build_env.write('.idea', 'project.iml', content=PROJECT_IML)

    build_env.write('buildout.cfg', content=f'''
[buildout]
develop = .
find-links = {build_env.link_server}
index = {build_env.link_server}/index
parts = idea

[idea]
recipe = cykooz.recipe.idea
eggs =
    test_develop
    demo
    zc.buildout 
''')

    build_env.run_buildout(True)

    result_path = Recipe(
        MockedBuildout(''), 'test',
        {'eggs': ''}
    ).result_path
    paths = get_result_paths(result_path)
    eggs_dir = Path(build_env.buildout_dir) / 'eggs'
    for i, egg_name in enumerate(('demo-0.3', 'demoneeded-1.1')):
        path = paths[i]
        expected_path = eggs_dir / egg_name
        assert path.startswith(f'file://{expected_path}')
        assert path.endswith('.egg')


def get_result_paths(xml_path):
    result = open(xml_path, 'rt').read()
    lines = (line.strip() for line in result.strip().split('\n'))
    return sorted(line[11:-4] for line in lines if line.startswith('<root'))


class Env:
    def __init__(self):
        self.globs = {}

    def install(self, name):
        zc.buildout.testing.install(name, self)

    def write(self, *names, content):
        self.globs['write'](*names, content)

    def mkdir(self, *names):
        self.globs['mkdir'](*names)

    def print(self, *args):
        self.globs['print_'](*args)

    def run_buildout(self, verbose=False):
        if verbose:
            self.print(self.globs['system'](
                self.globs['buildout']
            ))
        else:
            self.globs['system'](
                self.globs['buildout'] + ' -vvv'
            )

    @property
    def link_server(self):
        return self.globs['link_server']

    @property
    def buildout_dir(self) -> str:
        return self.globs['sample_buildout']


class MockedBuildout(Buildout):

    def __init__(self, link_server: str, config_path=''):
        for name in 'eggs', 'parts':
            if not os.path.exists(name):
                os.mkdir(name)
        Buildout.__init__(
            self, config_path,
            [
                ('buildout', 'directory', os.getcwd()),
                ('buildout', 'log-level', 'CRITICAL'),
                ('buildout', 'develop', '.'),
                ('buildout', 'find-links', link_server),
                ('buildout', 'index', link_server + '/index'),
            ],
            user_defaults=False,
        )

    Options = zc.buildout.testing.TestOptions


PROJECT_IML = '''<?xml version="1.0" encoding="UTF-8"?>
<module type="PYTHON_MODULE" version="4">
  <component name="NewModuleRootManager">
    <content url="file://$MODULE_DIR$">
      <sourceFolder url="file://$MODULE_DIR$/src" isTestSource="false" />
      <excludeFolder url="file://$MODULE_DIR$/.idea" />
      <excludeFolder url="file://$MODULE_DIR$/.pytest_cache" />
      <excludeFolder url="file://$MODULE_DIR$/.venv" />
      <excludeFolder url="file://$MODULE_DIR$/bin" />
      <excludeFolder url="file://$MODULE_DIR$/develop-eggs" />
      <excludeFolder url="file://$MODULE_DIR$/parts" />
    </content>
    <orderEntry type="jdk" jdkName="Python 3.9 (project)" jdkType="Python SDK" />
    <orderEntry type="sourceFolder" forTests="false" />
  </component>
  <component name="PyDocumentationSettings">
    <option name="format" value="PLAIN" />
    <option name="myDocStringFormat" value="Plain" />
  </component>
  <component name="TestRunnerService">
    <option name="PROJECT_TEST_RUNNER" value="py.test" />
  </component>
</module>
'''
