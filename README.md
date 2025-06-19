# SP Migration Assistant

This application is a Streamlit-based tool designed to assist in the migration of SQL Server stored procedures to Snowflake. It provides a step-by-step workflow for users to upload configuration files, select and flag procedures for migration, convert procedures using SnowConvert, process converted scripts, and execute unit tests to verify correctness.


## Workflow

1. **Initialize & Create Metadata**
    - Upload a `config.py` file containing database connection details.
    - Connects to SQL Server and Snowflake to fetch procedure definitions and populate a tracking table in Snowflake.
2. **Select, Flag & Extract Procedures**
    - Review and select stored procedures for migration.
    - Set conversion flags and extract source code of flagged procedures to local files.
3. **Convert Procedures with SnowConvert**
    - Automatically convert extracted SQL files to Snowflake-compatible syntax using SnowConvert tool.
4. **Process & Finalize Scripts**
    - Perform final adjustments on converted files, such as replacing schema names, to prepare scripts for deployment and testing.
5. **Execute Unit Tests & Review Results**
    - Run a suite of unit tests against the converted procedures in Snowflake.
    - Review and log test results for verification.

## User Interface

- **Sidebar Navigation**: Step-by-step navigation with progress tracking and session logs.
- **Main Content Area**: Contextual UI for each migration step, including file uploaders, buttons, and input fields.
- **Status Panel**: Displays current step, detailed descriptions, and completion status.

## Session State Management

- Tracks active workflow step, configuration, completion status, log messages, and user inputs using Streamlit's session state.

## Extensibility

- Modular design allows for easy integration of new migration steps or custom logic.
- External scripts (in the `scripts/` directory) handle database operations, conversion, and testing.

## Requirements

- Python 3.x
- Streamlit
- pandas
- Additional dependencies as required by scripts in the `scripts/` directory.

## Usage

1. Launch the app with:

   ```bash
   streamlit run app.py
   ```

2. Follow the sidebar workflow to complete each migration step.
3. Upload your `config.py` file and proceed through each step as guided by the UI.

## Note

- Ensure all required scripts are present in the `scripts/` directory.
- The `config.py` file must define `SNOWFLAKE_CONFIG` and `SQL_SERVER_CONFIG` dictionaries.
