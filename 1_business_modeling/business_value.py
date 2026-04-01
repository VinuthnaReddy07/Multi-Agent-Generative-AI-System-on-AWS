import streamlit as st

st.set_page_config(layout="wide")

st.title("Generative AI Value Model: Coffee Shop Multi-Agent Use Cases")

# Sidebar for controls and assumptions
with st.sidebar:
    st.header("Controls & Assumptions")
    st.markdown("**➡️ Select a Use Case:**")
    use_case = st.selectbox("\n", [
        "Order Taking & Processing",
        "Customer Support & Loyalty",
        "Inventory & Supply Chain"
    ])

    st.sidebar.markdown("---")
    
    if use_case == "Order Taking & Processing":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            queries_per_day = st.number_input("Orders/day", value=36000, min_value=1)
            agent_time = st.number_input("Human time (mins)", value=12.0, min_value=0.1)
            ai_time = st.number_input("AI time (mins)", value=2.5, min_value=0.1)
        with col2:
            agent_cost = st.number_input("Human cost/hr (\$)", value=30.0, min_value=0.0)
            ai_cost = st.number_input("AI cost/order (\$)", value=0.02, min_value=0.0)
            ai_resolution = st.slider("AI handles (%)", 0, 100, 80)
        
        st.sidebar.markdown("---")
        col3, col4 = st.sidebar.columns(2)
        with col3:
            csat_improve = st.slider("CSAT improve (%)", 0, 20, 10)
            conversion_lift = st.slider("Conversion lift (%)", 0, 30, 15)
        with col4:
            personalization_uplift = st.slider("Personalization (%)", 0, 10, 3)
            response_speed_uplift = st.slider("Response speed (%)", 0, 10, 4)
        recommendation_accuracy = st.slider("Recommendation accuracy (%)", 0, 10, 3)

    elif use_case == "Customer Support & Loyalty":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            tickets_per_day = st.number_input("Tickets/day", value=5000, min_value=1)
            agent_time = st.number_input("Human time (mins)", value=8.0, min_value=0.1)
            ai_time = st.number_input("AI time (mins)", value=2.0, min_value=0.1)
        with col2:
            agent_cost = st.number_input("Human cost/hr (\$)", value=28.0, min_value=0.0)
            ai_cost = st.number_input("AI cost/ticket (\$)", value=0.03, min_value=0.0)
            ai_resolution = st.slider("AI handles (%)", 0, 100, 70)
        
        st.sidebar.markdown("---")
        col3, col4 = st.sidebar.columns(2)
        with col3:
            csat_improve = st.slider("CSAT improve (%)", 0, 20, 8)
            conversion_lift = st.slider("Conversion lift (%)", 0, 30, 10)
        with col4:
            personalization_uplift = st.slider("Personalization (%)", 0, 10, 3)
            response_speed_uplift = st.slider("Response speed (%)", 0, 10, 4)
        recommendation_accuracy = st.slider("Recommendation accuracy (%)", 0, 10, 3)

    elif use_case == "Inventory & Supply Chain":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            inventory_checks_per_month = st.number_input("Checks/month", value=400, min_value=1)
            agent_time = st.number_input("Human time (mins)", value=30.0, min_value=0.1)
            ai_time = st.number_input("AI time (mins)", value=5.0, min_value=0.1)
        with col2:
            agent_cost = st.number_input("Human cost/hr (\$)", value=35.0, min_value=0.0)
            ai_cost = st.number_input("AI cost/check (\$)", value=0.10, min_value=0.0)
            ai_resolution = st.slider("AI automates (%)", 0, 100, 60)
        
        st.sidebar.markdown("---")
        col3, col4 = st.sidebar.columns(2)
        with col3:
            csat_improve = st.slider("CSAT improve (%)", 0, 10, 3)
            conversion_lift = st.slider("Waste reduction (%)", 0, 30, 20)
        with col4:
            personalization_uplift = st.slider("Personalization (%)", 0, 10, 3)
            response_speed_uplift = st.slider("Response speed (%)", 0, 10, 4)
        recommendation_accuracy = st.slider("Recommendation accuracy (%)", 0, 10, 3)

