import streamlit as st
import pandas as pd
from utils import to_zip

def process_data(rf01_df, hos01_df, selected_countries):
    countries_rf01_df = rf01_df[rf01_df["Country"].isin(selected_countries)].copy()
    countries_hos01_df = hos01_df[hos01_df["Country"].isin(selected_countries)].copy()

    merged_df = pd.merge(countries_hos01_df, countries_rf01_df, on="Country", suffixes=('_hos', '_rf'), how='inner')
    
    columns_to_compare = ["h_cost_rate", "h_trav_CM", "h_trav_PM", "mat_hand", "LaborGM", "PartsGM", "TP_LP_UP", "FP_LP_UP", "NBV_LAT", "NBV_NPC", "NBV_UPLIFT"]
    changes_list = []

    for column in columns_to_compare:
        col_hos = f"{column}_hos"
        col_rf = f"{column}_rf"
        if col_hos in merged_df.columns and col_rf in merged_df.columns:
            differences = merged_df[merged_df[col_hos] != merged_df[col_rf]]
            for _, row in differences.iterrows():
                changes_list.append({'Country': row['Country'], 'Column': column, 'Old Value': row[col_hos], 'New Value': row[col_rf]})
    
    changed_values_df = pd.DataFrame(changes_list)
    return changed_values_df, countries_rf01_df

def render():
    st.header("I01: Country Master Data Comparison")

    if 'selected_countries' not in st.session_state or not st.session_state['selected_countries']:
        st.warning("Please select countries on the '⚙️ Global Country Selection' page first.")
        return

    selected_countries = st.session_state['selected_countries']
    st.info(f"Processing for: **{', '.join(selected_countries)}**")

    col1, col2 = st.columns(2)
    with col1:
        rf01_file = st.file_uploader("Upload RF01 CSV File", type="csv", key="i01_rf")
    with col2:
        hos01_file = st.file_uploader("Upload HOS01 CSV File", type="csv", key="i01_hos")

    if rf01_file and hos01_file:
        if st.button("Process Files", key="i01_process"):
            with st.spinner("Processing..."):
                try:
                    rf01_df = pd.read_csv(rf01_file, encoding='utf-8-sig', low_memory=False)
                    hos01_df = pd.read_csv(hos01_file, encoding='utf-8-sig', low_memory=False)

                    required_cols_map = {
                        "RF01": (rf01_df, ['Country']),
                        "HOS01": (hos01_df, ['Country'])
                    }

                    for name, (df, cols) in required_cols_map.items():
                        df.columns = df.columns.str.strip()
                        if not all(col in df.columns for col in cols):
                            st.error(
                                f"**Error in {name} file!** It's missing one or more essential columns.\n\n"
                                f"**Required columns:** `{cols}`\n\n"
                                f"**Actual columns found:** `{df.columns.tolist()}`\n\n"
                                "Please check the CSV file for extra rows above the header or formatting issues."
                            )
                            return
                    
                    changed_df, rf_df_filtered = process_data(rf01_df, hos01_df, selected_countries)
                    st.session_state['i01_changed_df'] = changed_df
                    st.session_state['i01_rf_df_filtered'] = rf_df_filtered
                    st.session_state['i01_processed'] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
    
    if st.session_state.get('i01_processed', False):
        changed_df = st.session_state['i01_changed_df']
        rf_df_filtered = st.session_state['i01_rf_df_filtered']
        
        st.subheader("Results")
        if changed_df.empty:
            st.success("No differences found!")
        else:
            st.warning(f"Found {len(changed_df)} differences.")
            st.dataframe(changed_df)

        files_to_zip = {}
        if not changed_df.empty:
            files_to_zip["I01_changes.xlsx"] = changed_df

        for country in rf_df_filtered[rf_df_filtered['Country'].isin(selected_countries)]['Country'].unique():
            country_df = rf_df_filtered[rf_df_filtered['Country'] == country].iloc[:, :-4]
            files_to_zip[f"I01_{country}.xlsx"] = country_df

        if files_to_zip:
            zip_bytes = to_zip(files_to_zip)
            st.download_button("Download All Files as .zip", zip_bytes, "I01_Output.zip", "application/zip", key="i01_zip_dl")

        if st.button("Clear Results", key="i01_clear"):
            for key in ['i01_changed_df', 'i01_rf_df_filtered', 'i01_processed']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()
