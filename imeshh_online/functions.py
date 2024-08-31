# Copyright (C) 2024 Aditia A. Pratama | aditia.ap@gmail.com
#
# This file is part of imeshh_online.
#
# imeshh_online is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# imeshh_online is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with imeshh_online.  If not, see <https://www.gnu.org/licenses/>.
import bpy
import re
import os
import hashlib
import pathlib
import requests
from os import path, makedirs, listdir
from typing import List, Tuple
from dataclasses import dataclass
from bpy.utils import user_resource, script_paths
from bpy import app, data
from .constant import EXT
from . import dependencies

dependencies.preload_modules()  # type: ignore
from progress.bar import IncrementalBar  # type: ignore

ADDON = __package__


@dataclass
class Asset:
    file_path: str = ""
    img_path: str = ""


def get_name(filepath: str, context) -> str:
    """Return epured file name of given filepath."""
    curr_tab = context.scene.imeshh_am.tabs
    name = filepath.split(path.sep)[-1]
    for ext in EXT[curr_tab]:
        name = name.replace(ext, "")
    name = name.replace(" ", "-")
    return name


def zipfilepath(item):
    global ADDON
    prefs = bpy.context.preferences.addons[ADDON].preferences
    imeshh_dir = prefs.default_folder
    basename = path.splitext(path.basename(item["model"]))[0]
    cat_path = [c["slug"] for c in item["categories"]]
    download_paths = (
        [path.join(c["parent_name"], c["slug"], basename) for c in item["categories"]][
            0
        ]
        if len(cat_path) == 1
        else path.join(cat_path[-2:][0], cat_path[-2:][1], basename)
    )
    return os.path.join(imeshh_dir, download_paths, path.basename(item["model"]))


def addon_location():
    global ADDON
    scripts_path_to_check = []

    for path in script_paths():
        scriptpath = os.path.join(path, "addons", ADDON)
        scripts_path_to_check.append(scriptpath)

    return next((path for path in scripts_path_to_check if os.path.exists(path)), None)


def get_addon_dir():
    global ADDON
    user_resources = user_resource("SCRIPTS")
    return path.join(user_resources, "addons", ADDON, "lib")


def get_user_folder(suffix=False):
    global ADDON
    prefs = bpy.context.preferences.addons[ADDON].preferences
    imeshh_dir = prefs.default_folder

    if not imeshh_dir.endswith("/"):
        imeshh_dir += "/"

    if suffix:
        imeshh_dir += suffix + "/"

    return imeshh_dir


def get_tab_main_dirs(cls, context):
    """Return as enum items all main directories of the current tab.

    (identifier, name, description, icon, number)
    Return : [('path', 'name', path, 'NONE', idx), ...]"""
    global ADDON
    dir_items = []
    for dir in context.preferences.addons[ADDON].preferences.paths:
        if dir.type_dir == context.scene.imeshh_am.tabs:
            dir_items.append((dir.path, dir.name, dir.path, "NONE", len(dir_items)))
    return dir_items


def get_downloaded_file(type, url):
    imeshh_tmp_dir = get_user_folder(type)

    if not path.exists(imeshh_tmp_dir):
        makedirs(imeshh_tmp_dir)

    fname = os.path.splitext(os.path.basename(url))[0]
    extension = pathlib.Path(url).suffix
    file_path = imeshh_tmp_dir + fname + extension
    if not os.path.exists(file_path):
        print(f"Download file : {fname}{extension}")
        chunkSize = 10240
        if url.startswith("http") and not path.isfile(file_path):
            img_data = requests.get(url, stream=True)

            try:
                with open(file_path, "wb") as f:
                    pbar = IncrementalBar(
                        "Downloading",
                        max=int(img_data.headers["Content-Length"]) / chunkSize,
                        suffix="%(percent)d%%",
                    )
                    for chunk in img_data.iter_content(chunk_size=chunkSize):
                        if chunk:  # filter out keep-alive new chunks
                            pbar.next()
                            f.write(chunk)
                    pbar.finish()

                # with open(file_path, "wb") as handler:
                #     handler.write(img_data)

            except PermissionError:
                pass

            print(f"Succeesfully downloaded {fname}{extension}")
    return file_path


def contains_filetype(file_list, ext: str) -> bool:
    for f in file_list:
        if f.lower().endswith(ext):
            return True
    return False


def enum_members_from_type(rna_type, property):
    prop = rna_type.bl_rna.properties[property]
    return [e.identifier for e in prop.enum_items]


def enum_members_from_instance(data, property):
    """get all available entries for an enum property
    - data : (AnyType) data from wich tot ake property
    - property : (string) Edientifier property in data"""
    return enum_members_from_type(type(data), property)


