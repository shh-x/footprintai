import streamlit as st
import pandas as pd
from osint_fetcher import discover
from resolver import resolve

st.set_page_config(page_title="FootprintAI", layout="wide")
st.title("FootprintAI - Digital Identity Intelligence")

with st.sidebar:
    consent = st.checkbox("I confirm this image is consented / authorized for this analysis")
    img = st.file_uploader("Face image", type=["jpg", "jpeg", "png"])
    name = st.text_input("Name")
    context = st.text_input("Context (city, field, org)")
    use_mock = st.checkbox("Use mock data", value=True)
    run = st.button("Run analysis", disabled=not consent)

if run:
    if not name:
        st.error("Please enter a name")
    else:
        # Save uploaded image to temp file if provided
        image_path = None
        if img:
            image_path = f"temp_{img.name}"
            with open(image_path, "wb") as f:
                f.write(img.getbuffer())
        
        # Build target dict
        target = {
            "name": name,
            "context": context,
            "image": image_path or ""
        }
        
        # Discover candidates
        target_data, candidates = discover(name, context, use_mock)
        
        if target_data is None:
            st.error(f"No data found for name: {name}")
        else:
            # Resolve candidates
            results = resolve(target, candidates)
            
            # Store in session state
            st.session_state["target"] = target_data
            st.session_state["results"] = results

# Display results if available
if "results" in st.session_state:
    results = st.session_state["results"]
    target = st.session_state["target"]
    
    st.subheader(f"Results for: {target['name']}")
    
    tab1 = st.tabs(["Candidates"])
    
    with tab1[0]:
        # Build dataframe
        df_data = []
        for r in results:
            df_data.append({
                "Platform": r["platform"],
                "Username": r["username"],
                "Bio Score": f"{r['scores']['bio']:.3f}",
                "Graph Score": f"{r['scores']['graph']:.3f}",
                "Confidence": f"{r['confidence']:.3f}",
                "Decision": r["decision"],
                "Reason": r["reason"]
            })
        
        df = pd.DataFrame(df_data)
        
        # Color-code decision column
        def color_decision(val):
            if val == "verified":
                return "background-color: #d4edda; color: #155724"
            elif val == "needs_review":
                return "background-color: #fff3cd; color: #856404"
            else:
                return "background-color: #f8d7da; color: #721c24"
        
        styled_df = df.style.map(color_decision, subset=["Decision"])
        st.dataframe(styled_df, use_container_width=True)
