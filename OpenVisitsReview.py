import streamlit as st
import os
import json
import pandas as pd
import re
import pickle
from folium.features import DivIcon

import folium
from streamlit_folium import st_folium
st.set_page_config(page_title="Open Visit Schedules", page_icon="💁🔍", layout="wide")
st.markdown(
    "<h1 style='font-size:30px;'>📖 Review Open Visit Schedules</h1>",
    unsafe_allow_html=True
)
from flask import Response
from config import SchApp,logger
req_headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwic2NoZWR1bGVyIiwiY3J0Il0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiI0Mjc4MDciLCJwaWQiOiI2OTAiLCJpY29kZSI6IlN0YWdpbmciLCJ1dHlwZSI6ImFnZW5jeV9zdXBwb3J0X3VzZXIiLCJuYmYiOjE3NjU1MjkwMDQsImV4cCI6MTc2NTUzMjYwNCwiaXNzIjoiaHR0cHM6Ly9zdGFnaW5nLmthbnRpbWVoZWFsdGgubmV0L2lkZW50aXR5L3YyIn0.sh0bUjK3GGySVnGwsXK9EglfXhG7wvwHuOMgo8QDZcfeZj9tBrM-RTVZL4iV9wBMLkuEF9s5-MJO3-P_LaaTzw3-t-uHTKjjx8LCVLnjtCgSTYQAkAf3BKmsiWZRWiiVDDd_yJoZcssPY7sjMxwzfxwBG04wQ4joU7nnRDdOnlIvUT04EIqdsspLXJqCDyRX5RRBvVxxKn2KGzIwT8LvecnRHnZ4dxR5lWaG12zTyJS2c_SwAnzupOO-5exmazeD1i6XAq7_h-M80vRF2dgHojy33cWLeMzT76pevEivl7zzyGoJcBDABpSRWcdaWzHZzF24pqPAh6_GanOSs9bLgR8Ao6WFrpsLQSv-lfmE7aJ-I1GqeTgTXhe3mx0JLvL52ldMZxDAWGJ8-LH-oswP2JZeyjR1MhOYe9BUspy_OjyOTCd8jda4JFuHXgi_4z_SB8ifYn5NlPM7YGo-gyvReGidP5-1_8ysTlSDJuI_sbZl_ukhOZL465NrMgd7GRaMKTdw7OdArlY7xxk7rUphFvVjuy41BUoILK8EJRFEPM4T9ax_oySVSbd55Ab-zTOXS32yfWXvMGZ45zg2xaYiHvta7bDN7Q4ty_LokUTNUlkjcdaVplQASTq3UbTho7sPhv-poayiTp6DZUhw1q_CXyXtMtN-bM0oMLLucWusXLA",
    "Cookie": "kt_session_id=354aade0a4c84b88a7dc97d921b383cd"
}

def json_response(data, status=200):
    return Response(response=json.dumps(data, default=str), status=status, mimetype="application/json")

def load_client_details(org_id, location_id, req_headers):
    from common.service_functions import make_service_request
    try:
        payload = {
            'page_no': 1, 'page_size': 40000,
            'org_id': org_id,
            'client_locations': [location_id],
            'client_status': ['active', 'end_of_episode', 'on_hold', 'pending_soc', 'transferred', 'discharge_pending']
        }
        response_json = make_service_request("total_cl_lst", req_headers, payload, "json")
        if not response_json or 'items_list' not in response_json or not response_json['items_list']:
            return json_response({"error_code": "DATA_NOT_AVAILABLE", "error_message": "Data is not available"}, status=400)
        return response_json['items_list']
    except Exception as e:
        logger.exception("Error fetching client data")
        return json_response({"error_code": "INTERNAL_ERROR", "error_message": str(e)}, status=500)

def load_cg_details(org_id, req_headers):
    from common.service_functions import make_service_request
    try:
        payload = {'page_no': 1, 'page_size': 40000, 'org_id': org_id, "staff_types": ["both", "clinician"]}
        response_json = make_service_request("total_cg_lst", req_headers, payload, "json")
        if not response_json or 'items_list' not in response_json or not response_json['items_list']:
            return json_response({"error_code": "DATA_NOT_AVAILABLE", "error_message": "Data is not available"}, status=400)
        return response_json['items_list']
    except Exception as e:
        logger.exception("Error fetching cg data")
        return json_response({"error_code": "INTERNAL_ERROR", "error_message": str(e)}, status=500)

def get_alloc_capacity(clinician):
    if "avail_prod_points" in clinician and "capacity_prod_points" in clinician:
        return f"{int(clinician.get('avail_prod_points',0))}/{int(clinician.get('capacity_prod_points',0))}"
    elif "avail_hours" in clinician and "capacity_hours" in clinician:
        return f"{float(clinician.get('avail_hours',0))}/{float(clinician.get('capacity_hours',0))} hrs"
    else:
        return ""


