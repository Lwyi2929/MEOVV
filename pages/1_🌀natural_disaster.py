import streamlit as st
import ee
from google.oauth2 import service_account
import geemap.foliumap as geemap
import geopandas as gpd
import requests
import zipfile
import os

# --- 1. GEE 初始化與工具函式 ---
@st.cache_resource
def initialize_gee():
    try:
        service_account_info = st.secrets["GEE_SERVICE_ACCOUNT"]
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/earthengine"]
        )
        ee.Initialize(credentials)
    except Exception as e:
        st.error(f"Earth Engine 初始化失敗：請檢查您的 GEE_SERVICE_ACCOUNT 設定。錯誤訊息: {e}")
        st.stop() # 如果 GEE 無法初始化，則停止應用程式運行

@st.cache_data
def get_sentinel_image(point_coords, roi_coords, start_date, end_date): # 參數名稱變更為更明確的 coords
    """
    獲取指定日期範圍內雲量最低的 Sentinel-2 影像。
    使用 st.cache_data 緩存 GEE 影像查詢結果。
    現在接受座標列表作為 point 和 roi 的輸入。
    """
    try:
        # 將座標列表轉換回 ee.Geometry 物件
        point = ee.Geometry.Point(point_coords)
        roi = ee.Geometry.Rectangle(roi_coords)

        image = (
            ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
            .filterBounds(point)
            .filterDate(start_date, end_date)
            .sort('CLOUDY_PIXEL_PERCENTAGE')
            .first()
            .clip(roi)
            .select('B.*')
        )
        # 檢查影像是否為 None，如果沒有找到合適的影像，first() 可能返回 None
        if image.getInfo() is None:
            st.warning(f"在 {start_date} 到 {end_date} 期間，指定區域內未找到 Sentinel-2 影像。")
            return None
        return image
    except Exception as e:
        st.error(f"獲取 Sentinel 影像失敗 ({start_date} - {end_date}): {e}")
        return None
# --- 3. 地圖顯示函式 ---
def display_split_map(map_object, left_ee_image, left_name, right_ee_image, right_name, vis_params):
    """
    顯示左右分開的地圖。
    """
    if left_ee_image and right_ee_image:
        left_layer = geemap.ee_tile_layer(left_ee_image, vis_params, left_name)
        right_layer = geemap.ee_tile_layer(right_ee_image, vis_params, right_name)
        map_object.split_map(left_layer, right_layer)
    elif left_ee_image:
        map_object.addLayer(left_ee_image, vis_params, left_name)
    elif right_ee_image:
        map_object.addLayer(right_ee_image, vis_params, right_name)
    else:
        st.warning("沒有影像可以顯示。")

# --- 4. Streamlit 應用程式主體 ---
def main():
    st.set_page_config(layout="wide")
    st.title("🌀自然災害影響監測")

    # GEE 初始化
    initialize_gee()

    # 定義常用的 ROI 和中心點
    default_roi_coords = [121.116451, 24.020390, 121.21, 24.09]
    default_point_coords = [121.1617, 24.0495]

    # 在這裡創建 GEE 幾何物件，僅用於地圖初始化和顯示
    default_roi = ee.Geometry.Rectangle(default_roi_coords)
    default_point = ee.Geometry.Point(default_point_coords)

    vis_params = {'min': 100, 'max': 3500, 'bands': ['B11', 'B8', 'B3']} # 假彩色紅外影像

    # --- 卡努颱風區塊 ---
    st.header("🌪️ 卡努颱風影響 (2023)")
    st.write("影像：Harmonized Sentinel-2")
    st.write("---")

    # 獲取卡努颱風前後影像
    with st.spinner("正在載入卡努颱風前影像..."):
        kanu_img_bef = get_sentinel_image(default_point_coords, default_roi_coords, '2023-06-01', '2023-07-31')
    with st.spinner("正在載入卡努颱風後影像..."):
        kanu_img_aft = get_sentinel_image(default_point_coords, default_roi_coords, '2023-08-01', '2023-09-30')

    kanu_map = geemap.Map()
    if kanu_img_bef:
        kanu_map.centerObject(kanu_img_bef.geometry(), 13)
    else:
        kanu_map.centerObject(default_roi, 12) # 如果沒有影像，則中心定位到預設 ROI

    display_split_map(kanu_map, kanu_img_bef, '卡努颱風前 (2023/06/01-07/31)',
                      kanu_img_aft, '卡努颱風後 (2023/08/01-09/30)', vis_params)
    kanu_map.to_streamlit(height=600)
