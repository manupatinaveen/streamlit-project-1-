import streamlit as st
import pandas as pd
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from common.service_functions import make_service_request
from config import SchApp,logger
import requests
import json
from flask import Response
from streamlit_folium import st_folium
import folium
from folium.plugins import Fullscreen
from folium.features import DivIcon

def mask_name(name):
    if not isinstance(name, str):
        return name
    if len(name) <= 6:
        # For very short names, just mask middle character(s)
        mid = len(name) // 2
        return name[:mid] + '*' * (len(name) - mid)
    return name[:3] + '***' + name[-3:]
st.set_page_config(page_title="Soc Search", page_icon="🗺️", layout="wide")
st.markdown(
    "<h1 style='font-size:30px;'>SOC Search 🔍</h1>",
    unsafe_allow_html=True
)
def json_response(data, status=200):
    return Response(
        response=json.dumps(data, default=str),
        status=status,
        mimetype="application/json"
    )


def build_map(df, client_point):
    import folium
    from folium.features import DivIcon
    from folium.plugins import Fullscreen
    import pandas as pd

    # Ensure numeric lat/lng
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")

    # Reset index just in case
    df = df.reset_index(drop=True)

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

    for _, row in df.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lng"]):
            continue
        point = (row["lat"], row["lng"])
        bounds.append(point)

        rank = int(row.get("Rank", 999))
        color = "green" if rank <= 5 else "blue"
        popup_name = mask_name(row.get("Clinician Name", "Clinician"))

        folium.Marker(
            point,
            popup=f"<b>{popup_name}</b>",
            icon=DivIcon(
                icon_size=(24, 24),
                icon_anchor=(12, 12),
                html=(
                    f'<div style="width:26px;height:26px;line-height:24px;'
                    f'background:{color};color:white;border-radius:50%;'
                    f'border:1px solid white;text-align:center;font-size:13px;'
                    f'box-shadow:0 0 2px rgba(0,0,0,0.4);">{rank}</div>'
                )
            )
        ).add_to(m)

    # Fit map bounds and add fullscreen
    Fullscreen().add_to(m)
    if bounds:
        m.fit_bounds(bounds)

    return m


