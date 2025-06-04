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

# 初始化 GEE
ee.Initialize(credentials)

st.set_page_config(layout="wide")
st.title("🌍土地利用分析 ")
st.write("Harmonized Sentinel-2 MSI: MultiSpectral Instrument,
ESA/WorldCover/v200/2021 土地覆蓋 smileRandomForest(numberOfTrees=100) ")

#地理區域
roi = ee.Geometry.Rectangle([121.116451, 24.020390, 121.21, 24.09])

# 擷取 Harmonized Sentinel-2 MSI: MultiSpectral Instrument, Level-1C 衛星影像
image = (
    ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
    .filterBounds(roi)
    .filterDate("2021-01-01", "2022-01-01")
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .sort("CLOUDY_PIXEL_PERCENTAGE")
    .first()
    
)
vis = {'min': 100, 'max': 3500, 'bands': ['B11', 'B8', 'B3']}


# 土地覆蓋影像 (ESA WorldCover 2021)
my_lc = ee.Image('ESA/WorldCover/v200/2021')
my_lc = my_lc.clip(roi)

# Remap 類別值
classValues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
remapValues = ee.List.sequence(0, 10)
label = 'lc'
my_lc = my_lc.remap(classValues, remapValues, bandName='Map').rename(label).toByte()

# 顯示 land cover
classVis = {
    'min': 0,
    'max': 10,
    'palette': ['006400' ,'ffbb22', 'ffff4c', 'f096ff', 'fa0000', 'b4b4b4',
                'f0f0f0', '0064c8', '0096a0', '00cf75', 'fae6a0']
}

my_Map = geemap.Map()
left_layer = geemap.ee_tile_layer(image, vis, 'Sentinel-2 flase color')
right_layer = geemap.ee_tile_layer(my_lc, classVis, "ESA WorldCover")
Map.add_legend(title='ESA Land Cover Type', builtin_legend='ESA_WorldCover')
my_Map.split_map(left_layer, right_layer)

# 顯示地圖在 Streamlit
my_Map.to_streamlit(height=600)
