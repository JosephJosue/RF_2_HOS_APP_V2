import streamlit as st
import pandas as pd
from utils import to_zip

def process_data(rf34_df, selected_countries):
    countries_rf34_df = rf34_df[rf34_df["Country"].isin(selected_countries)].copy()
    return countries_rf34_df

def render():
    st.header("I34: Split by Country")
    
    if 'selected_countries' not in st.session_state or not st.session_state['selected_countries']:
        st.warning("Please select countries on the '⚙️ Global Country Selection' page first.")
        return
        
    selected_countries = st.session_state['selected_countries']
    st.info(f"Processing for: **{', '.join(selected_countries)}**")

    rf34_file = st.file_uploader("Upload I34 RF CSV File", type="csv", key="i34_rf")

    if rf34_file:
        if st.button("Process File", key="i34_process"):
            with st.spinner("Processing..."):
                try:
                    rf34_df = pd.read_csv(rf34_file, encoding='utf-8-sig', low_memory=False)
                    
                    required_cols = ['Country']
                    rf34_df.columns = rf34_df.columns.str.strip()
                    if not all(col in rf34_df.columns for col in required_cols):
                        st.error(
                            f"**Error in I34 RF file!** It's missing one or more essential columns.\n\n"
                            f"**Required columns:** `{required_cols}`\n\n"
                            f"**Actual columns found:** `{rf34_df.columns.tolist()}`\n\n"
                            "Please check the CSV file for extra rows above the header or formatting issues."
                        )
                        return

                    processed_df = process_data(rf34_df, selected_countries)
                    st.session_state['i34_processed_df'] = processed_df
                    st.session_state['i34_processed'] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

    if st.session_state.get('i34_processed', False):
        processed_df = st.session_state['i34_processed_df']

        st.subheader("Results")
        if processed_df.empty:
            st.info("No data found for the selected countries.")
        else:
            st.success(f"Data processed. Found data for {len(processed_df['Country'].unique())} countries.")
            
            files_to_zip = {}
            for country in processed_df['Country'].unique():
                country_df = processed_df[processed_df['Country'] == country].iloc[:, :-4]
                files_to_zip[f"I34_{country}.xlsx"] = country_df
            
            if files_to_zip:
                zip_bytes = to_zip(files_to_zip)
                st.download_button("Download All Files as .zip", zip_bytes, "I34_Output.zip", "application/zip", key="i34_zip_dl")

        if st.button("Clear Results", key="i34_clear"):
            for key in ['i34_processed_df', 'i34_processed']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()
