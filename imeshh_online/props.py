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
import shutil
import json
import pathlib
from threading import Timer
from os import path
from bpy.utils import previews
from bpy.props import (
    IntProperty,
    BoolProperty,
    EnumProperty,
    StringProperty,
    PointerProperty,
    CollectionProperty,
)
from bpy.types import Scene, PropertyGroup, WindowManager
from zipfile import ZipFile
from . import auth
from . import functions as fn
from . import util as ut

ADDON = __package__
CURR_PREVIEW = []
preview_collections = {}
the_categories = {}

wp_site_url = "https://shopimeshhcom.bigscoots-staging.com/"
wp_json = wp_site_url + "wp-json/"
wp_blenderapi = wp_json + "blender_api/"
wp_v2 = wp_json + "wp/v2/"
wp_imeshh = wp_blenderapi + "imeshhs/"
wp_product_cat = wp_v2 + "product_cat/"


def on_change_main_folder(cls, context):
    # clear subdir display
    context.scene.imeshh_am.ui_folder_list.clear()
    # add subdir display
    folder_list = context.scene.imeshh_am.ui_folder_list.add()
    # set his start folder
    folder_list.start_folder = context.scene.imeshh_am.ui_main_folder
    update_and_set_preview(cls, context)


def update_search_bar(cls, context):
    update_and_set_preview(cls, context)


def update_and_set_preview(cls, context):
    """Call update to previews list value and set to first item."""
    previews = update_previews(cls, context)
    if previews:
        context.window_manager.asset_manager_previews = previews[0][0]


def update_previews(cls, context):
    """Return items of the preview panel."""
    global CURR_PREVIEW
    if (
        isinstance(cls, IMESHH_scene_properties)
        or isinstance(cls, UIFolder)
        or not CURR_PREVIEW
    ):
        if context.scene.imeshh_am.ui_folder_list:
            items = []
            # from . import preview_collections

            curr_dir = context.scene.imeshh_am.ui_folder_list[-1].start_folder
            if path.exists(curr_dir):
                assets = fn.get_all_sub_assets(curr_dir, context)
                img_ids = {}
                for asset in assets:
                    if asset.img_path:
                        id = fn.load_preview(
                            asset.img_path, preview_collections["main"]
                        )
                        img_ids[id] = asset.file_path
                for id in img_ids.keys():
                    name = fn.get_name(img_ids[id].split(path.sep)[-1], context)
                    # (identifier, name, description, icon, number)
                    items.append((img_ids[id], name, name, id, len(items)))
                if context.scene.imeshh_am.search_bar:
                    items = fn.filter_items(context, items.copy())
                CURR_PREVIEW = items
    return CURR_PREVIEW


def on_change_subdir(cls, context):
    # clear subdirectories display
    fn.remove_higher(context, cls)
    fn.remove_higher(context, cls)
    if hasattr(cls, "list_subdirs") and cls.list_subdirs != "All":
        # add a new sub display
        folder_list = context.scene.imeshh_am.ui_folder_list.add()
        # set his start folder
        folder_list.start_folder = cls.list_subdirs
    update_and_set_preview(cls, context)


def on_change_web_categories(cls, context):
    # clear subdir display
    context.scene.imeshh_am.ui_web_list.clear()
    # add subdir display
    folder_list = context.scene.imeshh_am.ui_web_list.add()
    # Reset main folder dropdown value to 0
    items = fn.get_tab_main_dirs(cls, context)
    if items:
        context.scene.imeshh_am.ui_main_folder = items[0][0]
    # set his start folder
    folder_list.start_folder = context.scene.imeshh_am.ui_main_folder
    update_and_set_preview(cls, context)


def on_change_tab(cls, context):
    # clear subdir display
    context.scene.imeshh_am.ui_folder_list.clear()
    # add subdir display
    folder_list = context.scene.imeshh_am.ui_folder_list.add()
    # Reset main folder dropdown value to 0
    items = fn.get_tab_main_dirs(cls, context)
    if items:
        context.scene.imeshh_am.ui_main_folder = items[0][0]
    # set his start folder
    folder_list.start_folder = context.scene.imeshh_am.ui_main_folder
    update_and_set_preview(cls, context)


