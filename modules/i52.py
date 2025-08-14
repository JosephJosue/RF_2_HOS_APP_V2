import streamlit as st
import pandas as pd
from utils import to_zip

def process_data(rf52_df, rf51_df, hos36_df, selected_countries):
    countries_rf52_df = rf52_df[rf52_df["Country"].isin(selected_countries)].copy()
    countries_rf51_df = rf51_df[rf51_df["Country"].isin(selected_countries)].copy()
    countries_hos36_df = hos36_df[hos36_df["Country"].isin(selected_countries)].copy()

    rf51_os_codes = ["HEL_15T_IN", "HEL_30T_IN", "HEL_ING_IN", "EASYSWITCH_IN", "UQCM_IN"]
    rf51_os_df = countries_rf51_df[countries_rf51_df["Attribute Value Code"].isin(rf51_os_codes)].copy()

    converted_rows = []
    for _, row in rf51_os_df.iterrows():
        converted_rows.append({
            'Display Group Code': 'LI', 'Country': row.get('Country'),
            'Attribute Value Code': row.get('Attribute Value Code'),
            'Attribute Value Description': row.get('Attribute Value Description'),
            'Attribute Value Price Type': 'Lookup',
            'Attribute Value FP': row.get('Attribute Value FP'), 'Attribute Value TP': row.get('Attribute Value TP'),
            'Attribute Value LP': row.get('Attribute Value LP'), 'Attribute Value MMFP': row.get('Attribute Value MMFP'),
            'Attribute Value MMTP': row.get('Attribute Value MMTP'), 'Attribute Value MMLP': row.get('Attribute Value MMLP'),
            'Attribute Deactivated YN': row.get('Attribute Deactivated YN'), 'Customer Bank Value': row.get('Customer Bank Value'),
            'RSM Type': row.get('RSM Type'), 'RSM Consumption': row.get('RSM Consumption'), 'Currency': row.get('Currency'),
            'Local FP': row.get('Local FP'), 'Price Book Name': row.get('Price Book Name'), 'Server': row.get('Server'),
            'Changed On': row.get('Changed On'), 'Changed By': row.get('Changed By')
        })
    converted_df = pd.DataFrame(converted_rows)

    if not converted_df.empty:
        for col in countries_rf52_df.columns:
            if col not in converted_df.columns:
                converted_df[col] = None
        converted_df = converted_df[countries_rf52_df.columns]

    combined_i52_df = pd.concat([countries_rf52_df, converted_df], ignore_index=True)
    
    combined_i52_df["lookup_key"] = combined_i52_df["Country"].astype(str) + combined_i52_df["Attribute Value Code"].astype(str)
    countries_hos36_df["lookup_key"] = countries_hos36_df["Country"].astype(str) + countries_hos36_df["Attribute Value Code"].astype(str)

    final_merge_df = pd.merge(combined_i52_df, countries_hos36_df[["lookup_key"]], on='lookup_key', how='inner')
    return final_merge_df

def render():
    st.header("I52: Transform and Validate (I52/I51/I36)")

    if 'selected_countries' not in st.session_state or not st.session_state['selected_countries']:
        st.warning("Please select countries on the '⚙️ Global Country Selection' page first.")
        return

    selected_countries = st.session_state['selected_countries']
    st.info(f"Processing for: **{', '.join(selected_countries)}**")

    col1, col2, col3 = st.columns(3)
    with col1:
        rf52_file = st.file_uploader("Upload I52 RF", type="csv", key="i52_rf")
    with col2:
        rf51_file = st.file_uploader("Upload I51 RF", type="csv", key="i52_rf51")
    with col3:
        hos36_file = st.file_uploader("Upload I36 HOS", type="csv", key="i52_hos36")

    if rf52_file and rf51_file and hos36_file:
        if st.button("Process Files", key="i52_process"):
            with st.spinner("Processing..."):
                rf52_df = pd.read_csv(rf52_file, encoding='latin1')
                rf51_df = pd.read_csv(rf51_file, encoding='latin1')
                hos36_df = pd.read_csv(hos36_file, encoding='latin1')
                
                processed_df = process_data(rf52_df, rf51_df, hos36_df, selected_countries)
                st.session_state['i52_processed_df'] = processed_df
                st.session_state['i52_processed'] = True

    if st.session_state.get('i52_processed', False):
        processed_df = st.session_state['i52_processed_df']
        st.subheader("Results")
        if processed_df.empty:
            st.info("No matching records found.")
        else:
            st.success(f"Process complete! Found {len(processed_df)} matching records.")
            files_to_zip = {}
            for country in processed_df['Country'].unique():
                country_df = processed_df[processed_df['Country'] == country].iloc[:, :-5]
                files_to_zip[f"I52_{country}.xlsx"] = country_df
            
            if files_to_zip:
                zip_bytes = to_zip(files_to_zip)
                st.download_button("Download All Files as .zip", zip_bytes, "I52_Output.zip", "application/zip", key="i52_zip_dl")

        if st.button("Clear Results", key="i52_clear"):
            for key in ['i52_processed_df', 'i52_processed']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()