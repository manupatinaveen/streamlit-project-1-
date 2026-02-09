import streamlit as st
import pandas as pd
import json
import os
import folium
from streamlit_folium import st_folium
from config import SchApp,logger
from flask import Response
from folium.features import DivIcon
import pickle
from branca.element import Template, MacroElement

st.set_page_config(page_title="Follow-up Recommendations", page_icon="📋", layout="wide")
import plotly.express as px

st.markdown("<h2 style='text-align:center; color:black;'>📋 Follow-up Recommendations</h2>", unsafe_allow_html=True)
req_headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwic2NoZWR1bGVyIiwiY3J0Il0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiI0Mjc4MDciLCJwaWQiOiI2OTAiLCJpY29kZSI6IlN0YWdpbmciLCJ1dHlwZSI6ImFnZW5jeV9zdXBwb3J0X3VzZXIiLCJuYmYiOjE3NjU3ODE2MzUsImV4cCI6MTc2NTc4NTIzNSwiaXNzIjoiaHR0cHM6Ly9zdGFnaW5nLmthbnRpbWVoZWFsdGgubmV0L2lkZW50aXR5L3YyIn0.ccHy5ToY60UePm09iGwDpJeU3HhFwozVfgnDEtTCyiufmbwNY_MgOQxg5EpDYzeC1dBV2cvNnzgL65lWXCRlhyT3wAUDtrDp2EuEfEvOpSgePfrVzZA0Vz-t3WYbasMsUlnNDIandXPwDSRnaQchD8NDIWLH6b3PmAYIlieySmJ8B7kzsIUU8aGo0WbUWrI4RfMHgEeh4u9So5ti4hwewMBY6OVa-r9cDHizhHDjkFxPprv2Fj1GSjAHgPs-S4yYi-tY3ZpSt9_IXfC2IV3OPCTF067ihFI28pHr5hNR6vdAPqa4FuBxPWbGN28bwsG5VoEhqBIA3rU0BZOgi9pabJf0pt_M7QhxwldSDP6NmXCK9FNoAjhUTkMFaSQT-WEomqCiTT3rkUipv_zkN3eHv-CoEyh1kqYKfL2mnRWoGURsZAfcF3UeaXJTccFr4Ks4GtCEuDJWZBPJkkanQmcTffCStGdgOU3lMI_ZJD3gw9yvLqIEmzFeBKaPicGd6ruuI_oaRqo1qO0StQqCTDOPAIcAjOEo7EddG6Q9tzjNS6MLXEqkWuaFqKfZqr3TWFYrzSWPipoLVtlt0F3g6WzVq6BFVLSLmrcOKMBYO4IN5dOlAqnB1YzubcY_YoLw2SpALTbdk0ltRJQem5bBmQZNAqqbUa1RncOsCOOJPkansAQ",
    "Cookie": "kt_session_id=70234585aa6d4302b212227a2f774f80"
}
# --- JSON file path ---
file_path = "followup_data/recommendations.json"

# --- Helper function to add markers ---
def json_response(data, status=200):
    return Response(response=json.dumps(data, default=str), status=status, mimetype="application/json")


def get_intensity_color(dis_color, avl_hours, max_avl=55):
    """Darkens DIS color based on availability (darker = more available)"""
    if avl_hours <= 0:
        return "#808080"  # Gray for no availability

    # Convert hex to RGB
    hex_color = dis_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    # Intensity: higher availability = darker (0.4 light to 1.0 dark)
    ratio = min(avl_hours / max_avl, 1.0)
    intensity = 0.4 + (0.6 * ratio)  # 40% to 100% darkness

    # Darken each RGB channel
    darkened_rgb = tuple(int(c * intensity) for c in rgb)
    return f"#{darkened_rgb[0]:02x}{darkened_rgb[1]:02x}{darkened_rgb[2]:02x}"


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




