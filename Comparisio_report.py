import streamlit as st
import pandas as pd
import numpy as np
import json
import altair as alt

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Raw vs Optimized Schedules",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("<h1 style='text-align:center'>📊 Comparing Raw & Optimized Schedules</h1>", unsafe_allow_html=True)
st.sidebar.header("Filters")

# -------------------- LOAD DATA --------------------
with open(r'C:\Users\Podili.Aparna\Desktop\open_visit_api\raw_schedules_response.json', 'rb') as f1:
    raw_data = json.load(f1)

with open(r'C:\Users\Podili.Aparna\Desktop\New folder\autoscheduler_response_690.json', 'rb') as f2:
    optimized_data = json.load(f2)

raw_df = pd.json_normalize(raw_data, record_path='items_list')
optimized_df = pd.json_normalize(optimized_data, record_path=['results', 'rollover_schedules_list', 'schedules'])

# -------------------- DATE CONVERSION --------------------
raw_df['planned_date'] = pd.to_datetime(raw_df['planned_date'])
optimized_df['visitdate'] = pd.to_datetime(optimized_df['visitdate'])

# Optional: Filter by date
end_date = "2025-12-29"
raw_df = raw_df[raw_df['planned_date'] <= end_date]
optimized_df = optimized_df[optimized_df['visitdate'] <= end_date]

# -------------------- METRICS --------------------
total_raw = len(raw_df)
total_opt = len(optimized_df)
change_pct = ((total_opt - total_raw) / total_raw * 100) if total_raw > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Raw Visits", total_raw)
col2.metric("Total Optimized Visits", total_opt)
col3.metric("Change (%)", f"{change_pct:.2f}%", delta_color="normal" if change_pct >= 0 else "inverse")

st.markdown("---")

# -------------------- HEATMAPS --------------------
st.markdown("### 📅 Calendar Heatmaps")

col1, col2 = st.columns(2)

weekday_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

with col1:
    st.markdown("#### Raw Visits")
    raw_heat = raw_df.groupby('planned_date').size().reset_index(name='visits')
    raw_heat['day'] = raw_heat['planned_date'].dt.day
    raw_heat['weekday'] = pd.Categorical(raw_heat['planned_date'].dt.day_name().str[:3],
                                         categories=weekday_order, ordered=True)

    chart_raw = alt.Chart(raw_heat).mark_rect().encode(
        x=alt.X('day:O', title='Day of Month'),
        y=alt.Y('weekday:O', title='Weekday'),
        color=alt.Color('visits:Q', scale=alt.Scale(scheme='greens')),
        tooltip=['planned_date:T', 'visits:Q']
    ).properties(height=300)

    st.altair_chart(chart_raw, use_container_width=True)

with col2:
    st.markdown("#### Optimized Visits")
    opt_heat = optimized_df.groupby('visitdate').size().reset_index(name='visits')
    opt_heat['day'] = opt_heat['visitdate'].dt.day
    opt_heat['weekday'] = pd.Categorical(opt_heat['visitdate'].dt.day_name().str[:3],
                                         categories=weekday_order, ordered=True)

    chart_opt = alt.Chart(opt_heat).mark_rect().encode(
        x=alt.X('day:O', title='Day of Month'),
        y=alt.Y('weekday:O', title='Weekday'),
        color=alt.Color('visits:Q', scale=alt.Scale(scheme='blues')),
        tooltip=['visitdate:T', 'visits:Q']
    ).properties(height=300)

    st.altair_chart(chart_opt, use_container_width=True)



# -------------------- SERVICE BAR CHARTS --------------------
st.markdown("### 🏷 Visits by Service")
col1, col2 = st.columns(2)

with col1:
    raw_service = raw_df.groupby('service_name').size().reset_index(name='visits')
    chart_raw_service = alt.Chart(raw_service).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X('service_name:N', title='Service'),
        y=alt.Y('visits:Q', title='Visits'),
        color=alt.Color('service_name:N', legend=None),
        tooltip=['service_name:N', 'visits:Q']
    )
    text = chart_raw_service.mark_text(dy=-10, fontSize=12).encode(text='visits:Q')
    st.altair_chart(chart_raw_service + text, use_container_width=True)

with col2:
    opt_service = optimized_df.groupby('service_name').size().reset_index(name='visits')
    chart_opt_service = alt.Chart(opt_service).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X('service_name:N', title='Service'),
        y=alt.Y('visits:Q', title='Visits'),
        color=alt.Color('service_name:N', legend=None),
        tooltip=['service_name:N', 'visits:Q']
    )
    text = chart_opt_service.mark_text(dy=-10, fontSize=12).encode(text='visits:Q')
    st.altair_chart(chart_opt_service + text, use_container_width=True)

# -------------------- DISCIPLINE BAR CHARTS --------------------
st.markdown("### 🧾 Visits by Discipline")
col1, col2 = st.columns(2)

with col1:
    raw_disc = raw_df.groupby('discipline').size().reset_index(name='visits')
    chart_raw_disc = alt.Chart(raw_disc).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X('discipline:N', title='Discipline'),
        y=alt.Y('visits:Q', title='Visits'),
        color=alt.Color('discipline:N', legend=None),
        tooltip=['discipline:N', 'visits:Q']
    )
    text = chart_raw_disc.mark_text(dy=-10, fontSize=12).encode(text='visits:Q')
    st.altair_chart(chart_raw_disc + text, use_container_width=True)

with col2:
    opt_disc = optimized_df.groupby('dis').size().reset_index(name='visits')
    chart_opt_disc = alt.Chart(opt_disc).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X('dis:N', title='Discipline'),
        y=alt.Y('visits:Q', title='Visits'),
        color=alt.Color('dis:N', legend=None),
        tooltip=['dis:N', 'visits:Q']
    )
    text = chart_opt_disc.mark_text(dy=-10, fontSize=12).encode(text='visits:Q')
    st.altair_chart(chart_opt_disc + text, use_container_width=True)

st.markdown("---")
st.markdown("✅ Dashboard by Aparna Podili")
