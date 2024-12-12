from concurrent.futures import ThreadPoolExecutor
import functools
from pathlib import Path
from queue import Queue
from time import sleep
import bpy
from enum import Enum
from urllib.parse import urlencode
import threading
import requests
import urllib.parse

import os
from pathlib import Path

from .t3dn_bip import previews
from bpy.utils.previews import ImagePreviewCollection
from bpy.types import ImagePreview
from bpy.props import EnumProperty,StringProperty
import ctypes
# from requests import Response
BASE_URL = "https://shop.imeshh.com"
NEW_URL = " https://shopimeshhcom.bigscoots-staging.com/wp-json/imeshh/"
STORE = 'https://shop.imeshh.com/wp-json/wc/store/v1'

_item_map = dict() # dynamic enum bug 
def _make_item(enum_name, id_, name, descr, preview_id, uid, is_icon=False):
    if is_icon:
        lookup = f"{str(id_)}\0{str(name)}\0{str(descr)}\0{str(preview_id)}\0{str(uid)}"
    else:
        lookup = f"{str(id_)}\0{str(name)}\0{str(descr)}"
    if enum_name not in _item_map:
        _item_map[enum_name] = {}
    if lookup not in _item_map[enum_name]:
        if is_icon:
            _item_map[enum_name][lookup] = (id_, name, descr, preview_id, uid)
        else:
            _item_map[enum_name][lookup] = (id_, name, descr)

    return _item_map[enum_name][lookup]

import requests
import urllib.parse
import bpy
from bpy.props import StringProperty

class OBJECT_OT_ClickAsset(bpy.types.Operator):
    bl_idname = "object.click_asset"
    bl_label = "Click Asset"
    
    asset_name: StringProperty()

    def execute(self, context):
        print(f"Clicked on asset: {self.asset_name}")
        prefs = context.preferences.addons["imeshh_online"].preferences
        
        if prefs.subscription_id == 0 or prefs.access_token == "" or not prefs.subscription_id:
            print("Please authenticate and check subscription before downloading assets.")
            self.report({'ERROR'}, "Please authenticate and check subscription before downloading assets.")
            return {'FINISHED'}
        
        try:
            wp_site_url = 'https://shopimeshhcom.bigscoots-staging.com'
            products_endpoint = f"{wp_site_url}/wp-json/wc/v3/products"
            authorization_header = "Authorization: Bearer " + prefs.access_token
            
            # Prepare query parameters with URL encoding for the exact match
            params = {
                'search': self.asset_name,
            }
            headers = {
                'Authorization': authorization_header
            }
            url = f"{products_endpoint}?{urllib.parse.urlencode(params)}"
            print(f"Request URL: {url}")
            
            # Make the GET request for exact match
            response = requests.get(url, headers=headers)
            
            # Log the full response for debugging
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            
            product_data = response.json()

            if response.status_code != 200 or not product_data:
                print(f"Exact search failed; trying partial search for asset: {self.asset_name}")
                
                # Fallback to partial search using the first three words
                keywords = self.asset_name.split(" ")[:3]  # Get the first three words
                partial_search = " ".join(keywords)  # Join them into a single search string
                
                params['search'] = partial_search
                url = f"{products_endpoint}?{urllib.parse.urlencode(params)}"
                print(f"Partial Search Request URL: {url}")

                # Make the GET request for partial match
                response = requests.get(url)
                
                # Log the full response for debugging
                print(f"Status Code (partial): {response.status_code}")
                print(f"Response Text (partial): {response.text}")
                
                product_data = response.json()

            if response.status_code != 200 or not product_data:
                print(f"Failed to fetch product or product not found for asset: {self.asset_name}")
                return {'FINISHED'}

            # Extract product ID
            product_id = product_data[0].get('id')
            print(f"Product ID for asset '{self.asset_name}': {product_id}")
            
            if not product_id:
                print("Product ID is None; cannot retrieve downloads.")
                return {'FINISHED'}

            # Fetch Product Details to get Download URLs
            product_url = f"{products_endpoint}/{product_id}"
            response = requests.get(f"{product_url}", headers=headers)
            
            # Log the full response for debugging
            print(f"Status Code (details): {response.status_code}")
            print(f"Response Text (details): {response.text}")
            
            if response.status_code == 200:
                product_details = response.json()
                categories = product_details.get('categories', [])
                
                # Retrieve download URLs if available
                if 'downloads' in product_details:
                    download_links = [file['file'] for file in product_details['downloads']]
                    print(f"Download URLs: {download_links}")
                    # Get the default folder from preferences
                    prefs = bpy.context.preferences.addons['imeshh_online'].preferences
                    default_folder = prefs.default_folder

                    # Save the ZIP files to the appropriate category folder
                    for link in download_links:
                        category_names = [category['name'] for category in categories]
                        for category_name in category_names:
                            # Create category folder path
                            category_folder = os.path.join(default_folder, category_name)
                            os.makedirs(category_folder, exist_ok=True)

                            # Download and save the ZIP file
                            zip_file_name = os.path.basename(link)  # Extract file name from URL
                            zip_file_path = os.path.join(category_folder, zip_file_name)
                            
                            # skip the file with GLTF in the name
                            if "GLTF" in zip_file_name:
                                print(f"Skipping GLTF file: {zip_file_path}")
                                continue
                            
                            # skip the download if the file already exists
                            if os.path.exists(zip_file_path):
                                print(f"File already exists: {zip_file_path}")
                                new_asset = prefs.downloaded_assets.add()
                                new_asset.name = self.asset_name
                                new_asset.path = zip_file_path
                                continue

                            # Download the file
                            zip_response = requests.get(link)
                            if zip_response.status_code == 200:
                                with open(zip_file_path, 'wb') as zip_file:
                                    zip_file.write(zip_response.content)
                                print(f"Saved ZIP file: {zip_file_path}")
                            else:
                                print(f"Failed to download ZIP file from {link}. Status Code: {zip_response.status_code}")
                else:
                    print("No downloads found for this product.")
            else:
                print(f"Failed to retrieve product details. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Error fetching product downloads: {e}")

        return {'FINISHED'}