if os.path.exists(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    org_id = 690
    location_id = "664c6198b24e9f8127b38fbe"
    cg_file_path = "synth_testdata/690/664c6198b24e9f8127b38fbe_cg_data.bin"
    with open(cg_file_path, 'rb') as f:
        cg_data = pickle.load(f)
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
    st.session_state.cg_map = cg_map

    rows = []
    for client_entry in data:
        client_info = {
            "Client ID": client_entry.get("client"),
            "Client Name": client_entry.get("clientname"),
            "External Client ID": client_entry.get("external_client_id"),
            "Requested Date": client_entry.get("req_date"),
            "Service": client_entry.get("service"),
            "Service ID": client_entry.get("service_id"),
            "Client Location": client_entry.get("geo_location"),
        }

        for rec in client_entry.get("recommendations", []):
            row = client_info.copy()

            # Extract caregiver ID
            cg_id = rec.get("caregiver")
            availability_list = rec.get("availability", [])

            # Example: get total availability or average availability
            if availability_list:
                # Sum all availabilities
                total_availability = sum(item.get("availabilty", 0) for item in availability_list)
                # Average availability across weeks
                avg_availability = total_availability / len(availability_list)
            else:
                avg_availability = 0
            # Get location from cg_map if it exists
            cg_location = cg_map.get(cg_id, {}).get("location")

            row.update({
                "Caregiver ID": cg_id,
                "Caregiver Name": rec.get("cg_name"),
                "Discipline": rec.get("discipline"),
                "Distance (miles)": rec.get("distance"),
                "Weekly Availability":avg_availability,
                "Employment Type": rec.get("emp_type"),
                "Rank": rec.get("rank"),
                "Team": rec.get("team_name"),
                "CG Location": cg_location,  # <-- updated from cg_map
                "External Caregiver ID": rec.get("external_caregiver_id"),
                "CG Mandatory Score": rec["cg_preference_scores"]["mandatory_preference_score"],
                "CG Nice-to-Have Score": rec["cg_preference_scores"]["nice_to_have_preference_score"],
                "CG Total Pref Score": rec["cg_preference_scores"]["preference_score"],
                "CL Mandatory Score": rec["cl_preference_scores"]["mandatory_preference_score"],
                "CL Nice-to-Have Score": rec["cl_preference_scores"]["nice_to_have_preference_score"],
                "CL Total Pref Score": rec["cl_preference_scores"]["preference_score"],
            })
            rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sort_values(
        by=[
            "Distance (miles)",
            "CG Total Pref Score",
            "Weekly Availability"
        ],
        ascending=[
            True,  # distance → nearest first
            False,  # preference score → higher better
            False  # availability → higher better
        ]
    ).reset_index(drop=True)
    df["cg_lat"] = df["CG Location"].apply(
        lambda x: float(x.get("lat")) if isinstance(x, dict) else None
    )
    df["cg_lng"] = df["CG Location"].apply(
        lambda x: float(x.get("lng")) if isinstance(x, dict) else None
    )

    # Now assign geo_df
    geo_df = df.copy()
    geo_df = geo_df.dropna(subset=["cg_lat", "cg_lng"])
    # df = df.iloc[1:].reset_index(drop=True)
    # --- Prepare Map Center ---
    first_client_loc = df["Client Location"].dropna().iloc[0] if not df["Client Location"].dropna().empty else None
    map_center = [float(first_client_loc["lat"]), float(first_client_loc["lng"])] if first_client_loc else [37.0902, -95.7129]

    # --- Display maps side by side ---
    col1, col2 = st.columns(2)

    # --- Map 1: Client & Caregiver Locations ---
    with col1:
        st.subheader("Followup visit recommendations")
        m1 = folium.Map(location=map_center, zoom_start=10)
        bounds = []
        # Client markers
        for _, row in df.iterrows():
            loc = row["Client Location"]
            if loc and isinstance(loc, dict):
                folium.Marker(
                    location=[float(loc["lat"]), float(loc["lng"])],
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
                ).add_to(m1)

        # Caregiver markers
                lat = float(loc["lat"])
                lng = float(loc["lng"])

                radius_miles = [5, 10, 15]

                for miles in radius_miles:
                    folium.Circle(
                        location=[lat, lng],
                        radius=miles * 1609.34,  # miles to meters
                        fill_opacity=0.15,
                        weight=1,
                        dash_array='5'
                    ).add_to(m1)

                # For map bounds
                bounds.append([lat, lng])

        # Caregiver markers → green circles (filled)
        for idx, row in df.iterrows():
            loc = row["CG Location"]
            if idx < 5:
                color = "green"
            else:
                color = "blue"
            if loc and isinstance(loc, dict):
                folium.Marker(
                    location=[float(loc["lat"]), float(loc["lng"])],
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
                ).add_to(m1)

        st_folium(m1, use_container_width=True, height=500,key="folium_distance_map")

    # --- Map 2: Caregiver Preference Scores ---
    with col2:
        st.subheader("All Clinicians (Preference Score)")
        m2 = folium.Map(location=map_center, zoom_start=10)
        def score_to_green(score, max_score=2):
            try:
                score = float(score)
            except:
                score = 0
            if score <= 0:
                return None  # No color for 0 score
            green_val = int(255 * (score / max_score))  # 0→255
            green_val = min(255, max(0, green_val))
            hex_color = '#016e1e'
            return hex_color
        for _, row in df.iterrows():
            loc = row["Client Location"]
            if loc and isinstance(loc, dict):
                folium.Marker(
                    location=[float(loc["lat"]), float(loc["lng"])],
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
                ).add_to(m2)


        for idx, row in df.iterrows():
            loc = row["CG Location"]
            score = row["CG Total Pref Score"]
            if loc and isinstance(loc, dict):
                lat = float(loc["lat"])
                lng = float(loc["lng"])

                # CircleMarker with score color
                color = score_to_green(score)
                folium.CircleMarker(
                    location=[lat, lng],
                    radius=11,
                    color=color if color else "#09b030",  # fully transparent border for 0 score
                    fill=True,
                    fill_color=color if color else "#09b030",  # fully transparent fill
                    fill_opacity=0.8 if color else '#09b030',  # invisible for 0 score
                    popup=f"Caregiver: {row['Caregiver Name']}, Score: {score}",
                ).add_to(m2)
                # Add index number on marker
                folium.map.Marker(
                    [lat, lng],
                    icon=folium.DivIcon(
                        icon_size=(20, 20),
                        icon_anchor=(10, 10),
                        html=f"""<div style="
                                text-align:center;
                                font-size:12px;
                                color:white;
                                font-weight:bold;
                                line-height:20px;
                                ">{idx+1}</div>"""
                    )
                ).add_to(m2)

        st_folium(m2, use_container_width=True, height=500,key="folium_distanc")
        cols_to_drop = [
            'Client ID', 'External Client ID', 'Service ID', 'Client Location', 'Caregiver ID',
            'Employment Type', 'Rank', 'Team', 'CG Location', 'External Caregiver ID',
            'CG Mandatory Score', 'CG Nice-to-Have Score', 'CL Total Pref Score',
            'CL Mandatory Score', 'CL Nice-to-Have Score'
        ]
        def highlight_top5(row):
            return ['background-color: #d1e7dd; font-weight: bold;' if row.name < 3 else '' for _ in row]
        # Drop the columns
        df_cleaned = df.drop(columns=cols_to_drop)
        df_cleaned = df_cleaned.head(10)
        def mask_name(name):
            """Mask clinician name: keep first 3 + last 3 chars visible"""
            if not name or len(name) <= 6:
                return name
            return name[:3] + "*" * (len(name) - 6) + name[-3:]
        df_cleaned['Caregiver Name'] = df_cleaned['Caregiver Name'].apply(mask_name)
        df_cleaned['Client Name'] = df_cleaned['Client Name'].apply(mask_name)
        styled_df = df_cleaned.style.apply(highlight_top5, axis=1)
        with open("followup_data/availability.json", "r") as f:
            availability_data = json.load(f)
        rows = []
        for cg in availability_data:
            cg_uid = cg.get("caregiver_uid")
            dis = cg.get("caregiver_discipline")# 👈 IMPORTANT
            for day in cg["availability_info"]:
                rows.append({
                    "caregiver_uid": cg_uid,
                    "dis":dis,
                    "Date": pd.to_datetime(day["date"]),
                    "Weekday": pd.to_datetime(day["date"]).strftime("%a"),
                    "Available Hours": day["available_hours"],
                })

        avldf = pd.DataFrame(rows)
        cg_availability = (
            avldf.groupby(["caregiver_uid", "dis"], as_index=False)["Available Hours"].sum()
        )
        heatmap_df = geo_df.merge(
            cg_availability,
            left_on="Caregiver ID",  # from geo_df
            right_on="caregiver_uid",  # from availability
            how="inner"
        )
        heatmap_df = heatmap_df.dropna(subset=["cg_lat", "cg_lng"])
        heatmap_df["Available Hours"] = heatmap_df["Available Hours"].astype(float)
        weekdays = avldf.groupby("caregiver_uid")["Weekday"].first().reset_index()
        heatmap_df = heatmap_df.merge(
            weekdays,
            left_on="caregiver_uid",
            right_on="caregiver_uid",
            how="left"
        )


        def get_intensity_color(dis_color, avl_hours, max_avl=55):
            """Darkens base DIS color based on availability (darker = more available)"""
            if avl_hours <= 0:
                return "#808080"  # Gray for no availability

            # Convert hex to RGB
            hex_color = dis_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

            # Higher availability = darker color (0.4 light → 1.0 dark)
            ratio = min(avl_hours / max_avl, 1.0)
            intensity = 0.4 + (0.6 * ratio)  # 40% to 100% intensity

            # Apply darkening
            darkened_rgb = tuple(int(c * intensity) for c in rgb)
            return f"#{darkened_rgb[0]:02x}{darkened_rgb[1]:02x}{darkened_rgb[2]:02x}"


        dis_colors = {
            "RCG-Hybrid": "#FF6B6B",
            "RCG-PRSNL": "#4ECDC4",
            "RCG": "#CC6CE7",
            "AIDE": "#96CEB4",
            "PPS": "#FFEAA7",
            "default": "#95A5A6",
        }

        heatmap_df["dis_color"] = heatmap_df["dis"].map(lambda x: dis_colors.get(x, "#95A5A6"))

        m3 = folium.Map(location=map_center, zoom_start=10)

        # ✅ DYNAMIC MARKERS with intensity
        for idx, row in heatmap_df.iterrows():
            loc = row["CG Location"]
            avl = row["Weekly Availability"]
            dis = row["dis"]
            base_color = row["dis_color"]

            # ✅ GET INTENSITY COLOR
            marker_color = get_intensity_color(base_color, avl)

            if loc and isinstance(loc, dict):
                try:
                    lat = float(loc.get("lat"))
                    lng = float(loc.get("lng"))
                except:
                    continue

                folium.Marker(
                    [lat, lng],
                    popup=f"DIS: {dis}<br>Hours: {avl}",
                    icon=folium.DivIcon(
                        html=f'<div style="background:{marker_color};width:21px;height:22px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:1px solid white;box-shadow:0 0 4px rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;"><i class="fa fa-user" style="color:white;font-size:7px;transform:rotate(45deg);"></i></div>'
                    )
                ).add_to(m3)

        # Legend shows BASE colors (intensity varies per marker)
        legend_html = '''
        <div style="position: absolute; z-index: 1000; top: 10px; right: 10px;
                    background: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    font-family: Arial; font-size: 12px; min-width: 140px;">
            <b>📍 Discipline Legend</b><br>
            <small>(darker = more available)</small><br><br>
            <span style="display:inline-block;width:12px;height:12px;background:#FF6B6B;border-radius:50%;border:1px solid white;margin-right:5px;"></span>RCG-Hybrid<br>
            <span style="display:inline-block;width:12px;height:12px;background:#4ECDC4;border-radius:50%;border:1px solid white;margin-right:5px;"></span>RCG-PRSNL<br>
            <span style="display:inline-block;width:12px;height:12px;background:#CC6CE7;border-radius:50%;border:1px solid white;margin-right:5px;"></span>RCG<br>
            <span style="display:inline-block;width:12px;height:12px;background:#96CEB4;border-radius:50%;border:1px solid white;margin-right:5px;"></span>AIDE<br>
            <span style="display:inline-block;width:12px;height:12px;background:#FFEAA7;border-radius:50%;border:1px solid white;margin-right:5px;"></span>PPS
        </div>
        '''

        m3.get_root().html.add_child(folium.Element(legend_html))

with st.container():
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
col1, col2, col3 = st.columns([1, 2, 1])  # Left empty | Map | Right empty

with col2:  # Center column only
    st.markdown("### 📅 Caregiver weekly Availability")
    st_folium(m3, use_container_width=True, height=700, key="folium_avl")








