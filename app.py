import streamlit as st
from datetime import date

st.set_page_config(layout="wide", page_title="🐑清境農場周邊土地利用分類與環境變遷分析")

st.title("清境農場周邊土地利用分類與環境變遷分析")

st.markdown(
    """
    This multipage app template demonstrates various interactive web apps created using [streamlit](https://streamlit.io), [GEE](https://earthengine.google.com/), 
    [geemap](https://leafmap.org) and [leafmap](https://leafmap.org). 
    """
)

st.header("關於清境農場")

markdown = """
[清境農場官網](https://www.cingjing.gov.tw/about/index.php?index_id=25)
1. 1961年  安置滇緬戰區撤台的軍隊與榮民設立清境農場
2. 1980年 自給自足農場轉型為觀光農場。 
3. 1993年 釋出國有農地  使得外地者陸續進駐清境經營民宿  .
4. 造成山坡地過度開發
"""

st.markdown(markdown)




#st.title("選擇日期區間")


# 初始化 session_state
#if 'start_date' not in st.session_state:
#    st.session_state['start_date'] = date(2024, 1, 1)
#if 'end_date' not in st.session_state:
#    st.session_state['end_date'] = date.today()

#st.session_state['start_date'] = date(2024, 1, 1)
#st.session_state['end_date'] = date.today()


# 日期選擇器
#start_date = st.date_input(label = "選擇起始日期", value = st.session_state['start_date'], min_value = date(2018, 1, 1), max_value = date.today())
#end_date = st.date_input(label = "選擇結束日期", value = st.session_state['end_date'], min_value = start_date, max_value = date.today())

# 儲存使用者選擇
#st.session_state['start_date'] = start_date
#st.session_state['end_date'] = end_date

#st.success(f"目前選擇的日期區間為：{start_date} 到 {end_date}")


st.title("利用擴充器示範")
markdown = """
2016年~2024年的衛星影像時序動畫
"""
st.markdown(markdown)

with st.expander("播放真色影像mp4檔(landsat)"):
    video_file = open("qingjing_true (1).mp4", "rb")  # "rb"指的是讀取二進位檔案（圖片、影片）
    video_bytes = video_file.read()
    st.video(video_bytes)

with st.expander("播放假色影像mp4檔(sentinel2) bands=['B8', 'B4', 'B3']"):
    video_file = open("false_qingjing.mp4", "rb")  # "rb"指的是讀取二進位檔案（圖片、影片）
    video_bytes = video_file.read()
    st.video(video_bytes)
