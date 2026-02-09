import streamlit as st
import pandas as pd
import pickle
import os
# Page config
st.set_page_config(page_title="Client Data", page_icon="🧓", layout="wide")
st.markdown("# Active Clients 🧓")
st.sidebar.header("Client data")

# Load data dynamically based on selected agency_id
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
    file_path = os.path.join(base_path, f"{agency_id}_cl_data.bin")
else:
    st.warning("Please select an agency first on the Agency Selection page.")
    st.stop()

client_keys = ["client_uid", "Name", "Latitude", "Longitude", "Team"]

try:
    with open(file_path, 'rb') as f:
        cl_data = pickle.load(f)
except FileNotFoundError:
    st.error(f"Data not found for this location  {agency_id}.")
    st.stop()

if agency_id in cl_data:
    clients_data = cl_data[agency_id]
else:
    st.error(f"No client data found for agency ID: {agency_id}")
    st.stop()

clients = {}
col1, col2, col3 = st.columns([2, 2, 3])


def load_clients(cl_data):
    for rec in cl_data:
        name = f"{cl_data[rec]['first_name']} {cl_data[rec]['last_name']}"
        try:
            lat = cl_data[rec]['client_address'][0]['geo_location']['lat']
            lng = cl_data[rec]['client_address'][0]['geo_location']['lng']
            if lat is None or lng is None:
                continue
            team = cl_data[rec]['team_name']
            clients1 = {ky: val for (ky, val) in zip(client_keys, [rec, name, lat, lng, team])}
            clients[rec] = clients1
        except (IndexError, KeyError, TypeError):
            continue


load_clients(clients_data)
client_df = pd.DataFrame(clients.values())
for col in client_df.columns:
    types = client_df[col].apply(type).unique()
    if any(t == zip for t in types):
        st.error(f"Column '{col}' contains raw `zip` objects! Converting...")
        client_df[col] = client_df[col].apply(lambda x: list(x) if isinstance(x, zip) else x)
st.dataframe(client_df, use_container_width=True)