# Business logic calculations
if use_case == "Order Taking & Processing":
    agent_hours = (queries_per_day * agent_time) / 60
    agent_cost_period = agent_hours * agent_cost
    ai_cost_period = queries_per_day * ai_cost
    savings = (agent_cost_period - ai_cost_period) * (ai_resolution / 100)
    annual_savings = savings * 365
elif use_case == "Customer Support & Loyalty":
    agent_hours = (tickets_per_day * agent_time) / 60
    agent_cost_period = agent_hours * agent_cost
    ai_cost_period = tickets_per_day * ai_cost
    savings = (agent_cost_period - ai_cost_period) * (ai_resolution / 100)
    annual_savings = savings * 365
else:
    agent_hours = (inventory_checks_per_month * agent_time) / 60
    agent_cost_period = agent_hours * agent_cost
    ai_cost_period = inventory_checks_per_month * ai_cost
    savings = (agent_cost_period - ai_cost_period) * (ai_resolution / 100)
    annual_savings = savings * 12

total_cx_gain = csat_improve + personalization_uplift + response_speed_uplift + recommendation_accuracy

# Main panel for outputs - More compact layout
if use_case == "Order Taking & Processing":
    st.markdown("### Use Case: Order Taking & Processing")
    st.write("Automating order taking with AI enables faster service, reduced labor costs, and higher order accuracy.")
elif use_case == "Customer Support & Loyalty":
    st.markdown("### Use Case: Customer Support & Loyalty")
    st.write("AI-driven support boosts customer satisfaction and retention by resolving queries quickly and consistently.")
else:
    st.markdown("### Use Case: Inventory & Supply Chain")
    st.write("AI-powered inventory management reduces waste, prevents stockouts, and frees up manager time for higher-value tasks.")

# Use 3 main columns for all metrics to reduce vertical space
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("✅ Customer Experience")
    metric_cols1, metric_cols2 = st.columns(2)
    with metric_cols1:
        st.metric("CSAT Uplift", f"{csat_improve}%")
        st.metric("Personalization", f"{personalization_uplift}%")
    with metric_cols2:
        st.metric("Faster Response", f"{response_speed_uplift}%")
        st.metric("Better Recommendations", f"{recommendation_accuracy}%")
    st.metric("Total CX Gain", f"{total_cx_gain}%")

with col2:
    st.subheader("🛠 Employee Productivity")
    metric_cols3, metric_cols4 = st.columns(2)
    with metric_cols3:
        st.metric("Agent Hours", f"{agent_hours:,.1f}")
        st.metric("Agent Cost", f"${agent_cost_period:,.0f}")
    with metric_cols4:
        st.metric("AI Agent Cost", f"${ai_cost_period:,.2f}")
        st.metric("AI Resolution Rate", f"{ai_resolution}%")

with col3:
    st.subheader("💰 Business Operations")
    metric_cols5, metric_cols6 = st.columns(2)
    with metric_cols5:
        st.metric("Savings (Period)", f"${savings:,.0f}")
        st.metric("Annual Savings", f"${annual_savings:,.0f}")
    with metric_cols6:
        if use_case == "Inventory & Supply Chain":
            st.metric("Waste Reduction", f"{conversion_lift}%")
        else:
            st.metric("Conversion Lift", f"{conversion_lift}%")
        time_saved = ((agent_time - ai_time) * ai_resolution / 100)
        st.metric("Time Saved Per Interaction", f"{time_saved:.1f} mins")

# Add a chart section at the bottom using the full width
st.markdown("---")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Cost Comparison")
    chart_data = {
        "Human Process": agent_cost_period,
        "AI-Assisted Process": agent_cost_period * (1 - ai_resolution/100) + ai_cost_period
    }
    st.bar_chart(chart_data)

with chart_col2:
    st.subheader("Customer Experience Impact")
    cx_data = {
        "Baseline": 100,
        "With AI": 100 + total_cx_gain
    }
    st.bar_chart(cx_data)