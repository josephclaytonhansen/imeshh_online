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
import bpy
import os
import tempfile
import json
from . import auth
from .props import PathString
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, CollectionProperty
from bpy.app.handlers import persistent, load_post, load_pre

addon_name = __package__


def prefs_file_exists():
    prefs_json = os.path.join(auth.get_addon_dir(), "prefs.json")
    return os.path.exists(prefs_json)


class IMESHH_OT_save_preferences_json(Operator):
    """Save User Preferences as Json file"""

    bl_idname = "imeshh.save_preferences_json"
    bl_label = "Save Preferences"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        global addon_name
        prefs = context.preferences.addons[addon_name].preferences
        prefs_data = (prefs.default_folder,)
        prefs_json = os.path.join(auth.get_addon_dir(), "prefs.json")

        with open(prefs_json, "w") as file:
            json.dump(prefs_data, file, indent=2)

        return {"FINISHED"}


class IMESHH_addon_preferences(AddonPreferences):
    """!
    Loads the preferences panel list for iMeshh addon

    @param bpy.types.AddonPreferences Class: The panel to load this widget
    """

    bl_idname = __package__

    # Load the path names and icons
    paths: CollectionProperty(type=PathString)  # type: ignore
    scale_ui_popup: IntProperty(name="Thumbnail scale", default=8)  # type: ignore
    # my_login: StringProperty(name="Login Key", default="XXXX")  # type: ignore
    default_folder: StringProperty(
        name="Default Folder",
        # default=str(Path.home()),
        default=str(tempfile.gettempdir()),
        subtype="DIR_PATH",
    )  # type: ignore

    def draw(self, context):
        layout = self.layout
        row = self.layout.row()
        row.prop(self, "scale_ui_popup")
        layout.use_property_split = False
        layout.use_property_decorate = False

        wm = context.window_manager
        box = layout.box()

        auth_props = (
            ("Authenticate", "KEY_DEHLT")
            if not auth.auth_file_exists()
            else ("Authenticated", "KEYINGSET")
        )
        row = box.row()
        row.prop(self, "default_folder")
        row = box.row()
        row.operator(
            "imeshh.auth_initiate_token", text=auth_props[0], icon=auth_props[1]
        )
        row.operator(
            "imeshh.save_preferences_json", text="Save Settings", icon="IMPORT"
        )


def load_prefs_json():
    global addon_name

    if prefs_file_exists():
        prefs_json = os.path.join(auth.get_addon_dir(), "prefs.json")
        prefs = bpy.context.preferences.addons[addon_name].preferences

        with open(prefs_json, "r") as file:
            prefs_data = json.load(file)
            prefs.default_folder = prefs_data[0]

        print("Loaded iMeshh User Settings")


# ---------REGISTER ----------.

registry = [
    IMESHH_addon_preferences,
    IMESHH_OT_save_preferences_json,
]