import streamlit as st
import folium
from streamlit_folium import st_folium
import streamlit as st
import folium
from streamlit_folium import st_folium


def display_clinicians_intensity_map(df):
    """Map of all clinicians with green circles, intensity based on Match Score."""

    import folium
    from folium.features import DivIcon
    import streamlit as st
    import pandas as pd

    # Ensure lat/lng numeric
    df["Clinician Latitude"] = pd.to_numeric(df["Clinician Latitude"], errors="coerce")
    df["Clinician Longitude"] = pd.to_numeric(df["Clinician Longitude"], errors="coerce")

    clinician_df = df.dropna(subset=["Clinician Latitude", "Clinician Longitude"])
    if clinician_df.empty:
        st.warning("No valid clinician locations available.")
        return

    avg_lat = clinician_df["Clinician Latitude"].mean()
    avg_lng = clinician_df["Clinician Longitude"].mean()

    m = folium.Map(location=[avg_lat, avg_lng], zoom_start=12)

    total_rows = len(clinician_df)
    fade_values = [1.0 if i < 5 else max(0.9 - 0.05 * (i - 5), 0.3) for i in range(total_rows)]

    for (idx, row), opacity in zip(clinician_df.iterrows(), fade_values):
        lat = row["Clinician Latitude"]
        lng = row["Clinician Longitude"]
        cg_name = row["Clinician"]

        match_score = f"{int(opacity * 100)}%"

        # Add CircleMarker
        folium.CircleMarker(
            location=[lat, lng],
            radius=10,
            color="green",
            fill=True,
            fill_color="green",
            fill_opacity=opacity,
            popup=f"{cg_name} - Match Score: {match_score}"
        ).add_to(m)

        # Label with dataframe index
        folium.map.Marker(
            [lat, lng],
            icon=DivIcon(
                icon_size=(20, 20),
                icon_anchor=(10, 10),
                html=f"""<div style="
                        text-align:center;
                        font-size:12px;
                        color:white;
                        font-weight:bold;
                        line-height:20px;
                        "><b>{idx+1}</b></div>"""
            )
        ).add_to(m)

    return m

def build_map(df):
    import folium
    from folium.features import DivIcon
    from folium.plugins import Fullscreen
    import pandas as pd

    # Ensure numeric lat/lng
    df["Client Latitude"] = pd.to_numeric(df["Client Latitude"], errors="coerce")
    df["Client Longitude"] = pd.to_numeric(df["Client Longitude"], errors="coerce")
    client_point = [df.loc[0, "Client Latitude"], df.loc[0, "Client Longitude"]]

    # Reset index just in case
    df1 = df.reset_index(drop=True)

    # Base map
    m = folium.Map(zoom_start=15)
    bounds = []

    # --- Client Marker ---
    folium.Marker(
        client_point,
        popup="<b>Client</b>",
        icon=DivIcon(
            icon_size=(24, 24),
            icon_anchor=(12, 12),
            html=(
                '<div style="width:26px;height:26px;line-height:26px;'
                'background:brown;color:white;border-radius:50%;'
                'border:1px solid white;text-align:center;font-size:14px;'
                'box-shadow:0 0 2px rgba(0,0,0,0.4);">'
                '<i class="fa fa-user"></i></div>'
            )
        )
    ).add_to(m)
    folium.Circle(
        location=client_point,
        radius=5 * 1609.34,
        color='green',
        fill=True,
        fill_color='green',
        fill_opacity=0.2,
        weight=1,
        dash_array='5'
    ).add_to(m)
    bounds.append(client_point)

    # --- Clinician Markers ---
    def mask_name(name):
        """Mask clinician name: keep first 3 + last 3 chars visible"""
        if not name or len(name) <= 6:
            return name
        return name[:3] + "*" * (len(name) - 6) + name[-3:]

    for idx, row in df1.iterrows():
        if pd.isna(row["Clinician Latitude"]) or pd.isna(row["Clinician Longitude"]):
            continue
        point = (row["Clinician Latitude"], row["Clinician Longitude"])
        bounds.append(point)
        if idx < 5:
            color = "green"
        else:
            color = "blue"

        popup_name = mask_name(row.get("Clinician Name", "Clinician"))

        folium.Marker(
            point,
            icon=DivIcon(
                icon_size=(24, 24),
                icon_anchor=(12, 12),
                html=f"""
                <div style="
                    width:26px;height:26px;line-height:24px;
                    background:{color};color:white;
                    border-radius:50%;border:1px solid white;
                    text-align:center;font-size:13px;
                    box-shadow:0 0 2px rgba(0,0,0,0.4);
                ">
                    {idx + 1}
                </div>
                """
            ),
        ).add_to(m)


    # Fit map bounds and add fullscreen
    Fullscreen().add_to(m)
    if bounds:
        m.fit_bounds(bounds)

    return m
