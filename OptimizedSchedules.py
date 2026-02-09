import streamlit as st
import os
import json
import pandas as pd
from flask import Response
from config import SchApp,logger
from folium.plugins import Fullscreen
from folium.features import DivIcon
from streamlit_folium import st_folium
import folium
import requests
import ast
import pickle

def get_lat_lng(location, key):
    try:
        # If location is None or missing key, return None
        if location is None or key not in location:
            return None
        return float(location[key])
    except:
        return None

def build_map(df):
    if df.empty:
        return None

    # Drop rows with missing lat/lng for clients
    df = df.dropna(subset=["client_lat", "client_lng"])

    if df.empty:
        return None  # nothing to show on map

    # Center map at first client
    first_loc = [df.iloc[0]["client_lat"], df.iloc[0]["client_lng"]]
    m = folium.Map(location=first_loc, zoom_start=12)

    # Client markers
    for _, row in df.iterrows():
        if pd.notna(row["client_lat"]) and pd.notna(row["client_lng"]):
            folium.Marker(
                location=[row["client_lat"], row["client_lng"]],
                popup=f"Client: {row.get('client_name', 'N/A')}",
                icon=folium.Icon(color="blue")
            ).add_to(m)

    # Caregiver markers
    for _, row in df.iterrows():
        if pd.notna(row.get("cg_lat")) and pd.notna(row.get("cg_lng")):
            folium.Marker(
                location=[row["cg_lat"], row["cg_lng"]],
                popup=f"Caregiver: {row.get('caregiver_name', 'N/A')}",
                icon=folium.Icon(color="green", icon="user")
            ).add_to(m)

    return m

st.set_page_config(page_title="Autoscheduler", page_icon="💁🔍", layout="wide")
st.markdown(f"<h3 style='text-align: center;'>Review optimized Schedules</h4>",
            unsafe_allow_html=True)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
save_folder = os.path.join(ROOT_DIR, "autoscheduler_data")
os.makedirs(save_folder, exist_ok=True)
req_headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwiY3J0Iiwic2NoZWR1bGVyIl0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiIzMjg1NTMiLCJwaWQiOiI2OTAiLCJuYmYiOjE3NjA2MDkzNTYsImV4cCI6MTc2MDYxMjk1NiwiaXNzIjoiaHR0cHM6Ly9wcm9kcWEua2FudGltZWhlYWx0aC5uZXQvaWRlbnRpdHkvdjIifQ.mJBhuTtOOhoK1RP-KvAdoj3cUrvxoH0Q-y_sp92IsTStRGkHEax7qBbodWqsxrtYtIHM54CzrJfLb4jvbw4xynWfFow8YpCdaxRjxhlF0gjfwMmlm9dV6GCJaC8B0qB4MnAvKciUai-szwBkqoNiBROTB3lLEw26kkDzX39hLfOau_CzYnc2tmgk5cS7FOWbDPJ4K1VFMXQbnXMZT5GZfvBm_mQWImvGQZBjhrbIkVuTBbd1eCBl4d28g7cmAWGlNPX23ukn1vBCXP6V5mEhNVdWqhnFO9GbUMn_2ZJLeLuR5b_BmJqPBV4PqY-EerPbEW7FzKHgKwLL3u0sTVNv-T7OrGunobCyoSIgYU5Vle0hYXvJX1ht4oy6Bwtf1eGVMTjex34-V6J6pcMTUuvbAiGl_SP6XTgV3Xu0NrgCFx1RSdSfL7FW11RvOUvk0QZv5GwW1SKTLTguJdk9dWijd5RqDWayEoMl4zay1GJ7jGBhtkO66no680Xp_Tq1wG-mykeiepZlIzWne-GWM81Jd_8FLTPO8CYeVnw8Y-pCy5Bru8En0-hWOeQXufDv6FGWiurYRCZS4kxNXmv2_UwuufzFsfGUFg_bJrr4858HowNBGh6J4vqpKSu7nz19FoHwb1VKqyc3mnLoEgvujuiEaP3PYN5BW2IqAa5gQXbTFJE",
    "Cookie": "kt_session_id=040df1d888804df28aa02e181d8ab030"
}
files = [f for f in os.listdir(save_folder) if f.endswith(".json")]
def json_response(data, status=200):
    return Response(
        response=json.dumps(data, default=str),
        status=status,
        mimetype="application/json"
    )


