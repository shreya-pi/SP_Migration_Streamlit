# Dockerfile

# ===================================
# Stage 1: The "builder" stage
# We'll install dependencies here.
# ===================================
FROM python:3.11-slim AS builder

# Set the working directory
WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1



# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt




# ===================================
# Stage 2: The "final" production image
# This is the small, clean image we'll actually deploy.
# ===================================
FROM python:3.11-slim AS final

# Set a non-root user for security
# RUN useradd --create-home appuser
WORKDIR /app
# USER appuser


# [STEP 1: INSTALL ALL SYSTEM DEPENDENCIES IN A SINGLE LAYER]
# This unified RUN command prevents package version conflicts by allowing 'apt'
# to resolve the entire dependency tree at once.
RUN apt-get update && \
    # Install prerequisite tools for adding new repositories
    apt-get install -y --no-install-recommends gnupg curl ca-certificates && \
    \
    # Add the Microsoft GPG key and repository
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    \
    # Update package lists again after adding the new repository
    apt-get update && \
    \
    # Install all required packages together.
    # ACCEPT_EULA is required for the Microsoft driver.
    # gcc, g++, unixodbc-dev are for building pyodbc.
    # msodbcsql17 is the actual MS SQL driver.
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends gcc g++ unixodbc-dev msodbcsql17 && \
    \
    # [CLEANUP]
    # Remove temporary files to keep the final image size small.
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Copy the pre-built wheels from the "builder" stage
COPY --from=builder /app/wheels /wheels

# Install the dependencies from the local wheels
RUN pip install --no-cache /wheels/*

# Copy the application code
COPY . .

# Expose the port your app will run on
EXPOSE 8000

# The command to run your app
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]








# # ---- Base Stage ----
# # Use an official Python runtime as a parent image.
# # Using a specific version is good for reproducibility.
# # The '-slim' variant is smaller than the full one.
# FROM python:3.11-slim

# # Set the working directory in the container
# WORKDIR /app

# # Prevent python from writing pyc files to disc
# ENV PYTHONDONTWRITEBYTECODE=1
# # Ensure python output is sent straight to the terminal
# ENV PYTHONUNBUFFERED=1

# # ---- Builder Stage ----
# # This stage is for installing dependencies
# # FROM base AS builder

# # Install system dependencies that might be needed by some Python packages
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # Copy the requirements file into the container
# COPY requirements.txt .

# # Install the Python dependencies
# RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# # ---- Final Stage ----
# # This is the final image that will be used to run the app
# # FROM base AS final

# # Copy the pre-built wheels from the builder stage
# COPY --from=builder /app/wheels /wheels
# COPY --from=builder /usr/local/bin/streamlit /usr/local/bin/

# # Install the dependencies from the wheels
# RUN pip install --no-cache /wheels/*

# # Copy all your application source code into the container
# # IMPORTANT: This assumes all your .py files are in the same directory.
# COPY app.py .
# COPY py_output.py .
# COPY py_test.py .
# COPY create_metadata_table.py .
# COPY extract_procedures.py .
# COPY convert_scripts.py .
# COPY process_sc_script.py .
# COPY update_flag_st.py .

# # Expose the port that Streamlit runs on
# EXPOSE 8501

# # Set a healthcheck to ensure the container is running correctly
# HEALTHCHECK CMD streamlit hello --server.port 8501

# # The command to run your app when the container starts
# # --server.address=0.0.0.0 is needed to access the app from outside the container
# CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
 