import streamlit as st
#import leafmap.foliumap as leafmap

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
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

markdown = """
A Streamlit map app exercise
<https://geo3w.ncue.edu.tw/?Lang=zh-tw>
"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://i.imgur.com/UbOXYAU.png"
st.sidebar.image(logo)

st.title("合法民宿點位")
