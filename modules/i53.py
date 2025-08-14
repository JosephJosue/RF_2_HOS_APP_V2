import streamlit as st
import pandas as pd
from utils import to_zip

def process_data(rf53_df, hos35_df, selected_countries):
    countries_rf53_df = rf53_df[rf53_df["Country"].isin(selected_countries)].copy()
    countries_hos35_df = hos35_df[hos35_df["Country"].isin(selected_countries)].copy()

    countries_rf53_df["lookup_key"] = countries_rf53_df["Country"].astype(str) + countries_rf53_df["Attribute Value Code"].astype(str)
    countries_hos35_df["lookup_key"] = countries_hos35_df["Country"].astype(str) + countries_hos35_df["Attribute Value Code"].astype(str)

    final_merge_df = pd.merge(countries_rf53_df, countries_hos35_df[["lookup_key"]], on='lookup_key', how='inner')
    return final_merge_df

def render():
    st.header("I53: Validate Records (I53/I35)")
    st.info("Note: The I53 HOS file is uploaded but not used in the current processing logic, as per the original application design.")
    
    if 'selected_countries' not in st.session_state or not st.session_state['selected_countries']:
        st.warning("Please select countries on the '⚙️ Global Country Selection' page first.")
        return

    selected_countries = st.session_state['selected_countries']
    st.info(f"Processing for: **{', '.join(selected_countries)}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        rf53_file = st.file_uploader("Upload I53 RF", type="csv", key="i53_rf")
    with col2:
        hos53_file = st.file_uploader("Upload I53 HOS (Not Used)", type="csv", key="i53_hos")
    with col3:
        hos35_file = st.file_uploader("Upload I35 HOS", type="csv", key="i53_hos35")

    if rf53_file and hos35_file:
        if st.button("Process Files", key="i53_process"):
            with st.spinner("Processing..."):
                rf53_df = pd.read_csv(rf53_file, encoding='latin1')
                hos35_df = pd.read_csv(hos35_file, encoding='latin1')
                
                processed_df = process_data(rf53_df, hos35_df, selected_countries)
                st.session_state['i53_processed_df'] = processed_df
                st.session_state['i53_processed'] = True

    if st.session_state.get('i53_processed', False):
        processed_df = st.session_state['i53_processed_df']
        st.subheader("Results")
        if processed_df.empty:
            st.info("No matching records found.")
        else:
            st.success(f"Process complete! Found {len(processed_df)} matching records.")
            files_to_zip = {}
            for country in processed_df['Country'].unique():
                country_df = processed_df[processed_df['Country'] == country].iloc[:, :-5]
                files_to_zip[f"I53_{country}.xlsx"] = country_df
            
            if files_to_zip:
                zip_bytes = to_zip(files_to_zip)
                st.download_button("Download All Files as .zip", zip_bytes, "I53_Output.zip", "application/zip", key="i53_zip_dl")

        if st.button("Clear Results", key="i53_clear"):
            for key in ['i53_processed_df', 'i53_processed']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()