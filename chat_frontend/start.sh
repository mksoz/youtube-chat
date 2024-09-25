#!/bin/bash

# Function to install Miniforge if it's not installed
install_conda() {
    if [[ -d "$HOME/miniforge3" ]]; then
        echo "Miniforge is already installed. Skipping installation."
        return
    fi

    echo "Installing Miniforge for Linux..."
    wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
    bash Miniforge3-Linux-x86_64.sh -b -p $HOME/miniforge3

    # Add Conda to the PATH
    export PATH="$HOME/miniforge3/bin:$PATH"
    source $HOME/miniforge3/etc/profile.d/conda.sh
}

# Check if Conda is installed
check_conda() {
    if ! command -v conda &> /dev/null; then
        echo "Conda is not installed. Proceeding with installation..."
        install_conda
    else
        echo "Conda is already installed."
    fi
}

# Function to check if the requirements file exists
check_requirements() {
    if [[ ! -f "$1" ]]; then
        echo "ERROR: Requirements file not found at $1"
        exit 1
    fi
}

# Start frontend setup
echo "Starting frontend setup..."

# Check if Conda is installed
check_conda

# Set up the Conda environment
ENV_NAME="streamlit_env"
if conda env list | grep -q $ENV_NAME; then
    echo "Conda environment $ENV_NAME already exists. Trying to activate..."
    source $(conda info --base)/etc/profile.d/conda.sh
    if ! conda activate $ENV_NAME; then
        echo "Failed to activate environment $ENV_NAME. Recreating it..."
        conda remove --name $ENV_NAME --all -y
        conda create -n $ENV_NAME python=3.9 -y
        conda activate $ENV_NAME
    fi
else
    echo "Creating Conda environment $ENV_NAME..."
    conda create -n $ENV_NAME python=3.9 -y
    conda activate $ENV_NAME
fi

# Install project dependencies
REQ_FILE="requirements.txt"
echo "Installing project dependencies..."
check_requirements "$REQ_FILE"
pip install --upgrade pip
pip install -r "$REQ_FILE"

# Install watchdog to improve performance
echo "Installing watchdog for performance improvements..."
pip install watchdog

# Check if the app.py file exists
if [[ ! -f "app/app.py" ]]; then
    echo "ERROR: app/app.py file not found"
    exit 1
fi

# Run the frontend with Streamlit
echo "Starting frontend with Streamlit..."
streamlit run app/app.py --server.port=8501 --server.enableCORS=false --server.enableXsrfProtection=false
