"""
:Authors: cykooz
:Date: 03.12.2021
"""
import glob
import logging
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape

import zc.recipe.egg
from zc.buildout.buildout import bool_option


class Recipe:

    def __init__(self, buildout, name, options):
        self.name = name
        self.buildout = buildout
        self.idea_dir = Path(
            options.get('idea_dir') or f'{buildout["buildout"]["directory"]}/.idea'
        )
        self.result_path = self.idea_dir / 'libraries' / 'Buildout_Eggs.xml'
        self.include_develop = bool_option(options, 'include_develop', False)
        self.include_eggs = bool_option(options, 'include_eggs', True)
        self.include_other = bool_option(options, 'include_other', False)
        _ = options['eggs']  # Mute warning about unused option 'eggs'
        options = options.copy()
        options['relative-paths'] = 'false'
        self._eggs = zc.recipe.egg.Scripts(buildout, name, options)
        self._library_name = 'Buildout Eggs'

    def install(self):
        if not self.idea_dir.is_dir():
            logging.getLogger(self.name).debug(
                f'Directory of an Idea project ({self.idea_dir}) has not found.'
            )
            return ()
        iml_paths = list(self.idea_dir.glob('*.iml'))
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
        egg_link_dir = Path(buildout_cfg['develop-eggs-directory'])
        for egg_link in egg_link_dir.glob('*.egg-link'):
            with egg_link.open('rt') as f:
                path = Path(f.readline().strip())
                if path:
                    all_develop_paths.add(Path(path))

        egg_directory = Path(buildout_cfg['eggs-directory'])
        develop_paths = []
        egg_paths = []
        other_paths = []
        for dist in ws:
            path = Path(dist.location)
            if path in all_develop_paths:
                if self.include_develop:
                    develop_paths.append(path)
            elif egg_directory in path.parents:
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
                paths += [Path(p) for p in glob.glob(path)]
            else:
                paths.append(Path(path))

        # order preserving unique
        unique_paths = []
        for p in paths:
            if p not in unique_paths:
                unique_paths.append(p)

        return unique_paths

    def _write_paths(self):
        lines = [
            f'<component name="libraryTable">',
            f'  <library name="{self._library_name}" type="python">',
            f'    <CLASSES>',
        ]
        for path in self.get_paths():
            lines.append(
                f'      <root url="file://{escape(path.as_posix())}" />'
            )
        lines.extend((
            '    </CLASSES>',
            '    <JAVADOC />',
            '    <SOURCES />',
            '  </library>',
            '</component>',
            '',
        ))

        result_dir = self.idea_dir / 'libraries'
        if not result_dir.exists():
            result_dir.mkdir(exist_ok=True)

        with self.result_path.open('wt') as f:
            f.write('\n'.join(lines))
        logging.getLogger(self.name).debug(
            f'The library table with list of eggs paths has created in the file "{self.result_path}".'
        )

    def _update_idea_project(self, iml_path: Path):
        iml_data = iml_path.read_text()
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
                )
                with iml_path.open('wb') as f:
                    f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                    f.write(iml_data)
                logging.getLogger(self.name).debug(
                    f'IDEA project file updated ({iml_path}).'
                )
