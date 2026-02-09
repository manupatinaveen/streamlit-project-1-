import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta, date
st.set_page_config(page_title="Clinician Availability Data", page_icon="📅",layout="wide")
st.markdown("# Availability for the week 📅")
st.sidebar.header("Availability data")
clinician_ids = st.session_state.get("clinician_ids", [])
from config import SchApp,logger


if "selected_org" in st.session_state:
    selected_org = st.session_state["selected_org"]
    agency_id = selected_org["agency_id"]
    agency = selected_org["org_name"]
    branch = selected_org["branch_name"]
    org_id = str(selected_org["org_id"])
    st.session_state.org_id = org_id
    st.markdown(f"#### {agency} ({branch}) | Using org_id: `{org_id}`")
else:
    st.warning("Please select an agency first on the Agency Selection page.")
    st.stop()


def get_clin_dly_avlblty(clinids, stdt, org_id):
    try:
        from common.service_functions import make_service_request
        payload = {
            "caregiver_uids": clinids,"start_date": datetime.strftime(stdt, "%m/%d/%Y"),"number_of_days": 7,"org_id": org_id
        }
        req_headers = {
            "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwiY3J0Iiwic2NoZWR1bGVyIl0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiIzMjg1NTMiLCJwaWQiOiI2OTAiLCJuYmYiOjE3NTg1Mzg3OTksImV4cCI6MTc1ODU0MjM5OSwiaXNzIjoiaHR0cHM6Ly9wcm9kcWEua2FudGltZWhlYWx0aC5uZXQvaWRlbnRpdHkvdjIifQ.CSiE8rs7n1K2xdscbcp5psMauuEoYuTg-jM8uObYIhG1cTuybJBZP1zo8x-VSm-mfCUuZU32ltL5XpIN9vq318cRUCi7BcKcZ3mccbAbP3tiOycqE7dLfFCejsr8NDjh9nC3ydO52GACF963nKkF2pPYMMJHJ7MxdxaEMWZSlLzP433ClKwQEfPWs670p7snxjFWKKbfyUtO77bQDzD-hfqdNTL0FOc_Ztso1mIPCgUDELIr44eJaLMghCQvLooxislP2QsGEevqKS1FyeCP-l15b7vZ4iSxqFTlb3asfpQlPN4Q-2-uECF5AegKsAvqEltKwth6jKNTrLYRtkpRv2KYTfqW_SsnpWuyd417DiF58-7iAo--1anyhsXR0fMWYgY_KC8-U7crFqllP1-mbEuOYWiVhACiwWGrSa5vrd34PReWLsTtce60t0SB5lYVsxwgT2Dmn_da4r4rRUzPWXsmHSQrBM4piX12Fwvf4llBqL2ggeuKZ9Q9LVu7O3U6kNmJ5uepoMLkZjYkGmqtsV01jdk9HgqhEg0v8RGGleh7w4UirlnYRnDkZeQZih1KSgZCQIic3Sqb8l-XpeHshykfcyop0At0jPD2OGW7PqGVZlgpXIsbixVAcXaJq63ou4lJzsmkjUi-6lCB8w562_iB6vSvE4Wj6cD6xLqUQ_U",
            "Cookie": "kt_session_id=b70db0c71e2f422d8a5614499528247e"
        }
        response = make_service_request("int_cg_availability_daily", req_headers, payload, "json")
        return response
    except Exception as e:
        logger.info(e)
        errmsg = {
            "error_code": "SERVICE_API_FAIL",
            "error_message": "Daily availability C# API Fail: " + str(e)
        }
        return errmsg
req_st_date = st.date_input("Select Start Date",)
cg_availability = get_clin_dly_avlblty(clinician_ids, req_st_date, org_id)

