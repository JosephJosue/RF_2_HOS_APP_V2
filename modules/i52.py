import streamlit as st
import pandas as pd
from utils import to_zip

def process_data(rf52_df, rf51_df, hos36_df, selected_countries):
    """
    Processes the I52 data by transforming, combining, and validating unique records.
    """
    # 1. Filter all dataframes by selected countries
    countries_rf52_df = rf52_df[rf52_df["Country"].isin(selected_countries)].copy()
    countries_rf51_df = rf51_df[rf51_df["Country"].isin(selected_countries)].copy()
    countries_hos36_df = hos36_df[hos36_df["Country"].isin(selected_countries)].copy()

    # --- De-duplicate HOS36 (validation file) ---
    countries_hos36_df["lookup_key"] = countries_hos36_df["Country"].astype(str) + countries_hos36_df["Attribute Value Code"].astype(str)
    countries_hos36_df.drop_duplicates(subset=['lookup_key'], keep='first', inplace=True)

    # --- De-duplicate and transform RF51 data ---
    rf51_os_codes = ["HEL_15T_IN", "HEL_30T_IN", "HEL_ING_IN", "EASYSWITCH_IN", "UQCM_IN"]
    rf51_os_df = countries_rf51_df[countries_rf51_df["Attribute Value Code"].isin(rf51_os_codes)].copy()
    rf51_os_df["lookup_key"] = rf51_os_df["Country"].astype(str) + rf51_os_df["Attribute Value Code"].astype(str)
    rf51_os_df.drop_duplicates(subset=['lookup_key'], keep='first', inplace=True)

    converted_rows = []
    for _, row in rf51_os_df.iterrows():
        converted_rows.append({
            'Display Group Code': 'LI', 'Country': row.get('Country'),
            'Attribute Value Code': row.get('Attribute Value Code'),
            'Attribute Value Description': row.get('Attribute Value Description'),
            'Attribute Value Price Type': 'Lookup', 'Attribute Value FP': row.get('Attribute Value FP'), 
            'Attribute Value TP': row.get('Attribute Value TP'), 'Attribute Value LP': row.get('Attribute Value LP'), 
            'Attribute Value MMFP': row.get('Attribute Value MMFP'), 'Attribute Value MMTP': row.get('Attribute Value MMTP'), 
            'Attribute Value MMLP': row.get('Attribute Value MMLP'), 'Attribute Deactivated YN': row.get('Attribute Deactivated YN'), 
            'Customer Bank Value': row.get('Customer Bank Value'), 'RSM Type': row.get('RSM Type'), 
            'RSM Consumption': row.get('RSM Consumption'), 'Currency': row.get('Currency'), 'Local FP': row.get('Local FP'), 
            'Price Book Name': row.get('Price Book Name'), 'Server': row.get('Server'), 'Changed On': row.get('Changed On'), 
            'Changed By': row.get('Changed By'), 'lookup_key': row.get('lookup_key')
        })
    converted_df = pd.DataFrame(converted_rows)

    # --- De-duplicate RF52 data ---
    countries_rf52_df["lookup_key"] = countries_rf52_df["Country"].astype(str) + countries_rf52_df["Attribute Value Code"].astype(str)
    countries_rf52_df.drop_duplicates(subset=['lookup_key'], keep='first', inplace=True)

    if not converted_df.empty:
        for col in countries_rf52_df.columns:
            if col not in converted_df.columns:
                converted_df[col] = None
        converted_df = converted_df[countries_rf52_df.columns]

    combined_i52_df = pd.concat([countries_rf52_df, converted_df], ignore_index=True)
    combined_i52_df.drop_duplicates(subset=['lookup_key'], keep='first', inplace=True)

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
                try:
                    # **FIX**: Use 'utf-8-sig' encoding to handle potential BOM characters
                    rf52_df = pd.read_csv(rf52_file, encoding='utf-8-sig', low_memory=False)
                    rf51_df = pd.read_csv(rf51_file, encoding='utf-8-sig', low_memory=False)
                    hos36_df = pd.read_csv(hos36_file, encoding='utf-8-sig', low_memory=False)
                    
                    # Validate columns with a more robust and informative check
                    required_cols = ['Country', 'Attribute Value Code']
                    for name, df in [("I52 RF", rf52_df), ("I51 RF", rf51_df), ("I36 HOS", hos36_df)]:
                        # Proactively clean column names from whitespace just in case
                        df.columns = df.columns.str.strip()
                        if not all(col in df.columns for col in required_cols):
                            st.error(
                                f"**Error in {name} file!** It's missing one or more essential columns.\n\n"
                                f"**Required columns:** `{required_cols}`\n\n"
                                f"**Actual columns found:** `{df.columns.tolist()}`\n\n"
                                "This usually happens because of extra rows above the header in the CSV. "
                                "Please open the file, ensure the first row has the correct headers, save it, and try again."
                            )
                            return # Stop execution

                    processed_df = process_data(rf52_df, rf51_df, hos36_df, selected_countries)
                    st.session_state['i52_processed_df'] = processed_df
                    st.session_state['i52_processed'] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

    if st.session_state.get('i52_processed', False):
        processed_df = st.session_state['i52_processed_df']
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
                files_to_zip[f"I52_{country}.xlsx"] = country_df
            
            if files_to_zip:
                zip_bytes = to_zip(files_to_zip)
                st.download_button("Download All Files as .zip", zip_bytes, "I52_Output.zip", "application/zip", key="i52_zip_dl")

        if st.button("Clear Results", key="i52_clear"):
            for key in ['i52_processed_df', 'i52_processed']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()
