import os
import subprocess
import streamlit as st
import sys
import importlib
import unittest
import re
import pandas as pd




component_titles = {
    "create_metadata": "1. Initialize & Create Metadata",
    "update_flag": "2. Select, Flag & Extract Procedures",
    "convert_procs": "3. Convert Procedures with SnowConvert",
    "process_converted_procs": "4. Process & Finalize Scripts",
    "run_unit_tests": "5. Execute Unit Tests & Review Results"
}

# Sidebar labels (can be shorter)
sidebar_labels = {
    "create_metadata": "1. Initialize Metadata",
    "update_flag": "2. Select & Extract",
    "convert_procs": "3. Convert Procedures",
    "process_converted_procs": "4. Process Scripts",
    "run_unit_tests": "5. Run Unit Tests"
}

# Icons for a more professional feel
icons = {
    "create_metadata": "📦", "update_flag": "🎯", "convert_procs": "⚙️",
    "process_converted_procs": "✨", "run_unit_tests": "🧪"
}

# Detailed descriptions for the status panel
descriptions = {
    "create_metadata": "Upload your `config.py` to connect to your databases. This step fetches procedure definitions from SQL Server and populates a tracking table in Snowflake.",
    "update_flag": "Review the list of procedures and select which ones to migrate by setting their `CONVERSION_FLAG`. Then, extract the source code of flagged procedures to local files.",
    "convert_procs": "This step runs Mobilize.Net's SnowConvert tool on the extracted SQL files, automatically converting them to Snowflake-compatible syntax.",
    "process_converted_procs": "Perform final adjustments on the converted files, such as replacing placeholder schema names, to make them ready for deployment and testing.",
    "run_unit_tests": "Execute a suite of unit tests against the converted procedures in Snowflake. This verifies correctness and logs results for review."
}



# --- 2. SESSION STATE INITIALIZATION ---

def initialize_session_state():
    """Initialize session state variables to track component completion and other states."""
    if "active_component" not in st.session_state:
        st.session_state.active_component = "create_metadata"
    if "config_py" not in st.session_state:
        st.session_state.config_py = None  # will hold the uploaded file bytes
    # --- NEW: Initialize session state for the analytics toggle ---
    if "app_config" not in st.session_state:
        st.session_state.app_config = None
    if "show_analytics" not in st.session_state:
        st.session_state.show_analytics = False
    if "step_completion" not in st.session_state:
        st.session_state.step_completion = {key: False for key in component_titles}
    if 'test_results_df' not in st.session_state: st.session_state.test_results_df = None
    # --- NEW: Session state for processor inputs ---
    if 'source_schema' not in st.session_state:
        st.session_state.source_schema = ""
    if 'target_schema' not in st.session_state:
        st.session_state.target_schema = ""
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
    if "last_action_status" not in st.session_state:
        st.session_state.last_action_status = None


# Helper function to log messages from any component
def log_to_session(message):
    st.session_state.log_messages.append(message)
    # Optional: Keep log from getting too long
    if len(st.session_state.log_messages) > 100:
        st.session_state.log_messages.pop(0)


def process_action_flags():
    """Checks for temporary flags and updates the permanent state."""
    action = st.session_state.last_action_status
    if action:
        if action == 'create_metadata_success':
            st.session_state.step_completion['create_metadata'] = True
        elif action == 'update_flag_success':
            st.session_state.step_completion['update_flag'] = True
        elif action == 'convert_procs_success':
            st.session_state.step_completion['convert_procs'] = True
        elif action == 'process_procs_success':
            st.session_state.step_completion['process_converted_procs'] = True
        elif action == 'run_tests_success':
            st.session_state.step_completion['run_unit_tests'] = True
        
        # Clear the flag after processing
        st.session_state.last_action_status = None


st.set_page_config(page_title="SP Migration Assistant", layout="wide", initial_sidebar_state="expanded", menu_items=None)
initialize_session_state()
process_action_flags()



# --- SIDEBAR ---
with st.sidebar:
    st.header("SP Migration Assistant")
    st.markdown("Follow the workflow to migrate your stored procedures.")
    st.markdown("---")

    for key, label in sidebar_labels.items():
        is_completed = st.session_state.step_completion.get(key, False)
        is_active = (st.session_state.active_component == key)
        
        status_icon = "✅" if is_completed else "➡️" if is_active else "⏳"
        button_label = f"{status_icon} {label}"
        
        if st.button(button_label, use_container_width=True, type="secondary" if not is_active else "primary"):
            st.session_state.active_component = key
            st.rerun()

    st.markdown("---")
    # Overall Progress Bar
    completed_count = sum(1 for status in st.session_state.step_completion.values() if status)
    total_steps = len(component_titles)
    progress = completed_count / total_steps
    st.progress(progress, text=f"{completed_count} of {total_steps} Steps Complete")
    
    # Session Log Viewer
    with st.expander("Show Session Log"):
        st.code("\n".join(st.session_state.log_messages), language="log")

# --- MAIN PAGE LAYOUT ---
st.title("SQL Server to Snowflake Migration Tool for Stored Procedures")

# main_col, status_col = st.columns([2.5, 1.5])
main_col = st.container()  # Main content area

# --- RIGHT-HAND STATUS PANEL ---
# with status_col:
#     with st.container(border=True):
#         active_key = st.session_state.active_component
#         st.subheader(f"{icons[active_key]} Current Step")
#         st.markdown(f"**{component_titles[active_key]}**")
#         st.caption(descriptions[active_key])
        
#         st.markdown("---")
        
