bl_info = {
    "name": "iMeshh Online",
    "author": "iMeshh Ltd",
    "version": (0, 2, 63),
    "blender": (3, 6, 0),
    "category": "Asset Manager",
    "location": "View3D > Tools > iMeshh Online",
}

import bpy
import requests
import os
import threading
import urllib.parse
from bpy.utils import previews
from bpy.props import (
    CollectionProperty,
    EnumProperty,
    StringProperty,
    IntProperty,
    BoolProperty,
)
from bpy.types import Panel


# Configuration
wp_site_url = 'https://shopimeshhcom.bigscoots-staging.com'
token_endpoint = wp_site_url + "/wp-json/jwt-auth/v1/token"
products_endpoint = wp_site_url + "/wp-json/wc/v3/products"
thumbnails_per_page = 12

# Preview collections
preview_collections = {}

def register_window_manager_properties():
    if not hasattr(bpy.types.WindowManager, "asset_manager_previews"):
        bpy.types.WindowManager.asset_manager_previews = EnumProperty(items=lambda self, context: update_web_previews(self, context))

def unregister_window_manager_properties():
    if hasattr(bpy.types.WindowManager, "asset_manager_previews"):
        del bpy.types.WindowManager.asset_manager_previews

def init_previews():
    """Initialize the preview collections."""
    pcoll = previews.new()
    pcoll.my_previews = []
    pcoll.my_previews_data = {}
    bpy.context.window_manager.asset_manager_previews = pcoll  # Store as EnumProperty

def update_web_previews(self, context):
    """Update the previews list value."""
    global preview_collections
    pcoll = bpy.context.window_manager.asset_manager_previews
    items = []

    for asset in pcoll.my_previews_data.values():
        items.append((asset['name'], asset['name'], "", asset['icon_id'], len(items)))

    return items

