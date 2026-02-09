import os
import json
import requests
import streamlit as st
from flask import Response
from datetime import datetime
import pandas as pd
from config import SchApp,logger
st.set_page_config(page_title="Open Visit Allocation", page_icon="💁🔍", layout="wide")
base_url = SchApp.config()["server"]["base_url"]
endpoint_path = SchApp.config()["endpoint context"]["path"]
base_url = f"{base_url}{endpoint_path}/generate_open_visit_schedules?"
print("base_url",base_url)
st.title("Open Visit Scheduler")
col1, col2 = st.columns(2)
with col1:
    org_id = st.text_input("Org ID", value="")
    req_st_date = st.date_input("Start Date", value=datetime.today())

with col2:
    location_id = st.text_input("Location ID", value="")
    req_end_date = st.date_input("End Date")

selected_scenario = st.selectbox(
    "Select Scenario to Run:",
    options=["default_scenario", "dist_optimized", "emptype_optimized", "team_optimized"],
    index=0
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
save_folder = os.path.join(ROOT_DIR, "open_visit_data")
os.makedirs(save_folder, exist_ok=True)


params_template = {
    "org_id": org_id,
    "location_id": location_id,
    "stdt": req_st_date.strftime("%m-%d-%Y"),
    "endt": req_end_date.strftime("%m-%d-%Y"),
    "scenario": selected_scenario,
}
def json_response(data, status=200):
    return Response(
        response=json.dumps(data, default=str),
        status=status,
        mimetype="application/json"
    )
req_headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwic2NoZWR1bGVyIiwiY3J0Il0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiI0Mjc4MDciLCJwaWQiOiI2OTAiLCJpY29kZSI6IlN0YWdpbmciLCJ1dHlwZSI6ImFnZW5jeV9zdXBwb3J0X3VzZXIiLCJuYmYiOjE3NjU1MzI3NTEsImV4cCI6MTc2NTUzNjM1MSwiaXNzIjoiaHR0cHM6Ly9zdGFnaW5nLmthbnRpbWVoZWFsdGgubmV0L2lkZW50aXR5L3YyIn0.ssRdnjHr3DqF1E3Uo_K1rr-TF-IiZTLHIwxxcJFloWGI-Q8E0k_mt2wOn4yukjTahf4VBTM6C-buif-fFiFTcgqruz3iYzhnjxb24w92HQ7dLNQ9NhYKmOUnXH_7MOM0l7-oiBDMSH7vVUO1e6sp4qmd769blDnHwq2tHBA7EZN8WcB0-iVxaZyCb0KulDr7iaHDf7kPXiq16lmJ6pp_5yvWGh2oKLd2CbCzyqh5Vc_xmDh8VWmj839N5VFe_6UChEL58M6uPRyH7N8300LQXarsGoWL5epSHbq9TekcAUfu58b-BJX3z3vfvV19OZtW5ZqGI2S1xi1qM-VjY6hq_iy3luFyPKxH-EBD9wLfA2ubjOqp_B5Q4f5W5ZAQuDmhhPrgPYxQlnVjV2zTkNUq3jBvZQzrjU0cnCdl7nPMUmhMZF-F8fnF8JhctEWSP00kDQF-9jPGpkboD612h_5N7kM1xV7tpkCH8k72_c24Rar172HNhlfi-020q8cjK3p7rf4ktPS-jtKHP111jKVlSDso3Uyyz89ayMFSpxeCLmAeeUr7cLCDQ8glpTfaHtztHRunRka-injrU3AraLqRqQAPg10c5jkqetJd1h_uDpKTUm4OyyOv859UsDC9N9cAOLslMjybuhrOXH_VHH35Di3woA38j8yzpHuHcC3HYyY",
    "Cookie": "kt_session_id=354aade0a4c84b88a7dc97d921b383cd"
}
# --- CORE FUNCTION ---
def load_client_details(org_id,location_id,req_headers):
    from common.service_functions import make_service_request
    try:
        payload= {
            'page_no': 1,'page_size': 40000,'org_id': org_id,'client_locations': [location_id],'client_status': ['active', 'end_of_episode', 'on_hold', 'pending_soc', 'transferred', 'discharge_pending']
        }
        response_json = make_service_request("total_cl_lst", req_headers, payload, "json")
        if not response_json or 'items_list' not in response_json or not response_json['items_list']:
            errmsg = {
                "error_code": "DATA_NOT_AVAILABLE",
                "error_message": f"Data is not available "
            }
            return json_response(errmsg, status=400)
        response = response_json['items_list']
        return response
    except Exception as e:
        logger.exception("Error occurred while fetching client data")
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
clients_list, client_map, cg_list, cg_map = [], {}, [], {}

if org_id and location_id:
    clients_response = load_client_details(org_id, location_id, req_headers)

    # If it's a Flask Response → error case
    if isinstance(clients_response, Response):
        st.error("❌ Failed to load client details.")
        clients_list = []

    # If it's a dict with an items_list field
    elif isinstance(clients_response, dict) and "items_list" in clients_response:
        clients_list = clients_response["items_list"]

    # If it's already a list
    elif isinstance(clients_response, list):
        clients_list = clients_response

    # Unknown structure → print debug, but avoid crash
    else:
        st.warning("⚠️ Unexpected client response format")
        st.write(clients_response)
        clients_list = []

    # Build map
    client_map = {
        client["client_uid"]: f"{client['first_name']} {client['last_name']}"
        for client in clients_list
        if "client_uid" in client
    }

if org_id:
    cg_response = load_cg_details(org_id, req_headers)
    cg_list = cg_response.get("items_list", cg_response) if isinstance(cg_response, dict) else cg_response
    cg_map = {
        cg["caregiver_uid"]: f"{cg['first_name']} {cg['last_name']}"
        for cg in cg_list
    }
def run_open_visit_scheduler(url, params, save_folder):
    try:
        response = requests.post(url, params=params)
        if response.status_code == 200:
            try:
                data = response.json()
                if "open_visit_schedules" in data:
                    rows = []
                    for visit in data["open_visit_schedules"]:
                        client_uid = visit.get("clientid")
                        if client_uid in client_map:
                            visit["client_name"] = client_map[client_uid]
                        for clinician in visit.get("clinicians", []):
                            cg_uid = clinician.get("clinicianid")
                            if cg_uid in cg_map:
                                clinician["caregiver_name"] = cg_map[cg_uid]
                            else:
                                clinician["caregiver_name"] = "Unknown Caregiver"
                filename = f"{params['scenario']}_org{params['org_id']}_loc{params['location_id']}_{params['stdt']}.json"
                save_path = os.path.join(save_folder, filename)
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                st.session_state["last_saved_file"] = filename
                st.session_state["last_saved_params"] = params
                st.success(
                    f"✅ Response saved to `{filename}`\n\n"
                    f"👉 [Review the open visit schedules](OpenVisitReview)"
                )
            except json.JSONDecodeError:
                st.warning("⚠️ Response is not valid JSON")
                st.text(response.text)
        else:
            st.error(f"❌ API call failed with status code {response.status_code}")
            st.text(response.text)
    except Exception as e:
        st.error(f"💥 Exception occurred: {e}")
if st.button("Run Open Visit Scheduler", type="primary"):
    with st.spinner("⏳ Running Open Visit Scheduler... Please wait."):
        run_open_visit_scheduler(base_url, params_template, save_folder)