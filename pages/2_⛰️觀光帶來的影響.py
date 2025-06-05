import streamlit as st
import ee
from google.oauth2 import service_account
import geemap.foliumap as geemap
import geopandas as gpd # 由於您需要讀取 shp，geopandas 還是需要的
import requests
import zipfile
import os

st.title("⛰️ 清境農場歷年遊憩據點人次統計")
st.subheader("""
1985年，隸屬於退輔會的清境國民賓館落成，921地震後帶動了觀光業，清境的民宿從十家變一百多家，遊客量也大增，不少業者為了增加房間數，違法擴建。民宿爭奇鬥豔，違法亂象與坡地安全，造成非都市土地使用失控。
""")
st.write("""
資料來源:交通部觀光署觀光統計資料庫
""")
# Display the image
st.image("tourists.png", caption="Annual tourist visits to Qingjing Farm",use_container_width=True)


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
        'region': roi,
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

# --- 地圖創建與圖層添加 ---
my_Map = geemap.Map() # 創建 geemap 的地圖物件
my_Map.centerObject(my_newimg_2024, 12) # 將地圖中心設置到 2024 影像上

# 添加 Earth Engine 圖層 (geemap 的 addLayer 是 add_ee_layer 的別名)
my_Map.addLayer(my_newimg_2024, vis_params, "Sentinel-2")
my_Map.addLayer(my_newimgClassified2024, classVis, 'Classified_smileRandomForest')


# --- 下載並處理合法民宿 SHP 文件 ---
# 使用 st.cache_data 緩存下載和處理過程，避免每次執行都重複下載解壓縮
@st.cache_data
def load_and_process_hotel_shp(url):
    zip_path = "hotel_love.zip" # 直接在當前工作目錄下載
    extract_dir = "hotel_data" # 創建一個專門的資料夾來解壓縮

    # 確保下載目錄存在（如果 Streamlit Cloud 清理 /tmp 以外的目錄）
    os.makedirs(extract_dir, exist_ok=True)

    # 1. 下載 ZIP 文件
    st.write(f"正在下載 {url}...")
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status() # 檢查 HTTP 請求是否成功
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        st.write("下載完成。")
    except requests.exceptions.RequestException as e:
        st.error(f"下載失敗: {e}")
        return None

    # 2. 解壓縮 ZIP 文件
    st.write(f"正在解壓縮 {zip_path} 到 {extract_dir}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        st.write("解壓縮完成。")
    except zipfile.BadZipFile:
        st.error(f"'{zip_path}' 不是一個有效的 ZIP 文件。")
        return None
    except Exception as e:
        st.error(f"解壓縮失敗: {e}")
        return None

    # 3. 尋找 .shp 文件
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

    # 4. 讀取 GeoDataFrame 並處理 CRS
    try:
        gdf = gpd.read_file(shp_file_path)
        # CRS 轉換
        if gdf.crs is None:
            # 假設您的民宿資料是WGS84 (EPSG:4326)，如果不是，請修改這裡
            gdf = gdf.set_crs("EPSG:4326", allow_override=True)
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        st.write("民宿資料載入成功。")
        return gdf
    except Exception as e:
        st.error(f"讀取或處理 SHP 文件失敗: {e}")
        return None

# 調用緩存的函數來獲取 gdf
hotel_zip_url = "https://raw.githubusercontent.com/Lwyi2929/MEOVV/refs/heads/main/hotel_love.zip"
gdf_hotels = load_and_process_hotel_shp(hotel_zip_url)

if gdf_hotels is not None:
    # 使用 geemap 的 add_gdf 方法添加 GeoDataFrame
    # geemap 內部會處理 folium 的 GeoJson
    my_Map.add_gdf(gdf_hotels, layer_name='合法民宿')
    st.write("合法民宿點位已添加到地圖。")
else:
    st.warning("未能載入合法民宿點位，地圖上可能不會顯示。")

# 添加圖例
my_Map.add_legend(title='ESA Land Cover Type', builtin_legend='ESA_WorldCover')

# 顯示地圖
my_Map.to_streamlit(height=600)