# def display_client_map(filtered_df, client_name):
#     client_location = filtered_df[["Client Latitude", "Client Longitude"]].dropna().drop_duplicates()
#     if client_location.empty:
#         st.warning("No valid client location available for this selection.")
#         return
#     client_lat = client_location.iloc[0]["Client Latitude"]
#     client_lng = client_location.iloc[0]["Client Longitude"]
#     client_point = (client_lat, client_lng)
#     m = folium.Map(location=[client_lat, client_lng], zoom_start=12)
#     folium.Marker(
#         client_point,
#         popup="<b>Client</b>",
#         icon=DivIcon(
#             icon_size=(24, 24),
#             icon_anchor=(12, 12),
#             html=(
#                 '<div style="width:26px;height:26px;line-height:26px;'
#                 'background:brown;color:white;border-radius:50%;'
#                 'border:1px solid white;text-align:center;font-size:14px;'
#                 'box-shadow:0 0 2px rgba(0,0,0,0.4);">'
#                 '<i class="fa fa-user"></i></div>'
#             )
#         )
#     ).add_to(m)
#     folium.Circle(
#         location=client_point,
#         radius=5 * 1609.34,
#         color='green',
#         fill=True,
#         fill_color='green',
#         fill_opacity=0.2,
#         weight=1,
#         dash_array='5'
#     ).add_to(m)
#
#     # Add a label "CL" for client
#     if client_lat is not None and client_lng is not None:
#         folium.Marker(
#             location=(client_lat, client_lng),
#             icon=DivIcon(
#                 icon_size=(24, 24),
#                 icon_anchor=(12, 12),
#                 html="""
#                     <div style="
#                         width:24px;height:24px;line-height:24px;
#                         background:blue;color:white;
#                         border-radius:50%;border:1px solid white;
#                         text-align:center;font-size:14px;
#                         box-shadow:0 0 2px rgba(0,0,0,0.4);
#                     ">
#                         cl
#                     </div>
#                 """
#             )
#         ).add_to(m)
#
#     # Add all clinician markers as circles
#     for _, row in filtered_df.iterrows():
#         cg_lat, cg_lng = row.get("Clinician Latitude"), row.get("Clinician Longitude")
#         cg_name = row.get("Clinician")
#         if cg_lat and cg_lng:
#             folium.Marker(
#                 location=(cg_lat, cg_lng),
#                 icon=DivIcon(
#                     icon_size=(20, 20),
#                     icon_anchor=(10, 10),
#                     html="""
#                             <div style="
#                                 width:20px;height:20px;line-height:20px;
#                                 background:green;color:white;
#                                 border-radius:50%;border:1px solid white;
#                                 text-align:center;font-size:10px;font-weight:bold;
#                             ">
#                                 cg
#                             </div>
#                         """
#                 )
#             ).add_to(m)
#
#     # Display the map in Streamlit
#     st_folium(m, use_container_width=True, height=350)


# --- Load saved schedule files ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
save_folder = os.path.join(ROOT_DIR, "open_visit_data")
os.makedirs(save_folder, exist_ok=True)

files = [f for f in os.listdir(save_folder) if f.endswith(".json")]
if not files:
    st.warning("⚠️ No saved schedules found.")
