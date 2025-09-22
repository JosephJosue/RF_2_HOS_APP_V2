import streamlit as st

def render():
    """
    Renders the global settings page for country selection.
    """
    st.header("⚙️ Global Country Selection")
    st.write(
        "Select the countries you wish to process below. "
        "This selection will be applied to all modules in this session."
    )

    # Define a master list of all possible countries.
    ALL_POSSIBLE_COUNTRIES = sorted([
        "HK", "TW", "NZ", "AU", "BR", "CH", "CN", "IE", "IL", "IN", 
        "JP", "MX", "MY", "PL", "RO", "SA", "SG", "TH", "ZA", "ES", 
        "PT", "NL", "DK", "BE", "SE", "FI", "NO", "BD", "CA", "CZ",
        "FR", "DE", "HU", "GR", "ID", "KE", "QA", "KR", "TR", "GB",
        "US", "AF36", "SE36", "MY36", "ME36", "KR36"
    ])

    # Create the multiselect widget. 
    # The 'default' value is pulled from the session state to remember the user's previous choice.
    selected_countries = st.multiselect(
        "Select countries:",
        options=ALL_POSSIBLE_COUNTRIES,
        default=st.session_state.get('selected_countries', [])
    )

    # A button to confirm and save the selection into the session state.
    if st.button("Apply Country Selection"):
        st.session_state['selected_countries'] = selected_countries
        st.success(f"Selection updated! Processing will now be limited to {len(selected_countries)} countries.")
        # We use st.rerun() to immediately reflect the change in the info box below.
        st.rerun()

    st.markdown("---")

    # Always display the current selection for clarity.
    if st.session_state.get('selected_countries'):
        st.info(f"Current selection applied: **{', '.join(st.session_state['selected_countries'])}**")
    else:
        st.warning("No countries selected. Please make a selection to enable the other modules.")