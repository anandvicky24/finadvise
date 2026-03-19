import streamlit as st
from agents import fin_app
from langchain_core.messages import HumanMessage

st.set_page_config(page_title="FINAdvise AI Architect", layout="wide")

st.markdown("""
    <style>
    .stInfo { border-left: 5px solid #00d4ff; }
    .stWarning { border-left: 5px solid #ffa500; }
    .stSuccess { border-left: 5px solid #28a745; }
    .pulse { color: #00d4ff; font-weight: bold; animation: blinker 1.5s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .done-status { color: #28a745; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 FINAdvise: Comparative Intelligence")

st.sidebar.markdown("### 📡 System Status")
status_placeholder = st.sidebar.empty()
status_placeholder.info("System: Idle")

query = st.text_input("Enter your query here:")

if st.button("Run Full Intelligence Flow"):
    if query:
        initial_state = {
            "query": query, 
            "messages": [HumanMessage(content=query)], 
            "history": [], 
            "market_data": "", 
            "current_node": "Parsing..."
        }
        
        with st.spinner("Executing multi-agent flow..."):
            # Stream the graph and update the sidebar
            for chunk in fin_app.stream(initial_state):
                for node_name, node_state in chunk.items():
                    if "current_node" in node_state:
                        status_placeholder.markdown(f"**Agent:** <span class='pulse'>{node_state['current_node']}</span>", unsafe_allow_html=True)
            
            # Final result pull
            result = fin_app.invoke(initial_state)
            
            # Update the sidebar to "Done"
            status_placeholder.markdown("<p class='done-status'>✅ Process: Done</p>", unsafe_allow_html=True)
            
            # --- Results ---
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Combined Market Insights")
                st.info(result.get("market_data", "No data gathered."))
            with col2:
                st.subheader("⚠️ Comparative Risk Assessment")
                st.warning(result.get("risk_score", "Risk analysis skipped."))
            
            st.divider()
            st.subheader("📈 Final Strategic Recommendation")
            st.success(result.get("portfolio_rec", "Recommendation missing."))
            
            st.balloons() # Visual celebration for "Done"
    else:
        st.error("Please enter a query.")