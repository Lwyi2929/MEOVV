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
st.title("🌍 土地利用分析_監督式分類")
st.write("""
Harmonized Sentinel-2 MSI: MultiSpectral Instrument，
ESA/WorldCover/v200/2021 土地覆蓋分析，使用 smileRandomForest(numberOfTrees=100)
""")

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

# 讀取 ESA WorldCover 2021 土地覆蓋圖層
my_lc = ee.Image('ESA/WorldCover/v200/2021').clip(roi)

# Remap 土地覆蓋類別
classValues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
remapValues = ee.List.sequence(0, 10)
my_lc = my_lc.remap(classValues, remapValues, bandName='Map').rename('lc').toByte()

# 土地覆蓋視覺化參數
classVis = {
    'min': 0,
    'max': 10,
    'palette': [
        '006400', 'ffbb22', 'ffff4c', 'f096ff', 'fa0000',
        'b4b4b4', 'f0f0f0', '0064c8', '0096a0', '00cf75', 'fae6a0'
    ]
}

# 建立地圖並添加圖層
my_Map = geemap.Map()
left_layer = geemap.ee_tile_layer(image, vis_params, 'Sentinel-2 false color')
right_layer = geemap.ee_tile_layer(my_lc, classVis, "ESA WorldCover")
my_Map.split_map(left_layer, right_layer)
my_Map.add_legend(title='ESA Land Cover Type', builtin_legend='ESA_WorldCover')
my_Map.centerObject(roi, 12)

# 顯示地圖
my_Map.to_streamlit(height=600)

st.title("2016/2018/2024年土地利用分類")


st.write("""
🌍2016年土地利用分析_禁限建令施行後
""")

#隨機採樣
label = 'lc' 
sample = image.addBands(my_lc).stratifiedSample(**{
        'numPoints': 10000,
        'classBand': label,
        'region': roi,            # ✅ 使用 roi
        'scale': 10,
        'geometries': True
    })
#訓練
sample = sample.randomColumn()
trainingSample = sample.filter('random <= 0.8')
validationSample = sample.filter('random > 0.8')

my_trainedClassifier = ee.Classifier.smileRandomForest(numberOfTrees=100).train(**{
    'features': trainingSample,
    'classProperty': 'lc',
    'inputProperties': image.bandNames()
})
# 取得 2016 年影像並進行處理
my_newimg_2016 = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(my_point)
    .filterDate('2016-01-01', '2016-12-31')
    .sort('CLOUDY_PIXEL_PERCENTAGE')
    .first()
    .clip(roi)
    .select('B.*')
)
# 分類
my_newimgClassified2016 = my_newimg_2016.classify(my_trainedClassifier)

# 顯示地圖
my_Map = geemap.Map()
my_Map.centerObject(my_newimg_2016, 12)
my_Map.addLayer(my_newimg_2016, vis_params, "Sentinel-2")
my_Map.addLayer(my_newimgClassified2016, classVis, 'Classified_smileRandomForest')
my_Map.add_legend(title='ESA Land Cover Type', builtin_legend='ESA_WorldCover')
my_Map.to_streamlit(height=600)

st.write("""
10 Tree:60.22平方公里 ；30 Grassland:11.43平方公里 :40 Cropland:0.85平方公里 ；50 Built-up:0.66平方公里 ；80 Open Water:0.19平方公里

""")

st.write("""
🌍2018年土地利用分析_禁限建令解禁
""")
# 取得 2018 年影像並進行處理
my_newimg_2018 = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(my_point)
    .filterDate('2018-01-01', '2018-12-31')
    .sort('CLOUDY_PIXEL_PERCENTAGE')
    .first()
    .clip(roi)
    .select('B.*')
)
# 分類
my_newimgClassified2018 = my_newimg_2018.classify(my_trainedClassifier)

# 顯示地圖
my_Map = geemap.Map()
my_Map.centerObject(my_newimg_2018, 12)
my_Map.addLayer(my_newimg_2018, vis_params, "Sentinel-2")
my_Map.addLayer(my_newimgClassified2018, classVis, 'Classified_smileRandomForest')
my_Map.add_legend(title='ESA Land Cover Type', builtin_legend='ESA_WorldCover')
my_Map.to_streamlit(height=600)
st.write("""
10 Tree:58.88平方公里 ；30 Grassland:12.86平方公里 :40 Cropland:0.91平方公里 ；50 Built-up:0.53平方公里 ；80 Open Water:0.18平方公里

""")
st.write("""
🌍2024年土地利用分析_禁限建令解禁後多年
""")
# 取得 2024 年影像並進行處理
my_newimg_2024 = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(my_point)
    .filterDate('2024-01-01', '2024-12-31')
    .sort('CLOUDY_PIXEL_PERCENTAGE')
    .first()
    .clip(roi)
    .select('B.*')
)
# 分類
my_newimgClassified2024 = my_newimg_2024.classify(my_trainedClassifier)

# 顯示地圖
my_Map = geemap.Map()
my_Map.centerObject(my_newimg_2024, 12)
my_Map.addLayer(my_newimg_2024, vis_params, "Sentinel-2")
my_Map.addLayer(my_newimgClassified2024, classVis, 'Classified_smileRandomForest')
my_Map.add_legend(title='ESA Land Cover Type', builtin_legend='ESA_WorldCover')
my_Map.to_streamlit(height=600)
st.write("""
10 Tree:51.40平方公里 ；30 Grassland:16.12平方公里 :40 Cropland:3.93平方公里 ；50 Built-up:1.55平方公里 ；80 Open Water:0.35平方公里

""")


#環境變遷
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import numpy as np
import os


# 標題
st.title("🌍 環境變遷分析：土地使用變化")

# 資料建立
data = {
    '類別': ['10 Trees', '30 Grassland', '40 Cropland', '50 Built-up', '80 Open water'],
    '2016': [60.22, 11.43, 0.85, 0.66, 0.19],
    '2018': [58.88, 12.86, 0.91, 0.53, 0.18],
    '2024': [51.40, 16.12, 3.93, 1.55, 0.35]
}
df = pd.DataFrame(data)

# 畫圖
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(df['類別']))
width = 0.25

bars1 = ax.bar(x - width, df['2016'], width, label='2016')
bars2 = ax.bar(x, df['2018'], width, label='2018')
bars3 = ax.bar(x + width, df['2024'], width, label='2024')

ax.set_xlabel("Land classification")
ax.set_ylabel("Area (square kilometers)")
ax.set_xticks(x)
ax.set_xticklabels(df['類別'])
ax.legend(title="Year")

# 數值標註
def add_labels(bars):
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

add_labels(bars1)
add_labels(bars2)
add_labels(bars3)

plt.tight_layout()
st.pyplot(fig)

# 顯示原始資料表
with st.expander("📋 顯示原始資料表"):
    st.dataframe(df)
