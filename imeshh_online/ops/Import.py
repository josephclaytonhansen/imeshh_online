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
from bpy.props import BoolProperty
from bpy import ops
from ..functions import import_object, import_material, import_hdr_cycles

# from .. import utils, hdr_nodes


class IMESHH_OT_import_object(Operator):
    bl_idname = "imeshh.import_object"
    bl_label = "Append Object"
    bl_description = "Appends object to scene"
    bl_options = {"REGISTER", "UNDO"}
    link: BoolProperty(False)  # type: ignore

    def store_tool_settings(self, context):
        ts = context.scene.tool_settings
        self.settings = {
            "use_snap": ts.use_snap,
            "snap_elements": ts.snap_elements,
            "snap_target": ts.snap_target,
            "use_snap_align_rotation": ts.use_snap_align_rotation,
        }

    def restore_tool_settings(self, context):
        if hasattr(self, "settings"):
            for attr in self.settings.keys():
                try:
                    setattr(context.scene.tool_settings, attr, self.settings[attr])
                except:
                    continue

    def execute(self, context):
        import_object(context, link=self.link)
        if context.scene.imeshh_am.snap:
            self.store_tool_settings(context)
            context.window_manager.modal_handler_add(self)
            context.scene.tool_settings.use_snap = True
            context.scene.tool_settings.snap_elements = {"FACE"}
            context.scene.tool_settings.snap_target = "CLOSEST"
            context.scene.tool_settings.use_snap_align_rotation = False
            ops.transform.translate("INVOKE_DEFAULT")
            return {"RUNNING_MODAL"}
        else:
            return {"FINISHED"}

    def modal(self, context, event):
        if event.type in {"RIGHTMOUSE", "ESC", "LEFTMOUSE"}:
            self.restore_tool_settings(context)
            return {"FINISHED"}
        return {"RUNNING_MODAL"}


class IMESHH_OT_import_material(Operator):
    bl_idname = "imeshh.import_material"
    bl_label = "Import Material"
    bl_description = "Imports material to scene"
    link: BoolProperty(False)  # type: ignore

    def execute(self, context):
        import_material(context, link=self.link)
        return {"FINISHED"}


class IMESHH_OT_import_hdr(Operator):
    bl_idname = "imeshh.import_hdr"
    bl_label = "Import New HDRI"
    bl_description = "Imports an HDRI into the world material"

    def execute(self, context):
        import_hdr_cycles(context)

        return {"FINISHED"}


registry = [
    IMESHH_OT_import_object,
    IMESHH_OT_import_material,
    IMESHH_OT_import_hdr,
]
