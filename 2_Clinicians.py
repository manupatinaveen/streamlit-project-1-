import streamlit as st
import pandas as pd
import json
import pickle
import os
st.set_page_config(page_title="Clinician Data", page_icon="💁",layout="wide")
st.markdown("# Clinicians 💁")
st.sidebar.header("Clinician data")

if "selected_org" in st.session_state:
    selected_org = st.session_state["selected_org"]
    agency_id = selected_org["agency_id"]
    agency = selected_org["org_name"]
    branch = selected_org["branch_name"]
    org_id = str(selected_org["org_id"])
    st.session_state.org_id = org_id
    st.markdown(f"#### {agency} ({branch}) | Using org_id: `{org_id}`")
    DATA_DIR = os.getenv("DATA_DIR", "synth_testdata")
    base_path = os.path.join(DATA_DIR, org_id)
    file_path = os.path.join(base_path, f"{agency_id}_cg_data.bin")
else:
    st.warning("Please select an agency first on the Agency Selection page.")
    st.stop()

clinician_keys = ["id", "name", "discipline", "lat", "lng", "type", "teamid", "branchid", "zip"]
try:
    with open(file_path, 'rb') as f:
        cg_data = pickle.load(f)
except FileNotFoundError:
    st.error(f"Data not found for this location  {agency_id}.")
    st.stop()
if agency_id in cg_data:
    clinician_data = cg_data[agency_id]
else:
    st.error(f"No client data found for agency ID: {agency_id}")
    st.stop()


clinicians={}

def load_clinicians(data):
    for rec in data:
        clin_id = rec
        name = "{} {}".format(data[rec]['first_name'], data[rec]['last_name'])
        dis, emp_type = data[rec]['primary_discipline'], data[rec]['employee_type']
        lat = data[rec]['caregiver_address']['geo_location']['lat']
        lng = data[rec]['caregiver_address']['geo_location']['lng']
        zipcode, pr_branch = data[rec]['caregiver_address']['zip'], data[rec]['payroll_branch_uid']
        branches = [loc['location_uid'] for loc in data[rec]['locations']]
        team = data[rec]['team_uid'] if data[rec]['team_uid'] is not None else None
        teamname = data[rec]['team_name']
        teamdata = [team, teamname, pr_branch, None, zipcode]
        clinicians[clin_id] = dict(
            zip(
                clinician_keys,
                [clin_id, name, dis, lat, lng, emp_type, team, branches, zipcode]
            )
        )

load_clinicians(clinician_data)
clinician_ids = list(clinicians.keys())
st.session_state["clinician_ids"] = clinician_ids
cg_df = pd.DataFrame(clinicians.values())
cg_df