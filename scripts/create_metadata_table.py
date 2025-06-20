#!/usr/bin/env python3
# from config import SNOWFLAKE_CONFIG, SQL_SERVER_CONFIG
import streamlit as st
from scripts.log import log_info
import pyodbc
import snowflake.connector
from datetime import datetime

METADATA_TABLE = "procedures_metadata"

class CreateMetadataTable:
    def __init__(self, config:dict):
        if not config or "SNOWFLAKE_CONFIG" not in config:
            st.error("Configuration is missing or invalid.")
            st.stop()
        
        # Store the needed config parts as instance variables
        self.snowflake_config = config["SNOWFLAKE_CONFIG"]
        self.sql_server_config = config["SQL_SERVER_CONFIG"]
        
        # Now you can initialize your connection or other attributes
        # METADATA_TABLE = METADATA_TABLE
        pass

    def fetch_sqlserver_procedures(self):
        """Connects to SQL Server and returns a list of dicts with procedure metadata."""
        # cfg = SQL_SERVER_CONFIG
        sql_server_config = self.sql_server_config
    
        conn_str = f"DRIVER={sql_server_config['driver']};SERVER={sql_server_config['server']};DATABASE={sql_server_config['database']};UID={sql_server_config['username']};PWD={sql_server_config['password']}"
        rows = []
        try:
            cnxn = pyodbc.connect(conn_str)
            cursor = cnxn.cursor()
        
            # 1) Routines
            # Get all stored procedures
            
            cursor.execute("""
                SELECT 
                  SPECIFIC_CATALOG AS dbname,
                  SPECIFIC_SCHEMA  AS schema_name,
                  SPECIFIC_NAME    AS procedure_name,
                  ROUTINE_DEFINITION AS procedure_definition
                FROM INFORMATION_SCHEMA.ROUTINES
                WHERE ROUTINE_TYPE = 'PROCEDURE'
            """)
            procs = cursor.fetchall()
        
            # 2) Parameters 
            # Get all parameters for the stored procedures 
            cursor.execute("""
                SELECT
                  SPECIFIC_NAME      AS procedure_name,
                  PARAMETER_MODE     AS mode,
                  PARAMETER_NAME     AS name,
                  DATA_TYPE          AS data_type,
                  CHARACTER_MAXIMUM_LENGTH AS char_length
                FROM INFORMATION_SCHEMA.PARAMETERS
                ORDER BY SPECIFIC_NAME, ORDINAL_POSITION
            """)
            params = cursor.fetchall()
        
            # Group params by proc name
            # Create a dictionary where the key is the procedure name and the value is a list of parameter descriptions
            params_by_proc = {}
            for p in params:
                desc = f"{p.mode} {p.name} {p.data_type}"
                if p.char_length is not None:
                    desc += f"({p.char_length})"
                params_by_proc.setdefault(p.procedure_name, []).append(desc)
        
            # Build result
            # Create a list of dictionaries, each representing a procedure with its metadata and parameters
            # rows = []
            for r in procs:
                pname = r.procedure_name
                rows.append({
                    "SOURCE":               "SQLServer",
                    "DBNAME":               r.dbname,
                    "SCHEMA_NAME":          r.schema_name,
                    "PROCEDURE_NAME":       pname,
                    "PROCEDURE_DEFINITION": r.procedure_definition,
                    "PARAMETERS":           ", ".join(params_by_proc.get(pname, [])),
                })
        finally:
            cursor.close()
            cnxn.close()
        return rows
    

    #     """Connects to SQL Server and returns a list of dicts with procedure metadata."""
    def load_into_snowflake(self,proc_list):
        """Creates the target table if needed and bulk‐loads procedure metadata."""
        sf_cfg = self.snowflake_config
        inserted_count = 0
        updated_count = 0
        ctx = snowflake.connector.connect(
            user=sf_cfg['user'],
            password=sf_cfg['password'],
            account=sf_cfg['account'],
            warehouse=sf_cfg['warehouse'],
            database=sf_cfg['database'],
            schema=sf_cfg['schema'],
            role=sf_cfg['role']
        )
        cs = ctx.cursor()
        try:
            # create table
            # Check if the table already exists
            cs.execute(f"""
            CREATE TABLE IF NOT EXISTS {METADATA_TABLE} (
              SOURCE                STRING,
              DBNAME                STRING,
              SCHEMA_NAME           STRING,
              PROCEDURE_NAME        STRING,
              PROCEDURE_DEFINITION  STRING,
              CONVERSION_FLAG       BOOLEAN,
              LOAD_TIMESTAMP        TIMESTAMP_NTZ(9),
              SNOWFLAKE_DBNAME      STRING,
              SNOWFLAKE_SCHEMA_NAME STRING,
              SNOWFLAKE_DDL         STRING,
              PARAMETERS            STRING,
              IS_DEPLOYED           BOOLEAN,
              ERRORS                STRING
            )
            """)
        
                # --- MODIFIED LOGIC: Use MERGE instead of INSERT ---
            merge_sql = f"""
                MERGE INTO {METADATA_TABLE} AS T
                USING (
                    SELECT
                        %s AS SOURCE,
                        %s AS DBNAME,
                        %s AS SCHEMA_NAME,
                        %s AS PROCEDURE_NAME,
                        %s AS PROCEDURE_DEFINITION,
                        %s AS PARAMETERS
                ) AS S
                ON T.SCHEMA_NAME = S.SCHEMA_NAME AND T.PROCEDURE_NAME = S.PROCEDURE_NAME
                WHEN MATCHED THEN
                    UPDATE SET
                        T.PROCEDURE_DEFINITION = S.PROCEDURE_DEFINITION,
                        T.PARAMETERS = S.PARAMETERS,
                        T.LOAD_TIMESTAMP = CURRENT_TIMESTAMP()
                WHEN NOT MATCHED THEN
                    INSERT (
                        SOURCE, DBNAME, SCHEMA_NAME, PROCEDURE_NAME, PROCEDURE_DEFINITION,
                        PARAMETERS, CONVERSION_FLAG, LOAD_TIMESTAMP, SNOWFLAKE_DBNAME,
                        SNOWFLAKE_SCHEMA_NAME, SNOWFLAKE_DDL, IS_DEPLOYED, ERRORS
                    )
                    VALUES (
                        S.SOURCE, S.DBNAME, S.SCHEMA_NAME, S.PROCEDURE_NAME, S.PROCEDURE_DEFINITION,
                        S.PARAMETERS, %s, CURRENT_TIMESTAMP(), %s,
                        %s, '', FALSE, ''
                    )
                """
    
    
    
    
            # insert_sql = f"""
            # INSERT INTO {METADATA_TABLE} (
            #   SOURCE, DBNAME, SCHEMA_NAME, PROCEDURE_NAME, PROCEDURE_DEFINITION,
            #   CONVERSION_FLAG, LOAD_TIMESTAMP,
            #   SNOWFLAKE_DBNAME, SNOWFLAKE_SCHEMA_NAME, SNOWFLAKE_DDL,
            #   PARAMETERS, IS_DEPLOYED, ERRORS
            # ) VALUES (
            #   %s, %s, %s, %s, %s,
            #   %s, CURRENT_TIMESTAMP(),
            #   %s, %s, %s,
            #   %s, %s, %s
            # )
            # """
            # inserted_count = 0
            # updated_count = 0
    
        
            for p in proc_list:
            #     cs.execute(merge_sql, (
            #         p["SOURCE"],
            #         p["DBNAME"],
            #         p["SCHEMA_NAME"],
            #         p["PROCEDURE_NAME"],
            #         p["PROCEDURE_DEFINITION"],
            #         False,                      # CONVERSION_FLAG
            #         sf_cfg['database'],         # SNOWFLAKE_DBNAME
            #         sf_cfg['schema'],           # SNOWFLAKE_SCHEMA_NAME
            #         "",                         # SNOWFLAKE_DDL placeholder
            #         p["PARAMETERS"],
            #         False,                       # IS_DEPLOYED
            #         ""                          # ERRORS
            #     ))

                params_tuple = (
                    # For USING clause (6 items)
                    p["SOURCE"],
                    p["DBNAME"],
                    p["SCHEMA_NAME"],
                    p["PROCEDURE_NAME"],
                    p["PROCEDURE_DEFINITION"],
                    p["PARAMETERS"],
                    # For WHEN NOT MATCHED -> INSERT clause (3 items)
                    False,                      # CONVERSION_FLAG
                    sf_cfg['database'],         # SNOWFLAKE_DBNAME
                    sf_cfg['schema']            # SNOWFLAKE_SCHEMA_NAME
                )
                cs.execute(merge_sql, params_tuple)
    

                result_scan_query = 'SELECT "number of rows inserted", "number of rows updated" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))'
                cs.execute(result_scan_query)
                
                # Fetch the single row of results
                result_row = cs.fetchone()
                if result_row:
                    rows_inserted, rows_updated = result_row
                    inserted_count += rows_inserted
                    updated_count += rows_updated
        

            ctx.commit()
            log_info(f"   → New procedures inserted: {inserted_count}")
            log_info(f"   → Existing procedures updated: {updated_count}")
        finally:
            cs.close()
            ctx.close()
    
    
    def create_metadata_table(self):
        log_info("🔍 Fetching procedures from SQL Server…")
        procs = self.fetch_sqlserver_procedures()
        log_info(f"   → {len(procs)} procedures found.")
        log_info("⏫ Loading metadata into Snowflake…")
        if procs:
            self.load_into_snowflake(procs)

        log_info("✅ Done.")
    



# if __name__ == "__main__":
#     # CreateMetadataTable().create_metadata_table()
#     try:
#     # Step 1: Import the config variables from the config.py file
#     # This works because app.py created this file in the root directory.
#         from config import SNOWFLAKE_CONFIG, SQL_SERVER_CONFIG
    
#         # Step 2: Assemble the config dictionary that the class expects
#         app_config = {
#             "SNOWFLAKE_CONFIG": SNOWFLAKE_CONFIG,
#             "SQL_SERVER_CONFIG": SQL_SERVER_CONFIG
#         }
    
#         # Step 3: Now, instantiate the class WITH the config dictionary
#         metadata_creator = CreateMetadataTable(config=app_config)
#         metadata_creator.create_metadata_table()
        
#         print("Script finished successfully.")

#     except ImportError:
#         # This error will happen if config.py doesn't exist.
#         print("ERROR: config.py not found.")
#         print("This script is intended to be run by the main Streamlit app after config has been uploaded.")
#         exit(1) # Exit with a non-zero status code to indicate failure
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         exit(1)
    
    