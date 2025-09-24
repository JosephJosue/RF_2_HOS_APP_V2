import streamlit as st
import pandas as pd
from utils import to_zip

def process_data(rf53_df, hos35_df, selected_countries):
    """
    Validates records from I53 RF against I35 HOS for selected countries.
    """
    # Filter dataframes by the globally selected countries
    countries_rf53_df = rf53_df[rf53_df["Country"].isin(selected_countries)].copy()
    countries_hos35_df = hos35_df[hos35_df["Country"].isin(selected_countries)].copy()

    # Create a unique lookup key for de-duplication and merging
    countries_rf53_df["lookup_key"] = countries_rf53_df["Country"].astype(str) + countries_rf53_df["Attribute Value Code"].astype(str)
    countries_rf53_df.drop_duplicates(subset=['lookup_key'], keep='first', inplace=True)
    
    countries_hos35_df["lookup_key"] = countries_hos35_df["Country"].astype(str) + countries_hos35_df["Attribute Value Code"].astype(str)
    countries_hos35_df.drop_duplicates(subset=['lookup_key'], keep='first', inplace=True)

    # Find the records from I53 that also exist in I35
    final_merge_df = pd.merge(countries_rf53_df, countries_hos35_df[["lookup_key"]], on='lookup_key', how='inner')
    
    return final_merge_df

def render():
    """
    Renders the Streamlit UI for the I53 module.
    """
    st.header("I53: Validate Records (I53/I35)")
    
    # Check if countries have been selected globally
    if 'selected_countries' not in st.session_state or not st.session_state['selected_countries']:
        st.warning("Please select countries on the '⚙️ Global Country Selection' page first.")
        return

    selected_countries = st.session_state['selected_countries']
    st.info(f"Processing for: **{', '.join(selected_countries)}**")
    
    # UI for file uploads
    col1, col2, col3 = st.columns(3)
    with col1:
        rf53_file = st.file_uploader("Upload I53 RF", type="csv", key="i53_rf")
    with col2:
        hos35_file = st.file_uploader("Upload I35 HOS", type="csv", key="i53_hos35")

    # Processing logic
    if rf53_file and hos35_file:
        if st.button("Process Files", key="i53_process"):
            with st.spinner("Processing..."):
                try:
                    # Load CSVs with robust encoding and memory settings
                    rf53_df = pd.read_csv(rf53_file, encoding='utf-8-sig', low_memory=False)
                    hos35_df = pd.read_csv(hos35_file, encoding='utf-8-sig', low_memory=False)
                    
                    # Validate that required columns exist in both files
                    required_cols = ['Country', 'Attribute Value Code']
                    for name, df in [("I53 RF", rf53_df), ("I35 HOS", hos35_df)]:
                        df.columns = df.columns.str.strip() # Clean column headers
                        if not all(col in df.columns for col in required_cols):
                            st.error(
                                f"**Error in {name} file!** It's missing one or more essential columns.\n\n"
                                f"**Required columns:** `{required_cols}`\n\n"
                                f"**Actual columns found:** `{df.columns.tolist()}`\n\n"
                                "Please check the CSV file for extra rows above the header or formatting issues."
                            )
                            return
                    
                    # Run the data processing function
                    processed_df = process_data(rf53_df, hos35_df, selected_countries)
                    
                    # Store results in session state and rerun to display them
                    st.session_state['i53_processed_df'] = processed_df
                    st.session_state['i53_processed'] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

    # Display results if processing is complete
    if st.session_state.get('i53_processed', False):
        processed_df = st.session_state['i53_processed_df']
        st.subheader("Results")
        
        if processed_df.empty:
            st.info("No matching records found for the selected countries.")
        else:
            st.success(f"Process complete! Found {len(processed_df)} unique matching records.")
            # Display a preview of the results without the temporary lookup key
            st.dataframe(processed_df.drop(columns=['lookup_key'], errors='ignore'))
            
            # Prepare files for zip download
            files_to_zip = {}
            for country in processed_df['Country'].unique():
                country_df = processed_df[processed_df['Country'] == country].copy()
                country_df.drop(columns=['lookup_key'], inplace=True, errors='ignore')
                # Drop the last 4 columns as requested
                country_df = country_df.iloc[:, :-4]
                files_to_zip[f"I53_{country}.xlsx"] = country_df
            
            if files_to_zip:
                zip_bytes = to_zip(files_to_zip)
                st.download_button(
                    label="Download All Files as .zip", 
                    data=zip_bytes, 
                    file_name="I53_Output.zip", 
                    mime="application/zip", 
                    key="i53_zip_dl"
                )

        # Button to clear the results and start over
        if st.button("Clear Results", key="i53_clear"):
            for key in ['i53_processed_df', 'i53_processed']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()