def on_change_dld(cls, context):
    # clear subdir display
    context.scene.imeshh_am.ui_web_list.clear()
    # add subdir display
    folder_list = context.scene.imeshh_am.ui_web_list.add()
    # Reset main folder dropdown value to 0
    items = fn.get_tab_main_dirs(cls, context)
    if items:
        context.scene.imeshh_am.ui_main_folder = items[0][0]
    # set his start folder
    folder_list.start_folder = context.scene.imeshh_am.ui_main_folder
    update_and_set_preview(cls, context)


def load_previews_to_disk(self, context, search):
    """Save Load previews to Disk for faster reload"""


def load_previews(self, context, search):
    """EnumProperty callback"""
    global wp_imeshh
    global wp_product_cat

    enum_items = []

    if context is None:
        return enum_items

    pcoll = preview_collections["web"]
    request = auth.get_access(wp_imeshh)

    if 200 != request.status_code:
        # TODO: Show alert message.
        print("Failed to access API")
        return enum_items

    json_str = request.content

    if not json_str:
        return enum_items

    data = json.loads(json_str)
    pcoll.clear()

    json_data = json.dumps(data, indent=4)
    # print(json_data)
    if data["results"]:
        cat_path = ""
        idx = 0
        for item in data["results"]:
            cat_path = [c["slug"] for c in item["categories"]]
            parent_cat = next(
                (
                    c["parent"]
                    for c in item["categories"]
                    if len(item["categories"]) > 0
                ),
                None,
            )
            if parent_cat:
                parent_data_url = auth.get_access(
                    wp_product_cat + str(parent_cat) + "/"
                )
                parent_data_str = parent_data_url.content
                parent_data_load = json.loads(parent_data_str)
                parent_cat_name = parent_data_load["slug"]

            category = next(
                (c["slug"] for c in item["categories"] if len(item["categories"]) > 0),
                None,
            )
            if category:
                cat_name = category

            basename = os.path.splitext(os.path.basename(item["image_url"]))[0]
            suffix = (
                os.path.join(parent_cat_name, cat_name, basename)
                if len(cat_path) == 1
                else os.path.join(cat_path[-2:][0], cat_path[-2:][1], basename)
            )

            image_path = fn.get_downloaded_file(suffix, item["image_url"])

            icon = pcoll.get(image_path)
            if not icon:
                if item["name"] in pcoll:
                    continue
                thumb = pcoll.load(item["name"], image_path, "IMAGE")
            else:
                thumb = pcoll[item["name"]]

            new_data = {"parent_name": parent_cat_name}
            cat_list = item["categories"]
            for c in cat_list:
                c.update(new_data)

            enum_items.append((str(item["id"]), item["name"], "", thumb.icon_id, idx))
            pcoll.my_previews_data[item["id"]] = item

            idx += 1

    pcoll.my_previews = enum_items
    pcoll.my_previews_search_hash = search

    ut.ui_redraw()
    pcoll.my_previews_loading = False
    # print(pcoll.my_previews_data)

    # print(preview_collections["web"])

    return pcoll.my_previews


def load_web_categories(self, context):
    """EnumProperty callback"""

    global ADDON
    global wp_imeshh
    # print("Load Web Cat...")
    enum_items = []

    if context is None:
        return enum_items

    # Get the categories list from web (defined in register func).
    pcoll = the_categories["web"]
    prefs = context.preferences.addons[ADDON].preferences

    # if ":" not in prefs["my_login"]:
    #     # TODO: Show alert message.
    #     print("Login not set in preferences")
    #     return enum_items

    request = auth.get_access(wp_imeshh)

    if 200 != request.status_code:
        # TODO: Show alert message.
        print("Failed to access API")
        return enum_items

    json_str = request.content

    if not json_str:
        return enum_items

    data = json.loads(json_str)
    pcoll.clear()

    pcoll.my_categories = enum_items
    # pcoll.my_categories_search_hash = search
    ut.ui_redraw()
    # data.screens["Layout"].areas[3].regions[2].tag_redraw()

    pcoll.my_categories_loading = False

    return pcoll.my_categories


