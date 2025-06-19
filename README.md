# SP Migration Assistant

This application is a Streamlit-based tool designed to assist in the migration of SQL Server stored procedures to Snowflake. It provides a step-by-step workflow for users to upload configuration files, select and flag procedures for migration, convert procedures using SnowConvert, process converted scripts, and execute unit tests to verify correctness.

## Main Features

- **End-to-End Migration Workflow**  
    Navigate a guided, stepwise process that takes you from initial setup to final validation. Each stage is clearly defined, ensuring a structured and stress-free migration experience.

- **Secure, Configurable Database Connections**  
    Effortlessly manage and upload your SQL Server and Snowflake connection details via a dedicated `config.py` file. Sensitive information is handled securely, and connections are validated before proceeding.

- **Automated Procedure Discovery & Inventory**  
    Instantly connect to your SQL Server instance to scan, fetch, and display all available stored procedures. Review, filter, and select procedures for migration with ease—no manual cataloging required.

- **Granular Migration Control**  
    Select and flag only the procedures you wish to migrate. This selective approach gives you full control over the migration scope, supporting phased or targeted migrations.

- **Integrated SnowConvert Automation**  
    Harness the power of SnowConvert tool directly within the app. Automatically convert SQL Server stored procedures to Snowflake-compatible scripts, minimizing manual intervention and reducing conversion errors.

- **Customizable Script Post-Processing**  
    Apply automated post-processing to converted scripts, including schema name replacement, formatting, and other adjustments. Tailor the output to meet your organization’s deployment standards.

- **Built-in Unit Testing & Validation**  
    Execute comprehensive unit tests on migrated procedures within Snowflake. Detailed logs and result reports help you quickly identify issues and verify correctness before production deployment.

- **Intuitive, Interactive Streamlit UI**  
    Enjoy a modern, user-friendly interface with sidebar navigation, real-time progress indicators, and contextual help. Each migration step is accompanied by clear instructions and feedback.

- **Robust Session State Management**  
    All workflow progress, user inputs, and logs are preserved throughout your session. Pause and resume migration activities without losing your place or data.

- **Extensible & Modular Architecture**  
    The application’s modular design makes it easy to add new migration steps, integrate custom logic, or plug in external scripts—future-proofing your migration process.

- **Comprehensive Logging & Error Handling**  
    Every action is logged in detail, with clear error messages and troubleshooting guidance. This transparency aids in debugging, auditing, and continuous improvement.

- **Designed for Teams & Iterative Projects**  
    Whether you’re migrating a handful of procedures or hundreds, the tool supports collaborative workflows and iterative migrations, making it ideal for teams and large-scale projects.



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
