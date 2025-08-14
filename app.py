import streamlit as st
from modules import i01, i34, i38, i51, i52, i53, home

# Page configuration
st.set_page_config(
    page_title="RF 2 HOS Data Migration",
    layout="wide"
)

st.title("RF 2 HOS Data Migration Tool")
st.write("This tool automates the quarterly data preparation process for server migration.")

# Placeholder functions for unimplemented pages
def placeholder_page():
    st.header("Coming Soon")
    st.write("This feature is not yet implemented.")

# Dictionary to map page names to their render functions from the modules
PAGES = {
    "⚙️ Global Country Selection": home.render,
    "I01": i01.render,
    "I34": i34.render,
    "I38": i38.render,
    "I51": i51.render,
    "I52": i52.render,
    "I53": i53.render,
}

# Sidebar for navigation
st.sidebar.title('Migration Processes')
selection = st.sidebar.radio("Select a tool:", list(PAGES.keys()))

# Get the function to render the selected page
page_function = PAGES[selection]

# Render the selected page's UI
page_function()