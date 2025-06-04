import streamlit as st
import ee
from google.oauth2 import service_account
import geemap.foliumap as geemap
import zipfile
import os
import geopandas as gpd
import tempfile
import streamlit as st
import folium
from streamlit_folium import st_folium

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

st.header("📂 崩塌區圖層顯示")

# 指定你上傳檔案的位置
uploaded_zip_path = "/mnt/data/110崩塌.zip"

# 解壓縮並讀取 Shapefile
with tempfile.TemporaryDirectory() as tmpdir:
    with zipfile.ZipFile(uploaded_zip_path, "r") as zip_ref:
        zip_ref.extractall(tmpdir)

    # 尋找 .shp 檔
    shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
    if shp_files:
        shp_path = os.path.join(tmpdir, shp_files[0])
        gdf = gpd.read_file(shp_path)

        # 顯示資料表
        st.success(f"✅ 成功載入 {shp_files[0]}")
        st.dataframe(gdf.head())

        # 顯示在 Folium 地圖
        m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=13)
        folium.GeoJson(gdf, name="崩塌區").add_to(m)
        folium.LayerControl().add_to(m)
        st_folium(m, height=500)
    else:
        st.error("❌ ZIP 裡沒有找到 .shp 檔案。請確認 ZIP 包含 .shp, .shx, .dbf 等檔案。")


# 顯示標題
st.title("崩塌地圖展示 (collapse_110.shp)")
# 載入資料
in_shp = 'collapse_110.shp'  # ⚠️ 放在同一資料夾或換成你的路徑
gdf = gpd.read_file(in_shp)
# 建立 folium 地圖
center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
m = folium.Map(location=center, zoom_start=13)
# 加上 GeoData
folium.GeoJson(gdf).add_to(m)
# 顯示在 Streamlit 中
st_data = st_folium(m, width=700, height=500)

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
