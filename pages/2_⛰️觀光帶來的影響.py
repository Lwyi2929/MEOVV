import streamlit as st
import ee
from google.oauth2 import service_account
import geemap.foliumap as geemap

import geopandas as gpd
import requests
import zipfile
import os
import folium
from streamlit_folium import st_folium

st.title("⛰️ 清境農場歷年遊憩據點人次統計")
st.image("tourists.png", caption="Annual tourist visits to Qingjing Farm", use_container_width=True)

# GEE 授權
service_account_info = st.secrets["GEE_SERVICE_ACCOUNT"]
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/earthengine"]
)
ee.Initialize(credentials)

st.title("合法民宿點位")

# 定義研究區域
roi = ee.Geometry.Rectangle([121.116451, 24.020390, 121.21, 24.09])
my_point = ee.Geometry.Point([121.1617, 24.0495]);

# 擷取 Sentinel-2 影像
image = (
    ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
    .filterBounds(my_point)
    .filterDate("2021-01-01", "2022-01-01")
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .sort("CLOUDY_PIXEL_PERCENTAGE")
    .first()
    .clip(roi)
    .select('B.*')
)

# 可視化參數
vis_params = {'min': 100, 'max': 3500, 'bands': ['B11', 'B8', 'B3']}

# 土地覆蓋圖層
my_lc = ee.Image('ESA/WorldCover/v200/2021').clip(roi)
classValues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
remapValues = ee.List.sequence(0, 10)
my_lc = my_lc.remap(classValues, remapValues, bandName='Map').rename('lc').toByte()

classVis = {
    'min': 0,
    'max': 10,
    'palette': [
        '006400', 'ffbb22', 'ffff4c', 'f096ff', 'fa0000',
        'b4b4b4', 'f0f0f0', '0064c8', '0096a0', '00cf75', 'fae6a0'
    ]
}

# 隨機採樣與訓練
label = 'lc' 
sample = image.addBands(my_lc).stratifiedSample(**{
    'numPoints': 10000,
    'classBand': label,
    'region': roi,
    'scale': 10,
    'geometries': True
})
sample = sample.randomColumn()
trainingSample = sample.filter('random <= 0.8')
my_trainedClassifier = ee.Classifier.smileRandomForest(numberOfTrees=100).train(**{
    'features': trainingSample,
    'classProperty': 'lc',
    'inputProperties': image.bandNames()
})

# 2024 影像分類
my_newimg_2024 = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(my_point)
    .filterDate('2024-01-01', '2024-12-31')
    .sort('CLOUDY_PIXEL_PERCENTAGE')
    .first()
    .clip(roi)
    .select('B.*')
)
my_newimgClassified2024 = my_newimg_2024.classify(my_trainedClassifier)

# 建立 folium 地圖
m = folium.Map(location=[24.0495, 121.1617], zoom_start=13)

# 下載合法民宿 shp 並轉 GeoDataFrame
url = "https://github.com/Lwyi2929/MEOVV/raw/main/hotel_love.zip"
zip_path = "/tmp/hotel_love.zip"
extract_dir = "/tmp/shp"

r = requests.get(url)
with open(zip_path, "wb") as f:
    f.write(r.content)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

shp_files = [f for f in os.listdir(extract_dir) if f.endswith(".shp")]
in_shp = os.path.join(extract_dir, shp_files[0])
gdf = gpd.read_file(in_shp)

# 在地圖上加合法民宿
folium.GeoJson(gdf, name="合法民宿").add_to(m)

# 顯示地圖
st_data = st_folium(m, height=600)

