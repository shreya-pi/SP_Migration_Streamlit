
# --- START OF FILE convert_scripts.py ---

import subprocess
import os
import sys
import shutil
import platform
import tempfile
import datetime
import re
import requests
import tarfile
import zipfile
import time

# --- Helper to load .env file ---
def load_env_vars():
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.isfile(env_path):
        try:
            with open(env_path, "r") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    if key.strip() and key.strip() not in os.environ:
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")
            print("INFO: Loaded environment variables from .env")
        except Exception as e:
            print(f"ERROR: Failed to load .env: {e}")

load_env_vars()

class SnowConvertRunner:
    def __init__(self, ui_logger=None):
        """
        Initializes the runner.
        :param ui_logger: A callback function (e.g., st.write) to send logs to the UI.
        """
        self.input_path = "./extracted_procedures"
        self.output_path = "./converted_procedures"
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs("./logs", exist_ok=True)
        self.log_file = "./logs/assessment.txt"
        self.ui_logger = ui_logger

    def _log(self, message: str, level: str = "INFO"):
        """Logs a message to the UI logger if available, otherwise prints."""
        log_message = f"[{level}] {message}"
        if self.ui_logger:
            self.ui_logger(log_message)
        else:
            print(log_message)

    def setup_cli(self):
        """Checks if 'snowct' is on PATH and attempts to install it if not."""
        self._log("Verifying SnowConvert CLI (snowct) installation...")
        if shutil.which("snowct"):
            self._log("Found existing SnowConvert CLI on PATH.")
            return True

        current_os = platform.system().lower()
        self._log(f"'snowct' not found. Detected OS: {current_os}. Attempting automatic install…")

        try:
            if current_os == "darwin": self._install_cli_macos()
            elif current_os in ("windows", "win32"): self._install_cli_windows()
            else:
                self._log(f"Automatic install only supports macOS and Windows. Detected OS: {current_os}", "ERROR")
                self._log("Please install SnowConvert CLI manually and re-run.", "ERROR")
                return False
        except Exception as e:
            self._log(f"CLI installation failed: {e}", "ERROR")
            return False

        if not shutil.which("snowct"):
            self._log("'snowct' is still not on PATH after installation. Verify installation.", "ERROR")
            return False
        
        self._log("✅ SnowConvert CLI is ready.")
        return True

    def _install_cli_macos(self):
        # (This method's internal logic is the same, but uses self._log)
        machine = platform.machine().lower()
        if machine in ("x86_64", "amd64"): arch, url = "x64", "https://sctoolsartifacts.z5.web.core.windows.net/darwin_x64/prod/cli/SnowConvert-CLI-mac.tar"
        elif machine in ("arm64", "aarch64"): arch, url = "arm64", "https://sctoolsartifacts.z5.web.core.windows.net/darwin_arm64/prod/cli/SnowConvert-CLI-arm64-mac.tar"
        else: raise Exception(f"Unsupported macOS architecture: {machine}")
        
        extract_to = os.path.abspath("./SnowConvert-CLI-macos")
        orchestrator_path = os.path.join(extract_to, "orchestrator")
        
        self._log(f"Downloading SnowConvert for macOS ({arch})...")
        # Download and extraction logic here (unchanged, just replace log_info/error with self._log)
        with tempfile.TemporaryDirectory() as tmpdir:
            tar_path = os.path.join(tmpdir, "snowct.tar.gz")
            # ... download request with progress ...
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(tar_path, "wb") as f: f.write(r.content)
            
            self._log("Download complete. Extracting...")
            with tarfile.open(tar_path, "r:gz") as tar: tar.extractall(path=extract_to)

        os.environ["PATH"] = orchestrator_path + os.pathsep + os.environ.get("PATH", "")
        self._log(f"Added '{orchestrator_path}' to PATH.")

    def _install_cli_windows(self):
        # (This method's internal logic is the same, but uses self._log)
        machine = platform.machine().lower()
        if machine in ("amd64", "x86_64"): arch, url = "x64", "https://sctoolsartifacts.z5.web.core.windows.net/windows/prod/cli/SnowConvert-CLI-windows.zip"
        elif machine in ("arm64", "aarch64"): arch, url = "arm64", "https://sctoolsartifacts.z5.web.core.windows.net/windows/prod/cli/SnowConvert-CLI-arm64-windows.zip"
        else: raise Exception(f"Unsupported Windows architecture: {machine}")

        extract_to = os.path.abspath("./SnowConvert-CLI-windows")
        orchestrator_path = os.path.join(extract_to, "orchestrator")
        
        self._log(f"Downloading SnowConvert for Windows ({arch})...")
        # Download and extraction logic here (unchanged, just replace log_info/error with self._log)
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "snowct.zip")
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(zip_path, "wb") as f: f.write(r.content)
            
            self._log("Download complete. Extracting...")
            with zipfile.ZipFile(zip_path, "r") as z: z.extractall(extract_to)

        os.environ["PATH"] = orchestrator_path + os.pathsep + os.environ.get("PATH", "")
        self._log(f"Added '{orchestrator_path}' to PATH.")

    def setup_license(self):
        """Checks for an active license and installs one from env if needed."""
        self._log("Verifying SnowConvert license...")
        
        def get_ac_output():
            proc = subprocess.run(["snowct", "show-ac"], capture_output=True, text=True, input="Yes\n")
            return proc.stdout
        
        def has_active_license(output):
            now = datetime.datetime.now()
            for match in re.finditer(r"Expiration date:\s*(.+)", output):
                try:
                    exp_dt = datetime.datetime.strptime(match.group(1).strip(), "%m/%d/%Y %H:%M:%S")
                    if exp_dt > now: return True
                except ValueError: continue
            return False

        if has_active_license(get_ac_output()):
            self._log("✅ Found an existing active license.")
            return True

        self._log("No active license found. Checking SNOWCONVERT_ACCESS_CODE environment variable...")
        access_code = os.environ.get("SNOWCONVERT_ACCESS_CODE", "").strip()
        if not access_code:
            self._log("Environment variable SNOWCONVERT_ACCESS_CODE is not set.", "ERROR")
            return False

        self._log("Installing access code from environment...")
        try:
            subprocess.run(["snowct", "install-ac", access_code], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            self._log(f"Error installing access code: {e.stderr.strip()}", "ERROR")
            return False
        
        if not has_active_license(get_ac_output()):
            self._log("License was installed but is not active. Check the code.", "ERROR")
            return False
        
        self._log("✅ License installed and active.")
        return True

    def run_conversion(self):
        """Runs the main snowct conversion command."""
        command = ["snowct", "sql-server", "--input", self.input_path, "--output", self.output_path]
        self._log(f"Executing conversion: {' '.join(command)}")
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            self._write_log(result.stdout)
            self._log("✅ Conversion completed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            self._write_log(e.stderr)
            self._log(f"Conversion failed. Check logs at {self.log_file}", "ERROR")
            return False

    def _write_log(self, content):
        with open(self.log_file, "w") as f: f.write(content)

if __name__ == "__main__":
    runner = SnowConvertRunner()
    if runner.setup_cli() and runner.setup_license():
        runner.run_conversion()