def without_ext(file: str) -> str:
    return ".".join(file.split(".")[0:-1])


def is_asset_dir(directory, context):
    """Check if curr dir contain searched files (blend/hdr) and subdir not contain anyone
    and do not have more subfolder."""

    dirs, files = get_dir_content(directory)
    curr_tab = context.scene.imeshh_am.tabs
    # check that directory got at least one searched file
    if not contains_filetype(files, EXT[curr_tab]):
        return False
    if curr_tab in ["OBJECT", "MATERIAL"]:
        # check subdirs don't have searched files
        for dir in dirs:
            l_dirs, l_file = get_dir_content(dir)
            if contains_filetype(l_file, EXT[curr_tab]) or l_dirs:
                return False
    elif curr_tab == "HDRI":
        return False
    return True


def filter_items(context, items):
    to_del = []
    for item in items:
        # id -> asset.file_path
        if context.scene.imeshh_am.search_bar.lower() not in item[0].lower():
            to_del.append(item)
    for item in to_del:
        items.remove(item)
    return items


def contains_blend(file_list):
    for f in file_list:
        if f.lower().endswith(".blend"):
            return True
    return False


def load_preview(img_path: str, pcoll):
    """Load preview if needed and return it id."""
    if img_path in pcoll:
        return pcoll[img_path].icon_id
    else:
        img_type = "IMAGE"
        if img_path.endswith(".blend"):
            img_type = "BLEND"
        thumb = pcoll.load(img_path, img_path, img_type)
        return thumb.icon_id


def get_selected_file(context):
    return context.window_manager.asset_manager_previews


def get_selected_blend(context):
    file = get_selected_file(context)
    return file


def is_2_80():
    return app.version >= (2, 80, 0)


def select(obj):
    if is_2_80():
        obj.select_set(True)
    else:
        obj.select = True


def is_blend(file):
    return file.lower().endswith((".blend",))


def get_data_colls():
    if hasattr(data, "collections"):
        return data.collections
    elif hasattr(data, "groups"):
        return data.groups


def remove_higher(context, cls):
    to_del = []
    find = False
    for idx, f_list in enumerate(context.scene.imeshh_am.ui_folder_list):
        if find:
            to_del.append(idx)
        if f_list == cls:
            find = True
    for idx in to_del:
        context.scene.imeshh_am.ui_folder_list.remove(idx)


def create_instance_collection(collection, parent_collection):
    empty = data.objects.new(name=collection.name, object_data=None)
    empty.instance_collection = collection
    empty.instance_type = "COLLECTION"
    parent_collection.objects.link(empty)
    return empty


def select_coll_to_import(collection_names):
    """Select wich collection import following the file type and user preferences
    - collection_names : collections names array avalaibles in the blender file
    """
    # file has no collections (blander version < blender 2.80)
    if not collection_names:
        return None

    # User ask for import all collections of blend file
    if bpy.context.scene.imeshh_am.asset_manager_collection_import == True:
        return collection_names

    # there is a collection call 'Collection'
    if "Collection" in collection_names:
        return ["Collection"]

    # there is no 'Collection' but something like 'Collection.xxx'
    colls = []
    for col in collection_names:
        if re.match(r"(^collection)", col, re.IGNORECASE):
            colls.append(col)
    if colls:
        return colls
    # there is collection but no match, import all
    else:
        return collection_names


def link_collections(blend_file, parent_col):
    """Import collections of a blend file as instances collection if it's possible
    - blend_file : file with collection to import
    - parent_col : collection of actual file wich will get as child news instances collections
    """
    objects_linked = False
    with bpy.data.libraries.load(blend_file, link=True) as (data_from, data_to):
        data_to.collections = select_coll_to_import(data_from.collections)
        if data_to.collections == None:
            objects_linked = True
            data_to.objects = data_from.objects

    # fix if color space unrecognized
    for img in bpy.data.images:
        if img.colorspace_settings.name == "":
            possible_values = img.colorspace_settings.bl_rna.properties[
                "name"
            ].enum_items.keys()
            if "sRGB" in possible_values:
                img.colorspace_settings.name = "sRGB"
    # no collection found in blend file
    if objects_linked:
        for obj in data_to.objects:
            if (
                bpy.context.scene.imeshh_am.asset_manager_ignore_camera
                and obj.type == "CAMERA"
            ):
                continue
            parent_col.objects.link(obj)
            select(obj)
    else:
        # create all instances collections
        for col in data_to.collections:
            instance = create_instance_collection(col, parent_col)
            if (
                re.match(r"(^collection)", instance.name, re.IGNORECASE)
                and bpy.context.scene.imeshh_am.asset_manager_auto_rename == True
            ):
                instance.name = parent_col.name
            select(instance)


