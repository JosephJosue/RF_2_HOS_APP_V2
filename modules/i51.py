import streamlit as st
import pandas as pd
from utils import to_zip

def process_data(rf51_df, hos37_df, selected_countries):
    countries_rf51_df = rf51_df[rf51_df["Country"].isin(selected_countries)].copy()
    countries_hos37_df = hos37_df[hos37_df["Country"].isin(selected_countries)].copy()

    attributes_to_remove = ["HEL_15T_IN", "HEL_30T_IN", "HEL_ING_IN", "EASYSWITCH_IN", "UQCM_IN"]
    i51_cleaned_df = countries_rf51_df[~countries_rf51_df["Attribute Value Code"].isin(attributes_to_remove)].copy()

    i51_cleaned_df["lookup_key"] = i51_cleaned_df["Country"].astype(str) + i51_cleaned_df["Attribute Value Code"].astype(str)
    i51_cleaned_df.drop_duplicates(subset=['lookup_key'], keep='first', inplace=True)
    
    countries_hos37_df["lookup_key"] = countries_hos37_df["Country"].astype(str) + countries_hos37_df["Attribute Value Code"].astype(str)
    countries_hos37_df.drop_duplicates(subset=['lookup_key'], keep='first', inplace=True)
    
    final_merge_df = pd.merge(i51_cleaned_df, countries_hos37_df[["lookup_key"]], on='lookup_key', how='inner')
    return final_merge_df

def render():
    st.header("I51: Validate Records (I51/I37)")
    
    if 'selected_countries' not in st.session_state or not st.session_state['selected_countries']:
        st.warning("Please select countries on the '⚙️ Global Country Selection' page first.")
        return

    selected_countries = st.session_state['selected_countries']
    st.info(f"Processing for: **{', '.join(selected_countries)}**")

    col1, col2 = st.columns(2)
    with col1:
        rf51_file = st.file_uploader("Upload I51 RF", type="csv", key="i51_rf")
    with col2:
        hos37_file = st.file_uploader("Upload I37 HOS", type="csv", key="i51_hos37")

    if rf51_file and hos37_file:
        if st.button("Process Files", key="i51_process"):
            with st.spinner("Processing..."):
                try:
                    rf51_df = pd.read_csv(rf51_file, encoding='utf-8-sig', low_memory=False)
                    hos37_df = pd.read_csv(hos37_file, encoding='utf-8-sig', low_memory=False)

                    required_cols = ['Country', 'Attribute Value Code']
                    for name, df in [("I51 RF", rf51_df), ("I37 HOS", hos37_df)]:
                        df.columns = df.columns.str.strip()
                        if not all(col in df.columns for col in required_cols):
                            st.error(
                                f"**Error in {name} file!** It's missing one or more essential columns.\n\n"
                                f"**Required columns:** `{required_cols}`\n\n"
                                f"**Actual columns found:** `{df.columns.tolist()}`\n\n"
                                "Please check the CSV file for extra rows above the header or formatting issues."
                            )
                            return

                    processed_df = process_data(rf51_df, hos37_df, selected_countries)
                    st.session_state['i51_processed_df'] = processed_df
                    st.session_state['i51_processed'] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

    if st.session_state.get('i51_processed', False):
        processed_df = st.session_state['i51_processed_df']
        st.subheader("Results")
        if processed_df.empty:
            st.info("No matching records found.")
        else:
            st.success(f"Process complete! Found {len(processed_df)} unique matching records.")
            st.dataframe(processed_df.drop(columns=['lookup_key'], errors='ignore'))
            
            files_to_zip = {}
            for country in processed_df['Country'].unique():
                country_df = processed_df[processed_df['Country'] == country].copy()
                country_df.drop(columns=['lookup_key'], inplace=True, errors='ignore')
                country_df = country_df.iloc[:, :-4]
                files_to_zip[f"I51_{country}.xlsx"] = country_df
            
            if files_to_zip:
                zip_bytes = to_zip(files_to_zip)
                st.download_button("Download All Files as .zip", zip_bytes, "I51_Output.zip", "application/zip", key="i51_zip_dl")

        if st.button("Clear Results", key="i51_clear"):
            for key in ['i51_processed_df', 'i51_processed']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()
