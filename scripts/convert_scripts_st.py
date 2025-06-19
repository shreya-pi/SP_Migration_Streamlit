# --- START OF FILE convert_scripts_st.py ---

import streamlit as st
from scripts.convert_scripts import SnowConvertRunner # Import the refactored backend class
import re
import os

class ConvertPage:
    def __init__(self, config: dict):
        self.config = config
        # Initialize session state for this page if not already present
        if "show_analytics" not in st.session_state:
            st.session_state.show_analytics = False
        if "step_completion" not in st.session_state:
            st.session_state.step_completion = {
                'convert_procs': False
            }

    def display_page(self):
        """Renders the entire UI for the conversion component."""
        with st.container(border=True):
            st.subheader("⚙️ Run Code Conversion")
            st.markdown(
                """
                This tool converts SQL Server stored procedures to Snowflake using the SnowConvert
                Click the button below to start the process. The tool will:
                1.  Verify the SnowConvert command-line tool (`snowct`) is installed (and install it if missing).
                2.  Verify you have an active license (and install one from your `.env` file if needed).
                3.  Run the conversion on all files in the `extracted_procedures` directory.
                """
            )
            if st.button("▶️ **Run Conversion Process**", type="primary", use_container_width=True):
                self.run_conversion_workflow()

        if st.session_state.get("show_analytics"):
            st.markdown("---")
            with st.container(border=True):
                st.subheader("📊 Conversion Analytics")
                self.display_analytics_dashboard()

    def run_conversion_workflow(self):
        """Orchestrates the conversion process and displays real-time feedback."""
        log_container = st.container(border=True)
        
        # This function will be passed to the backend to stream logs to the UI
        def ui_logger(message):
            log_container.text(message)

        with st.status("Running conversion workflow...", expanded=True) as status:
            try:
                runner = SnowConvertRunner(ui_logger=ui_logger)
                
                status.update(label="Step 1/3: Setting up SnowConvert CLI...")
                if not runner.setup_cli():
                    raise Exception("Failed to set up SnowConvert CLI.")

                status.update(label="Step 2/3: Verifying license...")
                if not runner.setup_license():
                    raise Exception("Failed to set up SnowConvert license.")

                status.update(label="Step 3/3: Converting procedures...")
                if not runner.run_conversion():
                    raise Exception("The conversion command failed.")
                
                status.update(label="✅ Workflow Complete!", state="complete")
                st.session_state.show_analytics = True # Auto-show analytics on success
                st.session_state.step_completion['convert_procs'] = True

            except Exception as e:
                status.update(label=f"❌ Error: {e}", state="error")
        
        # Rerun to make the analytics dashboard appear if it was set to true
        if st.session_state.show_analytics:
            st.rerun()

    def display_analytics_dashboard(self):
        """Renders the assessment.txt summary dashboard."""
        assessment_file_path = "logs/assessment.txt"
        if not os.path.exists(assessment_file_path):
            st.error(f"❌ Assessment file not found at `{assessment_file_path}`.")
            return

        with open(assessment_file_path, "r", encoding='utf-8') as f:
            content = f.read()

        def parse_metrics(text):
            patterns = {
                "Files": r"- Files:\s+(\d+)", "Not Generated": r"- Files Not Generated:\s+(\d+)",
                "Total LOC": r"- Total lines of code:\s+(\d+)", "Auto-Conv %": r"- Automatically converted:\s+([\d\.]+%)",
                "Time": r"- Conversion time:\s+([\d:\.]+)", "Speed (LOC/s)": r"- Conversion speed:\s+(\d+)\s+lines",
            }
            data = {name: (match.group(1) if (match := re.search(p, text, re.M)) else "N/A") for name, p in patterns.items()}
            return data

        data = parse_metrics(content)
        c1, c2, c3 = st.columns(3)
        c1.metric("Files Converted", data["Files"])
        c2.metric("Total Lines of Code", data["Total LOC"])
        c3.metric("Conversion Time", data["Time"])
        c4, c5, c6 = st.columns(3)
        c4.metric("Files Not Generated", data["Not Generated"], delta_color="inverse")
        c5.metric("Automatic Conversion", data["Auto-Conv %"])
        c6.metric("Speed (LOC/sec)", data["Speed (LOC/s)"])

        with st.expander("View Full Assessment Report"):
            st.code(content, language='text')