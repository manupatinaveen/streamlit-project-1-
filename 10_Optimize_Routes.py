import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium
import folium

from flask import Response
from config import SchApp,logger
# ---------------- Page Config -----------------
st.set_page_config(page_title="Optimize Routes", page_icon="🗺️", layout="wide")
st.markdown(
    "<h1 style='font-size:30px;'>Optimize Routes 🗺️</h1>",
    unsafe_allow_html=True
)
st.sidebar.header("Optimize Routes")
# ---------------- Helper Functions -----------------
def json_response(data, status=200):
    return Response(
        response=json.dumps(data, default=str),
        status=status,
        mimetype="application/json"
    )
req_headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwiY3J0Iiwic2NoZWR1bGVyIl0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiIzMjg1NTMiLCJwaWQiOiI2OTAiLCJpY29kZSI6IkRldiIsInV0eXBlIjoiYWdlbmN5X3N1cHBvcnRfdXNlciIsIm5iZiI6MTc2NzkzODk5NywiZXhwIjoxNzY3OTQyNTk3LCJpc3MiOiJodHRwczovL3Byb2RxYS5rYW50aW1laGVhbHRoLm5ldC9pZGVudGl0eS92MiJ9.PzgLz7Yl8xc_wUiNOx19ozDSG1cZQ1KHv388fQUKvVsP263wpb4bkUUgL3O4NhrtRswan3Vl6-8df2k9epfTV-riRcdRIs3SIpk6LwepZbqblCOowgqGjDJQWLGvNrPSCghsdzkWCaZ6RyU5OXjWvoTRB6-agNtBWngmteVMk3v21XwNPyWFGks-2pAvIZGcC1JXfmyYNSrSdGelbeqwu9VO2_TfiZbCoFAw0zFy1lbfwknE8uJjqajGhpDQHXyJUZxz4HQUpQtygCzp4gmzQCl89nu9XpLlDytTA6PFYGWG0yyIYOmuYk_rx7k25jQZez8TdAfjCtlNR-Cf1_lDWKJBStC_UTxgY3kUFCQNjMhgWntMdGxBGdA72vfsvDjIkh4GKpnAlZgeYDd88Kl0AJx8kT8IWcNxDtTFjQOI572iWvBkcrxqp4LNY2z20_0uiwiYB13nL0nBZmJUA25vAPsRP7cNG-mPn4y9mdnU_w203PLMP6AGVOKoVWmzXo44CCVaPKzGK78aH_knNYG_muBvaOv7BQ7ij-3OeEeasNogB6n8saz1pduqooVetp_vm6Qt_Y2mm2Wl63Bc2F7ho1G5mDwb4mamKb_eSOw8GQ91MTpdHQuWaePVL37uy6SwS2v98KOzZRjv0gnhPMxGKhb4La7A8EU0a8kuDCmvJeA",
    "Cookie": "kt_session_id=28b9d898b3b443a7b2d5e32f9d747a76"
}
def get_cg_schedules(stdt, org_id, location_id, req_headers):
    from common.service_functions import make_service_request
    try:
        stdt_dt = datetime.combine(stdt, datetime.min.time())
        endt_dt = stdt_dt + timedelta(days=6)

        payload = {
            "start_date": stdt_dt.strftime("%m/%d/%Y"),
            "end_date": endt_dt.strftime("%m/%d/%Y"),
            "page_no": 1,
            "page_size": 5000,
            "client_locations": [location_id],
            "org_id": org_id
        }
        print(payload)
        logger.info(f"Fetching schedules from {stdt} to {endt_dt.strftime('%m/%d/%Y')} for location_id: {location_id}")
        response_json = make_service_request("int_schedules_list", req_headers,payload, "json")
        if not response_json or 'items_list' not in response_json or not response_json['items_list']:
            errmsg = {
                "error_code": "DATA_NOT_AVAILABLE",
                "error_message": f"Data is not available for location ID: {location_id}"
            }
            return json_response(errmsg, status=400)
        response = response_json['items_list']
        logger.info(f"Retrieved {len(response)} schedules for location_id: {location_id}")
        return response
    except Exception as e:
        logger.exception("Error occurred while fetching caregiver schedules")
        errmsg = {"error_code": "INTERNAL_ERROR", "error_message": str(e)}
        return json_response(errmsg, status=500)

def convert_to_hms_format(time_str):
    time_obj = datetime.strptime(time_str, '%I:%M %p')
    return time_obj.strftime('%H:%M:%S')

# ---------------- Parameters -----------------
col1, col2 = st.columns(2)
with col1:
    org_id = st.text_input("Enter Org ID",key="org_id_input")
with col2:
    location_id = st.text_input("Enter Location ID",key="loc_id_input")
req_st_date = st.date_input("Select Start Date", datetime.today())
# ---------------- Controlled API call -----------------
if org_id and location_id:
    if "sched_data" not in st.session_state or st.session_state.get("last_req_st_date") != req_st_date:
        with st.spinner("Fetching schedules..."):
            sched_response = get_cg_schedules(req_st_date, org_id, location_id, req_headers)
            logger.info("schedules data loaded from optimize route")
            if isinstance(sched_response, Response):
                st.error("Error fetching schedules. Please check logs or token.")
                st.stop()
            st.session_state.sched_data = sched_response
            st.session_state.last_req_st_date = req_st_date

    sched_data = st.session_state.sched_data