def enum_previews_from_directory_items(self, context):
    """! Loads imeges from web"""
    enum_items = []

    if context is None:
        return enum_items

    # from . import preview_collections

    pcoll = preview_collections["web"]

    if pcoll.my_previews_loading:
        return enum_items

    search = context.scene.imeshh_am.search_bar.lower()

    if pcoll.my_previews_search_hash == search:
        return pcoll.my_previews

    pcoll.my_previews_loading = True

    t = Timer(0.2, load_previews, [self, context, search])

    t.start()
    # print(preview_collections)
    return pcoll.my_previews


def enum_categories_from_directory_items(self, context):
    """! Loads categories from web"""

    # "Load Enum Categories..."
    enum_items = []
    search = context.scene.imeshh_am.search_bar.lower()

    if context is None:
        return enum_items

    pcoll = the_categories["web"]

    if pcoll.my_categories_loading:
        return enum_items

    if pcoll.my_categories_search_hash == search:
        return pcoll.my_categories

    pcoll.my_categories_loading = True

    t = Timer(0.2, load_web_categories, [self, context])
    t.start()

    # print(the_categories)

    return pcoll.my_categories


def download_zip_file_async(url, suffix=False):
    preview_collections["main"].my_previews_loading = True
    bpy.context.scene.imeshh_am.downloading = True
    t = Timer(0.1, download_zip_file, [url, suffix])
    t.start()
    # ut.ui_redraw()


def download_zip_file(url, suffix=False):
    file = fn.get_downloaded_file(suffix, url)
    file_name = pathlib.Path(file).stem
    # print(file_name)
    imeshh_tmp_dir = fn.get_user_folder(suffix)

    # if not path.exists(path.join(imeshh_tmp_dir, file_name)):
    try:
        with ZipFile(file, "r") as zObject:
            for info in zObject.infolist():
                if not info.is_dir():
                    pathlist = [p for p in info.filename.split(os.sep, 1)]
                    filepath = (
                        os.path.join(imeshh_tmp_dir, pathlist[1])
                        if len(pathlist) > 1
                        else os.path.join(imeshh_tmp_dir, pathlist[0])
                    )
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with zObject.open(info) as source, open(filepath, "wb") as target:
                        shutil.copyfileobj(source, target)
    except:
        pass

    files = fn.get_blend_files(imeshh_tmp_dir)

    for file in files:
        with bpy.data.libraries.load(file, link=False) as (data_from, data_to):
            data_to.objects = data_from.objects

        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)

    preview_collections["main"].my_previews_loading = False
    bpy.context.scene.imeshh_am.downloading = False
    # ut.ui_redraw()


class UIFolder(PropertyGroup):
    start_folder: StringProperty(name="start folder", default="")  # type: ignore
    list_subdirs: EnumProperty(
        items=fn.get_subdirs_as_items,
        name="Subdirs",
        description="Sub directories",
        update=on_change_subdir,
    )  # type: ignore
    idx: IntProperty(name="idx", default=-1)  # type: ignore


