import os
import json
import requests
import streamlit as st
from flask import Response
from datetime import datetime
import pandas as pd
from config import SchApp,logger
st.set_page_config(page_title="Autoscheduler", page_icon="💁🔍", layout="wide")


# ----------------- Sidebar Navigation -----------------
with st.sidebar:
    st.header("Navigation")
    st.markdown("[Run AutoScheduler](?page=Run_AutoScheduler)")
base_url = SchApp.config()["server"]["base_url"]
endpoint_path = SchApp.config()["endpoint context"]["path"]
base_url = f"{base_url}{endpoint_path}/auto_scheduler?"
st.title("Auto Scheduler")
col1, col2 = st.columns(2)
with col1:
    org_id = st.text_input("Org ID", value="")
    req_st_date = st.date_input("Start Date", value=datetime.today())
    rollover_event_uid = st.text_input("Enter Rollover Event UID", value="6856564c8b11a2e5d0573a73")

with col2:
    location_id = st.text_input("Location ID", value="")
    schedule_source = st.text_input("schedule", value="schedule")
    mode =st.text_input("mode",value="testing")

selected_scenarios = st.multiselect(
    "Select Scenarios to Run:",
    options=["default_scenario", "dist_optimized", "emptype_optimized", "team_optimized"],
    default=["default_scenario"]
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
save_folder = os.path.join(ROOT_DIR, "autoscheduler_data")
os.makedirs(save_folder, exist_ok=True)


params_template = {
    "org_id": org_id,
    "location_id": location_id,
    "req_st_date": req_st_date,
    "schedule_source": schedule_source,
    "rollover_event_uid":rollover_event_uid,
    "mode":mode,
    "scenario": ",".join(selected_scenarios),
}
def json_response(data, status=200):
    return Response(
        response=json.dumps(data, default=str),
        status=status,
        mimetype="application/json"
    )
req_headers = {
        "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwiY3J0Iiwic2NoZWR1bGVyIl0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiIzMjg1NTMiLCJwaWQiOiI2OTAiLCJuYmYiOjE3NTg3MDIxNDYsImV4cCI6MTc1ODcwNTc0NiwiaXNzIjoiaHR0cHM6Ly9wcm9kcWEua2FudGltZWhlYWx0aC5uZXQvaWRlbnRpdHkvdjIifQ.VJSjd-n1iH4Y2qsfBFkoH-Uiz6y0JYKn5aDEAp_OYdZ4p81AL9pLlZSIRYkG-LyG1tMHa_tYoWZDJXa5zXhu8zYzJhIDn5KL2Y9F_ZWGXFkF7CEWH56evDYprc6w06dza10iNUSuOfIDOF7ynDIwT-J0jL4x6oPBqeNmkrcYMteOUO4aQiwJRWObitxOazrmBQxSlVfUPZXjaB6KyvTxGmnstx99Z5AI3zsLNbacqw1mcQM2IXPNiZTln2PGXvDmkVkPAtUPi1IkXM3AGd14yqnMyidnbHK2TOtCRpP28NNg078v9SbDyOcGOmntBg-bPyyfTp2fPxbrce1gnS65gkrcCOHR9UbESMPyUBD971uB19vMminSMNuKzvBMryl6keuMjoNQGs9RKCTGj8nmKXx0fB1wlXvVgeEtadWqFDdP2fsrCZ3YGpuUfDcjSSuJhKrJen0WFEcFJUCFqn6akT8HJ7ffpcwRhsPjYoUH-uYUqH4IDYmrspwLVA25mpUkn2zhaqQExNk1jICqz-mIWQwpLc7ZaKq6JrBMx0_HFBGdB26YyZSlKWMeyIP-xZFUuXIGecPk3XVWa7jXHnMUod3KDzZ7BaF6t0sVoZwlMF_1JdSrwiwXaTHRMW7eWcNck8_LWbV6mWoJEOD8G9M5OuymvM1cOQjQOwukODWAfBo",
        "Cookie": "kt_session_id=c6a1ecfa1c584118bbfe0a69f7a52548"
    }
# --- CORE FUNCTION ---

def run_auto_scheduler(url, params, save_folder):
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            try:
                data = response.json()
                filename = f"{params['scenario']}_org{params['org_id']}_loc{params['location_id']}_{params['req_st_date']}.json"
                save_path = os.path.join(save_folder, filename)
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                st.session_state["last_saved_file"] = filename
                st.session_state["last_saved_params"] = params

            except json.JSONDecodeError:
                st.warning("⚠️ Response is not valid JSON")
                st.text(response.text)
        else:
            st.error(f"❌ API call failed with status code {response.status_code}")
            st.text(response.text)
    except Exception as e:
        st.error(f"💥 Exception occurred: {e}")
if st.button("Run AutoScheduler", type="primary"):
    with st.spinner("⏳ Running AutoScheduler... Please wait."):
        all_success = True
        for scenario in selected_scenarios:
            scenario_params = params_template.copy()
            scenario_params["scenario"] = scenario
            try:
                run_auto_scheduler(base_url, scenario_params, save_folder)
            except Exception as e:
                all_success = False
                st.error(f"❌ Failed for scenario {scenario}: {e}")

    if all_success:
        st.success(f"✅ Successfully processed {len(selected_scenarios)} scenarios!")
    else:
        st.warning("⚠️ Some scenarios failed. Please check logs above.")