req_headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwiY3J0Iiwic2NoZWR1bGVyIl0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiIzMjg1NTMiLCJwaWQiOiI2OTAiLCJuYmYiOjE3NjU1MjU1MDksImV4cCI6MTc2NTUyOTEwOSwiaXNzIjoiaHR0cHM6Ly9wcm9kcWEua2FudGltZWhlYWx0aC5uZXQvaWRlbnRpdHkvdjIifQ.aHfyp0g1hGZUaTRtTHps8UNdvhetIXdE27XaLfcUKD0AvdEuBmA_Gl_aN7JRThJ6XucBbWDMuAZKo0DT9OULAXOCnDDlJU-dHhYOQ6tIII4Pl6RFTvyzWmLHeMVZeGAe17pfgmYthgMBeP5iA87mpzZbXRbPzo2A9RAHZzWYUD1ST2AqTXRdBUWwiGfuBIqhBTami_Dx7Q9n6X0t9E-bj-8rCsxFuJ2bpnRB4IgCtRr2aV2IjLp4gZHjCPyQvUQZp8JelLdaN_Qrwm_ddBvtGNeMX8baSMkM0KkRY2pCFoWmYZw0vVjjVOMl-ChzN-oSZSmAcKBpakxVKBwzsT1Qszqot_5DfBry8laQD_PnGhn8BFVm4AtkLsMJE6XPOxN03P_YhCN4cTyCCjkkTMWBZSU7-r1aE1h83UDpeOOrbU5G9qbM4YIDt8eVgK8-zM1kvmpDE8Qs7F2tGoqAwyVvAdYjql-kthdV1Pq0ZkIuhSkaAcjh7RuDgXkBOHXCooSytl_qD20BS8Kx0P0thM7LuLKtMmQfM0w9k6Q8nY-C4ZGUbW0_fOXNMlFVIXW2be2WmHfTMw-75x-m0fp-lFxTVHMZRaeEunPyCQFnU49WjC_khOqKP2quG_w4ijKqHMuwvsduIa5ta0k2SWx35RCqo-_5rpQZN-JltoALrBwvMlE",
    "Cookie": "kt_session_id=1e9d921dfcbf4927970a94f56048c4e8"
}
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_clin_dly_avlblty(clinids, start_date, org_id, req_headers):

    result = {}
    try:
        from common.service_functions import make_service_request


        payload = {
            "caregiver_uids": clinids,
            "start_date": datetime.strftime(start_date, "%m/%d/%Y"),
            "number_of_days": 1,
            "org_id": org_id
        }

        response = make_service_request("int_cg_availability_daily", req_headers, payload, "json")
        logger.info("Received response from int_cg_availability_daily API. Total records: %d", len(response))

        avail_key = "max_productivity_points"
        alloc_key = "allocated_productivity_points"

        for res in response:
            try:
                caregiver_uid = res.get("caregiver_uid")
                caregiver_name = res.get("caregiver_name")
                avail_info = res.get("availability_info", [{}])[0]

                max_points = avail_info.get(avail_key, 0)
                alloc_points = avail_info.get(alloc_key, 0)
                caseload = max_points - alloc_points if max_points > 0 else 0

                result[caregiver_uid] = {
                    "caregiver_name": caregiver_name,
                    "caseload": caseload
                }


            except Exception as inner_e:
                logger.warning("Error processing caregiver record: %s | Error: %s", res, inner_e)


    except Exception as e:
        logger.exception("Daily availability API failed: %s", e)
        errmsg = {"error_code": "SERVICE_API_FAIL", "error_message": "Daily availability C# API Fail: " + str(e)}
        return errmsg

    return result

def daily_clin_avail(clin_lst, start_date,org_id,req_headers):
    dly_clin_avlblty_dict = {}
    try:
        dly_clin_avlblty_dict.update(get_clin_dly_avlblty(clin_lst, start_date,org_id,req_headers))
        return dly_clin_avlblty_dict
    except Exception as e:
        logger.info(e)
def load_cg_details(org_id,req_headers):
    from common.service_functions import make_service_request
    try:
        payload = {
            'page_no': 1, 'page_size': 40000, 'org_id': org_id, "staff_types": ["both", "clinician","physician"]
        }
        response_json = make_service_request("total_cg_lst", req_headers, payload, "json")
        if not response_json or 'items_list' not in response_json or not response_json['items_list']:
            errmsg = {
                "error_code": "DATA_NOT_AVAILABLE",
                "error_message": f"Data is not available "
            }
            return json_response(errmsg, status=400)
        response = response_json['items_list']
        return response
    except Exception as e:
        logger.exception("Error occurred while fetching cg data")
        errmsg = {"error_code": "INTERNAL_ERROR", "error_message": str(e)}
        return json_response(errmsg, status=500)

col1, col2,col3= st.columns(3)
with col1:
    org_id = st.text_input("Enter Org ID", key="org_id_input")
    st.session_state["org_id"] = org_id

with col2:
    location_id = st.text_input("Enter Location ID", key="loc_id_input")
    st.session_state["location_id"] = location_id


with col3:
    referral_range = st.date_input(
            "Referral Date Range",
            value=(datetime(2024,1,1), datetime.today())
        )
load_btn = st.button("🔍 Load Client Data")
def get_client_details_from_service_id(org_id, location_id, req_headers):
    payload = {
        "page_no": 1,
        "page_size": 40000,
        "org_id": org_id,
        "client_locations": [location_id],
        "client_status": ["pending_soc"]
    }
    return make_service_request("total_cl_lst", req_headers, payload, "json" )
