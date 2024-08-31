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
from os import path
from bpy.types import Operator
from ..props import download_zip_file_async


class IMESHH_OT_download(Operator):
    """Tooltip"""

    bl_idname = "object.imeshh_download"
    bl_label = "Download"

    # "Loading Download class..."

    @classmethod
    def poll(cls, context):
        from ..props import preview_collections

        return not preview_collections["web"].my_previews_loading

    def execute(self, context):
        #  "Downloading asset"
        from ..props import preview_collections

        selected = int(context.window_manager.web_asset_manager_previews)
        item = preview_collections["web"].my_previews_data[selected]
        basename = path.splitext(path.basename(item["image_url"]))[0]
        cat_path = [c["slug"] for c in item["categories"]]
        download_paths = (
            [
                path.join(c["parent_name"], c["slug"], basename)
                for c in item["categories"]
            ][0]
            if len(cat_path) == 1
            else path.join(cat_path[-2:][0], cat_path[-2:][1], basename)
        )

        download_zip_file_async(
            preview_collections["web"].my_previews_data[selected]["model"],
            download_paths,
        )
        return {"FINISHED"}


registry = [
    IMESHH_OT_download,
]