def get_clin_weekly_avlblty(cglist, start_date,org_id, num_weeks=1):
    from common.service_functions import make_service_request
    req_headers = {
        "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ2NzhGOTY3RUQyQTQwOEYwMzUwNUEwM0M5OUFDRTcyMUE2QTQwMTUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJzdXBwb3J0QGRlc2lyZWhvbWVjYXJlLmNvbSIsImFtciI6WyJwd2QiXSwiYXVkIjpbImhoIiwiY3J0Iiwic2NoZWR1bGVyIl0sImZpcnN0bmFtZSI6IlN1cHBvcnQiLCJsYXN0bmFtZSI6IkthblRpbWUiLCJ1aWQiOiIzMjg1NTMiLCJwaWQiOiI2OTAiLCJuYmYiOjE3NTg1Mzg3OTksImV4cCI6MTc1ODU0MjM5OSwiaXNzIjoiaHR0cHM6Ly9wcm9kcWEua2FudGltZWhlYWx0aC5uZXQvaWRlbnRpdHkvdjIifQ.CSiE8rs7n1K2xdscbcp5psMauuEoYuTg-jM8uObYIhG1cTuybJBZP1zo8x-VSm-mfCUuZU32ltL5XpIN9vq318cRUCi7BcKcZ3mccbAbP3tiOycqE7dLfFCejsr8NDjh9nC3ydO52GACF963nKkF2pPYMMJHJ7MxdxaEMWZSlLzP433ClKwQEfPWs670p7snxjFWKKbfyUtO77bQDzD-hfqdNTL0FOc_Ztso1mIPCgUDELIr44eJaLMghCQvLooxislP2QsGEevqKS1FyeCP-l15b7vZ4iSxqFTlb3asfpQlPN4Q-2-uECF5AegKsAvqEltKwth6jKNTrLYRtkpRv2KYTfqW_SsnpWuyd417DiF58-7iAo--1anyhsXR0fMWYgY_KC8-U7crFqllP1-mbEuOYWiVhACiwWGrSa5vrd34PReWLsTtce60t0SB5lYVsxwgT2Dmn_da4r4rRUzPWXsmHSQrBM4piX12Fwvf4llBqL2ggeuKZ9Q9LVu7O3U6kNmJ5uepoMLkZjYkGmqtsV01jdk9HgqhEg0v8RGGleh7w4UirlnYRnDkZeQZih1KSgZCQIic3Sqb8l-XpeHshykfcyop0At0jPD2OGW7PqGVZlgpXIsbixVAcXaJq63ou4lJzsmkjUi-6lCB8w562_iB6vSvE4Wj6cD6xLqUQ_U",
        "Cookie": "kt_session_id=b70db0c71e2f422d8a5614499528247e"
    }
    payload = {"caregiver_uids": cglist, "week_start": datetime.strftime(start_date, "%m/%d/%Y"),
               "number_of_weeks": num_weeks}
    response_json = make_service_request("cg_availability_weekly", req_headers, payload, "json")
    return response_json
cg_availability_weekly = get_clin_weekly_avlblty(clinician_ids, req_st_date, org_id,num_weeks=1)

avlblty_df = pd.json_normalize(cg_availability_weekly, record_path='available_weeks', \
                meta = ['caregiver_uid', 'caregiver_name', 'caregiver_discipline', 'caseload'], errors = "ignore")
avlblty_df.columns = ['Week No', 'Start', 'Avl Hours', 'Avl Prod Pts', 'Alloc Hours', 'Alloc Prod Pts', 'Id', 'Name', 'Discipline', 'Caseload']
disp_avlblty_df = avlblty_df[['Name', 'Discipline', 'Caseload', 'Week No', 'Start', 'Avl Hours', 'Avl Prod Pts', 'Alloc Hours', 'Alloc Prod Pts']]
avlblty_data = []
for cgrec in cg_availability :
    strtdt = cgrec['availability_info'][0]['date']
    ts = pd.Timestamp(strtdt)
    wk = ts.week
    avlhrs = sum([rec['available_hours'] + rec['allocated_hours'] for rec in cgrec['availability_info']])
    avlpp = sum([rec['available_productivity_points'] + rec['allocated_productivity_points'] \
                         for rec in cgrec['availability_info']])
    avlrec = [cgrec['caregiver_name'], cgrec['caregiver_discipline'], cgrec['caseload'], wk, strtdt, avlhrs, avlpp, 0, 0]
    avlblty_data.append(avlrec)
cols = ['Name', 'Discipline', 'Caseload', 'Week No', 'Start', 'Avl Hours', 'Avl Prod Pts', 'Alloc Hours', 'Alloc Prod Pts']
disp_avlblty_df = pd.DataFrame(avlblty_data, columns = cols)
disp_avlblty_df
st.subheader('Availability by Discipline')
avlblty_by_dis_df = disp_avlblty_df.groupby('Discipline')['Avl Hours'].sum()
st.bar_chart(avlblty_by_dis_df)

