import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="IoT Dashboard", layout="wide")

# 1. Authentication & Connection
try:
    creds = service_account.Credentials.from_service_account_file("fair-veld-481702-a1-d0ee1466211f.json")
    db = firestore.Client(credentials=creds, project="fair-veld-481702-a1", database="cpc357-assignment2")
    st.success("Connected to Firestore Successfully!")
except Exception as e:
    st.error(f"Failed to connect: {e}")

# 2. Fetching Data
st.header("📊 IoT Sensor Analysis Dashboard")

# Top controls: Status info and Manual Refresh
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.caption("🔍 Analyzing full historical data from Project: fair-veld-481702-a1")
with header_col2:
    if st.button("🔄 Sync Database", use_container_width=True):
        st.rerun()

st.divider()

docs = db.collection("sensor_readings").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()

data_list = []
for doc in docs:
    data_list.append(doc.to_dict())

if data_list:
    # Process Data
    df = pd.DataFrame(data_list)
    # Ensure timestamp is datetime objects for better plotting
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp') 
    # Get the most recent date available in your data
    latest_date = df['timestamp'].dt.date.max() 
    df_today = df[df['timestamp'].dt.date == latest_date].copy()
    
    latest = df.iloc[-1]

    # --- 3. DYNAMIC STATUS ---
    # Manual refresh data
    if not df.empty:
        last_sync = df['timestamp'].iloc[-1]
        
        # Use the same timezone as the data for the current time
        now = datetime.now(tz=last_sync.tzinfo)
        
        # Calculate time difference in minutes
        time_diff = (now - last_sync).total_seconds() / 60
        
        if time_diff < 60:
            st.success(f"✅ System Active: Last reading received {int(time_diff)} minutes ago.")
        else:
            # Use strftime to show the date/time clearly in the warning
            formatted_time = last_sync.strftime('%Y-%m-%d %H:%M')
            st.warning(f"🕒 Standby Mode: Last reading was {int(time_diff/60)} hours ago ({formatted_time}).")

    # --- 4. DATA VISUALIZATION ---
    col1, col2, col3, col4 = st.columns(4)
    
    # Air Quality Classification based on CO Level
    def get_air_quality(ppm):
        if ppm < 350: return "🍃 Fresh", "Normal outdoor level"
        elif ppm < 600: return "🏠 Good", "Normal indoor level"
        elif ppm < 1000: return "⚠️ Poor", "Poor ventilation"
        else: return "🚨 Danger", "Health Risk: Evacuate"
    aqi_status, aqi_desc = get_air_quality(latest['co_ppm'])

    aqi_status, aqi_desc = get_air_quality(latest['co_ppm'])
    with col1:
        st.metric("Latest CO Level", f"{latest['co_ppm']} PPM")
    with col2:
        st.metric("Latest Moisture", f"{latest['moisture']}%")
    with col3:
        st.metric("Air Quality", aqi_status, help=aqi_desc)
    with col4:
        # Show specific collection time
        reading_display = latest['timestamp'].strftime('%b %d, %H:%M')
        st.metric("Reading Recorded", reading_display)

    tab1, tab2 = st.tabs(["📈 Trend Analysis", "📋 History Log"])
    
    # Charts
    with tab1:
        st.subheader("📈 Integrated Trend Analysis")

        # Focus on recent data burst
        df_recent = df_today.tail(50).copy()
        df_recent['DisplayTime'] = df_recent['timestamp'].dt.strftime('%H:%M:%S')

        # DATA PROCESSING: Normalization (Feature Scaling)
        # We scale both co_ppm and moisture to a 0-1 range so they can be compared in one chart
        df_recent['CO_Scaled'] = df_recent['co_ppm'] / 1000.0
        df_recent['Moisture_Scaled'] = df_recent['moisture'] / 100.0

        st.write("#### Environmental Correlation: Gas vs. Humidity")
        st.line_chart(df_recent.set_index('DisplayTime')[['CO_Scaled', 'Moisture_Scaled']])
        st.caption("Values are normalized (0 to 1) to compare trends between different units (PPM vs %).")
        
        st.divider()
        
        # Individual charts below for absolute values
        col_left, col_right = st.columns(2)
        with col_left:
            st.write("##### Carbon Monoxide Levels (PPM)")
            st.line_chart(df_recent.set_index('DisplayTime')['co_ppm'], color="#ff4b4b")
        with col_right:
            st.write("##### Moisture (%)")
            st.line_chart(df_recent.set_index('DisplayTime')['moisture'], color="#0077b6")

    # Data log
    with tab2:

        df_display = df.copy()
        # Sorting newest at the top
        df_display['timestamp'] = pd.to_datetime(df_display['timestamp'])
        df_display = df_display.sort_values(by='timestamp', ascending=False)

        # Reorder the column
        cols = ['timestamp'] + [c for c in df_display.columns if c != 'timestamp']
        df_display = df_display[cols]

        # Index start from 1
        df_display = df_display.reset_index(drop=True)
        df_display.index = df_display.index + 1

        # Export Button
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Log (CSV)", data=csv, file_name="iot_log.csv", mime='text/csv')
        st.dataframe(df_display, use_container_width=True)
else:
    st.info("No data currently available in Firestore.")