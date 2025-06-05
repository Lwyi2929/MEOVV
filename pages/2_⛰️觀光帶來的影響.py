import streamlit as st
#import leafmap.foliumap as leafmap
# filename: app.py
import zipfile
import os
import geopandas as gpd
import tempfile

st.title("⛰️ 清境農場歷年遊憩據點人次統計")
st.subheader("""
1985年，隸屬於退輔會的清境國民賓館落成，921地震後帶動了觀光業，清境的民宿從十家變一百多家，遊客量也大增，不少業者為了增加房間數，違法擴建。民宿爭奇鬥豔，違法亂象與坡地安全，造成非都市土地使用失控。
""")
st.write("""
資料來源:交通部觀光署觀光統計資料庫
""")
# Display the image
st.image("tourists.png", caption="Annual tourist visits to Qingjing Farm",use_container_width=True)



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

st.sidebar.header("📁 hotel_love(.zip)")

uploaded_zip = st.sidebar.file_uploader("上傳 Shapefile ZIP 檔", type=["zip"])

if uploaded_zip:
    # 建立暫存資料夾
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "shapefile.zip")
        
        # 儲存上傳的 zip 檔案
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.read())

        # 解壓縮
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        # 尋找 .shp 檔案
        shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
        if shp_files:
            shp_path = os.path.join(tmpdir, shp_files[0])
            gdf = gpd.read_file(shp_path)
            st.success(f"✅ 成功載入 Shapefile：{shp_files[0]}")

            # 顯示屬性表
            st.dataframe(gdf.head())

            # 顯示在地圖上
            import folium
            from streamlit_folium import st_folium
            m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=13)
            folium.GeoJson(gdf).add_to(m)
            st_folium(m, height=500)
        else:
            st.error("❌ ZIP 壓縮檔中找不到 .shp 檔案")
my_Map.addLayer(my_newimgClassified2024, classVis, 'Classified_smileRandomForest')
my_Map.add_legend(title='ESA Land Cover Type', builtin_legend='ESA_WorldCover')


