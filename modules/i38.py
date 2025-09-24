import streamlit as st
import pandas as pd
from utils import to_zip

def process_data(rf38_df, hos38_df, hos37_df, selected_countries):
    countries_rf38_df = rf38_df[rf38_df["Country"].isin(selected_countries)].copy()
    countries_hos38_df = hos38_df[hos38_df["Country"].isin(selected_countries)].copy()
    countries_hos37_df = hos37_df[hos37_df["Country"].isin(selected_countries)].copy()

    for df in [countries_rf38_df, countries_hos38_df, countries_hos37_df]:
        df["lookup_key"] = df["Country"].astype(str) + df["Attribute Value Code"].astype(str)
        df.drop_duplicates(subset=['lookup_key'], keep='first', inplace=True)

    i38_merge_df = pd.merge(countries_rf38_df, countries_hos38_df[["lookup_key"]], on='lookup_key', how='inner')
    final_merge_df = pd.merge(i38_merge_df, countries_hos37_df[["lookup_key"]], on='lookup_key', how='inner')
    return final_merge_df

def render():
    st.header("I38: Validate Records (I38/I37)")

    if 'selected_countries' not in st.session_state or not st.session_state['selected_countries']:
        st.warning("Please select countries on the '⚙️ Global Country Selection' page first.")
        return

    selected_countries = st.session_state['selected_countries']
    st.info(f"Processing for: **{', '.join(selected_countries)}**")

    col1, col2, col3 = st.columns(3)
    with col1:
        rf38_file = st.file_uploader("Upload I38 RF", type="csv", key="i38_rf")
    with col2:
        hos38_file = st.file_uploader("Upload I38 HOS", type="csv", key="i38_hos")
    with col3:
        hos37_file = st.file_uploader("Upload I37 HOS", type="csv", key="i38_hos37")

    if rf38_file and hos38_file and hos37_file:
        if st.button("Process Files", key="i38_process"):
            with st.spinner("Processing..."):
                try:
                    rf38_df = pd.read_csv(rf38_file, encoding='utf-8-sig', low_memory=False)
                    hos38_df = pd.read_csv(hos38_file, encoding='utf-8-sig', low_memory=False)
                    hos37_df = pd.read_csv(hos37_file, encoding='utf-8-sig', low_memory=False)

                    required_cols = ['Country', 'Attribute Value Code']
                    for name, df in [("I38 RF", rf38_df), ("I38 HOS", hos38_df), ("I37 HOS", hos37_df)]:
                        df.columns = df.columns.str.strip()
                        if not all(col in df.columns for col in required_cols):
                            st.error(
                                f"**Error in {name} file!** It's missing one or more essential columns.\n\n"
                                f"**Required columns:** `{required_cols}`\n\n"
                                f"**Actual columns found:** `{df.columns.tolist()}`\n\n"
                                "Please check the CSV file for extra rows above the header or formatting issues."
                            )
                            return
                    
                    processed_df = process_data(rf38_df, hos38_df, hos37_df, selected_countries)
                    st.session_state['i38_processed_df'] = processed_df
                    st.session_state['i38_processed'] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
    
    if st.session_state.get('i38_processed', False):
        processed_df = st.session_state['i38_processed_df']
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
                files_to_zip[f"I38_{country}.xlsx"] = country_df
            
            if files_to_zip:
                zip_bytes = to_zip(files_to_zip)
                st.download_button("Download All Files as .zip", zip_bytes, "I38_Output.zip", "application/zip", key="i38_zip_dl")

        if st.button("Clear Results", key="i38_clear"):
            for key in ['i38_processed_df', 'i38_processed']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()
