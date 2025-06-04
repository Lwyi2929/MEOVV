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
st.subheader("""
清境地區民宿林立，引發過度開發質疑，南投縣政府2012年頒布全面停發建照的[禁限建令](https://e-info.org.tw/node/210847)，並連續四年進行安全監測，老舊眷村的禁建，與民宿過度開發有關。在2018年5月15日，針對老舊眷村，有條件解除禁建令，並規定如果建築基地位在山崩地滑敏感區，必須進行詳細的地質鑽探。
""")

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

#環境變遷
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import numpy as np
import os

# 下載 Noto Sans TC（適用 Linux/macOS/Windows）
font_url = "https://noto-website-2.storage.googleapis.com/pkgs/NotoSansTC-Regular.otf"
font_path = "NotoSansTC-Regular.otf"

if not os.path.exists(font_path):
    import urllib.request
    urllib.request.urlretrieve(font_url, font_path)

# 註冊字型
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'Noto Sans TC'
plt.rcParams['axes.unicode_minus'] = False

# 畫面標題
st.title("🌏 環境變遷分析")


# 數據
categories = ['10 樹林', '30 草地', '40 農地', '50 建築', '80 水域']
years = ['2016', '2018', '2024']
values = [
    [60.22, 11.43, 0.85, 0.66, 0.19],
    [58.88, 12.86, 0.91, 0.53, 0.18],
    [51.40, 16.12, 3.93, 1.55, 0.35]
]
df = pd.DataFrame(values, columns=categories, index=years).T

# 畫圖
fig, ax = plt.subplots(figsize=(10, 6))
bar_width = 0.25
x = np.arange(len(df.index))

for i, year in enumerate(df.columns):
    ax.bar(x + i * bar_width, df[year], width=bar_width, label=year)

ax.set_xticks(x + bar_width)
ax.set_xticklabels(df.index)
ax.set_xlabel("土地分類")
ax.set_ylabel("面積（平方公里）")
ax.set_title("清境農場各年份土地使用分類")
ax.legend(title="年份")

# 數值標籤
for i, year in enumerate(df.columns):
    for xi, yi in zip(x, df[year]):
        ax.text(xi + i * bar_width, yi + 0.5, f"{yi:.2f}", ha='center', va='bottom', fontsize=9)

plt.tight_layout()
st.pyplot(fig)


