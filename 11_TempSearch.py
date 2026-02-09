import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from flask import Response
import requests
import folium
from streamlit_folium import st_folium
from config import SchApp, logger
from folium.plugins import Fullscreen
from folium.features import DivIcon
st.set_page_config(page_title="Temp Search", page_icon="💁🔍", layout="wide")
st.markdown(
    "<h1 style='font-size:35px;'>Search Temp Clinicians 💁🔍</h1>",
    unsafe_allow_html=True
)
st.sidebar.header("Temp Search")
req_headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwic2NoZWR1bGVyIiwiY3J0Il0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiI0Mjc4MDciLCJwaWQiOiI2OTAiLCJpY29kZSI6IlN0YWdpbmciLCJ1dHlwZSI6ImFnZW5jeV9zdXBwb3J0X3VzZXIiLCJuYmYiOjE3NjU4ODQyNzAsImV4cCI6MTc2NTg4Nzg3MCwiaXNzIjoiaHR0cHM6Ly9zdGFnaW5nLmthbnRpbWVoZWFsdGgubmV0L2lkZW50aXR5L3YyIn0.fxuUokVJh8XU_Ta_Nr_glzznls64z967whb2yZK6w7gMrXKki5GDZt4p_zQ6rWseOmiS1VIFcAZviVDC_wrlN179S3ptmgQmC-8JDPZC3aD0UjhvKSmKpefNBjclUc6vZQaqP082oQYan3u_7i07HNYMJFgJJ7gULOeWhn89HWWPvm0PwBnKIRPx5tjMO0CCM0pmRRmwFKlIg2Fi9V3xBVdyMpJBFSW8tigZCsViLthe9sLA2yBISEEqVlHf1NmEquNGuTWW3BwxjhnlQsSpxeLZ01LrBLkIl77WYcpjKODkeOcobq1RASNOojrT1zjK5Adoa6tnh6LOGJaaexnw4RJX25AZlSYv5SbfR6Wj6yphXv4PR17VT_JeswcC7yLjyv0tzGODraHcknKpEim2_ijLZ3nPY-4IELx6_Yp8DkTTVQFNk_1IrMo4uJyemtjtOf2s3pPn1uZuImEQ9MJL4v1v1C3pwTHI2OI4CqZsFIRBflfJ-vGDNmebZ97xYgxChmoOHc3eQv5jV58bYcyXz9fIgl9DDd0_K3qVC6aYsOpMBC0UHKd6zg04tXs3woF8gFsS8JlpePaX5yXIHy34kPjGKSrfihlRipsBMwbglaGNUBCJCOnjZYa0SR8PX5ExQIuP07dYaISiVgZiBbXQ7WhDnRO6uNQQZgcXHnQdBk0",
    "Cookie": "kt_session_id=4581de52a1ac414da0a52b5de00178fa"
}
def json_response(data, status=200):
    return Response(response=json.dumps(data, default=str),
                    status=status,
                    mimetype="application/json")
def get_cg_schedules(stdt, org_id, req_headers):
    from common.service_functions import make_service_request
    try:
        stdt_dt = datetime.combine(stdt, datetime.min.time())
        endt_dt = stdt_dt + timedelta(days=6)
        payload = {
            "start_date": stdt_dt.strftime("%m/%d/%Y"),
            "end_date": endt_dt.strftime("%m/%d/%Y"),
            "caregiver_uids": [""],
            "page_no": 1,
            "page_size": 100,
            "org_id": org_id,
            "schedule_status": ['planned']
        }
        response_json = make_service_request("int_schedules_list", req_headers, payload, "json")
        if not response_json or 'items_list' not in response_json or not response_json['items_list']:
            errmsg = {"error_code": "DATA_NOT_AVAILABLE", "error_message": "Data is not available"}
            return json_response(errmsg, status=400)
        return response_json['items_list']
    except Exception as e:
        logger.exception("Error occurred while fetching caregiver schedules")
        errmsg = {"error_code": "INTERNAL_ERROR", "error_message": str(e)}
        return json_response(errmsg, status=500)
