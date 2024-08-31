# Copyright (C) 2024 Aditia A. Pratama | aditia.ap@gmail.com
#
# This file is part of imeshh_am.
#
# imeshh_am is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# imeshh_am is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with imeshh_am.  If not, see <https://www.gnu.org/licenses/>.

from bpy.utils import previews
from os import path, listdir
from .functions import get_addon_dir

__icon_manager__ = None


class IconManager:
    """Singleton class for handling icons in the Blender previews system."""

    icons = None
    _supported_formats = ".png"

    def __init__(self):
        self.icons = previews.new()
        template_dir = get_addon_dir()
        icons_dir = path.normpath(path.join(template_dir, "icons"))
        for icon_file in sorted(listdir(icons_dir)):
            name_tokens = path.splitext(icon_file)
            filepath = path.join(icons_dir, icon_file)
            if name_tokens[1] in self._supported_formats:
                self.icons.load(name_tokens[0], filepath, "IMAGE")
            else:
                print(f"Error: Unsupported icon format '{name_tokens[1]}': {filepath}")

    def unregister(self):
        """Remove the template's icon previews from Blender."""
        previews.remove(self.icons)
        self.icons = None


def get_icon(name):
    """Get an internal Blender icon ID from an icon name."""
    try:
        return __icon_manager__.icons[name].icon_id
    except KeyError:
        print(f"Error: Failed to find icon named '{name}'!")
        return None


def register():
    global __icon_manager__
    if __icon_manager__ is None:
        __icon_manager__ = IconManager()


def unregister():
    global __icon_manager__
    __icon_manager__.unregister()
    __icon_manager__ = None