def get_asset_col_name():
    asset_col_name = "_".join(["Imeshh_Assets", bpy.context.scene.name])
    return asset_col_name


def append_blend(blend_file, link=False):
    coll_name = path.splitext(path.basename(blend_file))[0].title()
    obj_coll = get_data_colls().new(coll_name)

    if is_2_80():
        asset_coll = get_data_colls()[get_asset_col_name()]
        asset_coll.children.link(obj_coll)

    if not link:
        with bpy.data.libraries.load(blend_file, link=link) as (data_from, data_to):
            data_to.objects = data_from.objects
        # fix if color space unrecognized
        for img in bpy.data.images:
            if img.colorspace_settings.name == "":
                # get colorspace possible values
                possible_values = img.colorspace_settings.bl_rna.properties[
                    "name"
                ].enum_items.keys()
                if "sRGB" in possible_values:
                    img.colorspace_settings.name = "sRGB"

        for obj in data_to.objects:
            if (
                bpy.context.scene.imeshh_am.asset_manager_ignore_camera
                and obj.type == "CAMERA"
            ):
                continue
            obj_coll.objects.link(obj)

            select(obj)
    else:
        link_collections(blend_file, obj_coll)

    bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)


def import_object(context, link):
    # active_layer = context.view_layer.active_layer_collection

    # Deselect all objects
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
    bpy.ops.object.select_all(action="DESELECT")

    # 2.79 and 2.80 killing me.
    if is_2_80():
        if get_asset_col_name() not in bpy.context.scene.collection.children.keys():
            asset_coll = bpy.data.collections.new(get_asset_col_name())
            context.scene.collection.children.link(asset_coll)

    blend = get_selected_blend(context)
    if blend:
        append_blend(blend, link)


def import_material(context, link):
    active_ob = context.active_object
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
    bpy.ops.object.select_all(action="DESELECT")

    blend = get_selected_blend(context)
    files = []
    with bpy.data.libraries.load(blend) as (data_from, data_to):
        for name in data_from.materials:
            files.append({"name": name})
    action = bpy.ops.wm.link if link else bpy.ops.wm.append
    action(directory=blend + "/Material/", files=files)

    if active_ob is not None:
        for file in files:
            mat = bpy.data.materials[file["name"]]
            active_ob.data.materials.append(mat)
            select(active_ob)


def get_blend_files(folder):
    files = []
    for path in pathlib.Path(folder).rglob("*.blend"):
        files.append(str(path))
    return files


def get_dir_content(parent_dir: str) -> Tuple[List[str], List[str]]:
    """Return directories and asset contained in parent_dir.

    Return : ( directories ([str]), files ([str]))
    """
    dirs = []
    files = []
    for element in listdir(parent_dir):
        element_fullpath = path.join(parent_dir, element)
        if path.isdir(element_fullpath):
            dirs.append(element_fullpath)
        else:
            files.append(element_fullpath)
    return (dirs, files)


def get_subdirs_as_items(cls, context):
    items = [("All", "All", "All", "NONE", 0)]
    if path.exists(cls.start_folder):
        curr_dir = cls.start_folder
        dirs, files = get_dir_content(curr_dir)
        for idx, dir_path in enumerate(dirs):
            # if not is_asset_dir(dir_path, context):
            name = dir_path.split(path.sep)[-1]
            items.append((dir_path, name, dir_path, "NONE", idx + 1))
    return items


def make_asset_from_afolder(dir_path, files, context):
    if files:
        curr_tab = context.scene.imeshh_am.tabs
        if curr_tab in ["OBJECT", "MATERIAL"]:  # hdri do not need mapping
            assets = []
            img_paths = []
            blend_paths = []
            for f in files:
                if f.lower().endswith((".png", ".jpg")):
                    img_paths.append(path.join(dir_path, f))
                elif f.lower().endswith(EXT[curr_tab]):
                    blend_paths.append(path.join(dir_path, f))
            for blend_path in blend_paths:
                if img_paths:
                    # Map 1st image of the stack
                    img_path = img_paths.pop(0)
                else:
                    # Image can be generated from blend file
                    img_path = blend_path
                assets.append(Asset(file_path=blend_path, img_path=img_path))
            return assets
    return None


