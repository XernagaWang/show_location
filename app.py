import random
import time

import folium
import pandas as pd
import requests

from tqdm import tqdm

tqdm.pandas(desc="Geocoding locations")

import streamlit as st
from streamlit_folium import st_folium
# from stqdm import stqdm  # 導入 stqdm


class CFG:
	"""
	配置類別，用於儲存 API 金鑰。
	"""

	API_KEY = "4b89b01bbb014329c7dde37d3b82f6aa"  # 替換為您的高德地圖 API 金鑰


def get_lat_lon(location):
	"""
	獲取指定地址的經緯度。

	參數：
									location：地址字符串。

	返回值：
									一個包含經緯度的元組，如果獲取失敗則返回 (None, None)。
	"""
	time.sleep(random.uniform(1, 5))  # 避免頻繁請求 API
	url = f"https://restapi.amap.com/v3/geocode/geo?key={CFG.API_KEY}&address={location}&city=北京"
	try:
		response = requests.get(url)
		data = response.json()
		if data["status"] == "1" and data["geocodes"]:  # 請求成功且有結果
			location_str = data["geocodes"][0]["location"]
			lon, lat = location_str.split(",")
			return lat, lon
		else:
			return None, None
	except Exception as e:
		print(f"Error processing location '{location}': {e}")  # 輸出錯誤訊息
		return None, None


@st.cache_data  # 使用缓存，避免重複計算
def geocode_dataframe(df):
	"""
	獲取數據集中所有地址的經緯度。

	參數：
									df：包含地址信息的 Pandas DataFrame。

	返回值：
									添加了經緯度列的 DataFrame。
	"""
	df[["lat","lon"]] = df["路口名称"].progress_apply(lambda x: pd.Series(get_lat_lon(x)))
	return df


st.title("Recommended Test Intersection Visualization")

if "geocoding_done" not in st.session_state:
	st.session_state.geocoding_done = False

uploaded_file = st.file_uploader("Please select a file to upload(.xlsx file only)", type=["xlsx"])

# if uploaded_file is not None:
if (uploaded_file is not None and not st.session_state.geocoding_done):  # 检查是否需要执行获取经纬度的操作
	df = pd.read_excel(uploaded_file, header=1)
	num_rows = len(df)
	estimated_time = num_rows * 5
	with st.spinner(f"Geocoding locations...Estimated time: {estimated_time} seconds"):
		df = geocode_dataframe(df)  # 调用缓存函数
	st.success("Geocoding complete!")
	st.session_state.geocoding_done = True  # 标记已经执行过获取经纬度的操作
	st.session_state.df = df  # 将 df 存储到会话状态中

if "df" in st.session_state:  # 检查 df 是否存在于会话状态中
	df = st.session_state.df  # 从会话状态中获取 df
	m = folium.Map(
		# location=[39.9042, 116.4074],
		location=[df["lat"].astype(float).mean(), df["lon"].astype(float).mean()],
		zoom_start=12,
		control_scale=True,
		tiles=
		"http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}&ltype=6",
		attr="高德地图",
		name="高德地图",
		overlay=True,
		control=True,
	)

	for locaiton_ in df.iterrows():
		if locaiton_[1]["lat"] and locaiton_[1]["lon"]:  # 檢查經緯度是否有效
			folium.Marker(
				location=[locaiton_[1]["lat"], locaiton_[1]["lon"]],
				popup=locaiton_[1]["路口名称"],
				).add_to(m)

	st_folium(m)
else:
	st.info("Please upload a file to start visualization.")
