bl_info = {
    "name": "iMeshh Online",
    "author": "iMeshh Ltd",
    "version": (0, 2, 5),
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

import subprocess
import sys

def ensure_flask_installed():
    try:
        import flask
        from requests_oauthlib import OAuth2Session
        from dotenv import load_dotenv
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests_oauthlib"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])

ensure_flask_installed()

import bpy
import requests
import os
from threading import Thread
from flask import Flask, request
from requests_oauthlib import OAuth2Session
from bpy.app.handlers import persistent
import time

load_dotenv()

wp_site_url = os.getenv("WP_SITE_URL")
redirect_uri = os.getenv("REDIRECT_URI")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

auth_endpoint = wp_site_url + "/wp-json/wp/v2/users/me"
product_categories_endpoint = wp_site_url + "/wp-json/wc/v3/products/categories"
products_endpoint = wp_site_url + "/wp-json/wc/v3/products"
token_url = wp_site_url + '/oauth/token'

app = Flask(__name__)
oauth_callback_received = False
oauth_token = None
token_expiration = None

def run_flask():
    app.run(port=5000)

@app.route("/callback")
def oauth_callback():
    global oauth_callback_received, oauth_token, token_expiration
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)
    oauth_token = oauth.fetch_token(
        token_url,
        authorization_response=request.url,
        client_secret=client_secret
    )
    oauth_callback_received = True
    token_expiration = time.time() + oauth_token.get('expires_in', 3600)
    return "OAuth login successful. You may close this window."

import webbrowser

class IMESHH_OT_OAuthLogin(bpy.types.Operator):
    bl_idname = "imeshh.oauth_login"
    bl_label = "Login to iMeshh"
    
    _timer = None
    _flask_thread = None

    def modal(self, context, event):
        global oauth_callback_received

        if event.type == 'TIMER':
            if oauth_callback_received:
                context.preferences.addons[__name__].preferences.auth_success = True
                bpy.context.window_manager.event_timer_remove(self._timer)
                self._flask_thread.join()
                self.report({'INFO'}, "Authentication successful!")
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        global oauth_callback_received
        oauth_callback_received = False
        self._flask_thread = Thread(target=run_flask)
        self._flask_thread.start()
        
        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)
        authorization_url, _ = oauth.authorization_url(wp_site_url + '/oauth/authorize')
        webbrowser.open(authorization_url)

        wm = context.window_manager
        self._timer = wm.event_timer_add(1.0, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        bpy.context.window_manager.event_timer_remove(self._timer)
        self._flask_thread.join()

        return {'CANCELLED'}


def refresh_access_token(prefs):
    global oauth_token, token_expiration
    if time.time() > token_expiration:
        oauth = OAuth2Session(client_id, token=oauth_token)
        extra = {
            'client_id': client_id,
            'client_secret': client_secret,
        }
        new_token = oauth.refresh_token(token_url, refresh_token=prefs.refresh_token, **extra)
        oauth_token = new_token
        prefs.access_token = new_token['access_token']
        prefs.refresh_token = new_token['refresh_token']
        token_expiration = time.time() + new_token.get('expires_in', 3600)

def fetch_product_categories():
    prefs = bpy.context.preferences.addons[__name__].preferences
    refresh_access_token(prefs)
    headers = {
        "Authorization": f"Bearer {prefs.access_token}"
    }
    response = requests.get(product_categories_endpoint, headers=headers)
    if response.status_code == 200:
        return response.json()
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

def fetch_thumbnails():
    bpy.context.scene.thumbnails_loaded = False
    bpy.context.scene.loaded_thumbnails.clear()
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
    if prefs.auth_success:
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

class AuthPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    access_token: bpy.props.StringProperty(name="Access Token", default="")
    refresh_token: bpy.props.StringProperty(name="Refresh Token", default="")
    auth_success: bpy.props.BoolProperty(name="Authentication Success", default=False)
    assets_location: bpy.props.StringProperty(
        name="Assets Location",
        description="Directory to save and load asset thumbnails",
        subtype='DIR_PATH',
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "assets_location")

        if self.auth_success:
            layout.label(text="Authenticated successfully", icon='CHECKMARK')
        else:
            layout.operator("imeshh.oauth_login", text="Authenticate with OAuth")

class ThumbnailItem(bpy.types.PropertyGroup):
    preview_icon_id: bpy.props.IntProperty()

def register():
    bpy.utils.register_class(AuthPreferences)
    bpy.utils.register_class(IMESHH_OT_OAuthLogin)
    bpy.utils.register_class(IMESHH_PT_AssetLibraryPanel)
    bpy.utils.register_class(ThumbnailItem)
    bpy.types.Scene.thumbnails_loaded = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.loaded_thumbnails = bpy.props.CollectionProperty(type=ThumbnailItem)
    bpy.app.handlers.load_post.append(on_load)

def unregister():
    bpy.utils.unregister_class(AuthPreferences)
    bpy.utils.unregister_class(IMESHH_OT_OAuthLogin)
    bpy.utils.unregister_class(IMESHH_PT_AssetLibraryPanel)
    bpy.utils.unregister_class(ThumbnailItem)
    del bpy.types.Scene.thumbnails_loaded
    del bpy.types.Scene.loaded_thumbnails

if __name__ == "__main__":
    register()