def fetch_assets(page=0):
    prefs = bpy.context.preferences.addons["imeshh_online"].preferences
    headers = {"Authorization": f"Bearer {prefs.access_token}"}
    params = {"per_page": thumbnails_per_page, "page": page + 1}

    try:
        response = requests.get(products_endpoint, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to fetch assets:", response.text)
    except Exception as e:
        print(f"Error fetching assets: {e}")
    return []

def fetch_thumbnail(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    print(f"Failed to fetch thumbnail from {url}. Status Code: {response.status_code}")
    return None

def save_thumbnail_to_cache(thumbnail_url, save_dir):
    thumbnail_filename = os.path.basename(urllib.parse.urlparse(thumbnail_url).path)
    thumbnail_path = os.path.join(save_dir, thumbnail_filename)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if not os.path.exists(thumbnail_path):
        image_data = fetch_thumbnail(thumbnail_url)
        if image_data:
            with open(thumbnail_path, 'wb') as f:
                f.write(image_data)
            print(f"Thumbnail saved: {thumbnail_path}")
    return thumbnail_path

def load_thumbnail_image(thumbnail_path):
    try:
        if os.path.exists(thumbnail_path):
            image = bpy.data.images.load(thumbnail_path)
            image.name = os.path.basename(thumbnail_path)
            return image
    except Exception as e:
        print(f"Failed to load thumbnail image from {thumbnail_path}: {e}")
    return None

def load_thumbnails(page=0):
    bpy.context.scene.thumbnails_loaded = False
    prefs = bpy.context.preferences.addons["imeshh_online"].preferences
    save_dir = prefs.assets_location
    bpy.context.scene.loaded_thumbnails.clear()

    def load_images():
        products = fetch_assets(page)
        if not products:
            return

        for product in products:
            if 'images' in product and product['images']:
                thumbnail_url = product['images'][0]['src']
                thumbnail_path = save_thumbnail_to_cache(thumbnail_url, save_dir)
                image = load_thumbnail_image(thumbnail_path)
                
                if image:
                    # Use the previews collection
                    preview = bpy.context.window_manager.asset_manager_previews.load(image.name, thumbnail_path, 'IMAGE')
                    if preview:
                        thumbnail_item = bpy.context.scene.loaded_thumbnails.add()
                        thumbnail_item.preview_icon_id = preview.icon_id
                    else:
                        print(f"Image loaded but has no preview: {thumbnail_path}")
                else:
                    print(f"Could not load thumbnail: {thumbnail_path}")

        bpy.context.scene.thumbnails_loaded = True

    threading.Thread(target=load_images).start()

class IMESHH_PT_AssetLibraryPanel(Panel):
    bl_label = "iMeshh Online Library"
    bl_idname = "IMESHH_PT_asset_library_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'iMeshh Online'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if not scene.thumbnails_loaded:
            layout.label(text="Loading assets...", icon='TIME')
        else:
            layout.label(text="Available Assets")
            row = layout.row()
            for i, thumbnail in enumerate(scene.loaded_thumbnails):
                if i % 4 == 0:
                    row = layout.row()
                row.operator("imeshh_online.load_asset", text="", icon_value=thumbnail.preview_icon_id)

            row = layout.row()
            row.operator("imeshh_online.prev_page", text="Previous Page")
            row.operator("imeshh_online.next_page", text="Next Page")


class AuthPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    username: StringProperty(name="Username", default="")
    password: StringProperty(name="Password", subtype='PASSWORD', default="")
    access_token: StringProperty(name="Access Token", default="", options={'HIDDEN'})
    assets_location: StringProperty(name="Assets Location", subtype='DIR_PATH', default="")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "assets_location")
        layout.prop(self, "username")
        layout.prop(self, "password")
        layout.operator("imeshh_online.authenticate", text="Authenticate", icon='KEY_HLT')


class ThumbnailItem(bpy.types.PropertyGroup):
    preview_icon_id: IntProperty()


class IMESHH_OT_Authenticate(bpy.types.Operator):
    bl_idname = "imeshh_online.authenticate"
    bl_label = "Authenticate"

    def execute(self, context):
        prefs = bpy.context.preferences.addons["imeshh_online"].preferences
        payload = {'username': prefs.username, 'password': prefs.password}
        
        try:
            response = requests.post(token_endpoint, data=payload)
            if response.status_code == 200:
                data = response.json()
                prefs.access_token = data['token']
                print("Authentication successful! Token saved.")
                load_thumbnails(0)
            else:
                print(f"Failed to authenticate. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error during authentication: {e}")

        return {'FINISHED'}


class IMESHH_OT_LoadAsset(bpy.types.Operator):
    bl_idname = "imeshh_online.load_asset"
    bl_label = "Load Asset"

    def execute(self, context):
        # Logic for loading an asset goes here
        return {'FINISHED'}


class IMESHH_OT_NextPage(bpy.types.Operator):
    bl_idname = "imeshh_online.next_page"
    bl_label = "Next Page"

    def execute(self, context):
        context.scene.current_page += 1
        load_thumbnails(context.scene.current_page)
        return {'FINISHED'}


class IMESHH_OT_PrevPage(bpy.types.Operator):
    bl_idname = "imeshh_online.prev_page"
    bl_label = "Previous Page"

    def execute(self, context):
        if context.scene.current_page > 0:
            context.scene.current_page -= 1
            load_thumbnails(context.scene.current_page)
        return {'FINISHED'}


def register():
    register_window_manager_properties()
    bpy.utils.register_class(IMESHH_PT_AssetLibraryPanel)
    bpy.utils.register_class(AuthPreferences)
    bpy.utils.register_class(IMESHH_OT_Authenticate)
    bpy.utils.register_class(IMESHH_OT_LoadAsset)
    bpy.utils.register_class(ThumbnailItem)
    bpy.utils.register_class(IMESHH_OT_NextPage)
    bpy.utils.register_class(IMESHH_OT_PrevPage)
    bpy.types.Scene.loaded_thumbnails = CollectionProperty(type=ThumbnailItem)
    bpy.types.Scene.current_page = IntProperty(default=0)
    bpy.types.Scene.thumbnails_loaded = BoolProperty(default=False)
    bpy.types.Scene.thumbnails_per_page = IntProperty(default=thumbnails_per_page)

    # Initialize previews
    init_previews()

def unregister():
    bpy.utils.unregister_class(IMESHH_PT_AssetLibraryPanel)
    bpy.utils.unregister_class(AuthPreferences)
    bpy.utils.unregister_class(IMESHH_OT_Authenticate)
    bpy.utils.unregister_class(IMESHH_OT_LoadAsset)
    bpy.utils.unregister_class(ThumbnailItem)
    bpy.utils.unregister_class(IMESHH_OT_NextPage)
    bpy.utils.unregister_class(IMESHH_OT_PrevPage)
    
    

    del bpy.types.Scene.loaded_thumbnails
    del bpy.types.Scene.current_page
    del bpy.types.Scene.thumbnails_loaded
    del bpy.types.Scene.thumbnails_per_page
    del bpy.context.window_manager.asset_manager_previews  # Clean up the previews


if __name__ == "__main__":
    register()
