import streamlit as st
import pandas as pd
import json
import os
st.set_page_config(page_title="Local Cache", page_icon="🖥️",layout="wide")
st.markdown("# Local Cache 🖥️")
st.sidebar.header("Cache Data")

@st.cache_data(show_spinner="Loading clients data...")
def load_clients(path):
    client_df = pd.read_pickle(file_path)
    first_key = list(client_df.keys())[0]
    data = client_df[first_key]
    df = pd.DataFrame.from_dict(data, orient='index')
    return df

@st.cache_data(show_spinner="Loading clinicians data...")
def load_clinicians(path):
    clinician_df = pd.read_pickle(file_path)
    first_key= list(clinician_df.keys())[0]
    data = clinician_df[first_key]
    df = pd.DataFrame.from_dict(data, orient="index")
    return df

@st.cache_data(show_spinner="Loading external clinicians data...")
def load_extl_clinicians(path):
    ext_clinician_df = pd.read_pickle(file_path)
    return ext_clinician_df

@st.cache_data(show_spinner="Loading distance matrix...")
def load_dist_matrix(path, opt):
    file_name_dict = {
        'client-client dist': 'google_cl_cl_matrix.bin',
        'clinician-client dist': 'google_cg_cl_matrix.bin',
        'client-client time': 'google_cl_cl_time_matrix.bin',
        'clinician-client time': 'google_cg_cl_time_matrix.bin'
    }
    fname = file_name_dict[opt]
    dist_matrix_df = pd.read_pickle(file_path)
    return dist_matrix_df

option = st.selectbox(
    "Select a data type: ",
    ("clients", "clinicians", "extl_clinicians", "distance_matrix")
)
if 'selected_org' in st.session_state :
    selected_org = st.session_state["selected_org"]
    agency_id = selected_org["agency_id"]   
    agency = selected_org["org_name"]       
    branch = selected_org["branch_name"]    
    org_id = str(selected_org["org_id"])
    st.markdown(f"#### {agency} ({branch}) | Using org_id: `{org_id}`")
    # path = fr'C:\Users\Podili.Aparna\Downloads\Kast\synth_testdata\\{org_id}\\{agency_id}_'
    # file_path = fr"{path}\{agency_id}_cg_data.bin"
    DATA_DIR = os.getenv("DATA_DIR","synth_testdata")
    base_path=os.path.join(DATA_DIR,org_id)
    file_path = os.path.join(base_path, f"{agency_id}_cg_data.bin")
    print("filepath",file_path)


else:
    st.warning("Please select an agency first on the Agency Selection page.")
    st.stop()
# path = r'C:\Users\Podili.Aparna\Downloads\Kast\synth_testdata\276\6564a5d6ef36a753481f6b3d_'

if 'agency' in st.session_state:
    st.markdown(f"#### {st.session_state.agency} - {option} data")

if option == 'clients':
    file_path = os.path.join(base_path, f"{agency_id}_cl_data.bin")
    df = load_clients(file_path)
elif option == 'clinicians':
    file_path = os.path.join(base_path, f"{agency_id}_cg_data.bin")
    df = load_clinicians(file_path)
elif option == 'extl_clinicians':
    file_path = os.path.join(base_path, f"{agency_id}_ext_cg_id.bin")
    df = load_extl_clinicians(file_path)
elif option == 'distance_matrix':
    selected_matrix = st.selectbox("Select matrix type", [
        'client-client dist',
        'clinician-client dist',
        'client-client time',
        'clinician-client time'
    ])
    df = load_dist_matrix(base_path + "/", selected_matrix)
st.dataframe(df, use_container_width=True)
