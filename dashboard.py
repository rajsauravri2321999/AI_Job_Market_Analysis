import streamlit as st
import pandas as pd
import plotly.express as px

# Setting page config
st.set_page_config(page_title="AI Job Market Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    # Reads the dataset from the same directory
    df = pd.read_csv("AI Job Market Analysis.csv")
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Dataset 'AI Job Market Analysis.csv' not found. Please ensure it's in the same directory.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# 1. Year Slider
min_year = int(df['job_posting_year'].min())
max_year = int(df['job_posting_year'].max())
selected_years = st.sidebar.slider("Select Year Range", min_year, max_year, (min_year, max_year))

# 2. Country Dropdown
countries = sorted(df['country'].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect("Select Country", options=countries)

# 3. Job Readiness Level Dropdown
readiness_levels = sorted(df['job_readiness_level'].dropna().unique().tolist())
selected_readiness = st.sidebar.multiselect("Select Job Readiness Level", options=readiness_levels)

# 4. Education Level Dropdown
education_levels = sorted(df['education_level'].dropna().unique().tolist())
selected_education = st.sidebar.multiselect("Select Education Level", options=education_levels)

# --- Apply Filters ---
filtered_df = df[
    (df['job_posting_year'] >= selected_years[0]) &
    (df['job_posting_year'] <= selected_years[1])
]

if selected_countries:
    filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]
if selected_readiness:
    filtered_df = filtered_df[filtered_df['job_readiness_level'].isin(selected_readiness)]
if selected_education:
    filtered_df = filtered_df[filtered_df['education_level'].isin(selected_education)]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()


# --- KPIs ---
st.title("AI Job Market Analysis Dashboard")

# Apply the same categorical filters
def apply_cats(d):
    res = d.copy()
    if selected_countries:
        res = res[res['country'].isin(selected_countries)]
    if selected_readiness:
        res = res[res['job_readiness_level'].isin(selected_readiness)]
    if selected_education:
        res = res[res['education_level'].isin(selected_education)]
    return res

# Calculate equivalent previous period for accurate deltas
start_year, end_year = selected_years

if start_year == end_year:
    baseline_year = start_year - 1
else:
    baseline_year = start_year

df_end = df[df['job_posting_year'] == end_year]
df_baseline = df[df['job_posting_year'] == baseline_year]

df_end = apply_cats(df_end)
df_baseline = apply_cats(df_baseline)

# KPI 1: Total Job openings
curr_openings = filtered_df['job_openings'].sum()
end_year_openings = df_end['job_openings'].sum()
baseline_openings = df_baseline['job_openings'].sum()
openings_delta = ((end_year_openings - baseline_openings) / baseline_openings * 100) if baseline_openings > 0 else 0

# KPI 2: Average Salary
curr_salary = filtered_df['salary'].mean()
end_year_salary = df_end['salary'].mean()
baseline_salary = df_baseline['salary'].mean()
if pd.isna(curr_salary): curr_salary = 0
if pd.isna(end_year_salary): end_year_salary = 0
if pd.isna(baseline_salary): baseline_salary = 0
salary_delta = ((end_year_salary - baseline_salary) / baseline_salary * 100) if baseline_salary > 0 else 0

# KPI 3: Remote Opportunity Index
curr_remote = filtered_df[filtered_df['remote_type'] == 'Remote']['job_openings'].sum()
end_year_remote = df_end[df_end['remote_type'] == 'Remote']['job_openings'].sum()
baseline_remote = df_baseline[df_baseline['remote_type'] == 'Remote']['job_openings'].sum()
remote_delta = ((end_year_remote - baseline_remote) / baseline_remote * 100) if baseline_remote > 0 else 0

# KPI 4: Hiring Urgency
# We are displaying "High Urgency" jobs as the primary urgency indicator.
curr_high_urgency = filtered_df[filtered_df['hiring_urgency'] == 'High']['job_openings'].sum()
end_year_urgency = df_end[df_end['hiring_urgency'] == 'High']['job_openings'].sum()
baseline_urgency = df_baseline[df_baseline['hiring_urgency'] == 'High']['job_openings'].sum()
urgency_delta = ((end_year_urgency - baseline_urgency) / baseline_urgency * 100) if baseline_urgency > 0 else 0

st.markdown(f"Metrics reflect the **total for the selected period**, with deltas showing the % change from **{baseline_year}** to **{end_year}**:")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Job Openings", f"{curr_openings:,}", f"{openings_delta:.1f}%")

with col2:
    st.metric("Average Salary", f"${curr_salary:,.0f}", f"{salary_delta:.1f}%")

with col3:
    st.metric("Remote Openings", f"{curr_remote:,}", f"{remote_delta:.1f}%")

with col4:
    st.metric("High Urgency Openings", f"{curr_high_urgency:,}", f"{urgency_delta:.1f}%")

st.markdown("---")


# --- Graphs ---

col_g1, col_g2 = st.columns(2)

# 1. Line chart: Showing yearly trend of total job openings
with col_g1:
    st.subheader("Yearly Trend of Total Job Openings")
    trend_df = filtered_df.groupby('job_posting_year', as_index=False)['job_openings'].sum()
    
    # We create the line chart 
    fig_line = px.line(trend_df, x='job_posting_year', y='job_openings', markers=True)
    fig_line.update_layout(xaxis=dict(tickmode='linear', dtick=1), xaxis_title="Year", yaxis_title="Total Openings")
    st.plotly_chart(fig_line, use_container_width=True)

# 2. Column chart: company_industry wise job openings
with col_g2:
    st.subheader("Job Openings by Industry")
    industry_df = filtered_df.groupby('company_industry', as_index=False)['job_openings'].sum().sort_values(by='job_openings', ascending=False)
    fig_col = px.bar(industry_df, x='company_industry', y='job_openings')
    fig_col.update_layout(xaxis_title="Industry", yaxis_title="Total Openings")
    st.plotly_chart(fig_col, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True) # Adding a bit spacing

col_g3, col_g4 = st.columns(2)

# 3. Donut chart: showing distribution of remote type job openings
with col_g3:
    st.subheader("Distribution of Remote Type Job Openings")
    remote_df = filtered_df.groupby('remote_type', as_index=False)['job_openings'].sum()
    fig_donut = px.pie(remote_df, names='remote_type', values='job_openings', hole=0.5)
    st.plotly_chart(fig_donut, use_container_width=True)

# 4. Column stacked chart: Showing % of job titles company size wise
with col_g4:
    st.subheader("% of Job Titles by Company Size")
    size_title_df = filtered_df.groupby(['company_size', 'job_title'], as_index=False)['job_openings'].sum()
    fig_stacked = px.bar(size_title_df, x='company_size', y='job_openings', color='job_title', barmode='relative')
    # Using 'percent' normalizes to 100%
    fig_stacked.update_layout(barnorm='percent', yaxis_title="Percentage (%)", xaxis_title="Company Size")
    st.plotly_chart(fig_stacked, use_container_width=True)


st.markdown("---")

# 5. Table: Job title by avg salary
st.subheader("Average Salary by Job Title")
title_salary_df = filtered_df.groupby('job_title', as_index=False)['salary'].mean().sort_values(by='salary', ascending=False)

# Formatting salary with generic styling
title_salary_df['salary'] = title_salary_df['salary'].apply(lambda x: f"${x:,.2f}")
title_salary_df.columns = ["Job Title", "Average Salary"]

st.dataframe(title_salary_df, use_container_width=True, hide_index=True)
