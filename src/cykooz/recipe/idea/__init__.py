"""
:Authors: cykooz
:Date: 03.12.2021
"""
import glob
import logging
import os.path
from xml.etree import ElementTree
from xml.sax.saxutils import escape

import zc.recipe.egg
from zc.buildout.buildout import bool_option


class Recipe:

    def __init__(self, buildout, name, options):
        self.name = name
        self.buildout = buildout
        self.idea_dir = options.get('idea_dir')
        if not self.idea_dir:
            self.idea_dir = os.path.join(buildout['buildout']['directory'], '.idea')
        self.result_path = os.path.join(self.idea_dir, 'libraries', 'Buildout_Eggs.xml')
        self.include_develop = bool_option(options, 'include_develop', False)
        self.include_eggs = bool_option(options, 'include_eggs', True)
        self.include_other = bool_option(options, 'include_other', False)
        _ = options['eggs']  # Mute warning about unused option 'eggs'
        options = options.copy()
        options['relative-paths'] = 'false'
        self._eggs = zc.recipe.egg.Scripts(buildout, name, options)
        self._library_name = 'Buildout Eggs'

    def install(self):
        if not os.path.isdir(self.idea_dir):
            logging.getLogger(self.name).debug(
                f'Directory of an Idea project ({self.idea_dir}) has not found.'
            )
            return ()
        iml_paths = glob.glob(os.path.join(self.idea_dir, '*.iml'))
        if not iml_paths:
            logging.getLogger(self.name).debug(
                f'Module files (.iml) has not found inside of directory of Idea project.'
            )
            return ()

        self._write_paths()
        self._update_idea_project(iml_paths[0])

        return ()

    update = install

    def get_paths(self):
        requirements, ws = self._eggs.working_set()
        buildout_cfg = self.buildout['buildout']

        all_develop_paths = set()
        pattern = os.path.join(buildout_cfg['develop-eggs-directory'], '*.egg-link')
        for egg_link in glob.glob(pattern):
            with open(egg_link, 'rt') as f:
                path = f.readline().strip()
                if path:
                    all_develop_paths.add(path)

        egg_directory = os.path.join(buildout_cfg['eggs-directory'], '')
        develop_paths = []
        egg_paths = []
        other_paths = []
        for dist in ws:
            path = dist.location
            if path in all_develop_paths:
                if self.include_develop:
                    develop_paths.append(path)
            elif os.path.commonprefix([path, egg_directory]) == egg_directory:
                if self.include_eggs:
                    egg_paths.append(path)
            elif self.include_other:
                other_paths.append(path)

        paths = [
            *develop_paths,
            *egg_paths,
            *other_paths,
        ]
        for path in self._eggs.extra_paths:
            if '*' in path:
                paths += glob.glob(path)
            else:
                paths.append(path)

        # order preserving unique
        unique_paths = []
        for p in paths:
            if p not in unique_paths:
                unique_paths.append(p)

        return [
            os.path.normcase(os.path.abspath(os.path.realpath(path)))
            for path in unique_paths
        ]

    def _write_paths(self):
        lines = [
            f'<component name="libraryTable">',
            f'  <library name="{self._library_name}" type="python">',
            f'    <CLASSES>',
        ]
        for path in self.get_paths():
            path = path.replace('\\', r'\\')
            lines.append(
                f'      <root url="file://{escape(path)}" />'
            )
        lines.extend((
            '    </CLASSES>',
            '    <JAVADOC />',
            '    <SOURCES />',
            '  </library>',
            '</component>',
            '',
        ))

        result_dir = os.path.join(self.idea_dir, 'libraries')
        if not os.path.exists(result_dir):
            os.makedirs(result_dir, exist_ok=True)

        with open(self.result_path, 'wt') as f:
            f.write('\n'.join(lines))
        logging.getLogger(self.name).debug(
            f'The library table with list of eggs paths has created in the file "{self.result_path}".'
        )

    def _update_idea_project(self, iml_path: str):
        iml_data = open(iml_path, 'rt').read()
        if f'name="{self._library_name}"' not in iml_data:
            iml_xml = ElementTree.fromstring(iml_data)
            element = iml_xml.find('component[@name="NewModuleRootManager"]')
            if element:
                last_tail = element[-1].tail
                element[-1].tail = '\n    '
                order_entry = ElementTree.Element(
                    'orderEntry',
                    attrib={
                        'type': 'library',
                        'name': self._library_name,
                        'level': 'project',
                    },
                )
                order_entry.tail = last_tail
                element.append(order_entry)
                iml_data = ElementTree.tostring(
                    iml_xml,
                    encoding='utf-8',
                    xml_declaration=True,
                )
                open(iml_path, 'wb').write(iml_data)
                logging.getLogger(self.name).debug(
                    f'IDEA project file updated ({iml_path}).'
                )
