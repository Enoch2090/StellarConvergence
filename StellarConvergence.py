import numpy as np
import pandas as pd
import streamlit as st
import pydeck as pdk
import requests
import hashlib
import os
import random
from scipy import stats
from datetime import datetime
from PIL import Image
import asyncio


# ----------------Definitions----------------

API_KEY = 'YOUR_KEY'  # 高德地图开发者密钥
if os.path.exists("USE_ENV_KEY"):
    print("Using API_KEY retrieved from os environment: ")
    API_KEY = os.environ.get('API_KEY')
Z_SCORE_THRESHOLD = 1.00

# ----------------Utilities----------------


async def delete(file_path):
    await asyncio.sleep(86400)
    os.remove(file_path)


def geoCode(address):
    par = {'address': address, 'key': API_KEY}
    base = 'https://restapi.amap.com/v3/geocode/geo'
    response = requests.get(base, par)
    answer = response.json()
    return list(map(float, answer['geocodes'][0]['location'].split(","))) if int(answer['count']) > 0 else "Error"


def geoDecode(location):
    loc = str(location[0])+","+str(location[1])
    par = {'location': loc, 'key': API_KEY}
    base = 'https://restapi.amap.com/v3/geocode/regeo'
    response = requests.get(base, par)
    answer = response.json()
    return answer['regeocode']['formatted_address'] if answer['info'] == 'OK' else "Error"


def getPos(map_data):
    # TODO: Better algo.
    lat_mean = round(map_data.mean(axis=0)['lat'], 6)
    lon_mean = round(map_data.mean(axis=0)['lon'], 6)
    return [lat_mean, lon_mean]


def removeOutliers(pos_data):
    # Remove outliers.
    z_scores = stats.zscore(pos_data)
    abs_z_scores = np.abs(z_scores)
    filtered_entries = (abs_z_scores < Z_SCORE_THRESHOLD).all(axis=1)
    return abs_z_scores, pos_data[filtered_entries]

    # ----------------Menu----------------


st.sidebar.title('StellarConvergence')
option = st.sidebar.selectbox(
    'Menu',
    ['提交位置', '查看地图', '使用帮助', '关于'])


# ----------------Functionalities----------------
if option == '提交位置':
    st.title('提交位置')
    data_submitted = False
    today = datetime.now()
    addr_cache = st.text_input('输入当前位置：')
    fname_cache = st.text_input('输入活动代码，若无则留空')
    if st.button('Submit'):  # Submit button clicked event
        if addr_cache == '':
            st.warning('地址不能为空！')
        else:
            try:
                [lon, lat] = geoCode(addr_cache)
            except ValueError:
                st.warning('无效地址，请重新输入。')
            if fname_cache == '':
                fname_cache = hashlib.sha1(
                    (addr_cache+str(random.randint(1, 1000))).encode('utf-8')).hexdigest()
            data_path = fname_cache+'.csv'
            if os.path.exists(data_path):
                df = pd.DataFrame(
                    columns=['date', 'lat', 'lon'], data=[[today.strftime('%a, %b %d %H:%M'), lat, lon]])
                df.to_csv(data_path, mode='a', header=False)
                '提交成功。'
            else:
                df = pd.DataFrame(
                    columns=['date', 'lat', 'lon'], data=[[today.strftime('%a, %b %d %H:%M'), lat, lon]])
                df.to_csv(data_path)
                '提交成功。您的活动代码为'
                fname_cache
                '请将此代码分享给其他人来共用这一活动。活动有效期为 24 小时。'
                asyncio.run(delete(data_path))
elif option == '查看地图':
    st.title('查看地图')
    fname_cache = st.text_input('输入活动代码，若无则留空')
    if st.button('Submit'):
        if fname_cache == '':
            st.warning('无效代码，请重新输入。')
        else:
            data_path = fname_cache+'.csv'
            if not os.path.exists(data_path):
                st.warning('未找到活动，请重新输入代码。')
            else:
                map_data = pd.read_csv(data_path, usecols=[2, 3])
                map_data = map_data.reindex(index=range(len(map_data)))
                st.dataframe(map_data)
                [lat_mean, lon_mean] = getPos(map_data)
                st.pydeck_chart(pdk.Deck(
                    map_style='mapbox://styles/mapbox/basic-v9',
                    initial_view_state=pdk.ViewState(
                        latitude=lat_mean,
                        longitude=lon_mean,
                        zoom=15,
                        pitch=50,
                    ),
                    layers=[
                        pdk.Layer(
                            'ScatterplotLayer',
                            data=map_data,
                            get_position='[lon, lat]',
                            get_color='[200, 30, 0, 160]',
                            get_radius=450,
                        ),
                        pdk.Layer(
                            'ScatterplotLayer',
                            data=pd.DataFrame(columns=['lat', 'lon'], data=[
                                              [lat_mean, lon_mean]]),
                            get_position='[lon, lat]',
                            get_color='[30, 200, 0, 160]',
                            get_radius=650,
                        ),
                    ],
                ))

                '中心点的位置是：('+str(lat_mean)+", "+str(lon_mean)+")"
                '中心点的大致地址：'+geoDecode([lon_mean, lat_mean])

elif option == '使用帮助':
    f = open('README.md', 'r')
    lines = f.readlines()
    f.close()
    README = ''
    for line in lines:
        README += line
    st.markdown(README)

elif option == '关于':
    st.title('关于')
    '''
    [WhiteGivers](https://whitegivers.com).
    [Enoch2090](https://enoch2090.me).
    '''
# ----------------Hide Development Menu----------------
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