if not files:
    st.warning("⚠️ No saved schedules found.")
else:
    st.session_state.setdefault("page", "summary")
    st.session_state.setdefault("schedules_loaded", False)
    if st.session_state["page"] == "summary":

        file_map = {}
        scenarios_dict = {}
        for f in files:
            try:
                name = f.replace(".json", "")
                parts = name.rsplit("_", 3)
                if len(parts) != 4:
                    continue
                scenario, org_part, loc_part, date = parts
                org_id = org_part.replace("org", "")
                loc_id = loc_part.replace("loc", "")
                file_map[(scenario, org_id, loc_id, date)] = f
                if scenario not in scenarios_dict:
                    scenarios_dict[scenario] = {}
                if org_id not in scenarios_dict[scenario]:
                    scenarios_dict[scenario][org_id] = {}
                if loc_id not in scenarios_dict[scenario][org_id]:
                    scenarios_dict[scenario][org_id][loc_id] = []
                scenarios_dict[scenario][org_id][loc_id].append(date)
            except Exception:
                continue
        selected_scenarios = st.multiselect("Scenario", sorted(scenarios_dict.keys()), default=None)
        col1, col2, col3 = st.columns([2, 2, 2])
        valid_orgs = set()
        valid_locs = set()
        valid_dates = set()
        for scenario in selected_scenarios:
            for org in scenarios_dict[scenario]:
                valid_orgs.add(org)
                for loc in scenarios_dict[scenario][org]:
                    valid_locs.add(loc)
                    valid_dates.update(scenarios_dict[scenario][org][loc])
        with col1:
            selected_org = st.selectbox("Org ID", sorted(valid_orgs))
        with col2:
            selected_loc = st.selectbox("Location ID", sorted(valid_locs))
        with col3:
            selected_date = st.selectbox("Date", sorted(valid_dates))
        st.session_state["selected_org"] = selected_org
        st.session_state["selected_loc"] = selected_loc
        st.session_state["selected_date"] = selected_date
        load_clicked = st.button("🔍 Load Summary")
        if load_clicked or "summary_dict" not in st.session_state:
            st.session_state["schedules_loaded"] = True
            summary_dict = {}
            schedules_by_scenario = {}
            for scenario in selected_scenarios:
                fte_pp_cnt = overtime_pp_cnt = prn_pp_cnt = stky_allc_cnt= total_distance = total_schedules = total_schedules_generated = 0
                scenario_schedules = []
                matched_files = [f for f in files if f.startswith(scenario + "_")]
                for f in matched_files:
                    file_path = os.path.join(save_folder, f)
                    with open(file_path, "r", encoding="utf-8") as file:
                        data = json.load(file)
                    if "results" in data and isinstance(data["results"], list):
                        for result in data["results"]:
                            if "rollover_schedules_list" in result:
                                for rollover in result["rollover_schedules_list"]:
                                    if "schedules" in rollover:
                                        scenario_schedules.extend(rollover["schedules"])
                            if "rollover_summary" in result:
                                summary = result["rollover_summary"]
                                total_schedules += summary.get("total_schedules", 0)
                                total_schedules_generated += summary.get("total_schedules_generated", 0)
                                fte_pp_cnt += summary.get("fte_pp_cnt", 0)
                                overtime_pp_cnt += summary.get("overtime_pp_cnt", 0)
                                prn_pp_cnt += summary.get("prn_pp_cnt", 0)
                                stky_allc_cnt +=summary.get("stky_allc_cnt", 0)
                                total_distance += summary.get("total_distance", 0)
                schedules_by_scenario[scenario] = scenario_schedules
                summary_dict[scenario] = {
                    "Total Schedules": total_schedules,
                    "Total Schedules Optimized": total_schedules_generated,
                    "FTE Prod Points Count": int(fte_pp_cnt),
                    "Overtime Prod Points Count": int(overtime_pp_cnt),
                    "Temp Prod Points Count": int(prn_pp_cnt),
                    "Total Sticky Allocations":int(stky_allc_cnt),
                    "Total Distance (km)": float(total_distance)
                }
            st.session_state["summary_dict"] = summary_dict
            st.session_state["schedules_by_scenario"] = schedules_by_scenario
            st.session_state["schedules_loaded"] = True


        if "summary_dict" in st.session_state:
            summary_df = pd.DataFrame(st.session_state["summary_dict"]).T
            summary_df.reset_index(inplace=True)
            summary_df.rename(columns={"index": "Scenario"}, inplace=True)
            st.session_state.setdefault("page", "summary")
            st.session_state.setdefault("schedules_by_scenario", st.session_state.get("schedules_by_scenario", {}))
            if st.session_state["page"] == "summary":
                st.markdown(f"<h4 style='text-align: center;'>Summary</h4>", unsafe_allow_html=True)
                st.markdown("""
                <style>
                div[data-testid="stButton"] > button {
                    background-color: #007BFF;
                    color: white;
                    padding: 4px 10px;
                    font-size: 8px;
                    border-radius: 3px;
                    border: none;
                    cursor: pointer;
                }
                div[data-testid="stButton"] > button:hover {
                    background-color: #0056b3;
                }
                </style>
                """, unsafe_allow_html=True)
                header_cols = st.columns(len(summary_df.columns) + 1)
                for i, col_name in enumerate(summary_df.columns):
                    header_cols[i].markdown(f"**{col_name}**")
                header_cols[-1].markdown("**Action**")
                for _, row in summary_df.iterrows():
                    row_cols = st.columns(len(summary_df.columns) + 1)
                    for i, col_name in enumerate(summary_df.columns):
                        row_cols[i].markdown(str(row[col_name]))
                    if row_cols[-1].button("View Schedules", key=row["Scenario"]):
                        st.session_state["view_scenario"] = row["Scenario"]
                        st.session_state["page"] = "details"
    elif st.session_state["page"] == "details":
        scenario = st.session_state.get("view_scenario")

        st.markdown(
            "<h1 style='text-align: center;'>📖 Autoscheduler</h1>",
            unsafe_allow_html=True
        )
        schedules_by_scenario = st.session_state.get("schedules_by_scenario", {})
        scenario_dfs = {}
        for scenario_name, scn_schedules in schedules_by_scenario.items():
            df = pd.DataFrame(scn_schedules)
            df["scenario"] = scenario_name  # optional: track scenario
            scenario_dfs[scenario_name] = df
        clients_list, client_map, cg_list, cg_map = [], {}, [], {}
        if "selected_org" in st.session_state:
            org = st.session_state["selected_org"]
            loc = st.session_state["selected_loc"]
            date = st.session_state["selected_date"]
            if org and loc:
                cl_file_path ="synth_testdata/690/664c6198b24e9f8127b38fbd_cl_data.bin"
                with open(cl_file_path , 'rb') as f:
                    clients_data = pickle.load(f)
                branch_data = clients_data.get(str(loc), {})
                if 'no_cl' in branch_data.keys():
                    branch_data = {}
                clients_list = list(branch_data.values())  # list of clients for this branch

                client_map = {
                    client["client_uid"]: client["client_address"][0]["geo_location"]
                    for client in clients_list
                    if client.get("client_address") and client["client_address"][0].get("geo_location")
                }

                # cg_response = load_cg_details(org, req_headers)
                cg_file_path ="synth_testdata/690/664c6198b24e9f8127b38fbd_cg_data.bin"
                with open(cg_file_path , 'rb') as f:
                    cg_data = pickle.load(f)
                branchs_data = cg_data.get(str(loc), {})
                if 'no_cg' in branchs_data.keys():
                    branch_data = {}
                cg_list = list(branchs_data.values())
                cg_map = {
                    cg["caregiver_uid"]: cg["caregiver_address"]["geo_location"]
                    for cg in cg_list
                    if cg.get("caregiver_address") and cg["caregiver_address"].get("geo_location")
                }
        scenario_dfs = {}
        all_caregivers = set()  # to collect all unique caregivers across scenarios

        for scenario_name, scn_schedules in schedules_by_scenario.items():
            for sched in scn_schedules:
                client_id = sched.get("clientid")
                cg_id = sched.get("caregiver_id")
                if cg_id in cg_map:
                    sched["cg_location"] = cg_map[cg_id]
                else:
                    sched["cg_location"] = None
                if client_id in client_map:
                    sched["client_location"] = client_map[client_id]
                else:
                    sched["client_location"] = None
            df = pd.DataFrame(scn_schedules)
            df["scenario"] = scenario_name

            if not df.empty:
                df["client_lat"] = df["client_location"].apply(lambda x: get_lat_lng(x, "lat"))
                df["client_lng"] = df["client_location"].apply(lambda x: get_lat_lng(x, "lng"))
                df["cg_lat"] = df["cg_location"].apply(lambda x: get_lat_lng(x, "lat"))
                df["cg_lng"] = df["cg_location"].apply(lambda x: get_lat_lng(x, "lng"))

                # Drop rows with missing coordinates
                df = df.dropna(subset=["client_lat", "client_lng", "cg_lat", "cg_lng"])

            scenario_dfs[scenario_name] = df
            all_caregivers.update(df["caregiver_name"].unique())

        # 2️⃣ Create a single selectbox for all scenarios
        all_caregivers = list(all_caregivers)
        if "selected_cg" not in st.session_state and all_caregivers:
            st.session_state.selected_cg = all_caregivers[0]

        selected_cg = st.selectbox(
            "Select Caregiver to view on map (all scenarios)",
            all_caregivers,
            index=all_caregivers.index(st.session_state.selected_cg),
            key="selected_cg"
        )

        # 3️⃣ Filter each scenario DataFrame by the selected caregiver
        filtered_scenario_dfs = {}
        for scenario_name, df in scenario_dfs.items():
            filtered_df = df[df["caregiver_name"] == selected_cg]
            filtered_scenario_dfs[scenario_name] = filtered_df

        client_color_list = ["red", "orange", "purple", "blue"]

        # Collect all clients across all scenarios
        all_clients = []
        for df in filtered_scenario_dfs.values():
            all_clients.extend(df["client_name"].unique())
        all_clients = list(dict.fromkeys(all_clients))  # remove duplicates while preserving order


        def mask_name(name):
            """Mask clinician name: keep first 3 + last 3 chars visible"""
            if not name or len(name) <= 6:
                return name
            return name[:3] + "*" * (len(name) - 6) + name[-3:]
        # Map each client to a color (cycle through 4 colors)
        client_colors = {client: client_color_list[i % 4] for i, client in enumerate(all_clients)}

        # Create columns for maps
        num_scenarios = len(filtered_scenario_dfs)
        cols = st.columns(num_scenarios)

        for idx, (scenario_name, filtered_df) in enumerate(filtered_scenario_dfs.items()):
            with cols[idx]:
                st.markdown(f"### 🗺️ Scenario: {scenario_name}")
                filtered_df = filtered_df.reset_index(drop=True)
                filtered_df['caregiver_name'] = filtered_df['caregiver_name'].apply(mask_name)
                filtered_df['client_name'] = filtered_df['client_name'].apply(mask_name)

                if not filtered_df.empty:
                    # ---- 🗓️ Visit Date Filter ----
                    unique_dates = sorted(filtered_df["visitdate"].dropna().unique())
                    selected_dates = st.multiselect(
                        f"Select visit date(s) for {scenario_name}:",
                        options=unique_dates,
                        default=unique_dates[:1] if unique_dates else None,
                        key=f"visitdate_{scenario_name}_{idx}"
                    )

                    # Filter based on selected visitdate(s)
                    if selected_dates:
                        filtered_df = filtered_df[filtered_df["visitdate"].isin(selected_dates)]
                    else:
                        st.warning("Please select at least one visit date to display the map.")
                        continue

                    if filtered_df.empty:
                        st.info("No visits found for the selected date(s).")
                        continue

                    # Convert lat/lng to numeric
                    filtered_df["cg_lat"] = pd.to_numeric(filtered_df["cg_lat"], errors="coerce")
                    filtered_df["cg_lng"] = pd.to_numeric(filtered_df["cg_lng"], errors="coerce")
                    filtered_df["client_lat"] = pd.to_numeric(filtered_df["client_lat"], errors="coerce")
                    filtered_df["client_lng"] = pd.to_numeric(filtered_df["client_lng"], errors="coerce")

                    # Center map on average of all points
                    avg_lat = filtered_df[["cg_lat", "client_lat"]].stack().mean()
                    avg_lng = filtered_df[["cg_lng", "client_lng"]].stack().mean()
                    m = folium.Map(location=[avg_lat, avg_lng], zoom_start=9, tiles="cartodb positron")
                    Fullscreen().add_to(m)

                    # Add caregiver marker (blue circular icon)
                    folium.Marker(
                        location=[filtered_df["cg_lat"].iloc[0], filtered_df["cg_lng"].iloc[0]],
                        icon=DivIcon(
                            icon_size=(24, 24),
                            icon_anchor=(12, 12),
                            html="""
                                <div style="
                                    width:26px;height:26px;line-height:26px;
                                    background:blue;color:white;
                                    border-radius:50%;border:1px solid white;
                                    text-align:center;font-size:14px;
                                    box-shadow:0 0 2px rgba(0,0,0,0.4);
                                ">
                                    <i class="fa fa-user"></i>
                                </div>
                            """,
                        ),
                    ).add_to(m)

                    # Add client markers (numbered)
                    for i, (_, row) in enumerate(filtered_df.iterrows(), start=1):
                        folium.Marker(
                            location=[row["client_lat"], row["client_lng"]],
                            popup=f"<b>Client:</b> {row['client_name']}<br><b>Date:</b> {row['visitdate']}<br><b>Service:</b> {row['service_name']}",
                            icon=DivIcon(
                                icon_size=(24, 24),
                                icon_anchor=(12, 12),
                                html=f"""
                                    <div style="
                                        width:26px;height:26px;line-height:26px;
                                        background:brown;color:white;
                                        border-radius:50%;border:1px solid white;
                                        text-align:center;font-size:14px;
                                        box-shadow:0 0 2px rgba(0,0,0,0.4);
                                    ">
                                       {i}
                                    </div>
                                """,
                            ),
                        ).add_to(m)

                        # Draw line caregiver → client
                        folium.PolyLine(
                            locations=[[row["cg_lat"], row["cg_lng"]],
                                       [row["client_lat"], row["client_lng"]]],
                            color="gray", weight=2, opacity=0.5
                        ).add_to(m)


                    # Fit map to bounds
                    bounds = filtered_df.apply(
                        lambda r: [[r["cg_lat"], r["cg_lng"]],
                                   [r["client_lat"], r["client_lng"]]], axis=1
                    ).explode().tolist()
                    m.fit_bounds(bounds)

                    # Display map
                    st_folium(m, width=450, height=450, key=f"map_{scenario_name}_{idx}")
                    filtered_df.rename(columns={'prod_pts': 'Availability'}, inplace=True)
                    # Optional: Show filtered dataframe
                    st.dataframe(filtered_df[[ "caregiver_name","client_name", "Availability","dis","service_name","visitdate"]])

                else:
                    st.info("No visits for this caregiver in this scenario.")

        # if st.button("⬅ Back to Summary"):
        #     st.session_state["page"] = "summary"
        # if schedules:
        #     df = pd.DataFrame(schedules)
        #     df["time_range"] = (
        #             df["starttime"] + " - " + df["endtime"] + " (" + df["dis"] + ")" +
        #             "<br>Dist: " + df["dist"].astype(str) + " km" +
        #             "<br>Duration: " + df["duration"].astype(str) + " hrs"
        #     )
        #     pivot_df = df.pivot_table(
        #         index=["caregiver_name", "client_name"],
        #         columns="visitdate",
        #         values="time_range",
        #         aggfunc="first"
        #     ).reset_index()
        #     pivot_df["caregiver_name"] = pivot_df["caregiver_name"].mask(
        #         pivot_df["caregiver_name"].duplicated(), ""
        #     )
        #     html_table = pivot_df.to_html(index=False, escape=False)
        #     styled_html = f"""
        #     <div style="overflow-x:auto;">
        #         <style>
        #             table {{
        #                 border-collapse: collapse;
        #                 width: 100%;
        #             }}
        #             th, td {{
        #                 border: 1px solid #ddd;
        #                 padding: 8px;
        #                 text-align: left;
        #                 vertical-align: top;
        #             }}
        #             th {{
        #                 background-color: #007BFF;
        #                 color: white;
        #             }}
        #             tr:nth-child(even) {{background-color: #f2f2f2;}}
        #             tr:hover {{background-color: #ddd;}}
        #         </style>
        #         {html_table}
        #     </div>
        #     """
        #     # st.markdown(styled_html, unsafe_allow_html=True)
        #     import folium
        #     from folium.features import DivIcon
        #     from streamlit_folium import st_folium
        #     from folium.plugins import Fullscreen
        #
        #
        #     def safe_float(val):
        #         """Convert val to float if possible, else return None"""
        #         try:
        #             return float(val)
        #         except (TypeError, ValueError):
        #             return None
        #     df=pd.DataFrame(schedules)
        #
        #
        #     def safe_parse(location):
        #         if isinstance(location, dict):
        #             return location  # already parsed
        #         try:
        #             return json.loads(location)  # JSON-like string
        #         except Exception:
        #             try:
        #                 return ast.literal_eval(location)  # Python dict-style string
        #             except Exception:
        #                 return {"lat": None, "lng": None}  # fallback
        #
        #
        #     def get_lat_lng(location, key):
        #         try:
        #             # If location is None or missing key, return None
        #             if location is None or key not in location:
        #                 return None
        #             return float(location[key])
        #         except:
        #             return None
        #
        #
        #     df["client_location"] = df["client_location"].apply(safe_parse)
        #     df["cg_location"] = df["cg_location"].apply(safe_parse)
        #
        #     # Extract numeric lat/lng columns
        #     df["client_lat"] = df["client_location"].apply(lambda x: get_lat_lng(x, "lat"))
        #     df["client_lng"] = df["client_location"].apply(lambda x: get_lat_lng(x, "lng"))
        #     df["cg_lat"] = df["cg_location"].apply(lambda x: get_lat_lng(x, "lat"))
        #     df["cg_lng"] = df["cg_location"].apply(lambda x: get_lat_lng(x, "lng"))
        #     if "selected_cg" not in st.session_state:
        #         st.session_state.selected_cg = df["caregiver_name"].iloc[0]  # default to first caregiver
        #
        #     # Dropdown for selecting caregiver
        #     selected_cg = st.selectbox(
        #         "Select Caregiver to view on map",
        #         df["caregiver_name"].unique(),
        #         index=list(df["caregiver_name"].unique()).index(st.session_state.selected_cg),
        #         key="selected_cg"
        #     )
        #
        #     # Filter DataFrame based on caregiver
        #     filtered_df = df[df["caregiver_name"] == selected_cg]
        #     filtered_df
        #     if not filtered_df.empty:
        #         # Center map on caregiver’s location
        #         cg_lat = filtered_df["cg_lat"].iloc[0]
        #         cg_lng = filtered_df["cg_lng"].iloc[0]
        #         m = folium.Map(location=[cg_lat, cg_lng], zoom_start=11)
        #
        #         # Add caregiver marker
        #         folium.Marker(
        #             [cg_lat, cg_lng],
        #             popup=f"<b>Caregiver:</b> {selected_cg}",
        #             icon=folium.Icon(color="blue", icon="user")
        #         ).add_to(m)
        #
        #         # Add client markers
        #         for _, row in filtered_df.iterrows():
        #             folium.Marker(
        #                 [row["client_lat"], row["client_lng"]],
        #                 popup=(f"<b>Client:</b> {row['client_name']}<br>"
        #                        f"<b>Date:</b> {row['visitdate']}<br>"
        #                        f"<b>Service:</b> {row['service_name']}"),
        #                 icon=folium.Icon(color="green", icon="home")
        #             ).add_to(m)
        #
        #         # Draw lines from caregiver to each client
        #         for _, row in filtered_df.iterrows():
        #             folium.PolyLine(
        #                 locations=[[row["cg_lat"], row["cg_lng"]], [row["client_lat"], row["client_lng"]]],
        #                 color="gray", weight=2, opacity=0.6
        #             ).add_to(m)
        #
        #         # Display map
        #         st_folium(m, width=900, height=600)
        #
        #
        #
        # else:
        #     st.info("No schedules found in the selected file.")
        #
        #