redraw_queue = Queue()
def execute_queued_items():
    while not redraw_queue.empty():
        item,value = redraw_queue.get()
        setattr(_manager,item,value)
        redraw_ui()
    return 0.1

class FetchStatus(Enum):
    NOT_INITIATED = -1
    FETCHING = 1
    SUCCESS = 2
    FAILED = 3
    CANCELLED = 4
    BACKGROUND_FETCHING = 5
    BACKGROUND_SUCCESS = 6

MAX_THREADS = 20

def is_authenticated():
    """Check if the user is authenticated by verifying the presence of the access token."""
    prefs = bpy.context.preferences.addons['imeshh_online'].preferences
    return prefs.access_token != ''

def download_all_thumbnails():
    global _manager

    if not is_authenticated():
        print("You must authenticate before downloading assets.")
        return  # Exit if the user is not authenticated

    url = STORE + '/products'
    res = requests.head(url)
    total_products = res.headers['X-WP-Total']

    url = url + f"?per_page={total_products}&page=1"
    prefs = bpy.context.preferences.addons['imeshh_online'].preferences
    headers = {
        "Authorization": f"Bearer {prefs.access_token}"
    }
    res = requests.get(url, headers=headers)

    futures = total_products
    for asset in res.json():
        if 'images' not in asset.keys():
            continue
        if len(asset['images']) == 0:
            continue
        thumb_path = _manager.get_thumbnail_location(asset)
        if thumb_path.exists() and thumb_path.is_file():
            continue
        fut = _manager.t_queue_thumbnail_download(asset)
        futures.append(fut)


def redraw_ui(context=None):
    """Force a redraw of the 3D and preferences panel from operator calls."""
    if not context:
        context = bpy.context
    try:
        for wm in bpy.data.window_managers:
            for window in wm.windows:
                for area in window.screen.areas:
                    if area.type not in ("VIEW_3D", "PREFERENCES"):
                        continue
                    for region in area.regions:
                        region.tag_redraw()
    except AttributeError:
        pass 

def get_icon(name:str):
    return bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.get(name)
