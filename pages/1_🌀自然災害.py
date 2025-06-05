import streamlit as st
import ee
from google.oauth2 import service_account
import geemap.foliumap as geemap
import geopandas as gpd 
import requests
import zipfile
import os

# 從 Streamlit Secrets 讀取 GEE 服務帳戶金鑰 JSON
service_account_info = st.secrets["GEE_SERVICE_ACCOUNT"]

# 使用 google-auth 進行 GEE 授權
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/earthengine"]
)

# 初始化 Earth Engine
ee.Initialize(credentials)

# Streamlit 設定
st.set_page_config(layout="wide")
st.title("🌀自然災害影響")

st.write("""
Harmonized Sentinel-2 
卡努颱風前(2023/06/01-2023/07/31) : 卡努颱風後(2023/08/01-2023/09/30)
""")
my_Map  = geemap.Map()
roi = my_Map.user_roi
if roi is None:
    roi = ee.Geometry.Rectangle([ 121.116451, 24.020390, 121.21, 24.09] )#設定研究區域
    my_Map.addLayer(roi)
    my_Map.centerObject(roi, 10)
my_point = ee.Geometry.Point([121.1617, 24.0495]);
my_Map .centerObject(roi, 12)

# 取得 2023 年影像並進行處理
my_newimg_Bef = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(my_point)
    .filterDate('2023-06-1', '2023-7-31')
    .sort('CLOUDY_PIXEL_PERCENTAGE')
    .first()
    .clip(roi)
    .select('B.*')
)
my_newimg_Aft = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(my_point)
    .filterDate('2023-08-1', '2023-9-30')
    .sort('CLOUDY_PIXEL_PERCENTAGE')
    .first()
    .clip(roi)
    .select('B.*')
)

# 影像顯示參數
vis_params = {'min': 100, 'max': 3500, 'bands': ['B11', 'B8', 'B3']}
my_Map = geemap.Map()
my_Map.centerObject(my_newimg_Bef.geometry(), 13)
left_layer = geemap.ee_tile_layer(my_newimg_Bef,vis_params, '卡努颱風前')
right_layer = geemap.ee_tile_layer(my_newimg_Aft,vis_params, '卡努颱風後')
my_Map.split_map(left_layer, right_layer)

# 顯示地圖
my_Map.to_streamlit(height=600)


st.write("""
Harmonized Sentinel-2 
康芮颱風前(2024/09/01-2024/10/29) : 康芮颱風後(2024/10/30-2024/12/30)
""")

my_Map2  = geemap.Map()
roi = my_Map.user_roi
if roi is None:
    roi = ee.Geometry.Rectangle([ 121.116451, 24.020390, 121.21, 24.09] )#設定研究區域
    my_Map.addLayer(roi)
    my_Map.centerObject(roi, 10)
my_point = ee.Geometry.Point([121.1617, 24.0495]);
my_Map .centerObject(roi, 12)

# 取得 2024 年影像並進行處理
my_newimg_Bef = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(my_point)
    .filterDate('2024-09-01', '2024-10-29')
    .sort('CLOUDY_PIXEL_PERCENTAGE')
    .first()
    .clip(roi)
    .select('B.*')
)
my_newimg_Aft = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(my_point)
    .filterDate('2024-10-30', '2024-12-30')
    .sort('CLOUDY_PIXEL_PERCENTAGE')
    .first()
    .clip(roi)
    .select('B.*')
)

# 影像顯示參數
vis_params = {'min': 100, 'max': 3500, 'bands': ['B11', 'B8', 'B3']}
my_Map = geemap.Map()
my_Map.centerObject(my_newimg_Bef.geometry(), 13)
left_layer = geemap.ee_tile_layer(my_newimg_Bef,vis_params, '康芮颱風前')
right_layer = geemap.ee_tile_layer(my_newimg_Aft,vis_params, '康芮颱風後')
my_Map.split_map(left_layer, right_layer)
# 顯示地圖
my_Map.to_streamlit(height=600)

st.write("### 🌿_康芮颱風造成NDVI值變化 差異圖")

# 取得 NDVI 災前/災後影像（康芮）
ndvi_bef = my_newimg_Bef.normalizedDifference(['B8', 'B4']).rename('NDVI_Before')
ndvi_aft = my_newimg_Aft.normalizedDifference(['B8', 'B4']).rename('NDVI_After')
ndvi_diff = ndvi_aft.subtract(ndvi_bef).rename('NDVI_Diff')

ndvi_vis = {
    'min': -1,
    'max': 1,
    'palette': ['red', 'white', 'green']
}

# 建立地圖顯示 NDVI 差異
ndvi_map = geemap.Map()
ndvi_map.centerObject(ndvi_diff.geometry(), 13)
ndvi_map.addLayer(ndvi_diff, ndvi_vis, 'NDVI 差異圖 (災後 - 災前)')

# 顯示地圖
ndvi_map.to_streamlit(height=600)


@st.cache_data
def load_and_process_hotel_shp(url):
    zip_path = "collapse.zip" # 直接在當前工作目錄下載
    extract_dir = "collapse_data" # 創建一個專門的資料夾來解壓縮

    # 確保下載目錄存在（如果 Streamlit Cloud 清理 /tmp 以外的目錄）
    os.makedirs(extract_dir, exist_ok=True)

    # 下載 ZIP 文件
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status() # 檢查 HTTP 請求是否成功
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.exceptions.RequestException as e:
        st.error(f"下載失敗: {e}")
        return None

    # 解壓縮 ZIP 文件
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except zipfile.BadZipFile:
        st.error(f"'{zip_path}' 不是一個有效的 ZIP 文件。")
        return None
    except Exception as e:
        st.error(f"解壓縮失敗: {e}")
        return None

    # 尋找 .shp 文件
    shp_file_path = None
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(".shp"):
                shp_file_path = os.path.join(root, file)
                break
        if shp_file_path:
            break

    if shp_file_path is None:
        st.error("在解壓縮的資料夾中找不到 .shp 文件。")
        return None

    # 讀取 GeoDataFrame 並處理 CRS
    try:
        gdf = gpd.read_file(shp_file_path)
        # CRS 轉換
        if gdf.crs is None:
            # 假設您的民宿資料是WGS84 (EPSG:4326)，如果不是，請修改這裡
            gdf = gdf.set_crs("EPSG:4326", allow_override=True)
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        return gdf
    except Exception as e:
        st.error(f"讀取或處理 SHP 文件失敗: {e}")
        return None

# 調用緩存的函數來獲取 gdf
collapse_zip_url = "https://raw.githubusercontent.com/Lwyi2929/MEOVV/refs/heads/main/hotel_love.zip"
gdf_hotels = load_and_process_hotel_shp(hotel_zip_url)

if gdf_hotels is not None:
    # 使用 geemap 的 add_gdf 方法添加 GeoDataFrame
    # geemap 內部會處理 folium 的 GeoJson
    my_Map.add_gdf(gdf_hotels, layer_name='崩塌範圍')
else:
    st.warning("未能載入崩塌資料，地圖上可能不會顯示。")

# 添加圖例
my_Map.add_legend(title='ESA Land Cover Type', builtin_legend='ESA_WorldCover')

# 顯示地圖
my_Map.to_streamlit(height=600)