def load_cg_details(org_id,req_headers):
    from common.service_functions import make_service_request
    try:
        payload = {
            'page_no': 1, 'page_size': 40000, 'org_id': org_id, "staff_types": ["both", "clinician"]
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
def get_clin_dly_avlblty(clinids, start_date,org_id,req_headers):
    try:
        from common.service_functions import make_service_request
        payload = {"caregiver_uids": clinids, "start_date": datetime.strftime(start_date, "%m/%d/%Y"),
                   "number_of_days": 1, "org_id":org_id}
        response = make_service_request("int_cg_availability_daily", req_headers, payload, "json")
        avail="max_productivity_points"
        alloc="allocated_productivity_points"
        result = {}
        for res in response:
            caseload = 0
            if res["availability_info"][0][avail] > 0:
                caseload = res["availability_info"][0][avail] - res["availability_info"][0][alloc]
            else:
                caseload = 0
            result[res["caregiver_uid"]] = {
                "caregiver_name": res["caregiver_name"],
                "caseload": caseload
            }
    except Exception as e:
        logger.info(e)
        errmsg = {}
        errmsg = {"error_code": "SERVICE_API_FAIL", "error_message": "Daily availability C# API Fail: " + str(e)}
    return result
def daily_clin_avail(clin_lst, start_date,org_id,req_headers):
    dly_clin_avlblty_dict = {}
    try:
        dly_clin_avlblty_dict.update(get_clin_dly_avlblty(clin_lst, start_date,org_id,req_headers))
        return dly_clin_avlblty_dict
    except Exception as e:
        logger.info(e)
# ---------------- Session Init -----------------
for key in ["sched_data", "result_json", "selected_uid", "client_map", "org_id"]:
    if key not in st.session_state:
        st.session_state[key] = None
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
def build_map(df):
    m = folium.Map(zoom_start=8)
    bounds = []
    if {"cl_lat", "cl_lng"}.issubset(df.columns):
        c_lat = df["cl_lat"].iloc[0]
        c_lng = df["cl_lng"].iloc[0]
        client_point = (c_lat, c_lng)
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
    if {"cg_lat", "cg_lng"}.issubset(df.columns):
        for idx, row in df.iterrows():
            if pd.isna(row["cg_lat"]) or pd.isna(row["cg_lng"]):
                continue

            point = (row["cg_lat"], row["cg_lng"])
            bounds.append(point)
            if idx < 5:
                color = "green"
            else:
                color = "blue"
            folium.Marker(
                point,
                popup=f"<b>{row.get('Clinician', 'Clinician')}</b>",
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
                        {idx+1}
                    </div>
                    """
                ),
            ).add_to(m)
    if bounds:
        m.fit_bounds(bounds)
    return m
    colors = ["blue"]
    for i, row in enumerate(df.itertuples(index=False), start=1):
        if pd.notna(row.cg_lat) and pd.notna(row.cg_lng):
            point = (row.cg_lat, row.cg_lng)
            bounds.append(point)
            this_color = colors[(i - 1) % len(colors)]
            clinician = f"{getattr(row,'caregiver_lastname','')}, {getattr(row,'caregiver_firstname','')}"
            folium.Marker(
                point,
                popup=f"<b>{clinician}</b>",
                icon=DivIcon(
                    icon_size=(24, 24),
                    icon_anchor=(12, 12),
                    html=f"""
                    <div style="
                        width:27px;height:27px;line-height:25px;
                        background:{this_color};
                        color:white;border-radius:50%;
                        text-align:center;font-size:10px;font-weight:bold;
                        border:1px solid white;
                    ">{i}</div>
                    """
                )
            ).add_to(m)
    Fullscreen().add_to(m)
    if bounds:
        m.fit_bounds(bounds)
    return m
def fetch_temp_clinicians():
    selected_client = st.session_state.client_choice
    if not selected_client:
        return
    schedule_uid = st.session_state.client_map[selected_client]
    st.session_state.selected_uid = schedule_uid
    base_url = SchApp.config()["server"]["base_url"]
    endpoint_path = SchApp.config()["endpoint context"]["path"]
    url_avail = (
        f"{base_url}{endpoint_path}/temp_clinician_search?"
        f"org_id={st.session_state.org_id}&max_recommendation=10"
        f"&schedule_uid={schedule_uid}&distance=false&availability=true"
    )
    url_dist = (
        f"{base_url}{endpoint_path}/temp_clinician_search?"
        f"org_id={st.session_state.org_id}&max_recommendation=10"
        f"&schedule_uid={schedule_uid}&distance=true&availability=false"
    )
    try:
        with st.spinner(f"Searching clinicians for {selected_client}..."):
            resp_avail = requests.get(url_avail, headers=req_headers,timeout=(30, 180))
            print("resp_avail",resp_avail)
            resp_dist  = requests.get(url_dist,  headers=req_headers,timeout=(30, 180))
            print("resp_dist",resp_dist)
            if resp_avail.status_code == 200:
                st.session_state.result_json_avail = resp_avail.json()
            else:
                st.error(f"Availability API error {resp_avail.status_code}: {resp_avail.text}")
                st.session_state.result_json_avail = None
            if resp_dist.status_code == 200:
                st.session_state.result_json_dist = resp_dist.json()
            else:
                st.error(f"Distance API error {resp_dist.status_code}: {resp_dist.text}")
                st.session_state.result_json_dist = None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.session_state.result_json_avail = None
        st.session_state.result_json_dist = None
col1, col2, col3 = st.columns(3)
with col1:
    org_id = st.text_input("Enter Org ID", key="org_id_input")
with col2:
    req_st_date = st.date_input("Select Start Date", datetime.today())
if org_id:
    st.session_state.org_id = org_id
    if (st.session_state.get("sched_data") is None or
        st.session_state.get("last_req_st_date") != req_st_date or
        st.session_state.get("last_org_id") != org_id):
        sched_response = get_cg_schedules(req_st_date, org_id, req_headers)

        if isinstance(sched_response, Response):
            st.error("Error fetching schedules. Check token or logs.")
            st.stop()
        st.session_state.sched_data = sched_response
        st.session_state.last_req_st_date = req_st_date
        st.session_state.last_org_id = org_id
    raw_df = pd.json_normalize(st.session_state.sched_data)
    raw_df = raw_df[raw_df["client_name"].notnull()].reset_index(drop=True)
    filtered_df = raw_df[
        ["client_name", "client_uid", "actual_start_time",
         "team_name", "payer_name","discipline", "primary_discipline", "service_type", "schedule_uid"]
    ].copy()
    client_discipline = filtered_df["primary_discipline"].iloc[0]
    client_map = dict(zip(filtered_df["client_name"], filtered_df["schedule_uid"]))
    st.session_state.client_map = client_map
    cg_response = load_cg_details(org_id, req_headers)
    if hasattr(cg_response, 'get_data'):
        response_data = cg_response.get_data(as_text=True)
        import json
        cg_list = json.loads(response_data).get('data', [])
    elif isinstance(cg_response, dict):
        cg_list = cg_response.get('data', cg_response)
    else:
        cg_list = []
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
    dly_clin_avlblty = daily_clin_avail(caregiver_uids, req_st_date, org_id,req_headers)
    client_discipline = filtered_df["primary_discipline"].iloc[0]
    matching_caregivers = {
        uid: info
        for uid, info in cg_map.items()
        if info.get("discipline") == client_discipline
    }
    st.session_state["matching_caregivers"] = matching_caregivers
    st.session_state["dly_clin_avlblty"] = dly_clin_avlblty
    with col3:
        st.selectbox(
            "Select Client to start Temp Search",
            options=list(client_map.keys()),
            index=None,
            placeholder="Choose a client...",
            key="client_choice",
            on_change=fetch_temp_clinicians
        )
    if (st.session_state.get("result_json_avail") and
        st.session_state.get("result_json_dist") and
        st.session_state.get("selected_uid")):
        uid = st.session_state.selected_uid
        sel_row = filtered_df[filtered_df["schedule_uid"] == uid]
        st.markdown("## 📌 Selected Client Details")
        sel_row_renamed = sel_row.rename(columns={
            "client_name": "Client",
            "scheduled_start_time": "Original Visit Time",
            "team_name": "Team",
            "payer_name": "Payer",
            "discipline": "Discipline",
            "service_type": "Service",
            "schedule_uid": "Schedule UID"
        })
        styled_df = sel_row_renamed.style.set_table_styles([
            {'selector': 'thead th',
             'props': [('background-color', '#4CAF50'),  # green header
                       ('color', 'white'),  # white text
                       ('font-weight', 'bold')]}  # bold text
        ])
        st.table(styled_df)

        rows_for_avail=[]
        for caregiver in st.session_state.result_json_avail:
            for tour in caregiver.get("caregiver_tour", []):
                if tour.get("temp_client") == "Yes":
                    rows_for_avail.append({
                        "caregiver_uid": caregiver.get("caregiver_uid"),
                        "caregiver_firstname": caregiver.get("caregiver_firstname"),
                        "caregiver_lastname": caregiver.get("caregiver_lastname"),
                        "additional_distance_to_travel": caregiver.get("distance_miles"),
                        "cg_lat":caregiver.get("lat"),
                        "cg_lng":caregiver.get("lng"),
                        "Visits": caregiver.get("number_of_visits", 0),
                        "team_name": caregiver.get("team_name"),
                        "visit_date": caregiver.get("visit_date"),
                        "client_uid": tour.get("client_uid"),
                        "first_name": tour.get("first_name"),
                        "last_name": tour.get("last_name"),
                        "scheduled_start_time": tour.get("scheduled_start_time"),
                        "scheduled_end_time": tour.get("scheduled_end_time"),
                        "cl_lat": tour.get("lat"),
                        "cl_lng": tour.get("lng"),
                        "cg_cl_distance": tour.get("cg_cl_dist"),
                        "cl_cl_dist": tour.get("cl_cl_dist"),
                        "Avilability": caregiver.get("capacity_pp"),
                        "discipline":tour.get("caregiver_discipline")
                    })
        df = pd.DataFrame(rows_for_avail)
        df = df.drop_duplicates(subset=["caregiver_uid", "client_uid"], keep="first")  # choose your key columns
        rows_for_dist=[]
        for caregiver in st.session_state.result_json_dist:
            for tour in caregiver.get("caregiver_tour", []):
                if tour.get("temp_client") == "Yes":
                    rows_for_dist.append({
                        "caregiver_uid": caregiver.get("caregiver_uid"),
                        "caregiver_firstname": caregiver.get("caregiver_firstname"),
                        "caregiver_lastname": caregiver.get("caregiver_lastname"),
                        "additional_distance_to_travel":caregiver.get("distance_miles"),
                        "cg_lat": caregiver.get("lat"),
                        "cg_lng": caregiver.get("lng"),
                        "Visits": caregiver.get("number_of_visits", 0),
                        "team_name": caregiver.get("team_name"),
                        "visit_date": caregiver.get("visit_date"),
                        "client_uid": tour.get("client_uid"),
                        "first_name": tour.get("first_name"),
                        "last_name": tour.get("last_name"),
                        "scheduled_start_time": tour.get("scheduled_start_time"),
                        "scheduled_end_time": tour.get("scheduled_end_time"),
                        "cl_lat": tour.get("lat"),
                        "cl_lng": tour.get("lng"),
                        "cg_cl_distance": tour.get("cg_cl_dist"),
                        "cl_cl_dist": tour.get("cl_cl_dist"),
                        "Avilability":caregiver.get("capacity_pp"),
                        "discipline": tour.get("caregiver_discipline")

                    })
        df1 = pd.DataFrame(rows_for_dist)
        df1= df1.drop_duplicates(subset=["caregiver_uid", "client_uid"], keep="first")
        if not df1.empty and {"cl_lat", "cl_lng"}.issubset(df1.columns):
            c_lat = df["cl_lat"].iloc[0]
            c_lng = df["cl_lng"].iloc[0]
            client_point = (c_lat, c_lng)
        with st.container():
            colA, colB = st.columns(2)
            with colA:
                st.markdown(
                    "<h1 style='font-size:35px;'> 🟢 Availability-Based Recommendations</h1>",
                    unsafe_allow_html=True
                )
                st_folium(
                    build_map(df),
                    use_container_width=True,
                    height=500,
                    key="folium_availability_map"
                )
                # df.index = range(1, len(df) + 1)
                df["Clinician"] = df["caregiver_firstname"] + ", " + "xxxxxxx"
                df_selected = df[
                    ["Clinician", "scheduled_start_time", "cg_cl_distance", "Avilability",
                     "additional_distance_to_travel", "Visits"]
                ]
                df_selected = df_selected.head(5)
                def highlight_top5(row):
                    return ['background-color: #d1e7dd; font-weight: bold;' if row.name < 2 else '' for _ in row]
                styled_df = df_selected.style.apply(highlight_top5, axis=1).set_table_styles([
                    {'selector': 'th', 'props': [('font-size', '18px')]},
                    {'selector': 'td', 'props': [('font-size', '18px')]},
                ])
                st.dataframe(styled_df, use_container_width=True)
            with colB:
                st.markdown(
                    "<h1 style='font-size:35px;'> 🔵 Distance-Based Recommendations</h1>",unsafe_allow_html=True)
                st_folium(
                    build_map(df1),
                    use_container_width=True, height=500,key="folium_distance_map"
                )
                # df1.index = range(1, len(df1) + 1)
                df1["Clinician"]=df1["caregiver_firstname"]+", "+" xxxxxxx"
                df1_selected=df1[["Clinician","scheduled_start_time","cg_cl_distance","Avilability","additional_distance_to_travel","Visits"]]
                df1_selected= df1_selected.head(5)
                styled_df = df1_selected.style.apply(highlight_top5, axis=1)
                st.dataframe(styled_df, use_container_width=True)
        with st.container():
            st.markdown(
                "<h1 style='font-size:25px;'> 🟣 Clinician Availability</h1>",
                unsafe_allow_html=True
            )
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                m = build_caregiver_map(client_point)
                st_data = st_folium(m, width=700, height=500)
else:
    st.warning("Please enter Org ID to fetch schedules.")