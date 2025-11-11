import numpy as np
import streamlit as st
from streamlit_folium import st_folium

from fetchLST import fetch_lst
from anomaly import analyze_anomalies, calculate_emission_score
from folium_map import create_map


st.set_page_config(page_title="Factory Emissions Visualizer",
                page_icon="🌍",
                layout="wide")

st.title("🌍 Factory Emissions Visualizer")

with st.sidebar:
    st.header("Factory Coordinates")
    lat = st.number_input("Latitude",  value=20.95150000, format="%.8f")
    lon = st.number_input("Longitude", value=85.2157, format="%.8f")
    run_btn = st.button("Analyze Emissions", type="primary")

if run_btn:
    try:
        with st.spinner("Fetching LST data from Google Earth Engine…"):
            npy_url = fetch_lst(lat, lon)

        with st.spinner("Detecting temperature anomalies…"):
            lst_array, anomaly_indices = analyze_anomalies(npy_url)

        st.success("Analysis complete!")

        col_map, col_metrics = st.columns([3, 1], gap="large")

        with col_map:
            m = create_map(lat, lon, lst_array, anomaly_indices)
            st_folium(m, width=800, height=600)

        with col_metrics:
            st.metric("Anomaly pixels", len(anomaly_indices))
            st.metric("Average Max LST (°C)", f"{np.nanmax(lst_array):.2f}")
            st.metric("Average Min LST (°C)", f"{np.nanmin(lst_array):.2f}")
            st.metric("Mean LST (°C)", f"{np.nanmean(lst_array):.2f}")
            st.metric("Average Emission Score",f"{calculate_emission_score(lst_array, anomaly_indices):.2f}")

    except Exception as e:
        st.error(f"**Error:** {e}")
#


import time
time.sleep(100)
