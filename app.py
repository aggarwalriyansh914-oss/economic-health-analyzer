import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration for a modern look
st.set_page_config(
    page_title="India Economic Health Analyzer",
    page_icon="🇮🇳",
    layout="wide"
)

# --- 0. CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        border: 1px solid #3d425a;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #b0b3c1 !important;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .category-badge {
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)


# --- 1. SETTING UP THE MODERN UI (SIDEBAR) ---
st.sidebar.title("📊 Control Panel")
st.sidebar.markdown("Adjust settings to explore the data.")

# --- 2. LOADING DATA & CLEANING ---
@st.cache_data
def load_data():
    # Load the raw CSV file, translating various missing strings to NaN
    df = pd.read_csv("data.csv", na_values=['missing', '?', 'not_available', 'NaN', ''])
    
    # 1. Clean the raw data: Ensure numeric columns are forced to numeric
    # Any strings that couldn't be parsed will become NaN
    cols = ['GDP_Growth', 'Inflation', 'Unemployment', 'Sensex']
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # 2. Handle duplicates: The raw data contains multiple entries for the same year
    # We group by Year and calculate the mean to get a single, clean record per year
    df = df.groupby('Year', as_index=False).mean()
    
    # 3. Handle remaining missing values (NaNs) by forward and backward filling
    df = df.ffill().bfill()
    
    # 4. Rename columns to match the existing application format standards
    df.rename(columns={
        'GDP_Growth': 'GDP Growth (%)',
        'Inflation': 'Inflation Rate (%)',
        'Unemployment': 'Unemployment Rate (%)',
        'Sensex': 'Sensex'
    }, inplace=True)
    
    # 5. Ensure Year is an integer (groupby might have turned it into float)
    df['Year'] = df['Year'].astype(int)
    
    return df

df = load_data()

# --- 3. NORMALIZATION & LOGIC (SIMPLE MIN-MAX) ---
def calculate_scores(data, weights):
    # Copy data to avoid modifying original
    df_calc = data.copy()
    
    # Identify indicators
    indicators = ['GDP Growth (%)', 'Inflation Rate (%)', 'Unemployment Rate (%)', 'Sensex']
    
    # Normalize each column to a 0-1 scale
    # Min-Max Scaling: (value - min) / (max - min)
    for col in indicators:
        min_val = df_calc[col].min()
        max_val = df_calc[col].max()
        
        # If max-min is 0, avoid division by zero
        if max_val != min_val:
            df_calc[f'{col}_Scaled'] = (df_calc[col] - min_val) / (max_val - min_val)
        else:
            df_calc[f'{col}_Scaled'] = 0.5
            
    # REVERSE SCORING for Inflation and Unemployment (Lower is better)
    # We want 1 to be "good" (low inflation/unemployment) and 0 to be "bad"
    df_calc['Inflation Rate (%)_Scaled'] = 1 - df_calc['Inflation Rate (%)_Scaled']
    df_calc['Unemployment Rate (%)_Scaled'] = 1 - df_calc['Unemployment Rate (%)_Scaled']
    
    # Calculate weighted score (0-100)
    df_calc['Health Score'] = (
        df_calc['GDP Growth (%)_Scaled'] * weights['GDP'] +
        df_calc['Inflation Rate (%)_Scaled'] * weights['Inflation'] +
        df_calc['Unemployment Rate (%)_Scaled'] * weights['Unemployment'] +
        df_calc['Sensex_Scaled'] * weights['Sensex']
    ) * 100
    
    return df_calc

# --- 4. SIDEBAR INPUTS ---
# Year Slider
selected_year = st.sidebar.select_slider(
    "Select Year to Analyze",
    options=df['Year'].tolist(),
    value=df['Year'].max()
)

# Weight Adjustment (Advanced but simple for student understanding)
st.sidebar.markdown("---")
st.sidebar.write("💡 **Indicator Weights** (Total must be 100%)")
w_gdp = st.sidebar.slider("GDP Growth Weight", 0, 100, 40)
w_inf = st.sidebar.slider("Inflation Weight", 0, 100, 20)
w_unemp = st.sidebar.slider("Unemployment Weight", 0, 100, 20)
w_sensex = st.sidebar.slider("Sensex Weight", 0, 100, 20)

