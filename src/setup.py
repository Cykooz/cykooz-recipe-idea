from setuptools import setup, find_packages


setup(
    name='cykooz.recipe.idea',
    version='0.1',
    url='https://github.org/cykooz/cykooz.recipe.idea',
    author='Kirill Kuzminykh',
    author_email='cykooz@gmail.com',
    description='zc.buildout recipe that creates a file with list of '
                'external libraries for PyCharm of IntelliJ IDEA.',
    long_description=(
            open('README.rst').read() + '\n\n' +
            open('CHANGES.rst').read()
    ),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Framework :: Buildout',
        'Framework :: Buildout::Recipe',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'License :: OSI Approved :: Apache Software License',
    ],
    packages=find_packages(),
    package_dir={'': '.'},
    namespace_packages=['cykooz', 'cykooz.recipe'],
    install_requires=[
        'setuptools',
        'zc.buildout',
        'zc.recipe.egg',
    ],
    extras_require={
        'test': [
            'pytest',
            'zc.buildout[test]',
            'cykooz.testing',
        ]
    },
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'zc.buildout': [
            'default = cykooz.recipe.idea:Recipe',
        ],
        'console_scripts': [
            'recipe_tests = cykooz.recipe.idea.runtests:runtests [test]',
        ]
    }
)