#         if st.session_state.step_completion.get(active_key, False):
#             st.success("Status: Completed ✅")
#         else:
#             st.warning("Status: Pending ⏳")



# --- LEFT-HAND MAIN CONTENT AREA ---
with main_col:
    active_key = st.session_state.active_component


    # 1) If we're on “Create Metadata Table,” show a file_uploader for config.py
    # --- Component 1: Create Metadata ---
    if active_key == "create_metadata":
        with st.container(border=True):
            st.subheader("Configuration")
            st.markdown("Upload your `config.py` file to provide the database connection details for the application.")
            
            uploaded = st.file_uploader(label="Upload `config.py`", type=["py"], label_visibility="collapsed")
            
            if uploaded:
                try:
                    raw_bytes = uploaded.read()
                    config_code = raw_bytes.decode("utf-8")
                    ns = {}
                    exec(config_code, {}, ns)
                    st.session_state.app_config = {
                        "SNOWFLAKE_CONFIG": ns["SNOWFLAKE_CONFIG"],
                        "SQL_SERVER_CONFIG": ns["SQL_SERVER_CONFIG"]
                    }
                    # We don't need to save the bytes anymore, as we pass the dict directly
                    st.success("Config loaded successfully. You can now run the initialization.")
                    log_to_session("Config file parsed and loaded.")
                except Exception as e:
                    st.error(f"Failed to parse config: {e}")
                    log_to_session(f"ERROR: Failed to parse config - {e}")
                    st.session_state.app_config = None
            
            st.markdown("---")
    
            # The Run button is now the primary action for this component
            st.subheader("Execution")
            st.markdown("Click the button below to connect to your databases and create/update the metadata table in Snowflake.")
            
            if st.button("🚀 Run Initialization", disabled=not st.session_state.app_config, use_container_width=True, type="primary"):
                with st.spinner("Connecting to databases and creating metadata..."):
                    try:
                        # Import the class directly
                        from scripts.create_metadata_table import CreateMetadataTable
                        
                        # Instantiate with the config from session_state and the logger
                        creator = CreateMetadataTable(
                            config=st.session_state.app_config
                            # logger=log_to_session
                        )
                        
                        # Run the method directly
                        creator.create_metadata_table()
                        
                        # THIS IS THE CRITICAL PART: Now it will be reached on success
                        st.toast("✅ Metadata table created/updated successfully!")
                        st.session_state.step_completion['create_metadata'] = True
                        st.rerun() # Rerun to update the sidebar and status panel
    
                    except Exception as e:
                        # Catch errors from the direct execution
                        st.error(f"Metadata creation failed: {e}")
                        log_to_session(f"ERROR: Metadata creation failed - {e}")
    

            
    # 2) If we are on the update_flag page
    elif active_key == "update_flag":
        # config = load_config_from_session()
        # if config:
        if st.session_state.app_config:
            try:
                from scripts.update_flag_st import SelectProcedures
                select_procedures = SelectProcedures(config=st.session_state.app_config)
                select_procedures.run_update_flag()
                st.session_state.step_completion['update_flag'] = True
            except ImportError:
                 st.error("❌ `update_flag_st.py` not found. Make sure it's in the same directory.")
            except Exception as e:
                st.error(f"❌ Error running the update flag interface: {e}")
        else:
            # Guide the user if the config isn't loaded
            st.warning("`config.py` has not been uploaded. Please go to '1. Create Metadata Table' to upload it.")
    
    
    elif active_key == "convert_procs":
            if st.session_state.app_config:
                try:
                    # Import our new page class
                    from scripts.convert_scripts_st import ConvertPage
                    
                    # Create an instance and pass the config
                    convert_ui = ConvertPage(config=st.session_state.app_config)
                    
                    # Call the main method to render the page
                    convert_ui.display_page()

                    
        
                except ImportError:
                    st.error("❌ `convert_scripts_st.py` not found. Make sure it's in the same directory.")
                except Exception as e:
                    st.error("❌ An error occurred while loading the conversion page:")
                    st.exception(e)
            else:
                # Guide the user if the config isn't loaded
                st.warning("`config.py` has not been uploaded. Please go to '1. Create Metadata Table' to upload it.")
    
    
    
    elif active_key == "run_unit_tests":
        if st.session_state.app_config:
            try:
                # Import our new page class
                from scripts.run_py_tests import UnitTestPage
                
                # Create an instance and pass the config
                unit_test_ui = UnitTestPage(config=st.session_state.app_config)
                
                # Call the main method to render the page
                unit_test_ui.display_page()
                # st.session_state.step_completion['run_unit_tests'] = True
    
            except ImportError:
                st.error("❌ `run_unit_tests_st.py` not found. Make sure it's in the same directory.")
            except Exception as e:
                st.error("❌ An error occurred while loading the unit test page:")
                st.exception(e)
        else:
            # Guide the user if the config isn't loaded
            st.warning("`config.py` has not been uploaded. Please go to '1. Create Metadata Table' to upload it.")
    
    
    
    elif active_key == "process_converted_procs":
                        # This component's UI can be defined here or modularized
        with st.container(border=True):
             st.subheader("Schema Replacement")
             source_schema = st.text_input("Source Schema (in converted files)", "dbo")
             target_schema = st.text_input("Target Snowflake Schema", "MIGRATION_SCHEMA")
             if st.button("🚀 Process Files", use_container_width=True):
                 from scripts.process_sc_script import ScScriptProcessor
                 ScScriptProcessor(source_schema, target_schema).process_all_files()
                 st.success("✅ Processing complete!")
                 st.session_state.step_completion['process_converted_procs'] = True
                 st.rerun()
 