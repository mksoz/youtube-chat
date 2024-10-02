#!/bin/bash

# Function to detect current OS and Architecture
detect_os_and_arch() {
    OS=$(uname -s)
    ARCH=$(uname -m)
    case "$OS" in
        Darwin)
            if [[ "$ARCH" == "arm64" ]]; then
                echo "macOS ARM detected."
                MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"
            else
                echo "macOS x86_64 detected."
                MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh"
            fi
            ;;
        Linux)
            if [[ "$ARCH" == "x86_64" ]]; then
                echo "Linux x86_64 detected."
                MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
            elif [[ "$ARCH" == "aarch64" ]]; then
                echo "Linux ARM64 detected."
                MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"
            elif [[ "$ARCH" == "ppc64le" ]]; then
                echo "Linux POWER detected."
                MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-ppc64le.sh"
            else
                echo "Unsupported architecture."
                exit 1
            fi
            ;;
        MINGW* | MSYS* | CYGWIN* | Windows_NT)
            echo "Windows detected."
            MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe"
            ;;
        *)
            echo "Unsupported operating system."
            exit 1
            ;;
    esac
}

# Function to check if the correct Miniforge is installed
check_correct_miniforge() {
    if ! command -v conda &> /dev/null; then
        echo "Conda is not installed. Proceeding with Miniforge installation."
        return 1  # Conda is not installed, needs to install Miniforge
    fi

    # Check if the installed Conda matches the current OS and architecture
    CONDA_PATH=$(conda info --base)
    CONDA_BIN="$CONDA_PATH/condabin/conda"

    INSTALLED_ARCH=$(uname -m)
    INSTALLED_OS=$(uname -s)

    if [[ "$INSTALLED_OS" == "Darwin" ]]; then
        if [[ "$INSTALLED_ARCH" == "arm64" && ! "$CONDA_BIN" =~ "MacOSX-arm64" ]]; then
            echo "Incorrect Miniforge detected for macOS ARM64. Reinstalling..."
            return 1
        elif [[ "$INSTALLED_ARCH" == "x86_64" && ! "$CONDA_BIN" =~ "MacOSX-x86_64" ]]; then
            echo "Incorrect Miniforge detected for macOS x86_64. Reinstalling..."
            return 1
        fi
    elif [[ "$INSTALLED_OS" == "Linux" ]]; then
        if [[ "$INSTALLED_ARCH" == "x86_64" && ! "$CONDA_BIN" =~ "Linux-x86_64" ]]; then
            echo "Incorrect Miniforge detected for Linux x86_64. Reinstalling..."
            return 1
        elif [[ "$INSTALLED_ARCH" == "aarch64" && ! "$CONDA_BIN" =~ "Linux-aarch64" ]]; then
            echo "Incorrect Miniforge detected for Linux ARM64. Reinstalling..."
            return 1
        elif [[ "$INSTALLED_ARCH" == "ppc64le" && ! "$CONDA_BIN" =~ "Linux-ppc64le" ]]; then
            echo "Incorrect Miniforge detected for Linux POWER. Reinstalling..."
            return 1
        fi
    elif [[ "$INSTALLED_OS" == "Windows_NT" ]]; then
        if [[ ! "$CONDA_BIN" =~ "Windows-x86_64" ]]; then
            echo "Incorrect Miniforge detected for Windows. Reinstalling..."
            return 1
        fi
    fi

    echo "Correct Miniforge is already installed."
    return 0  # Correct Miniforge is installed
}

# Function to uninstall incorrect Miniforge
uninstall_miniforge() {
    echo "Uninstalling current Miniforge..."
    CONDA_PATH=$(conda info --base)
    rm -rf "$CONDA_PATH"
    rm -f "${HOME}/.condarc"
    rm -fr "${HOME}/.conda"
}

# Function to install Miniforge if it's not installed or if it's incorrect
install_conda() {
    if check_correct_miniforge; then
        return  # Miniforge is correct, no need to reinstall
    fi

    # Uninstall if incorrect Miniforge is installed
    if command -v conda &> /dev/null; then
        uninstall_miniforge
    fi

    echo "Installing the correct Miniforge for this system."
    curl -LO $MINIFORGE_URL

    if [[ "$OS" == "Windows_NT" ]]; then
        start /wait "" $(basename $MINIFORGE_URL) /S /D=%UserProfile%\miniforge3
    else
        bash $(basename $MINIFORGE_URL) -b -p $HOME/miniforge3
    fi
    export PATH="$HOME/miniforge3/bin:$PATH"
    source $HOME/miniforge3/etc/profile.d/conda.sh
}

# Function to clear pip cache
clear_cache() {
    echo "Clearing pip cache..."
    pip cache purge
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

# Function to setup Conda environment
setup_conda_env() {
    ENV_NAME="llama_env"
    
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

# Install llama-cpp-python with appropriate configuration
install_llama_cpp() {
    echo "Installing llama-cpp-python..."
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
    # 1. Detect OS and Architecture
    detect_os_and_arch

    # 2. Install Conda (Miniforge)
    install_conda

    # 3. Clear pip cache
    clear_cache

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
