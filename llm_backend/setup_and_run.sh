#!/bin/bash

# Function to check for a GPU and configure CMAKE_ARGS
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        echo "Found an NVIDIA GPU. Using CUDA."
        export CMAKE_ARGS="-DGGML_CUDA=on"
    else
        echo "No NVIDIA GPU found. Using CPU with OpenBLAS."
        export CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"
    fi
}

# Function to install Miniforge if it's not installed
install_conda() {
    if [[ -d "$HOME/miniforge3" ]]; then
        echo "Miniforge is already installed."
        export PATH="$HOME/miniforge3/bin:$PATH"
        source $HOME/miniforge3/etc/profile.d/conda.sh
        return
    fi

    echo "Installing Miniforge..."
    wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
    bash Miniforge3-Linux-x86_64.sh -b -p $HOME/miniforge3

    export PATH="$HOME/miniforge3/bin:$PATH"
    source $HOME/miniforge3/etc/profile.d/conda.sh
}

# Function to check if Conda is installed
check_conda() {
    if ! command -v conda &> /dev/null; then
        echo "Conda is not installed. Installing Miniforge..."
        install_conda
    else
        echo "Conda is already installed."
    fi
}

# Function to clear pip cache
clear_cache() {
    echo "Clearing pip cache..."
    pip cache purge
}

# Detect the operating system and set CMAKE_ARGS
detect_os_and_set_cmake_args() {
    OS=$(uname -s)
    case "$OS" in
        Linux)
            echo "Linux detected."
            check_gpu
            ;;
        Darwin)
            echo "macOS detected. Using Metal for acceleration."
            export CMAKE_ARGS="-DGGML_METAL=on"
            ;;
        MINGW* | MSYS* | CYGWIN* | Windows_NT)
            echo "Windows detected. Using MinGW for compilation."
            # Check if w64devkit is present
            if [[ ! -d "C:/w64devkit" ]]; then
                echo "w64devkit is required for compiling on Windows."
                echo "Please download and extract it to C:/w64devkit."
                exit 1
            fi
            echo "Configuring CMAKE_ARGS for MinGW on Windows."
            export CMAKE_GENERATOR="MinGW Makefiles"
            export CMAKE_ARGS="-DGGML_OPENBLAS=on -DCMAKE_C_COMPILER=C:/w64devkit/bin/gcc.exe -DCMAKE_CXX_COMPILER=C:/w64devkit/bin/g++.exe"
            ;;
        *)
            echo "Unsupported operating system. Exiting."
            exit 1
            ;;
    esac
}

# Function to check the numpy version and uninstall if it is >= 2.0.0
check_and_uninstall_numpy() {
    if python -c "import numpy; assert numpy.__version__ >= '2.0.0'" 2>/dev/null; then
        echo "Numpy version is >= 2.0.0. Uninstalling numpy..."
        pip uninstall -y numpy
    else
        echo "Numpy version is less than 2.0.0. No need to uninstall."
    fi
}

# Configure the Conda environment
setup_conda_env() {
    ENV_NAME="llama_env"
    
    # Check if the environment exists and is functional
    if conda env list | grep -q $ENV_NAME; then
        echo "Conda environment $ENV_NAME found. Trying to activate it..."
        source $(conda info --base)/etc/profile.d/conda.sh
        if ! conda activate $ENV_NAME; then
            echo "Failed to activate environment $ENV_NAME. Recreating it..."
            conda remove --name $ENV_NAME --all -y
            conda create -n $ENV_NAME python=3.9 -y
            conda activate $ENV_NAME
        fi
    else
        echo "Conda environment $ENV_NAME not found. Creating it..."
        conda create -n $ENV_NAME python=3.9 -y
        conda activate $ENV_NAME
    fi
}

# Install llama-cpp-python with the appropriate configuration
install_llama_cpp() {
    echo "Installing llama-cpp-python with specific configurations..."
    pip uninstall llama-cpp-python -y
    CMAKE_ARGS=$CMAKE_ARGS pip install llama-cpp-python==0.2.27 --no-cache-dir
}

# Install project dependencies
install_dependencies() {
    echo "Installing project dependencies..."
    REQ_FILE="requirements.txt"
    if [[ -f "$REQ_FILE" ]]; then
        pip install --upgrade pip
        pip install -r "$REQ_FILE"
    else
        echo "ERROR: Requirements file not found at $REQ_FILE"
        exit 1
    fi
}

# Start the backend with FastAPI
start_backend() {
    echo "Starting backend with FastAPI..."
    if ! command -v uvicorn &> /dev/null; then
        pip install uvicorn
    fi
    uvicorn app.main:app --host 0.0.0.0 --port 8000
}

# Main execution of the script
main() {
    # 1. Check if Conda is installed
    check_conda

    # 2. Clear pip cache
    clear_cache

    # 3. Detect the operating system and set CMAKE_ARGS
    detect_os_and_set_cmake_args

    # 4. Setup Conda environment
    setup_conda_env

    # 5. Check and uninstall numpy if it is >= 2.0.0
    check_and_uninstall_numpy

    # 6. Install project dependencies
    install_dependencies

    # 7. Install llama-cpp-python
    install_llama_cpp

    # 8. Start the backend
    start_backend
}

# Execute the script
main
