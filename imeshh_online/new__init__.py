bl_info = {
    "name": "iMeshh Online",
    "author": "iMeshh Ltd",
    "version": (0, 2, 14),
    "blender": (3, 6, 0),
    "category": "Asset Manager",
    "location": "View3D > Tools > iMeshh Online",
}

import bpy
import requests
import os
from bpy.app.handlers import persistent
import time

wp_site_url = 'https://shopimeshhcom.bigscoots-staging.com'
token_endpoint = wp_site_url + "/wp-json/jwt-auth/v1/token"
product_categories_endpoint = wp_site_url + "/wp-json/wc/v3/products/categories"
products_endpoint = wp_site_url + "/wp-json/wc/v3/products"

oauth_token = None

def authenticate(prefs):
    payload = {
        'username': prefs.username,
        'password': prefs.password
    }
    
    try:
        response = requests.post(token_endpoint, data=payload)
        if response.status_code == 200:
            data = response.json()
            prefs.access_token = data['token']
            print("Authentication successful! Token saved.")
        else:
            print(f"Failed to authenticate. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error during authentication: {e}")

def refresh_access_token(prefs):
    global oauth_token
    oauth_token = {
        'access_token': prefs.access_token
    }

def fetch_product_categories():
    prefs = bpy.context.preferences.addons[__name__].preferences
    refresh_access_token(prefs)
    headers = {
        "Authorization": f"Bearer {prefs.access_token}"
    }
    response = requests.get(product_categories_endpoint, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch product categories. Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    return []

def fetch_products_in_category(category_id):
    prefs = bpy.context.preferences.addons[__name__].preferences
    refresh_access_token(prefs)
    headers = {
        "Authorization": f"Bearer {prefs.access_token}"
    }
    response = requests.get(f"{products_endpoint}?category={category_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch products in category {category_id}. Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    return []

def fetch_thumbnail(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    print(f"Failed to fetch thumbnail from {url}. Status Code: {response.status_code}")
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
    if not categories:
        print("No categories found.")
        return
    for category in categories:
        products = fetch_products_in_category(category['id'])
        if not products:
            print(f"No products found in category {category['name']}")
            continue
        for product in products:
            if 'images' in product and product['images']:
                thumbnail_url = product['images'][0]['src']
                image_data = fetch_thumbnail(thumbnail_url)
                if image_data:
                    subcategory = product.get('categories', [{'name': 'default'}])[0]['name']
                    save_thumbnail_to_cache(thumbnail_url, category['name'], subcategory, product['name'], image_data)
                else:
                    print(f"Failed to download thumbnail for product {product['name']}")

def fetch_thumbnails():
    bpy.context.scene.thumbnails_loaded = False
    bpy.context.scene.loaded_thumbnails.clear()
    print("Fetching and organizing assets...")
    fetch_and_organize_assets()
    bpy.app.timers.register(load_thumbnails)

def load_thumbnails():
    context = bpy.context
    base_dir = context.preferences.addons[__name__].preferences.assets_location
    if not os.path.exists(base_dir):
        print(f"Assets location not found: {base_dir}")
        return

    context.scene.loaded_thumbnails.clear()
    print(f"Loading thumbnails from {base_dir}")

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.png'):
                thumbnail_path = os.path.join(root, file)
                try:
                    image = bpy.data.images.load(thumbnail_path)
                    thumbnail_item = context.scene.loaded_thumbnails.add()
                    thumbnail_item.preview_icon_id = image.preview.icon_id
                    print(f"Loaded thumbnail {thumbnail_path}")
                except Exception as e:
                    print(f"Failed to load image {thumbnail_path}: {e}")

    context.scene.thumbnails_loaded = True
    return None

@persistent
def on_load(dummy):
    prefs = bpy.context.preferences.addons[__name__].preferences
    if prefs.access_token:
        bpy.context.scene.thumbnails_loaded = False
        bpy.context.scene.loaded_thumbnails.clear()
        bpy.app.timers.register(fetch_thumbnails)

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
            if not prefs.access_token:
                layout.label(text="Please authenticate to access the library")
            layout.label(text="Loading assets...", icon='TIME')
        else:
            layout.label(text="Available Assets")
            row = layout.row()
            for i, thumbnail in enumerate(scene.loaded_thumbnails):
                if i % 4 == 0:
                    row = layout.row()
                row.operator("imeshh_online.load_asset", text="", icon_value=thumbnail.preview_icon_id)

class AuthPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    username: bpy.props.StringProperty(name="Username", default="")
    password: bpy.props.StringProperty(name="Password", subtype='PASSWORD', default="")
    access_token: bpy.props.StringProperty(name="Access Token", default="", options={'HIDDEN'})
    assets_location: bpy.props.StringProperty(
        name="Assets Location",
        description="Directory to save and load asset thumbnails",
        subtype='DIR_PATH',
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "assets_location")
        layout.prop(self, "username")
        layout.prop(self, "password")

        row = layout.row()
        row.operator("imeshh_online.authenticate", text="Authenticate", icon='KEY_HLT')

        if self.access_token:
            layout.label(text="Authenticated with token", icon='CHECKMARK')
        else:
            layout.label(text="Please authenticate with username and password")

class IMESHH_OT_Authenticate(bpy.types.Operator):
    bl_idname = "imeshh_online.authenticate"
    bl_label = "Authenticate"

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        if prefs.username and prefs.password:
            authenticate(prefs)
        else:
            self.report({'WARNING'}, "Please provide both username and password")
        return {'FINISHED'}

class ThumbnailItem(bpy.types.PropertyGroup):
    preview_icon_id: bpy.props.IntProperty()

def register():
    bpy.utils.register_class(AuthPreferences)
    bpy.utils.register_class(IMESHH_PT_AssetLibraryPanel)
    bpy.utils.register_class(IMESHH_OT_Authenticate)
    bpy.utils.register_class(ThumbnailItem)
    bpy.types.Scene.thumbnails_loaded = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.loaded_thumbnails = bpy.props.CollectionProperty(type=ThumbnailItem)
    bpy.app.handlers.load_post.append(on_load)

def unregister():
    bpy.utils.unregister_class(AuthPreferences)
    bpy.utils.unregister_class(IMESHH_PT_AssetLibraryPanel)
    bpy.utils.unregister_class(IMESHH_OT_Authenticate)
    bpy.utils.unregister_class(ThumbnailItem)
    del bpy.types.Scene.thumbnails_loaded
    del bpy.types.Scene.loaded_thumbnails
    bpy.app.handlers.load_post.remove(on_load)

if __name__ == "__main__":
    register()
