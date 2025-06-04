import streamlit as st
import ee
from google.oauth2 import service_account
import geemap.foliumap as geemap

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