if load_btn:
    if not org_id or not location_id:
        st.warning("Please enter both Org ID and Location ID.")
    else:
        st.session_state["org_id"] = org_id
        st.session_state["location_id"] = location_id
        with st.spinner("Loading client details…"):
            resp = get_client_details_from_service_id(org_id, location_id, req_headers)
        if resp and "items_list" in resp:
            st.session_state["client_data"] = resp["items_list"]
            st.success(f"Loaded {len(resp['items_list'])} records.")
        else:
            st.info("No client details found.")
            st.session_state.pop("client_data", None)
if "client_data" in st.session_state:
    client_data = st.session_state["client_data"]
    data, payload_list,payload_list1 = [], [], []
    for item in client_data:
        client_name = f"{item.get('first_name','')} {item.get('last_name','')}".strip()
        referral_date = item.get("referral_date", "")
        soc_date_raw = item.get("soc", {}).get("soc_date", "")
        soc_date = ""
        if soc_date_raw:
            try:
                soc_date = datetime.strptime(soc_date_raw, "%m/%d/%Y").strftime("%Y-%m-%d")
            except ValueError:
                pass
        client_uid = item.get("client_uid", "")
        cl_lat = cl_lng = ""
        for addr in item.get("client_address", []):
            if addr.get("is_primary_address", False):
                geo = addr.get("geo_location", {})
                cl_lat, cl_lng = geo.get("lat", ""), geo.get("lng", "")
                break
        data.append({
            "Client Name": client_name,
            "Referral Date": referral_date,
            "SOC Date": soc_date,
            "Search": "🔍",
            "cl_lat": cl_lat,
            "cl_lng": cl_lng,

        })
        payload_list.append({
            "socreq_date": soc_date,
            "clientid": "",
            "visit_duration": 60,
            "preferred_clinician": "",
            "lat": cl_lat,
            "lng": cl_lng,
            "cg_soc_srv_discs": ["RN"],
            "cg_followup_srv_discs": ["LPN"],
            "only_soc_clinician_enabled": False,
            "ignore_followup_capacity": True,
            "is_non_credential_service": None,
            "non_credential_discipline": None
        })
        payload_list1.append({
            "socreq_date": soc_date,
            "clientid": "",
            "visit_duration": 60,
            "preferred_clinician": "",
            "lat": cl_lat,
            "lng": cl_lng,
            "cg_soc_srv_discs": ["RN"],
            "cg_followup_srv_discs": ["LPN"],
            "only_soc_clinician_enabled": False,
            "ignore_followup_capacity": True,
            "is_non_credential_service": None,
            "non_credential_discipline": None
        })
    df = pd.DataFrame(data)
    start, end = referral_range
    df["Referral Date_dt"] = pd.to_datetime(df["Referral Date"], errors="coerce")
    df = df[(df["Referral Date_dt"] >= pd.to_datetime(start))
            & (df["Referral Date_dt"] <= pd.to_datetime(end))]
    df.drop(columns="Referral Date_dt", inplace=True)
    if not df.empty:
        client_names = df["Client Name"].tolist()
        selected_name = st.selectbox("Select a client", client_names)
        if selected_name:
            selected_idx = df.index[df["Client Name"] == selected_name][0]
            selected = df.loc[selected_idx]
            st.session_state["selected_client"] = selected
            st.session_state["selected_payload"] = payload_list[selected_idx]
            st.session_state["selected_payload1"] = payload_list1[selected_idx]