else:
    st.warning("⚠️ Please enter both Org ID and Location ID to fetch schedules.")
    st.stop()
# ---------------- Data preparation -----------------
raw_schedules_df = pd.json_normalize(sched_data)
clin_options = sorted(list(set(raw_schedules_df['caregiver_name'].dropna().tolist())))
date_options = sorted(list(set(raw_schedules_df['planned_date'].dropna().tolist())))

col1, col2,col3,col4= st.columns(4)
with col1:
    clin_selected = st.selectbox("Select a clinician:", clin_options, index=None)
with col2:
    date_selected = st.selectbox("Select a date:", date_options, index=None)
with col3:
    start_time_at_home = st.time_input("Start Time at Home", datetime.strptime("09:00", "%H:%M").time())
    if clin_selected:
        matching_rows = raw_schedules_df[raw_schedules_df["caregiver_name"] == clin_selected]
        if not matching_rows.empty:
            caregiver_uid = matching_rows["caregiver_uid"].iloc[0]
        else:
            caregiver_uid = None
            st.warning("⚠️ No matching caregiver UID found for the selected clinician.")
    else:
        caregiver_uid = None
if "last_clin" not in st.session_state:
    st.session_state.last_clin = None
if "last_date" not in st.session_state:
    st.session_state.last_date = None
if clin_selected != st.session_state.last_clin or date_selected != st.session_state.last_date:
    if "resp_json" in st.session_state:
        del st.session_state["resp_json"]
    st.session_state.last_clin = clin_selected
    st.session_state.last_date = date_selected
# ---------------- Build Payload & Display Map -----------------
# if date_selected and clin_selected:
filtered_df = raw_schedules_df[(raw_schedules_df['planned_date'] == date_selected) &(raw_schedules_df['caregiver_name'] == clin_selected)]
client_options = sorted(set(filtered_df['client_name'].dropna().tolist()))
with col4:
    first_visit_client = st.selectbox("Choose First Client", client_options, index=None)
if not date_selected:
    date_selected = datetime.today().strftime("%m/%d/%Y")
date_obj = datetime.strptime(date_selected, "%m/%d/%Y")
formatted_date = date_obj.strftime("%Y-%m-%d")
print(formatted_date)
visits_to_optimize = []
for _, row in filtered_df.iterrows():
    visits_to_optimize.append({
        "schedule_uid": row['schedule_uid'],
        "client_uid": row['client_uid'],
        "visit_start_time": convert_to_hms_format(row['planned_start_time']),
        "visit_end_time": convert_to_hms_format(row['planned_end_time']),
        "is_pinned": row.get('is_pinned', False),
        "preferred_slot": None,
        "visit_duration_in_min": 60,
        "is_first_visit": row['client_name'] == first_visit_client if first_visit_client else False,
        "disc": row.get('discipline'),
        "prod_pts": 1.0,
        "client_branch_uid": row.get('client_branch_uid'),
        "schedule_status": row.get('status'),
        "is_televisit": False,
        "actual_start_time": None,
        "actual_end_time": None
    })
