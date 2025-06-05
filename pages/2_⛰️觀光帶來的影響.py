import streamlit as st
import ee
from google.oauth2 import service_account
import geemap
import requests
import zipfile
import os

# 標題與圖片
st.title("⛰️ 清境農場歷年遊憩據點人次統計")
st.subheader("1985年，隸屬於退輔會的清境國民賓館落成，921地震後帶動了觀光業...")
st.image("tourists.png", caption="Annual tourist visits to Qingjing Farm", use_container_width=True)

# Earth Engine 初始化
service_account_info = st.secrets["GEE_SERVICE_ACCOUNT"]
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/earthengine"]
)
ee.Initialize(credentials)

# 設定區域與影像
roi = ee.Geometry.Rectangle([121.116451, 24.020390, 121.21, 24.09])
my_point = ee.Geometry.Point([121.1617, 24.0495])

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

# 土地分類訓練與應用
my_lc = ee.Image('ESA/WorldCover/v200/2021').clip(roi)
classValues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
remapValues = ee.List.sequence(0, 10)
my_lc = my_lc.remap(classValues, remapValues, bandName='Map').rename('lc').toByte()

sample = image.addBands(my_lc).stratifiedSample(
    numPoints=10000,
    classBand='lc',
    region=roi,
    scale=10,
    geometries=True
).randomColumn()

trainingSample = sample.filter('random <= 0.8')
my_trainedClassifier = ee.Classifier.smileRandomForest(100).train(
    features=trainingSample,
    classProperty='lc',
    inputProperties=image.bandNames()
)

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

# 顯示地圖
my_Map = geemap.Map()
my_Map.centerObject(my_newimg_2024, 12)
my_Map.addLayer(my_newimg_2024, {'min': 100, 'max': 3500, 'bands': ['B11', 'B8', 'B3']}, "Sentinel-2")
my_Map.addLayer(my_newimgClassified2024, {
    'min': 0,
    'max': 10,
    'palette': [
        '006400', 'ffbb22', 'ffff4c', 'f096ff', 'fa0000',
        'b4b4b4', 'f0f0f0', '0064c8', '0096a0', '00cf75', 'fae6a0'
    ]
}, 'Classified_smileRandomForest')

# 下載 ZIP 並載入 Shapefile
url = "https://github.com/Lwyi2929/MEOVV/raw/main/hotel_love.zip"
zip_path = "/tmp/hotel_love.zip"
extract_dir = "/tmp/shp"

r = requests.get(url)
with open(zip_path, "wb") as f:
    f.write(r.content)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

shp_files = [f for f in os.listdir(extract_dir) if f.endswith(".shp")]
if shp_files:
    in_shp = os.path.join(extract_dir, shp_files[0])
    my_Map.add_shp(in_shp, layer_name='hotel')
    st.success(f"✅ 成功載入圖層：{shp_files[0]}")
else:
    st.error("❌ 找不到 .shp 檔案")

my_Map.add_legend(title='ESA Land Cover Type', builtin_legend='ESA_WorldCover')
my_Map.to_streamlit(height=600)



