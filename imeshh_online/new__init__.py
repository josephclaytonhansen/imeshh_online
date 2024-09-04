bl_info = {
    "name": "iMeshh Online",
    "author": "iMeshh Ltd",
    "version": (0, 2, 3),
    "blender": (3, 6, 0),
    "category": "Asset Manager",
    "location": "View3D > Tools > iMeshh Online",
}

addon_version = ".".join(str(x) for x in bl_info["version"])
print("\n")
print("_____________________________________")
print("|                                    |")
print(f"| iMeshh Online version {addon_version} |")
print("| Thank you for using our software   |")
print("|____________________________________|")
print("\n")

import bpy
import requests
from requests.auth import HTTPBasicAuth
import asyncio
import concurrent.futures
import os
from bpy.app.handlers import persistent

wp_site_url = "https://shopimeshhcom.bigscoots-staging.com"
auth_endpoint = wp_site_url + "/wp-json/wp/v2/users/me"
product_categories_endpoint = wp_site_url + "/wp-json/wc/v3/products/categories"
products_endpoint = wp_site_url + "/wp-json/wc/v3/products"

def authenticated(username, password):
    response = requests.get(auth_endpoint, auth=HTTPBasicAuth(username, password))
    print (response)
    return response.status_code == 200

def fetch_product_categories():
    response = requests.get(product_categories_endpoint)
    if response.status_code == 200:
        return response.json()
    return []

def fetch_products_in_category(category_id):
    response = requests.get(f"{products_endpoint}?category={category_id}")
    if response.status_code == 200:
        return response.json()
    return []

def fetch_thumbnail(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return None

def save_thumbnail_to_cache(thumbnail_url, category, subcategory, product_name, image_data):
    base_dir = bpy.context.preferences.addons[__name__].preferences.assets_location
    category_path = os.path.join(base_dir, category, subcategory)
    os.makedirs(category_path, exist_ok=True)
    thumbnail_path = os.path.join(category_path, f"{product_name}.png")
    
    with open(thumbnail_path, 'wb') as f:
        f.write(image_data)
    
    return thumbnail_path

def fetch_and_organize_assets():
    categories = fetch_product_categories()
    for category in categories:
        products = fetch_products_in_category(category['id'])
        for product in products:
            if 'images' in product and product['images']:
                thumbnail_url = product['images'][0]['src']
                image_data = fetch_thumbnail(thumbnail_url)
                subcategory = product.get('categories', [{'name': 'default'}])[0]['name']
                save_thumbnail_to_cache(thumbnail_url, category['name'], subcategory, product['name'], image_data)

class AuthPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    username: bpy.props.StringProperty(
        name="Username",
        description="Username",
        default="",
        update=lambda self, context: self.update_auth_status(context)
    )
    password: bpy.props.StringProperty(
        name="Password",
        description="Password",
        default="",
        subtype='PASSWORD',
        update=lambda self, context: self.update_auth_status(context)
    )
    assets_location: bpy.props.StringProperty(
        name="Assets Location",
        description="Directory to store assets",
        default="",
        subtype='DIR_PATH'
    )
    auth_success: bpy.props.BoolProperty(
        name="Authentication Success",
        description="Indicates if the authentication was successful",
        default=False
    )

    def update_auth_status(self, context):
        self.auth_success = False

    def draw(self, context):
        layout = self.layout
        layout.label(text="Enter your iMeshh Online credentials")
        layout.prop(self, "username")
        layout.prop(self, "password")
        layout.prop(self, "assets_location")

        if self.auth_success:
            layout.label(text="Authentication successful", icon='CHECKMARK')
        else:
            layout.operator("imeshh_online.save_credentials", text="Save Credentials")

class IMESHH_OT_Authenticate(bpy.types.Operator):
    bl_idname = "imeshh_online.save_credentials"
    bl_label = "Save Credentials"

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        if authenticated(prefs.username, prefs.password):
            prefs.auth_success = True
            self.report({'INFO'}, "Authentication successful")
        else:
            prefs.auth_success = False
            self.report({'ERROR'}, "Authentication failed")
        return {'FINISHED'}

class IMESHH_PT_AssetLibraryPanel(bpy.types.Panel):
    bl_label = "iMeshh Online Library"
    bl_idname = "IMESHH_PT_asset_library_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'iMeshh Online'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        prefs = context.preferences.addons[__name__].preferences

        if not scene.thumbnails_loaded:
            if not prefs.auth_success:
                layout.label(text="Please authenticate to access the library")
            layout.label(text="Loading assets...", icon='TIME')
        else:
            layout.label(text="Available Assets")
            row = layout.row()
            for i, thumbnail in enumerate(scene.loaded_thumbnails):
                if i % 4 == 0:
                    row = layout.row()
                row.operator("imeshh_online.load_asset", text="", icon_value=thumbnail.preview_icon_id)

class ThumbnailItem(bpy.types.PropertyGroup):
    preview_icon_id: bpy.props.IntProperty()

async def fetch_thumbnails_async(context):
    with concurrent.futures.ThreadPoolExecutor() as pool:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(pool, fetch_and_organize_assets)
        thumbnails = []
        base_dir = context.preferences.addons[__name__].preferences.assets_location
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.png'):
                    thumbnail_path = os.path.join(root, file)
                    image = bpy.data.images.load(thumbnail_path)
                    thumbnail_item = context.scene.loaded_thumbnails.add()
                    thumbnail_item.preview_icon_id = image.preview.icon_id

        context.scene.thumbnails_loaded = True

def load_thumbnails():
    context = bpy.context
    asyncio.run(fetch_thumbnails_async(context))
    return 1.0

@persistent
def on_load(dummy):
    prefs = bpy.context.preferences.addons[__name__].preferences
    if prefs.auth_success:
        bpy.context.scene.thumbnails_loaded = False
        bpy.context.scene.loaded_thumbnails.clear()
        bpy.app.timers.register(load_thumbnails)

def register():
    bpy.utils.register_class(AuthPreferences)
    bpy.utils.register_class(IMESHH_OT_Authenticate)
    bpy.utils.register_class(IMESHH_PT_AssetLibraryPanel)
    bpy.utils.register_class(ThumbnailItem)
    bpy.types.Scene.thumbnails_loaded = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.loaded_thumbnails = bpy.props.CollectionProperty(type=ThumbnailItem)
    bpy.app.handlers.load_post.append(on_load)

def unregister():
    bpy.utils.unregister_class(AuthPreferences)
    bpy.utils.unregister_class(IMESHH_OT_Authenticate)
    bpy.utils.unregister_class(IMESHH_PT_AssetLibraryPanel)
    bpy.utils.unregister_class(ThumbnailItem)
    del bpy.types.Scene.thumbnails_loaded
    del bpy.types.Scene.loaded_thumbnails

if __name__ == "__main__":
    register()