if st.button("Search", type="primary"):
    if "selected_payload" and "selected_payload1" not in st.session_state:
        st.warning("Please select a client first.")
    else:
        base_url = SchApp.config()["server"]["base_url"]
        endpoint_path = SchApp.config()["endpoint context"]["path"]
        selected_payload = st.session_state["selected_payload"]
        selected_payload1 = st.session_state["selected_payload1"]
        api_url_dist = (f"{base_url}{endpoint_path}/soc_recommend?"f"max_clincnt=3"f"&location_id={st.session_state.get('location_id')}"f"&org_id={st.session_state.get('org_id')}"
            f"&priority=distance"
        )
        api_url_avl= (f"{base_url}{endpoint_path}/soc_recommend?"f"max_clincnt=3"f"&location_id={st.session_state.get('location_id')}"f"&org_id={st.session_state.get('org_id')}"
            f"&priority=availability"
        )
        with st.spinner("Fetching SOC Recommendations..."):
            try:
                response_dist = requests.post(api_url_dist, json=selected_payload,headers=req_headers,timeout=(60, 500))
                response_avl = requests.post(api_url_avl, json=selected_payload,headers=req_headers,timeout=(60, 500))

                folloup_response_dist = requests.post(api_url_dist, json=selected_payload1,headers=req_headers,timeout=(60, 500))
                folloup_response_avl = requests.post(api_url_avl, json=selected_payload1,headers=req_headers,timeout=(60, 500))

                logger.info(f"Payload sent: {json.dumps(selected_payload, indent=2)}")
                response_dist.raise_for_status()
                result_dist = response_dist.json()
                result_avl = response_avl.json()
                folloup_response_dist.raise_for_status()
                folloup_response_result_dist = folloup_response_dist.json()
                folloup_response_result_avl = folloup_response_avl.json()
                recommendations_dist = result_dist.get("recommendations", [])
                recommendations_avl = result_avl.get("recommendations", [])
                followup_recomm_dist = folloup_response_result_dist.get("recommendations", [])
                followup_recomm_avl = folloup_response_result_avl.get("recommendations", [])

                if not recommendations_dist and not followup_recomm_dist:
                    st.warning("No recommendations found.")
                else:
                    table_data_dist,table_data_avl,table_data_followup_dist,table_data_followup_avl = [],[],[],[]
                    cg_response = load_cg_details(org_id, req_headers)
                    cg_list = cg_response.get("items_list", cg_response) if isinstance(cg_response, dict) else cg_response
                    cg_map = {
                        cg["caregiver_uid"]: {
                            "name": f"{cg['first_name']} {cg['last_name']}",
                            "discipline": cg.get("primary_discipline"),
                            "cg_lat": float(cg.get('caregiver_address', {}).get('geo_location', {}).get('lat') or 0.0),
                            "cg_lng": float(cg.get('caregiver_address', {}).get('geo_location', {}).get('lng') or 0.0),

                        }
                        for cg in cg_list
                    }
                    st.session_state["new_cg_map"] = cg_map
                    for rec in recommendations_dist:
                        clinician_id = rec.get("clinician")
                        rec["cg_lat"] = cg_map.get(clinician_id, {}).get("cg_lat")
                        rec["cg_lng"] = cg_map.get(clinician_id, {}).get("cg_lng")
                        team_name = rec.get("team_name") or (rec.get("teams")[0].get("team_name") if rec.get("teams") else "N/A")
                        table_data_dist.append({
                            "Rank": rec["rank"],
                            "Clinician Name": rec["clin_name"],
                            "Availability":rec["availability"],
                            "Team": team_name,
                            "Distance (mi)": rec["distance"],
                            "Est. Visit Time": rec["est_visit_time"],
                            "lat": rec["cg_lat"],
                            "lng": rec["cg_lng"]
                        })
                    for rec in recommendations_avl:
                        clinician_id = rec.get("clinician")
                        rec["cg_lat"] = cg_map.get(clinician_id, {}).get("cg_lat")
                        rec["cg_lng"] = cg_map.get(clinician_id, {}).get("cg_lng")
                        team_name = rec.get("team_name") or (rec.get("teams")[0].get("team_name") if rec.get("teams") else "N/A")
                        table_data_avl.append({
                            "Rank": rec["rank"],
                            "Clinician Name": rec["clin_name"],
                            "Availability": rec["availability"],
                            "Team": team_name,
                            "Distance (mi)": rec["distance"],
                            "Est. Visit Time": rec["est_visit_time"],
                            "lat": rec["cg_lat"],
                            "lng": rec["cg_lng"]
                        })
                    for rec in followup_recomm_dist:
                        clinician_id = rec.get("clinician")
                        rec["cg_lat"] = cg_map.get(clinician_id, {}).get("cg_lat")
                        rec["cg_lng"] = cg_map.get(clinician_id, {}).get("cg_lng")
                        team_name = rec.get("team_name") or (rec.get("teams")[0].get("team_name") if rec.get("teams") else "N/A")
                        table_data_followup_dist.append({
                            "Rank": rec["rank"],
                            "Clinician Name": rec["clin_name"],
                            "Availability": rec["availability"],
                            "Team": team_name,
                            "Distance (mi)": rec["distance"],
                            "Est. Visit Time": rec["est_visit_time"],
                            "lat": rec["cg_lat"],
                            "lng": rec["cg_lng"]
                        })
                    for rec in followup_recomm_avl:
                        clinician_id = rec.get("clinician")
                        rec["cg_lat"] = cg_map.get(clinician_id, {}).get("cg_lat")
                        rec["cg_lng"] = cg_map.get(clinician_id, {}).get("cg_lng")
                        team_name = rec.get("team_name") or (rec.get("teams")[0].get("team_name") if rec.get("teams") else "N/A")
                        table_data_followup_avl.append({
                            "Rank": rec["rank"],
                            "Clinician Name": rec["clin_name"],
                            "Availability": rec["availability"],
                            "Team": team_name,
                            "Distance (mi)": rec["distance"],
                            "Est. Visit Time": rec["est_visit_time"],
                            "lat": rec["cg_lat"],
                            "lng": rec["cg_lng"]
                        })
                    # cg_response = load_cg_details(org_id, req_headers)
                    # cg_list = cg_response.get("items_list", cg_response) if isinstance(cg_response,
                    #                                                                    dict) else cg_response
                    #
                    # cg_map = {}
                    # for cg in cg_list:
                    #     geo = cg.get('caregiver_address', {}).get('geo_location', {})
                    #     lat, lng = geo.get('lat'), geo.get('lng')
                    #     if lat is not None and lng is not None:
                    #         cg_map[cg["caregiver_uid"]] = {
                    #             "name": f"{cg['first_name']} {cg['last_name']}",
                    #             "discipline": cg.get("primary_discipline"),
                    #             "cg_lat": lat,
                    #             "cg_lng": lng
                    #         }
                    # caregiver_uids = list(cg_map.keys())
                    df_rec_dist = pd.DataFrame(table_data_dist)
                    df_rec_avl = pd.DataFrame(table_data_avl)
                    df_rec_avl.reset_index(drop=True, inplace=True)
                    df_rec_avl.index = df_rec_avl.index + 1
                    df_rec_dist.reset_index(drop=True, inplace=True)
                    df_rec_dist.index = df_rec_dist.index + 1
                    df_followup_rec_dist = pd.DataFrame(table_data_followup_dist)
                    df_followup_rec_avl = pd.DataFrame(table_data_followup_avl)
                    df_followup_rec_avl.index = range(1, len(df_followup_rec_avl) + 1)
                    df_followup_rec_dist.index = range(1, len(df_followup_rec_dist) + 1)
                    st.session_state["recommendations_df_dist"] = df_rec_dist
                    st.session_state["recommendations_df_avl"] = df_rec_avl
                    st.session_state["recommendations_df_followup_dist"] = df_followup_rec_dist
                    st.session_state["recommendations_df_followup_avl"] = df_followup_rec_avl

            except requests.exceptions.RequestException as e:
                st.error(f"❌ API call failed: {e}")