class IMESHH_scene_properties(PropertyGroup):
    blend: EnumProperty(
        # TODO: load this from json categories
        items=[("cycles", "Cycles", "Test", 0), ("corona", "Corona", "Some", 1)],
        name="Blend",
        description="Select blend",
    )  # type: ignore
    current_folder: StringProperty(name="current_folder", default="")  # type: ignore

    ui_folder_list: CollectionProperty(type=UIFolder)  # type: ignore

    ui_web_list: CollectionProperty(type=UIFolder)  # type: ignore

    ui_main_folder: EnumProperty(
        items=fn.get_tab_main_dirs,
        name="directory",
        description="main root directory",
        update=on_change_main_folder,
    )  # type: ignore

    # TODO: load this from json categories
    ui_web_categories: EnumProperty(
        # items=[('architectural', 'Architectural', '', 0),('beds', 'Beds', '', 0),('rugs', 'Rugs', '', 0),('bathroom', 'Bathroom', '', 0),('clohting', 'CClothing', '', 3),('decorations', 'Decorations', '', 0),('dinning', 'Dinning', '', 0),('Electronics', 'Electronics', '', 0),('Food_drink', 'Food & Drink', '', 0)],
        # (identifier, name, description, icon, number)
        items=[("load", "Loading...", "TIME", 0)],
        # items=load_web_categories(),
        name="3D Models",
        description="web api server - products",
        update=on_change_web_categories,
    )  # type: ignore

    snap: BoolProperty(name="snap", default=False)  # type: ignore
    search_bar: StringProperty(name="searchbar", default="", update=update_search_bar)  # type: ignore
    # Tabs
    tabs: EnumProperty(
        # (identifier, name, description, icon, number)
        items=[
            ("OBJECT", "Object", "Object tab", "MESH_MONKEY", 0),
            ("MATERIAL", "Material", "Material tab", "MATERIAL", 1),
            ("HDRI", "Hdri", "Hdri tab", "WORLD_DATA", 2),
        ],
        name="Tabs",
        description="Selected tab",
        update=on_change_tab,
    )  # type: ignore

    downloads: EnumProperty(
        # (identifier, name, description, icon, number)
        items=[
            ("OBJECT", "Object", "Object tab", "MESH_MONKEY", 0),
            ("MATERIAL", "Material", "Material tab", "MATERIAL", 1),
            ("SCENE", "Scene", "Material tab", "CAMERA_DATA", 2),
            ("HDRI", "Hdri", "Hdri tab", "WORLD_DATA", 3),
        ],
        name="Downloads",
        description="Selected model",
        update=on_change_dld,
    )  # type: ignore
    the_im_url: StringProperty(name="the_im_url", default="")  # type: ignore

    asset_manager_collection_import: BoolProperty(
        name="Import other collections if available",
        default=False,
        description="If there are multiple collections in this file, and you don't want to just import the scene collection, then tick this box",
    )  # type: ignore

    asset_manager_auto_rename: BoolProperty(
        name="Auto rename Collection to file name",
        default=True,
        description="This addon, by default, will just import the scene collection. This will then auto-rename the scene collection to the assets file name. This will make it easier to find in the library",
    )  # type: ignore

    asset_manager_ignore_camera: BoolProperty(
        name="Ignore camera when importing",
        default=True,
        description="This addon will ignore all cameras by default. If you want to import cameras then untick this box",
    )  # type: ignore

    downloading: BoolProperty(default=False)  # type: ignore


class PathString(PropertyGroup):
    """!
    Defines the path for local folders and types of objects to save there
    """

    path: StringProperty(subtype="DIR_PATH")  # type: ignore
    name: StringProperty()  # type: ignore
    type_dir: EnumProperty(
        # (identifier, name, description, icon, number)
        items=[
            ("OBJECT", "Object", "Object tab", "MESH_MONKEY", 0),
            ("MATERIAL", "Material", "Material tab", "MATERIAL", 1),
            ("HDRI", "Hdri", "Hdri tab", "WORLD_DATA", 2),
        ],
        name="Types",
        description="Selected tab",
    )  # type: ignore


registry = [
    PathString,
    UIFolder,
    IMESHH_scene_properties,
]


def register():
    # Load the Asset Manager UI
    Scene.imeshh_am = PointerProperty(type=IMESHH_scene_properties)

    # Main
    preview_coll = previews.new()
    # Main preview enum
    WindowManager.asset_manager_previews = EnumProperty(items=update_previews)
    preview_collections["main"] = preview_coll

    # Web
    preview_coll = previews.new()
    preview_coll.my_previews = []
    preview_coll.my_previews_data = {}
    preview_coll.my_previews_search = ""
    preview_coll.my_previews_search_hash = -1
    preview_coll.my_previews_loading = False
    # Web preview enum
    WindowManager.web_asset_manager_previews = EnumProperty(
        items=enum_previews_from_directory_items
    )
    WindowManager.imeshh_dir = StringProperty(name="Default Folder", subtype="DIR_PATH")
    preview_collections["web"] = preview_coll

    # Categories enum
    WindowManager.web_categories_list = EnumProperty(items=load_web_categories)
    # WindowManager.web_categories_list = bpy.props.EnumProperty(items=utils.enum_previews_from_directory_items)
    the_categories["web"] = []


def unregister():
    del Scene.imeshh_am
    del WindowManager.asset_manager_previews
    del WindowManager.imeshh_dir

    for preview_coll in preview_collections.values():
        previews.remove(preview_coll)

    preview_collections.clear()
