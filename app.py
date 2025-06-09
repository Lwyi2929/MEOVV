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


# Display the image
st.image("sheep.png", caption="""青青草原""",use_container_width=True)





st.title("利用擴充器示範")
markdown = """
衛星影像時序動畫
"""
st.markdown(markdown)

with st.expander("播放真色影像mp4檔(landsat)1984年~2024年"):
    video_file = open("qingjing_true (1).mp4", "rb")  # "rb"指的是讀取二進位檔案（圖片、影片）
    video_bytes = video_file.read()
    st.video(video_bytes)

with st.expander("播放假色影像mp4檔(sentinel2) bands=['B8', 'B4', 'B3']2016年~2024年"):
    video_file = open("false_qingjing.mp4", "rb")  # "rb"指的是讀取二進位檔案（圖片、影片）
    video_bytes = video_file.read()
    st.video(video_bytes)