def build_caregiver_map(client_point):
    caregivers_loc = st.session_state.get("matching_caregivers", {})
    caregiver_avl = st.session_state.get("dly_clin_avlblty", {})

    m = folium.Map(zoom_start=5)
    bounds = []
    folium.Marker(
        client_point,
        popup="<b>Client</b>",
        icon=DivIcon(
            icon_size=(24, 24),
            icon_anchor=(12, 12),
            html="""
                <div style="
                    width:26px;height:26px;line-height:26px;
                    background:brown;color:white;
                    border-radius:50%;border:1px solid white;
                    text-align:center;font-size:14px;
                    box-shadow:0 0 2px rgba(0,0,0,0.4);
                ">
                    <i class="fa fa-user"></i>
                </div>
                """

        ),
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

    for uid, info in caregivers_loc.items():
        lat = info.get("cg_lat")
        lng = info.get("cg_lng")
        if not lat or not lng:
            continue

        caregiver_name = info.get("name", f"Caregiver {uid}")
        caseload = caregiver_avl.get(uid, {}).get("caseload", 0)
        intensity = min(max(caseload / 10, 0), 1)
        green_val = int(255 - (intensity * 150))
        color = f"rgb(0, {green_val}, 0)"

        folium.Marker(
            [lat, lng],
            popup=f"<b>{caregiver_name}</b><br>Caseload: {caseload}",
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    width:20px;height:20px;line-height:20px;
                    background:{color};
                    color:white;border-radius:50%;
                    border:1px solid white;
                    text-align:center;font-size:10px;
                    box-shadow:0 0 2px rgba(0,0,0,0.4);
                "></div>
                """
            )
        ).add_to(m)

        bounds.append((lat, lng))

    if bounds:
        m.fit_bounds(bounds)
    # Add legend for intensity
    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        right: 20px;
        z-index:9999;
        background-color: white;
        padding: 10px;
        border: 2px solid grey;
        border-radius: 5px;
        box-shadow: 0 0 5px rgba(0,0,0,0.3);
        font-size: 12px;
    ">
    <b>Availability</b><br>
    <div style="display: flex; align-items: center; margin-top: 4px;">
      <div style="width: 20px; height: 10px; background: rgb(0,255,0); margin-right: 5px;"></div>Low
    </div>
    <div style="display: flex; align-items: center; margin-top: 4px;">
      <div style="width: 20px; height: 10px; background: rgb(0,180,0); margin-right: 5px;"></div>Medium
    </div>
    <div style="display: flex; align-items: center; margin-top: 4px;">
      <div style="width: 20px; height: 10px; background: rgb(0,105,0); margin-right: 5px;"></div>High
    </div>
    </div>
    """
    Fullscreen().add_to(m)
    m.get_root().html.add_child(folium.Element(legend_html))

    return m
def add_client_marker(map_obj, client_point, client_name):
    folium.Marker(
        client_point,
        popup=f"Client: {client_name}",
        icon=DivIcon(
            icon_size=(24, 24),
            icon_anchor=(12, 12),
            html="""
                <div style="
                    width:24px;height:24px;line-height:24px;
                    background:white;color:black;
                    border-radius:50%;border:1px solid white;
                    text-align:center;font-size:14px;
                    box-shadow:0 0 2px rgba(0,0,0,0.4);
                ">
                    <i class="fa fa-user"></i>
                </div>
            """
        )
    ).add_to(map_obj)

def add_caregiver_markers(map_obj, df, client_point, colors):
    for i, row in enumerate(df.itertuples(index=False), start=1):
        if pd.notna(row.lat) and pd.notna(row.lng):
            this_color = colors[(i - 1) % len(colors)]
            point = (row.lat, row.lng)
            folium.Marker(
                point,
                icon=DivIcon(
                    icon_size=(20, 20),
                    icon_anchor=(10, 10),
                    html=f"""
                        <div style="
                            width:20px;height:20px;line-height:20px;
                            background:{this_color};
                            color:white;border-radius:50%;
                            text-align:center;font-size:10px;font-weight:bold;
                            border:1px solid white;
                        ">{i}</div>
                    """
                )
            ).add_to(map_obj)
            if client_point:
                folium.PolyLine([client_point, point], color=this_color, weight=2, opacity=0.6).add_to(map_obj)

# ------------------------------
# 2️⃣ Load session_state data
# ------------------------------
if (
    "recommendations_df_dist" in st.session_state and
    "recommendations_df_avl" in st.session_state and
    "recommendations_df_followup_dist" in st.session_state and
    "recommendations_df_followup_avl" in st.session_state
):
    df_rec_dist = st.session_state["recommendations_df_dist"]
    df_rec_avl = st.session_state["recommendations_df_avl"]
    df_followup_rec_dist = st.session_state["recommendations_df_followup_dist"]
    df_followup_rec_avl = st.session_state["recommendations_df_followup_avl"]
    cg_response = load_cg_details(org_id, req_headers)


    cg_list = cg_response.get("items_list", cg_response) if isinstance(cg_response, dict) else cg_response

    cg_map = {}
    for cg in cg_list:
        geo = cg.get('caregiver_address', {}).get('geo_location', {})
        lat, lng = geo.get('lat'), geo.get('lng')
        if lat is not None and lng is not None:
            cg_map[cg["caregiver_uid"]] = {
                "name": f"{cg['first_name']} {cg['last_name']}",
                "discipline": cg.get("primary_discipline"),
                "cg_lat": lat,
                "cg_lng": lng
            }
    caregiver_uids = list(cg_map.keys())
    start_date = datetime.strptime(soc_date, '%Y-%m-%d')
    dly_clin_avlblty = daily_clin_avail(caregiver_uids, start_date, org_id,req_headers)

    client_discipline = {
        disc
        for item in payload_list if "cg_soc_srv_discs" in item
        for disc in item["cg_soc_srv_discs"]
    }
    matching_caregivers = {
        uid: info
        for uid, info in cg_map.items()
        if info.get("discipline") in client_discipline
    }

    st.session_state["matching_caregivers"] = matching_caregivers
    st.session_state["dly_clin_avlblty"] = dly_clin_avlblty
    client_lat = float(st.session_state["selected_client"].get("cl_lat", 0))
    client_lng = float(st.session_state["selected_client"].get("cl_lng", 0))
    selected = st.session_state.get("selected_client", {})
    client_point = (
        float(selected.get("cl_lat", 0)),
        float(selected.get("cl_lng", 0))
    )
    client_name = st.session_state["selected_client"].get("Client Name", "Unknown")
    colors = ["red", "blue", "purple", "orange", "darkred", "darkblue"]

    # Create 2 rows with 2 columns each for 4 maps
    # st.markdown(
    #     "<h3 style='text-align:center; color:black;'>Consider only SOC Clinicians</h3>",
    #     unsafe_allow_html=True
    # )
    # row1_col1, row1_col2 = st.columns(2)
    st.markdown(
        "<h3 style='text-align:center; color:black;'>SOC Search</h3>",
        unsafe_allow_html=True
    )


    def highlight_top5(row):
        return ['background-color: #d1e7dd; font-weight: bold;' if row.name < 2 else '' for _ in row]
    with st.container():
        colA, colB = st.columns(2)
        with colA:
            st.markdown(
                "<h1 style='font-size:35px;'> 🟢 Availability-Based Recommendations</h1>",
                unsafe_allow_html=True
            )
            st_folium(
                build_map(df_followup_rec_avl,client_point),
                use_container_width=True, height=500, key="folium_distance_map"
            )
            df_followup_rec_avl['Clinician Name'] = df_followup_rec_avl['Clinician Name'].apply(mask_name)

            df_followup_rec_avl.index = range(1, len(df_followup_rec_avl) + 1)
            df_followup_rec_avl5=df_followup_rec_avl.head(5)
            df_followup_rec_avl5_display = df_followup_rec_avl5.drop(columns=['lat', 'lng'], errors='ignore')

            styled_df = df_followup_rec_avl5_display.style.apply(highlight_top5, axis=1)

            st.dataframe(styled_df, use_container_width=True)
        with colB:
            st.markdown(
                "<h1 style='font-size:35px;'> 🔵 Distance-Based Recommendations</h1>", unsafe_allow_html=True)
            st_folium(
                build_map(df_followup_rec_dist,client_point),
                use_container_width=True, height=500, key="folium_avl_map"
            )
            df_followup_rec_dist['Clinician Name'] = df_followup_rec_dist['Clinician Name'].apply(mask_name)

            df_followup_rec_dist5=df_followup_rec_dist.head(5)
            df_followup_rec_dist5_display = df_followup_rec_dist5.drop(columns=['lat', 'lng'], errors='ignore')

            styled_df = df_followup_rec_dist5_display.style.apply(highlight_top5, axis=1)

            st.dataframe(styled_df, use_container_width=True)

    # --- Row 1, Column 1: SOC Distance ---
    # with row1_col1:
    #     st.markdown("<h3 style='font-size:16px;'> Distance</h3>", unsafe_allow_html=True)
    #     m1 = folium.Map(location=[client_lat, client_lng], zoom_start=12)
    #     add_client_marker(m1, client_point, client_name)
    #     add_caregiver_markers(m1, df_rec_dist, client_point, colors)
    #     Fullscreen().add_to(m1)
    #     st_folium(m1, use_container_width=True, height=350, key="folium_soc_dist")
    #     st.dataframe(df_rec_dist, use_container_width=True)
    # # --- Row 2, Column 1: SOC Availability ---
    # with row1_col2:
    #     st.markdown("<h3 style='font-size:16px;'> Availability</h3>", unsafe_allow_html=True)
    #     m3 = folium.Map(location=[client_lat, client_lng], zoom_start=12)
    #     add_client_marker(m3, client_point, client_name)
    #     add_caregiver_markers(m3, df_rec_avl, client_point, colors)
    #     Fullscreen().add_to(m3)
    #     st_folium(m3, use_container_width=True, height=350, key="folium_soc_avl")
    #     st.dataframe(df_rec_avl, use_container_width=True)
    # --- Row 1, Column 2: Follow-up Distance ---
    # with row2_col1:
    #
    #     st.markdown("<h3 style='font-size:16px;'> Availability</h3>", unsafe_allow_html=True)
    #     m4 = folium.Map(location=[client_lat, client_lng], zoom_start=12)
    #     add_client_marker(m4, client_point, client_name)
    #     add_caregiver_markers(m4, df_followup_rec_avl, client_point, colors)
    #     Fullscreen().add_to(m4)
    #     st_folium(m4, use_container_width=True, height=350, key="folium_followup_avl")
    #     st.dataframe(df_followup_rec_avl, use_container_width=True)
    #
    #
    #
    # # --- Row 2, Column 2: Follow-up Availability ---
    # with row2_col2:
    #     st.markdown("<h3 style='font-size:16px;'> Distance</h3>", unsafe_allow_html=True)
    #     m2 = folium.Map(location=[client_lat, client_lng], zoom_start=12)
    #     add_client_marker(m2, client_point, client_name)
    #     add_caregiver_markers(m2, df_followup_rec_dist, client_point, colors)
    #     Fullscreen().add_to(m2)
    #     st_folium(m2, use_container_width=True, height=350, key="folium_followup_dist")
    #     st.dataframe(df_followup_rec_dist, use_container_width=True)
with st.container():
    st.markdown(
        "<h1 style='font-size:20px;'> 🟣 Clinician Availability</h1>",
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])  # adjust ratios to control width
    with col2:
        st_folium(
            build_caregiver_map(client_point),
            height=450,
            use_container_width=True,
            key="folium_caregiver_map"
        )

    # col1, col2, col3 = st.columns([1, 2, 1])  # adjust ratios to control width
    # with col2:
    #     st_folium(
    #         build_caregiver_map(client_point),
    #         height=450,
    #         use_container_width=True,
    #         key="folium_caregiver_map"
    #     )