class IMeshh_Manager():
    threads = []

    cached_query:dict[str,dict] = {}

    cache_store = {
        
        'model3d':{
            'categories':[],
            'level':2,
            'category1>category2':{
                "search":{
                    "total":52,
                    "totalpages":3,
                    "page1":[],
                    "page2":[]
                }
            }
        },
        'materials':{},
        'scene':{}
    }

    query_fetch_status:FetchStatus = FetchStatus.NOT_INITIATED
    bgq_status:FetchStatus = FetchStatus.NOT_INITIATED
    query_result:dict = {}
    qr_assets:list = []
    qr_pages:int = 0 # total pages this query result
    qr_page:int = 0 # particular page of this query result

    display_assets:list =[] # list of asset that we iterate on to display in the panel
    
    online_thumbs_dir = Path('~').expanduser() / 'imeshh' / 'online_thumbnails'
    online_thumbs_dir.mkdir(parents=True,exist_ok=True)

    def get_threadpool(self, max_threads:None):
        if max_threads is None:
            max_threads = MAX_THREADS
        if self.thread_pool is None:
            self.thread_pool = ThreadPoolExecutor(max_workers=max_threads)
        # print("Thread pool: ", self.thread_pool)
        return self.thread_pool

    def queue_thread(self, func,max_threads,*args,**kwargs):
        tpe = self.get_threadpool(max_threads)
        future = tpe.submit(func,*args,**kwargs)
        return future

    def run_threaded(max_threads=None):
        def actual_run_threaded(f):
            @functools.wraps(f)
            def wrapper(self,*args, **kwargs):
                args = (self, ) + args
                return self.queue_thread(f, max_threads, *args, **kwargs)
            return wrapper
        return actual_run_threaded

    def get_thumbnail_location(self, asset):
        """Get the location to save the thumbnail for the given asset."""
        prefs = bpy.context.preferences.addons["imeshh_online"].preferences
        default_folder = Path(prefs.default_folder)

        # Create the 'thumbs' folder inside the user's selected folder
        thumbs_folder = default_folder / 'thumbs'
        if not thumbs_folder.exists():
            thumbs_folder.mkdir(parents=True, exist_ok=True)
            # Make the 'thumbs' folder hidden
            try:
                if os.name == 'nt':
                    FILE_ATTRIBUTE_HIDDEN = 0x02
                    ctypes.windll.kernel32.SetFileAttributesW(str(thumbs_folder), FILE_ATTRIBUTE_HIDDEN)
                elif os.name == 'posix':
                    os.system(f"chflags hidden {thumbs_folder}")
            except Exception as e:
                print(f"Failed to hide folder: {e}")


        # Generate the thumbnail path inside the 'thumbs' folder
        thumbnail_filename = f"{asset['id']}_{asset['slug']}.png"
        thumb_path = thumbs_folder / thumbnail_filename
        return thumb_path

    @run_threaded(max_threads=MAX_THREADS)
    def t_queue_thumbnail_download(self, asset):
        # print(asset['name'])
        thumb_path = self.get_thumbnail_location(asset)
        # print(thumb_path.is_file() and thumb_path.exists())
        if thumb_path.is_file() and thumb_path.exists():
            return
        
        main_image = asset['images'][0]
        download_url = main_image['thumbnail']
        # print(download_url)

        # small size thumbnails. no need for chunking
        stream = requests.get(download_url,stream=False)
        with open(thumb_path, "wb") as file:
            file.write(stream.content)
        
        with self.lock_asset_previews:
            if asset['name'] in self.ongoing_thumbnail_download:
                self.ongoing_thumbnail_download.remove(asset['name'])
        redraw_ui()

    def get_thumbnail(self, asset, load_thumb = True) -> int:
        '''get thumbnail for given asset. if thumbnail is not present locally,
        if not then queue it for the download
        load_thumb = True will load the thumbnail into blender
        '''
        name = asset['name']

        with self.lock_asset_previews:
            if name in self.ongoing_thumbnail_download:
                return get_icon('IMPORT').value

        if name == 'dummy':
            return get_icon('NONE').value

        if 'images' not in asset.keys():
            # print(f"{name} does not have images")
            return get_icon('ERROR').value
        if len(asset['images']) == 0:
            # print(f"{name} does not have images")
            return get_icon('ERROR').value
        
        with self.lock_asset_previews:
            if name in self.asset_previews:
                return self.asset_previews[name].icon_id

        thumb_path = self.get_thumbnail_location(asset)
        # print(thumb_path)
        if thumb_path.exists():
            if load_thumb is False:
                return None
            with self.lock_asset_previews:
                try:
                    self.asset_previews.load(name,str(thumb_path),'IMAGE')
                except KeyError:
                    self.asset_previews[name].reload()
                    # self.asset_previews[name].reload()
                # redraw_ui()
                return self.asset_previews[name].icon_id
        
        with self.lock_asset_previews:
            if name not in self.ongoing_thumbnail_download:
                self.ongoing_thumbnail_download.append(name)
                # print("queuing ",name)
                self.t_queue_thumbnail_download(asset)

        return get_icon('CUBE').value

    def register(self):
        self.threads = []
        self.lock_cached_query = threading.Lock()
        self.thread_pool = None
        self.ongoing_queries = [] # background queries that are running
        # this helps in preventing spawing duplicate threads for the same page

        self.query_fetch_status:FetchStatus = FetchStatus.NOT_INITIATED
        self.bgq_status:FetchStatus = FetchStatus.NOT_INITIATED
        self.forground_query = ''
        self.query_result:dict = {} 
        self.qr_assets:list = [] # asset list of this query
        self.qr_pages:int = 0 # total pages this query result
        self.qr_page:int = 0 # particular page of this query result
        
        self.search:str = ''
        self.per_page:int = 20
        self.current_total_pages:int = 0
        self.current_page:int = 1
        self.display_assets:list =[] # list of asset that we iterate on to display in the panel

        self.current_assettype = 36902# "3DMODEL"
        self.current_cat1 = "All assets"
        self.current_cat2 = "All assets"

        self.lock_asset_previews = threading.Lock() # this is required as asset_previews will be access and modified in threads
        self.asset_previews = previews.new()
        self.ongoing_thumbnail_download = [] # asset names whose thumbnail are currently downloading
        self.get_category_tree(use_thread=True)
        # self.register_properties()
        self.get_assets(use_thread=True)
        bpy.app.timers.register(execute_queued_items)

        
    def register_properties(self):
        # 1st enum will be the asset type i.e, 3d-asset, material, scenes
        # hard coding the 2 layer of category right now as that suffice the need.
        # in future make it dynamic based on the max depth of any asset_type

        def get_asset_category1(self, context):
            items = []
            if context is None:
                return items
            asset_type = int(context.scene.imeshh_asset_type)
            global _manager
            if not _manager.categories or asset_type not in _manager.categories:
                return items
            
            items.append(_make_item("asset_category1","All assets","All assets","All assets",None,None))
            for cat in _manager.categories[asset_type]["children"]:
                items.append(_make_item("asset_category1",str(cat["id"]),cat["name"],cat["name"],None,None))
            return items
        
        def get_asset_category2(self, context):
            items = []
            if context is None:
                return items

            if context.scene.imeshh_asset_category1 == '' or context.scene.imeshh_asset_category1=="All assets":
                items.append(_make_item("asset_category2","All assets","All assets","All assets",None,None))
                return items
            
            asset_type = int(context.scene.imeshh_asset_type)
            category1 = int(context.scene.imeshh_asset_category1)
            
            global _manager
            if not _manager.categories or asset_type not in _manager.categories:
                return items

            for cat in _manager.categories[asset_type]["children"]:
                if category1 == cat["id"]:
                    category1 = cat
                    break
            
            items.append(_make_item("asset_category2","All assets","All assets","All assets",None,None))
            for cat in category1["children"]:
                items.append(_make_item("asset_category2",str(cat["id"]),cat["name"],cat["name"],None,None))
            return items

        def update_assettype(self, context):
            print("Update assettype")
            global _manager
            _manager.current_assettype = self.imeshh_asset_type
            self.imeshh_asset_category1
            # self.imeshh_asset_category1 = "All assets"
            # _manager.current_cat1 = "All assets"
            self.imeshh_asset_category1 = str(_manager.categories[int(_manager.current_assettype)]["children"][0]["id"])
            _manager.current_cat1 = str(_manager.categories[int(_manager.current_assettype)]["children"][0]["id"])
            
        def update_asset_category1(self, context):
            global _manager
            if _manager.current_cat1 == self.imeshh_asset_category1:
                return
            print("Update Cat1")
            
            self.imeshh_asset_category2
            self.imeshh_asset_category2 = "All assets"
            _manager.current_cat2 = "All assets"
            _manager.current_cat1 = self.imeshh_asset_category1

        def update_asset_category2(self, context):
            global _manager
            if _manager.current_cat1 == self.imeshh_asset_category1 and\
                _manager.current_cat2 == self.imeshh_asset_category2:
                return
            print("Update Cat2")
            _manager.current_page = 1
            _manager.current_cat1 = self.imeshh_asset_category1
            _manager.current_cat2 = self.imeshh_asset_category2
            _manager.get_assets()

        def update_search_string(self, context):
            if _manager.search == self.imeshh_search:
                return
            _manager.search = self.imeshh_search
            _manager.get_assets(search=_manager.search)

        asset_types=[(asset_type["id"],asset_type["name"]) 
                     for asset_type in self.categories.values()
                     if len(asset_type["children"])>0]
        
        asset_type_enum = [(str(id),name,f"Product Category: {name}") for id,name in asset_types]
        bpy.types.Scene.imeshh_asset_type = EnumProperty(items=asset_type_enum, update=update_assettype)
        bpy.types.Scene.imeshh_asset_category1 = EnumProperty(items=get_asset_category1,update=update_asset_category1)
        bpy.types.Scene.imeshh_asset_category2= EnumProperty(items=get_asset_category2,update=update_asset_category2)
        bpy.types.Scene.imeshh_search = StringProperty(update=update_search_string)

    @staticmethod
    def build_category_tree(categories):
        # Create a dictionary to hold all categories by their IDs
        category_dict = {category['id']: category for category in categories}
        # Initialize children list for each category
        for category in category_dict.values():
            category['children'] = []
        
        # Populate the children lists
        for category in categories:
            parent_id = category['parent']
            if parent_id != 0:
                if parent_id in category_dict:
                    category_dict[parent_id]['children'].append(category)
        
        # Extract the root categories (those with parent == 0)

        roots = {category["id"]:category for category in category_dict.values() if category['parent'] == 0}
        roots[36902]["children"]=roots[36902]["children"][0]["children"][:]
        # print(len(roots[36902]["children"]))
        return roots

    def t_api_get_categories(self, url: str, query_params: dict):
        try:
            query_string = urlencode(query_params)
            url = f"{url}?{query_string}"
            
            prefs = bpy.context.preferences.addons["imeshh_online"].preferences
            headers = {
                "Authorization": f"Bearer {prefs.access_token}"
            }
            
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            data = res.json()
            self.categories = self.build_category_tree(data)
            # print("manager categories: ", self.categories)
        except Exception as e:
            print("Error fetching categories: ", e)
            
        self.register_properties()

    def get_category_tree(self, use_thread=False):
        url = STORE + "/products/categories"
        query_params = {}
        if use_thread:
            print("====:::categories inside thread :::====")
            args = (url, query_params)
            vThread = threading.Thread(
                target=self.t_api_get_categories,
                args=args
            )
            vThread.daemon = 1
            vThread.start()
            self.threads.append(vThread)
        else:
            self.t_api_get_categories(url, query_params)

    def t_api_get_assets(self,url:str,query_params:dict, is_background:bool):
        try:
            page = query_params["page"]
            category = f"{self.current_assettype}>{self.current_cat1}>{self.current_cat2}"
            key = f"{category}_{query_params['search']}_{query_params['per_page']}"
            # print(url)
            res = requests.get(url)
            res.raise_for_status()
            #handle the exceptions
            # int(res.headers['X-WP-Total'])
            self.qr_pages = int(res.headers['X-WP-TotalPages'])
            self.qr_assets = res.json()

            for asset in self.qr_assets:
                self.get_thumbnail(asset, load_thumb=False)
            if not is_background:
                self.current_total_pages = int(res.headers['X-WP-TotalPages'])
                print("Total pages: ",self.current_total_pages)
                self.current_page = page
        
        except Exception as e:
            print("Error fetching assets: ",e)
            if not is_background:
                redraw_queue.put(("query_fetch_status",FetchStatus.FAILED))
            if is_background:
                redraw_queue.put(("bgq_status",FetchStatus.FAILED))
            return

        with self.lock_cached_query:
            if key not in self.cached_query.keys():
                self.cached_query[key] = {}
            self.cached_query[key][page] = (res.json(),int(res.headers['X-WP-TotalPages']))
        # print(self.cached_query[key][page])
        try:
            # print(f"removing key {page}_{key} from ongoing")
            # print("current length: ", len(self.ongoing_queries))
            self.ongoing_queries.remove(f"{page}_{key}")
        except ValueError as e :
            print("==>",f"{page}_{key}","<==")
            print(e)

        if self.forground_query == f"{page}_{key}":
            redraw_queue.put(("query_fetch_status",FetchStatus.SUCCESS))
            redraw_ui()
        if is_background:
            redraw_queue.put(("bgq_status",FetchStatus.BACKGROUND_SUCCESS))
        if not is_background:
            redraw_ui()
        
    def get_category_slug(self):
        if self.current_cat2 != "All assets":
            return self.current_cat2
        if self.current_cat1 != "All assets":
            return self.current_cat1
        if self.current_cat1 == "All assets" and self.current_cat2 == "All assets":
            return self.current_assettype
        # something went wrong with current cat1&2. we should not reach here
        return self.current_assettype 

    def get_assets(self,page=-1,per_page=20,search='',order='asc',order_by='',use_thread=True, is_background=False):
        redraw_ui()
        if page==-1:
            page = self.current_page
        product_path = STORE + '/products'

        query_params = {
            "per_page" : per_page,
            "category": int(self.get_category_slug()),
            "page" : page,
            "search" : search,
            # "order" : order
        }
        query_string = urlencode(query_params)
        url = f"{product_path}?{query_string}"

        category = f"{self.current_assettype}>{self.current_cat1}>{self.current_cat2}"
        key = f"{category}_{query_params['search']}_{query_params['per_page']}"
        
        if not is_background:
            self.search = search
            self.per_page = per_page
            self.forground_query = f"{page}_{key}"
        if f"{page}_{key}" in self.ongoing_queries:
            redraw_queue.put(("query_fetch_status",FetchStatus.FETCHING))
            redraw_ui()
            return
        
        with self.lock_cached_query:
            if key in self.cached_query.keys():
                # print(f"Key {key} in cached_query")
                if page in self.cached_query[key].keys():
                    # print(f"Page {page} in cached_query")
                    self.qr_assets = self.cached_query[key][page][0]
                    self.qr_pages = self.cached_query[key][page][1]
                    self.current_total_pages = self.cached_query[key][page][1]
                    redraw_queue.put(("query_fetch_status",FetchStatus.SUCCESS))
                    redraw_ui()
                    return

        print(query_params["page"])
        
        self.ongoing_queries.append(f"{page}_{key}")
        
        # self.query_fetch_status = FetchStatus.BACKGROUND_FETCHING if is_background else FetchStatus.FETCHING
        if is_background and self.forground_query not in self.ongoing_queries:
            redraw_queue.put(("bgq_status",FetchStatus.BACKGROUND_FETCHING))
        else:
            redraw_queue.put(("query_fetch_status",FetchStatus.FETCHING))
            
        if use_thread:
            args = (url,query_params, is_background)
            vThread = threading.Thread(
                    target=self.t_api_get_assets,
                    args=args
                )
            vThread.daemon = 1
            vThread.start()
            self.threads.append(vThread)
        else:
            self.t_api_get_assets(url,query_params,is_background)
        redraw_ui()

    def get_display_assets(self,page):
        category = f"{self.current_assettype}>{self.current_cat1}>{self.current_cat2}"
        key = f"{category}_{self.search}_{self.per_page}"
        if key not in self.cached_query.keys():
            return []
        if self.query_fetch_status is FetchStatus.FETCHING or f"{page}_{key}" in self.ongoing_queries:
            dummy={
                "name":'dummy',
            }
            dummy_list =[dummy] * self.per_page
            # print(len(dummy_list))
            return dummy_list
        
        display_assets = self.cached_query[key][page][0][:]
        return display_assets

    def build_navigation(self, layout:bpy.types.UILayout):
        # print("toatin ui: ",self.current_total_pages)
        layout=layout.column()
        if self.query_fetch_status == FetchStatus.FETCHING:
            layout.enabled = False
        # if self.query_fetch_status==FetchStatus.BACKGROUND_FETCHING:
        #     layout.row().label(text="background fetching")
        # if self.query_fetch_status==FetchStatus.BACKGROUND_SUCCESS:
        #     layout.row().label(text="background success")
        layout=layout.row()
        left = layout.row()
        ml = layout.row()
        middle = layout.row(align=True)
        mr = layout.row()
        right = layout.row()

        if self.current_page == 1:
            left.enabled = False
        op_props = left.operator("simple.move_to", icon="TRIA_LEFT",text="")
        op_props.page = self.current_page - 1

        if self.current_page == self.current_total_pages:
            right.enabled = False
        op_props = right.operator("simple.move_to", icon="TRIA_RIGHT",text="")
        op_props.page = self.current_page + 1

        # op_props = ml.operator("simple.move_to", text="1",depress= 1==self.current_page)
        # op_props.page = 1
        
        num_pages_max = 10
        if self.current_total_pages>num_pages_max:
            last_page = self.current_total_pages
            op_props = mr.operator("simple.move_to", text=str(last_page),depress= self.current_page==last_page)
            op_props.page = self.current_total_pages

        idx_page_current = self.current_page
        
        idx_page_start:int = 1
        idx_page_end:int = 1

        if self.current_total_pages > num_pages_max:
            idx_page_start = idx_page_current - int(num_pages_max / 2)
            idx_page_end = idx_page_current + int(num_pages_max / 2)
            if idx_page_start < 0:
                idx_page_start = 0
                idx_page_end = num_pages_max
            elif idx_page_end >= self.current_total_pages:
                idx_page_start = self.current_total_pages - num_pages_max
                idx_page_end = self.current_total_pages
        else:
            if self.current_total_pages == 1:
                idx_page_start:int = 1
                idx_page_end:int = 1
            else:
                idx_page_start = 1
                idx_page_end = self.current_total_pages+1
        # print("Start, End: ",idx_page_start,", ", idx_page_end)

        for i in range(idx_page_start,idx_page_end):
            if i==0:
                continue
            self.get_assets(page=i,use_thread=True,is_background=True)
            op_props = middle.operator("simple.move_to", text=str(i), depress= i==self.current_page)
            op_props.page = i

    def build_asset_grid(self, layout):
        print("asset grid UI")
        grid = layout.grid_flow(row_major=True, columns=5, even_columns=True, even_rows=True, align=False)
        print("current page: ", self.current_page)
        assets = self.get_display_assets(self.current_page)
        prefs = bpy.context.preferences.addons["imeshh_online"].preferences
    
        for asset in assets:
            cell = grid.column().box()
            icon_id = self.get_thumbnail(asset)
            cell.template_icon(icon_value=icon_id, scale=3)
            
            asset_name = asset["name"]  # Define asset_name here
    
            # if the asset name is in prefs.downloaded_assets, don't add the Download button
            asset_exists = any(downloaded_asset.name == asset_name for downloaded_asset in prefs.downloaded_assets)
    
            if asset_exists:
                cell.operator("object.click_asset", text="Download").asset_name = asset_name
            else:
                # add an Append asset instead but for now, pass
                pass
    
            label_len = len(asset_name) // 2
            if prefs.show_asset_name:
                cell.label(text=asset_name[:label_len])
                cell.label(text=asset_name[label_len:])
            
    def build_ui(self, layout:bpy.types.UILayout, context):
        row = layout.row(align=True)
        row.prop(context.scene,"imeshh_search",text='',icon="VIEWZOOM")    
        row = layout.row(align=True)
        self.build_navigation(row)
        self.build_asset_grid(layout)
        row = layout.row(align=True)
        # #Create a button that takes the user to imeshh.com
        row.operator("wm.url_open", text="Visit Imeshh.com").url = "https://www.imeshh.com/"

print("creating _manager")
_manager = IMeshh_Manager()
print("_manager created: ", _manager)

def register():
    global _manager
    _manager.register()
    bpy.utils.register_class(OBJECT_OT_ClickAsset)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ClickAsset)
    global _manager
    if _manager.thread_pool is not None:
        _manager.thread_pool.shutdown(wait=True)
        bpy.utils.previews.remove(_manager.asset_previews)

    # if "_manager" in globals():
    #     del _manager