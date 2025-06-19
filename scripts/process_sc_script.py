import re
import os
from pathlib import Path
from scripts.log import log_info,log_error


class ScScriptProcessor:
    def __init__(self, source_schema, target_schema):
        self.source_schema = source_schema
        self.target_schema = target_schema

        input_folder = "./converted_procedures/Output/SnowConvert"
        output_folder = "./processed_procedures"

        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)  # Create output folder if it doesn't exist

    def process_sql_script(self, sql_script):
        """Processes a SQL script by applying transformations."""
        # Step 1: Remove all SQL-style comments
        sql_script = re.sub(r'--.*', '', sql_script)  # Remove single-line comments
        sql_script = re.sub(r'/\*.*?\*/', '', sql_script, flags=re.DOTALL)  # Remove multi-line comments


        # Convert source_schema to target_schema for all occurrences except for 'PROCEDURE'
        # sql_script = re.sub(r'(?<!PROCEDURE\s){source_schema}\.([A-Za-z_][A-Za-z0-9_]*)', r'{target_schema}\1', sql_script)
        sql_script = re.sub(rf"\b{self.source_schema}\b", self.target_schema, sql_script, flags=re.IGNORECASE)

        # Step 2: Convert column names to string format (except for `dbo.table_name`)
        # sql_script = re.sub(
        #     r'\b(?!{source_schema}\.[a-zA-Z_0-9]*)\b([a-zA-Z_]+)\.([a-zA-Z_]+)',
        #     lambda m: f"{m.group(1)}.\"{m.group(2)}\"",
        #     sql_script
        # )

        # Step 3: Remove lines after '!!!RESOLVE EWI!!!'
        lines = sql_script.splitlines()
        processed_lines = []
        skip_next = False

        for line in lines:
            if '!!!RESOLVE EWI!!!' in line:
                skip_next = True  # Mark the next line for removal
                continue
            if skip_next:
                skip_next = False
                continue
            processed_lines.append(line)

        sql_script = '\n'.join(processed_lines)


        # Step 5: Convert 'dbo' to 'TESTSCHEMA_MG'
        # sql_script = re.sub(rf'\b{source_schema}\b', f"{target_schema}", sql_script)

        return sql_script
    
    

    def process_all_files(self):
        """Processes all SQL files in the input folder and saves the processed versions."""
        for sql_file in self.input_folder.glob("*.sql"):
            with sql_file.open("r", encoding="utf-8-sig") as file:
                sql_script = file.read()

            processed_sql = self.process_sql_script(sql_script)

            # Save the processed SQL script
            output_file_path = self.output_folder / f"processed_{sql_file.name}"
            with output_file_path.open("w", encoding="utf-8") as output_file:
                output_file.write(processed_sql)

            log_info(f"Processed: {sql_file.name} → {output_file_path.name}")





