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
from bpy.types import Panel
from .ui_main import IMESHH_main_panel
from ..auth import auth_file_exists
from .. import bl_info


class IMESHH_PT_auth(IMESHH_main_panel, Panel):
    version = ".".join(str(num) for num in bl_info["version"])
    bl_label = f"iMeshh Online v{version}"

    @classmethod
    def poll(cls, context):
        return not auth_file_exists()

    def draw(self, context):
        layout = self.layout
        col = layout.column(heading="Please authorize your addon")
        box = col.box()
        auth_props = (
            ("Authenticate", "KEY_DEHLT")
            if not auth_file_exists()
            else ("Authenticated", "KEYINGSET")
        )
        row = box.row()
        row.label(text="Please authorize your addon!")
        row = box.row()
        row.operator(
            "imeshh.auth_initiate_token", text=auth_props[0], icon=auth_props[1]
        )


registry = [
    IMESHH_PT_auth,
]