final_payload = {"schedule_uids": [], "visits_to_optimize": visits_to_optimize}
print("final_payload",final_payload)
# st.dataframe(filtered_df[['client_name', 'planned_start_time', 'planned_end_time', 'is_pinned']], use_container_width=True)
# ---------------- Optimize All Three Routes -----------------
if st.button("🚀 Optimize Routes") or "resp_all_routes" in st.session_state:
    if "resp_all_routes" not in st.session_state:
        with st.spinner("Optimizing all three routes, please wait..."):
            base_url = SchApp.config()["server"]["base_url"]
            endpoint_path = SchApp.config()["endpoint context"]["path"]
            api_url = f"{base_url}{endpoint_path}/optimize_clinician_route?"
            print("api_url",api_url)
            # preferred_routes = [None,"Near-to-Near", "Near-to-Far", "Far-to-Near"]
            preferred_routes = ["Near-to-Near"]
            resp_all_routes = {}
            for route in preferred_routes:
                params = {
                    "use_goole_api": "Y",
                    "org_id": org_id,
                    "caregiver_uid": caregiver_uid,
                    "date": formatted_date,
                    "work_start_time": start_time_at_home.strftime("%H:%M:%S"),
                    "location_id": location_id,
                    "is_recompute": "N",
                    "day_start_from_home": "Y"
                }
                if route is not None:
                    params["preferred_route"] = route
                label = route or "default"
                try:
                    r = requests.post(api_url, params=params, json=final_payload,headers=req_headers, timeout=120)
                    print("api_url", api_url)
                    print("params", params)
                    print("final_payload", final_payload)
                    print("status_code", r.status_code)

                    if r.status_code == 200:
                        resp_all_routes[label] = r.json()
                    else:
                        print("response_text", r.text)  # raw body
                        print("response_headers", r.headers)  # optional but useful
                        st.error(f"{route}: Failed {r.status_code} – {r.text}")
                        resp_all_routes[label] = None
                except requests.exceptions.RequestException as e:
                    # Catches timeouts, connection errors, etc.
                    st.error(f"{label}: Request error {e}")
                    resp_all_routes[label] = None

            st.session_state.resp_all_routes = resp_all_routes
    resp_all_routes = st.session_state.resp_all_routes
    cols = st.columns(4)
    # routes_list = ["default","Near-to-Near", "Near-to-Far", "Far-to-Near"]
    routes_list = ["Near-to-Near"]

    totals = {
        r: (
            resp_all_routes.get(r, {}).get("total_distance", float("inf")),
            resp_all_routes.get(r, {}).get("total_time_to_travel_in_mins", float("inf")),
            resp_all_routes.get(r, {}).get("overall_total_distance", float("inf")),
        )
        for r in routes_list
    }
    min_distance = min(v[0] for v in totals.values())
    min_time = min(v[1] for v in totals.values())
    min_tour_distance = min(v[2] for v in totals.values())
    for i, route in enumerate(routes_list):
        result = resp_all_routes.get(route)
        with cols[i]:
            st.markdown(
                f"<h4 style='font-size:20px; margin-top:0'>{route}</h4>",
                unsafe_allow_html=True
            )
            if not result:
                st.warning("No data available.")
                continue
            caregiver_geo = result.get("caregiver_address", {}).get("geo_location", {})
            caregiver_lat = float(caregiver_geo.get("lat", 0))
            caregiver_lng = float(caregiver_geo.get("lng", 0))
            m = folium.Map(location=[caregiver_lat, caregiver_lng], zoom_start=10)
            folium.Marker(
                [caregiver_lat, caregiver_lng],
                popup="Clinician Location",
                icon=folium.Icon(color="blue", icon="user", prefix="fa")
            ).add_to(m)
            prev_lat, prev_lng = caregiver_lat, caregiver_lng
            rows = []
            for idx, visit in enumerate(result.get("caregiver_tour", []), start=1):
                client_addresses = visit.get("client_address", [])
                if client_addresses:
                    geo = client_addresses[0].get("geo_location", {})
                    c_lat, c_lng = float(geo.get("lat", 0)), float(geo.get("lng", 0))
                    client_name = f"{visit.get('first_name', '')} {visit.get('last_name', '')}"
                    rows.append({
                        "Client Name": client_name,
                        "Distance to Travel": visit.get("dist_to_travel", 0),
                        "Time to Travel": visit.get("time_to_travel_in_mins",0)
                    })
                    folium.Marker(
                        [c_lat, c_lng],
                        popup=f"Visit {idx}: {client_name}",
                        icon=folium.Icon(color="red", icon=str(idx), prefix="fa")
                    ).add_to(m)
                    folium.PolyLine([[prev_lat, prev_lng], [c_lat, c_lng]],color="blue", weight=1.8, opacity=0.7).add_to(m)
                    prev_lat, prev_lng = c_lat, c_lng
            with st.container():
                st_folium(m, use_container_width=True, height=350, key=f"map_{i}_{route}")
                total_dist = result.get("total_distance", 0)
                tour_distance = result.get("overall_total_distance", 0)

                if total_dist == min_distance:
                    dist_value = f"<span style='color:green;'>{total_dist} miles</span>"
                else:
                    dist_value = f"{total_dist} miles"
                total_time = result.get("total_time_to_travel_in_mins", 0)
                if total_time == min_time:
                    time_value = f"<span style='color:green;'>{total_time} mins</span>"
                else:
                    time_value = f"{total_time} mins"
                if tour_distance == min_tour_distance:
                    tour_distance_value = f"<span style='color:green;'>{tour_distance} miles</span>"
                else:
                    tour_distance_value = f"{tour_distance} miles"

                dist_value = f"<span style='color:green; font-weight:bold;'>{total_dist}</span>" \
                    if total_dist == min_distance else str(total_dist)
                time_value = f"<span style='color:green;font-weight:bold;'>{total_time}</span>" \
                    if total_time == min_time else str(total_time)
                st.markdown(
                    f"""
                    <div style="font-size:18px;">  <!-- Change 18px to any size you want -->
                        🚗 <span style="color:#1E90FF; font-weight:bold;">Tour Distance: </span>
                        {dist_value} miles<br>
                        ♻️ <span style="color:#1E90FF; font-weight:bold;">Tour distance from Clinician home: </span>
                        {tour_distance_value} miles<br>
                        ⏱️ <span style="color:#1E90FF; font-weight:bold;">Travel Time: </span>
                        {time_value} mins
                    </div>
                    """,
                    unsafe_allow_html=True
                )


                def mask_name(name):
                    if not name or len(name) <= 6:
                        return name
                    return name[:3] + "*" * (len(name) - 6) + name[-3:]
                if rows:
                    df = pd.DataFrame(rows, index=range(1, len(rows) + 1))
                    df['Client Name'] = df['Client Name'].apply(mask_name)
                    st.dataframe(df, use_container_width=True, height=400)
                else:
                    st.info("No client visits to display.")