def make_assets_from_files(parent_dir, files: List[str], context):
    """Make an asset with blend an image with the same name."""

    assets = []
    curr_tab = context.scene.imeshh_am.tabs
    if files:
        if curr_tab in ["OBJECT", "MATERIAL"]:
            blend_files = []
            # TODO Not compatible with list,
            # need to change if multiple ext for material or object
            ext_not_dot = EXT[curr_tab][0].replace(".", "")
            # gather all blend files
            for f in files:
                if f.lower().endswith(EXT[curr_tab]):
                    blend_files.append(without_ext(f))
            # remove them from original list
            for b_file in blend_files:
                files.remove(".".join([b_file, ext_not_dot]))

            # create Asset with blend and images with same name
            for f in files:
                no_ext_f = without_ext(f)
                if f.lower().endswith((".png", ".jpg")) and no_ext_f in blend_files:
                    blend_files.remove(no_ext_f)
                    assets.append(
                        Asset(
                            file_path=path.join(
                                parent_dir,
                                (".".join([no_ext_f, ext_not_dot])),
                            ),
                            img_path=path.join(parent_dir, f),
                        )
                    )

            # create Asset with no matched blend file
            for b_file in blend_files:
                f_path = path.join(parent_dir, (".".join([b_file, ext_not_dot])))
                assets.append(Asset(file_path=f_path, img_path=f_path))
        elif curr_tab == "HDRI":
            for f in files:
                if f.lower().endswith(EXT[curr_tab]):
                    full_path = path.join(parent_dir, f)
                    assets.append(Asset(file_path=full_path, img_path=full_path))
    return assets


def get_dir_assets(dir, files, context):
    "Return assets contained in files depending on dirtype."
    assets = []
    if is_asset_dir(dir, context):
        assets = make_asset_from_afolder(dir, files, context)
    else:
        assets = make_assets_from_files(dir, files, context)
    return assets


def get_all_sub_assets(parent_dir: str, context) -> List[str]:
    """Return all find below parent_dir in the file hierarchy.

    Return : files ([str])"""
    all_assets = []
    dirs_to_explore = [parent_dir]
    while dirs_to_explore:
        temp_explore_list = dirs_to_explore.copy()
        for dir in temp_explore_list:
            dirs, files = get_dir_content(dir)
            assets = get_dir_assets(dir, files, context)
            if assets:
                all_assets.extend(assets)
            dirs_to_explore.remove(dir)
            dirs_to_explore.extend(dirs)

    return all_assets


def import_hdr_cycles(context):
    hdr = get_selected_file(context)

    if not hdr:
        return

    scene = context.scene
    world = scene.world
    world.use_nodes = True
    node_tree = world.node_tree

    path_nodes_blend = path.join(path.dirname(__file__), "lib", "hdrinodes.blend")

    if not "OUTPUTNODE" in node_tree.nodes:
        node_output = None
        for node in node_tree.nodes:
            if node.bl_idname == "ShaderNodeOutputWorld":
                node_output = node
        if not node_output:
            node_output = node_tree.nodes.new("ShaderNodeOutputWorld")
        node_output.name = "OUTPUTNODE"
    else:
        node_output = node_tree.nodes["OUTPUTNODE"]

    if (
        not "Ground Projection Off/On" in bpy.data.node_groups
        or not "HDRI Nodes" in bpy.data.node_groups
    ):
        with bpy.data.libraries.load(path_nodes_blend, link=False) as (
            data_from,
            data_to,
        ):
            data_to.node_groups = data_from.node_groups

    if not "HDRI_GROUP" in node_tree.nodes:
        hdri_group = node_tree.nodes.new("ShaderNodeGroup")
        hdri_group.name = "HDRI_GROUP"
        hdri_group.node_tree = bpy.data.node_groups["HDRI Nodes"]
    else:
        hdri_group = node_tree.nodes["HDRI_GROUP"]

    if not "GROUND_PROJECTION" in node_tree.nodes:
        ground_projection = node_tree.nodes.new("ShaderNodeGroup")
        ground_projection.name = "GROUND_PROJECTION"
        ground_projection.node_tree = bpy.data.node_groups["Ground Projection Off/On"]
    else:
        ground_projection = node_tree.nodes["GROUND_PROJECTION"]

    if not "ENVTEX" in node_tree.nodes:
        node_env_tex = node_tree.nodes.new("ShaderNodeTexEnvironment")
        node_env_tex.name = "ENVTEX"
    else:
        node_env_tex = node_tree.nodes["ENVTEX"]

    nodes = [
        node_output,
        hdri_group,
        node_env_tex,
        ground_projection,
    ]
    x = 600

    for i, node in enumerate(nodes):
        x -= nodes[i].width
        x -= 80
        node.location.x = x

    node_tree.links.new(
        ground_projection.outputs["Color"], node_env_tex.inputs["Vector"]
    )
    node_tree.links.new(node_env_tex.outputs["Color"], hdri_group.inputs["HDRI"])
    node_tree.links.new(hdri_group.outputs["Shader"], node_output.inputs["Surface"])

    # Load in the HDR
    hdr_image = bpy.data.images.load(hdr)
    node_env_tex.image = hdr_image