# --- NDVI 差異圖區塊 (卡努颱風) ---
    st.header("🌿 卡努颱風造成 NDVI 值變化差異圖")
    if kanu_img_bef and kanu_img_aft:
        ndvi_bef = kanu_img_bef.normalizedDifference(['B8', 'B4']).rename('NDVI_Before')
        ndvi_aft = kanu_img_aft.normalizedDifference(['B8', 'B4']).rename('NDVI_After')
        ndvi_diff = ndvi_aft.subtract(ndvi_bef).rename('NDVI_Diff')

        ndvi_vis = {
            'min': -1,
            'max': 1,
            'palette': ['red', 'white', 'green'] # 紅色表示減少，綠色表示增加
        }

        ndvi_map = geemap.Map()
        ndvi_map.centerObject(ndvi_diff.geometry(), 13)
        ndvi_map.addLayer(ndvi_diff, ndvi_vis, 'NDVI 差異圖 (災後 - 災前)')
        ndvi_map.add_colorbar(ndvi_vis, label="NDVI 差異", orientation="horizontal", layer_name='NDVI 差異')
        ndvi_map.to_streamlit(height=600)
    else:
        st.info("由於缺乏卡努颱風前後影像，無法顯示 NDVI 差異圖。")
    st.markdown("---") # 分隔線

    # --- 康芮颱風區塊 ---
    st.header("🌪️ 康芮颱風影響 (2024)")
    st.write("影像：Harmonized Sentinel-2")
    st.write("---")

    # 獲取康芮颱風前後影像
    with st.spinner("正在載入康芮颱風前影像..."):
        kangrui_img_bef = get_sentinel_image(default_point_coords, default_roi_coords, '2024-09-01', '2024-10-29')
    with st.spinner("正在載入康芮颱風後影像..."):
        kangrui_img_aft = get_sentinel_image(default_point_coords, default_roi_coords, '2024-10-30', '2024-12-30')

    kangrui_map = geemap.Map()
    if kangrui_img_bef:
        kangrui_map.centerObject(kangrui_img_bef.geometry(), 13)
    else:
        kangrui_map.centerObject(default_roi, 12) # 如果沒有影像，則中心定位到預設 ROI

    display_split_map(kangrui_map, kangrui_img_bef, '康芮颱風前 (2024/09/01-10/29)',
                      kangrui_img_aft, '康芮颱風後 (2024/10/30-12/30)', vis_params)
    kangrui_map.to_streamlit(height=600)

    st.markdown("---") # 分隔線

    # --- NDVI 差異圖區塊 (康芮颱風) ---
    st.header("🌿 康芮颱風造成 NDVI 值變化差異圖")
    if kangrui_img_bef and kangrui_img_aft:
        ndvi_bef = kangrui_img_bef.normalizedDifference(['B8', 'B4']).rename('NDVI_Before')
        ndvi_aft = kangrui_img_aft.normalizedDifference(['B8', 'B4']).rename('NDVI_After')
        ndvi_diff = ndvi_aft.subtract(ndvi_bef).rename('NDVI_Diff')

        ndvi_vis = {
            'min': -1,
            'max': 1,
            'palette': ['red', 'white', 'green'] # 紅色表示減少，綠色表示增加
        }

        ndvi_map = geemap.Map()
        ndvi_map.centerObject(ndvi_diff.geometry(), 13)
        ndvi_map.addLayer(ndvi_diff, ndvi_vis, 'NDVI 差異圖 (災後 - 災前)')
        ndvi_map.add_colorbar(ndvi_vis, label="NDVI 差異", orientation="horizontal", layer_name='NDVI 差異')
        ndvi_map.to_streamlit(height=600)
    else:
        st.info("由於缺乏康芮颱風前後影像，無法顯示 NDVI 差異圖。")

    st.markdown("---") # 分隔線

@st.cache_data
def load_and_process_hotel_shp(url):
    zip_path = "hotel_love.zip" # 直接在當前工作目錄下載
    extract_dir = "hotel_data" # 創建一個專門的資料夾來解壓縮

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
        
    st.header("⛰️ 崩塌範圍圖層")
    st.write("---")
    collapse110_zip_url = "https://raw.githubusercontent.com/Lwyi2929/MEOVV/474afe38979b8bf19bf640acce7289ad48d1f786/collapse110.zip"
    gdf_collapse110 = load_and_process_shp(collapse110_zip_url)
    if gdf_collapse110 is not None:
        my_Map.add_gdf(gdf_collapse110, layer_name='崩塌範圍 (110年)', zoom_to_layer=False)
    else:
        st.warning("未能載入崩塌圖資，地圖上可能不會顯示。")

    # 顯示地圖
    my_Map.to_streamlit(height=600)

if __name__ == "__main__":
    main()
