cykooz.recipe.idea
******************

This recipe for buildout_ creates a ``.idea/libraries/Buildout_Eggs.xml`` file.
This file may be used by ``PyCharm`` (or ``IntelliJ IDEA``) as list of external
libraries and contains paths to all the specified eggs and their dependencies.

Usage
=====

This is a minimal ``buildout.cfg`` file which creates a xml-file with paths
to eggs::

    [buildout]
    parts =
        application
        idea

    [application]
    recipe = zc.recipe.egg:scripts
    eggs =
        my_application
        ipython

    [idea]
    recipe = cykooz.recipe.idea
    eggs =
        ${application:eggs}


Available options
=================

eggs
    The eggs that will be used to generate a file with paths. You don’t need to
    include transitive dependencies. This is done automatically.

idea_dir
    Path to directory of ``PyCharm`` project. Default: ``${buildout:directory}/.idea``
    The recipe won't create any files or directories if given directory is absent
    or it not contains .iml file.

include_develop
    Set it as ``true`` if you need to add paths to develop packages.
    Default: ``false``.

include_eggs
    Set it as ``false`` if you need to exclude paths to the specified eggs.
    Default: ``true``.

include_other
    Set it as ``true`` if you need to add paths to other directories that
    contains required packages or it dependencies but that was installed
    not by ``zc.buildout``. For example path to ``site-packages`` directory
    from used Python.
    Default: ``false``.

extra-paths
    Extra paths to include in a generated xml file.


.. _buildout: http://pypi.python.org/pypi/zc.buildout
