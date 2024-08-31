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

from bpy.types import Operator
from bpy.props import IntProperty

addon = __package__


class IMESHH_OT_add_folder_path(Operator):
    """!
    Operate the local folders, adding a new forlder to the paths
    """

    bl_idname = "imeshh.add_folder_path"
    bl_label = "Add folder entry"
    bl_description = "Add a row to config iMeshh folder"
    bl_options = {"UNDO", "REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global addon
        col = context.preferences.addons[addon].preferences.paths
        col.add()
        return {"FINISHED"}


class IMESHH_OT_remove_folder_path(Operator):
    """!
    Operate the local folders, removing forlder from the paths
    """

    bl_idname = "imeshh.remove_folder_path"
    bl_label = "Remove folder entry"
    bl_description = "Remove a row to config iMeshh folder"
    bl_options = {"UNDO", "REGISTER"}
    index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global addon
        col = context.preferences.addons[addon].preferences.paths
        col.remove(self.index)
        return {"FINISHED"}


registry = [
    IMESHH_OT_add_folder_path,
    IMESHH_OT_remove_folder_path,
]
