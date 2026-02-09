import streamlit as st
import logging
import sys
import os

# ------------- Streamlit Page Setup -------------
st.set_page_config(page_title="Agency Branch Selection", page_icon="\U0001F3E2", layout="wide")
st.markdown("# Agency Branch Selection \U0001F3E2")

def get_branch_names(org_id):
    try:
        from common.service_functions import make_service_request
        req_headers = {
            "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QG1qaHMub3JnIiwiYW1yIjpbInB3ZCJdLCJhdWQiOlsiaGgiLCJjZGEiLCJjYm8iLCJzY2hlZHVsZXIiLCJwYXlyb2xsIiwiaGNtIiwibWFhcyIsImF1dGhvcml6YXRpb24iLCJjcnQiXSwiZmlyc3RuYW1lIjoiU3VwcG9ydCIsImxhc3RuYW1lIjoiS2FuVGltZSIsInVpZCI6Ijk3OTg4MiIsInBpZCI6IjYwMDMiLCJ1dHlwZSI6ImFnZW5jeV9zdXBwb3J0X3VzZXIiLCJuYmYiOjE3NTk5NDkxNTIsImV4cCI6MTc1OTk1Mjc1MiwiaXNzIjoiaHR0cHM6Ly9zdGFnaW5nLmthbnRpbWVoZWFsdGgubmV0L2lkZW50aXR5L3YyIn0.MqpQzbeTEFucwFqFOqwXLxCPyIAOBUDGk7hz5XM5V1yke_bO2CKTeiWa0Sx-wuraDYxoiWfSPDr4VKUnVm3bFOU5JGx7XObZDKnAIIUvu4dER35biYP2f89kfWpp4hEtf7QCupbqdhYvswA7lbj2ZWZa90ZP0yNKCYE32f6hG9LywVLn3AcyVZVlDhYLuZtS907yi8JG87sxJ-sBZtqEPlCYiLw2OhA-sGZHqtzxXuT73rGPh_DQ2pzMhU8igJLKDISdY4sPINTWDfS__orwB63s8pM6sU_88pgB-bNSec954HhBmqUgQgWhRk0qtM_2ECTcXyrhp5BK0W8C0_zUkS7aiReCBbzGRYzTsw7wXShEwJ8rY7cWOBwlXjy9lz7O1A3rDW8K9RZsQsQT_uET9GfKh7yUQonErXEwE3f5ly_ekYabx5uOSCu3Ilz2XiZWWrgDvXpAzFZyky5P7fc-um7qc6JUArWOZRg1edRnr9cKWhAqcrFar1YNvR3c1gdDb9uLwzIrKHiYOUdOQj9YJ27cl5URZK821II-sA9SysQl4DhXOd6V8hwVLlT2eK4zDJckgmtwCyz1zSYIc2iGgr0KUhtfaASsDf8BKmWRBEu_l1LHnKVSfCyRBuBaA06mlkv7ajCrm1pqhkr5B3BGgCeTruHriRCXr13h5vEZ74A",
            "Cookie": "kt_session_id=93710e40192e493294199efeed3c4f70"
        }
        payload = {"org_id": org_id}
        response = make_service_request("agency_location_info", req_headers, payload, "json")
        logging.info("agency_location_info: %s", response)
        return response
    except Exception as e:
        errmsg = {
            "error_code": "SERVICE_API_FAIL",
            "error_message": f"agency info C# API Fail: {e}"
        }
        logging.exception("Error while fetching agency info")
        return errmsg

def select_org_id():
    org_dict = {"Pinnacle": 276, "Desire": 690, "Test": 115}
    prev_selection = st.session_state.get("selected_org", {})
    prev_org_id = prev_selection.get("org_id")
    prev_org_name = prev_selection.get("org_name")
    if prev_org_id in org_dict.values():
        default_org = prev_org_name
    else:
        default_org = list(org_dict.keys())[0]
    selected_name = st.selectbox("Select an Org:", list(org_dict.keys()),
                                 index=list(org_dict.keys()).index(default_org),
                                 key="org_selector_page1")
    selected_org = org_dict[selected_name]
    branches = get_branch_names(selected_org)
    if isinstance(branches, list) and branches:
        branch_dict = {b["location_uid"]: b["location_name"] for b in branches}
        prev_branch_uid = prev_selection.get("agency_id")
        if prev_org_id == selected_org and prev_branch_uid in branch_dict:
            default_branch_uid = prev_branch_uid
        else:
            default_branch_uid = list(branch_dict.keys())[0]
        selected_branch_uid = st.selectbox("Select a Branch UID:", list(branch_dict.keys()),
                                           index=list(branch_dict.keys()).index(default_branch_uid),
                                           key="branch_selector")
        selected_branch_name = branch_dict[selected_branch_uid]
        file_name = f"{selected_branch_uid}_cg_data.bin"
        data_folder = os.path.join("synth_testdata", str(selected_org))
        file_path = os.path.join(data_folder, file_name)
        has_data = os.path.exists(file_path)
        st.session_state["selected_org"] = {
            "org_id": selected_org,
            "org_name": selected_name,
            "agency_id": selected_branch_uid,
            "branch_name": selected_branch_name,
            "has_data": has_data
        }
        if has_data:
            st.success(f"✅ Data available for {selected_branch_uid}")
        else:
            st.warning(f"⚠️ No data found for {selected_branch_uid}")
        return st.session_state["selected_org"]
    else:
        st.warning("No branches found for this Org.")
        return None
select_org_id()