# Normalize weights to sum up to 1.0
total_w = w_gdp + w_inf + w_unemp + w_sensex
weights = {
    'GDP': w_gdp / total_w,
    'Inflation': w_inf / total_w,
    'Unemployment': w_unemp / total_w,
    'Sensex': w_sensex / total_w
}

# --- 5. EXECUTE LOGIC ---
df_with_scores = calculate_scores(df, weights)
year_data = df_with_scores[df_with_scores['Year'] == selected_year].iloc[0]

# Determine Category
score = year_data['Health Score']
if score >= 80:
    category, color = "Strong", "green"
elif score >= 60:
    category, color = "Stable", "blue"
elif score >= 40:
    category, color = "Warning", "orange"
else:
    category, color = "Risk", "red"

# --- 6. MAIN DISPLAY ---
st.title(" India Economic Health Analyzer")
st.markdown(f"**Year Under Review: {selected_year}**")

# Metrics Display
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("GDP Growth (%)", f"{year_data['GDP Growth (%)']:.1f}%")
with col2:
    st.metric("Inflation Rate (%)", f"{year_data['Inflation Rate (%)']:.1f}%", delta_color="inverse")
with col3:
    st.metric("Unemployment (%)", f"{year_data['Unemployment Rate (%)']:.1f}%", delta_color="inverse")
with col4:
    st.metric("Sensex", f"{year_data['Sensex']:,.0f}")

st.markdown("---")

# Health Score Display
score_col1, score_col2 = st.columns([1, 2])

with score_col1:
    st.subheader("Economic Health Score")
    
    # Gauge Chart instead of simple box
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Category: {category}", 'font': {'size': 20}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#ffcdd2'},
                {'range': [40, 60], 'color': '#fff9c4'},
                {'range': [60, 80], 'color': '#bbdefb'},
                {'range': [80, 100], 'color': '#c8e6c9'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score}
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)
    



with score_col2:
    st.subheader("Economic Balance & Components")
    
    values = [
        year_data['GDP Growth (%)_Scaled'] * 100,
        year_data['Inflation Rate (%)_Scaled'] * 100,
        year_data['Unemployment Rate (%)_Scaled'] * 100,
        year_data['Sensex_Scaled'] * 100
    ]
    
    comp_data = {
        "Indicator": ["GDP", "Inflation", "Unemployment", "Sensex"],
        "Strength Score": values
    }
    
    fig_bar = px.bar(
        comp_data, x="Indicator", y="Strength Score", 
        color="Indicator", text_auto=".1f",
        range_y=[0, 100], template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_bar.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_bar, use_container_width=True)


# Visual Trends
st.markdown("---")
st.subheader("📈 10-Year Economic Trends")

chart_tabs = st.tabs(["Health Score Trend", "Indicators Over Time", "Data Table"])

with chart_tabs[0]:
    fig_trend = px.line(df_with_scores, x="Year", y="Health Score", markers=True, 
                         title="India's Economic Health Score Transition (2014-2023)")
    fig_trend.update_layout(hovermode="x unified", height=400)
    st.plotly_chart(fig_trend, use_container_width=True)

with chart_tabs[1]:
    df_plot = df_with_scores.melt(id_vars=["Year"], value_vars=['GDP Growth (%)', 'Inflation Rate (%)', 'Unemployment Rate (%)'])
    fig_multi = px.line(df_plot, x="Year", y="value", color="variable", markers=True,
                         title="Major Economic Indicators Comparison")
    fig_multi.update_layout(height=400)
    st.plotly_chart(fig_multi, use_container_width=True)

with chart_tabs[2]:
    raw_df = pd.read_csv("data.csv", dtype=str)
    st.dataframe(raw_df, use_container_width=True)


# Footer
st.markdown("---")
st.caption("Crafted for Educational Purposes | Data Source: Manual CSV Dataset (2014-2023)")