else:
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = files[0]

    selected_file = st.selectbox("Select a saved schedule file:", files, index=files.index(st.session_state.selected_file))
    st.session_state.selected_file = selected_file

    # Load JSON once
    if "loaded_data" not in st.session_state or st.session_state.selected_file != selected_file:
        file_path = os.path.join(save_folder, selected_file)
        with open(file_path, "r", encoding="utf-8") as f:
            st.session_state.loaded_data = json.load(f)

    data = st.session_state.loaded_data

    # Load clients and caregivers once
    if "client_map" not in st.session_state or "cg_map" not in st.session_state:
        match = re.search(r'org(\d+)_loc([a-f0-9]+)', selected_file)
        if not match:
            st.error("No org/location match found in filename")
            st.stop()
        org_id, location_id = match.group(1), match.group(2)

        cl_file_path = "synth_testdata/690/664c6198b24e9f8127b38fbe_cl_data.bin"
        with open(cl_file_path, 'rb') as f:
            clients_data = pickle.load(f)
        branch_data = clients_data.get(str(location_id), {})
        if 'no_cl' in branch_data.keys():
            branch_data = {}
        clients_list = list(branch_data.values())
        client_map = {
            client["client_uid"]: {
                "name": f"{client.get('first_name', '')} {client.get('last_name', '')}".strip(),
                "location": client["client_address"][0]["geo_location"]
            }
            for client in clients_list
            if client.get("client_address") and client["client_address"][0].get("geo_location")
        }
        cg_file_path = "synth_testdata/690/664c6198b24e9f8127b38fbe_cg_data.bin"
        with open(cg_file_path, 'rb') as f:
            cg_data = pickle.load(f)
        print("cg_data",cg_data)
        branchs_data = cg_data.get(str(location_id), {})
        if 'no_cg' in branchs_data.keys():
            branch_data = {}
        cg_list = list(branchs_data.values())
        cg_map = {
            cg["caregiver_uid"]: {
                "name": f"{cg['first_name']} {cg['last_name']}",
                "location": cg.get("caregiver_address", {}).get("geo_location")
            }
            for cg in cg_list
        }

        st.session_state.client_map = client_map
        st.session_state.cg_map = cg_map

    # Build DataFrame
    def highlight_top5(row):
        return ['background-color: #d1e7dd; font-weight: bold;' if row.name < 3 else '' for _ in row]
    def build_df():
        rows = []
        client_map = st.session_state.client_map
        cg_map = st.session_state.cg_map

        for visit in data["open_visit_schedules"]:
            client_uid = visit.get("clientid")
            client_info = client_map.get(client_uid, {})
            visit["client_name"] = client_info.get("name")
            visit["client_location"] = client_info.get("location")
            lat = visit["client_location"]["lat"] if visit["client_location"] else None
            lng = visit["client_location"]["lng"] if visit["client_location"] else None

            if visit.get("clinicians"):
                for clinician in visit["clinicians"]:
                    cg_uid = clinician.get("clinicianid")
                    cg_lat, cg_lng = None, None
                    if cg_uid in cg_map and cg_map[cg_uid].get("location"):
                        cg_lat = cg_map[cg_uid]["location"].get("lat")
                        cg_lng = cg_map[cg_uid]["location"].get("lng")

                    rows.append({
                        "Client": visit["client_name"] ,
                        "Client Latitude": lat,
                        "Client Longitude": lng,
                        "Visit Date": visit["planned_date"] ,
                        "Service": visit["service"] ,
                        "Discipline": visit["dis"] ,
                        "Clinician": cg_map[cg_uid]["name"] if cg_uid in cg_map else clinician.get("caregiver_name"),
                        "Clinician Latitude": cg_lat,
                        "Clinician Longitude": cg_lng,
                        "Proposed Start": clinician["starttime"],
                        "Proposed End": clinician["endtime"],
                        "Distance (mi)": clinician.get("distance_from_home") if clinician.get("distance_from_home") not in ("", None) else None,
                        "Allocated / Capacity": get_alloc_capacity(clinician),
                        "Match Score": clinician.get("Reason", {}).get("Match_score")
                    })
                    first = False
            else:
                rows.append({
                    "Client": visit["client_name"],
                    "Client Latitude": lat,
                    "Client Longitude": lng,
                    "Visit Date": visit["planned_date"],
                    "Service": visit["service"],
                    "Discipline": visit["dis"],
                    "Clinician": "No clinicians proposed ❌",
                    "Clinician Latitude": None,
                    "Clinician Longitude": None,
                    "Proposed Start": "",
                    "Proposed End": "",
                    "Distance (mi)": "",
                    "Allocated / Capacity": "",
                     "Match Score": ""
                })
        return pd.DataFrame(rows)

    if "df" not in st.session_state:
        st.session_state.df = build_df()

    df = st.session_state.df

    if "selected_client" not in st.session_state:
        st.session_state.selected_client = df["Client"].iloc[0]

    selected_client = st.selectbox(
        "Select Client to view on map",
        df["Client"].unique(),
        index=list(df["Client"].unique()).index(st.session_state.selected_client),
        key="selected_client"
    )
    def mask_name(name):
        """Mask clinician name: keep first 3 + last 3 chars visible"""
        if not name or len(name) <= 6:
            return name
        return name[:3] + "*" * (len(name) - 6) + name[-3:]
    filtered_df = df[df["Client"] == selected_client]
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df['Clinician'] = filtered_df['Clinician'].apply(mask_name)
    filtered_df['Client'] = filtered_df['Client'].apply(mask_name)
    df_cleaned = filtered_df.drop(columns=[
        'Client Latitude',
        'Client Longitude',
        'Clinician Latitude',
        'Clinician Longitude',
        'Proposed Start',
        'Proposed End',
    ])
    df_cleaned = df_cleaned.reset_index(drop=True)
    df_cleaned = df_cleaned.head(5)
    styled_df = df_cleaned.style.apply(highlight_top5, axis=1)


    # Side-by-side columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Open visit recommendations")
        st_folium(
            build_map(filtered_df),
            use_container_width=True, height=500, key="open_visit"
        )

    with col2:
        st.subheader("All Clinicians (Preference Score)")
        m2 = display_clinicians_intensity_map(filtered_df)
        st_folium(m2, use_container_width=True, height=500)
    st.dataframe(styled_df, use_container_width=True)




