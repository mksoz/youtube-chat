# **Youtube Chat**

This project contains both a frontend and backend component that runs in separate terminal instances. The frontend uses **Streamlit** for a web interface, and the backend uses **FastAPI** with **Langgraph** and **Llama-CPP** for managing and executing AI workflows.

## Prerequisites

Before setting up the project, ensure that the following prerequisites are met:

1. **Miniforge/Conda**: Miniforge or Conda must be installed for environment management.  
   You can install Miniforge/Conda by following the instructions at [Installing conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).
   
2. **Python 3.9+**: This project requires **Python 3.9** for compatibility with the dependencies.

3. **NVIDIA GPU (Optional)**: If using a GPU, ensure that the following are properly installed and configured:
   - **NVIDIA drivers**: Confirm that the drivers are installed correctly. Run `nvidia-smi` to check if your GPU is recognized.
   - **CUDA Toolkit**: Ensure the **CUDA** version matches the one required by the `llama-cpp-python` version. Use [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit).
   - **cuDNN**: Install the appropriate cuDNN library as required for CUDA.

4. **C++ Compiler**:  
   - **Linux/macOS**: Ensure you have **gcc** or **clang** installed.  
   - **Windows**: If you encounter errors regarding `nmake` or `CMAKE_C_COMPILER`, ensure you have installed **w64devkit** and configured the environment variables for CMake accordingly.

## LLM Model: Mistral-7B-Instruct-v0.3.Q8_0.gguf

This project uses the `Mistral-7B-Instruct-v0.3.Q8_0.gguf` model as the default language model. The model is located inside the `llm_backend/app/models` directory and is already set as the default in the backend configuration.

### Model Details
- **Model Name:** Mistral-7B-Instruct-v0.3
- **Quantization Format:** Q8_0
- **File Type:** GGUF (latest)
- **Location:** `llm_backend/app/models`

This model is optimized for instruction-following tasks and has been fine-tuned for various natural language processing tasks. The `Q8_0` quantization provides a balance between model size and inference speed while maintaining accuracy.

### Using a Different Model

If you would like to use a different model, follow these steps:

1. **Check Compatibility:** Ensure that the new model is compatible with the version of `llama-cpp` being used. You can check the compatibility in the [llama.cpp GitHub repository](https://github.com/ggerganov/llama.cpp).

2. **Download a New Model:**
   - You can use the [LM Studio](https://lmstudio.ai/) application to explore and download compatible models.
   - After downloading, place the new model files inside the `llm_backend/app/models` directory.

3. **Update the Model Path:**
   - Modify the `model_path` in your backend code `llm_backend/app/llm_chain.py` to point to the new model file:
     ```python
     llm = LlamaCpp(
         model_path="path/to/your/new_model.gguf",
         n_gpu_layers=n_gpu_layers,
         n_batch=n_batch,
         ...
     )
     ```

### Model Quantization

- **Q8_0 Quantization**: This quantization level reduces the size of the model by storing it in 8-bit precision, which enables faster inference without sacrificing too much accuracy.
- If your system supports GPU inference, ensure that the `CMAKE_ARGS` are properly configured to take advantage of CUDA or other supported accelerators.

### Notes on Model Performance
- Depending on the model size and your hardware configuration (CPU or GPU), inference speeds may vary.
- If you are using a GPU, ensure that CUDA and related libraries are properly installed and configured as described in the [NVIDIA Toolkit Installation](https://developer.nvidia.com/cuda-toolkit).

For more information on llama.cpp model usage, refer to the [official llama.cpp documentation](https://github.com/ggerganov/llama.cpp#readme).


## **How to Obtain a YouTube API Key**

To use the YouTube API in your project, you need to obtain an API key from the Google Developers Console. Follow these steps to get your API key:

 **1: Create a Google Cloud Project**

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in with your Google account if you haven't already.
3. Click on the project dropdown (top bar) and select **New Project**.
4. Provide a **project name** and select your **organization** (if any).
5. Click **Create** and wait for the project to be created.

**2: Enable YouTube Data API**

1. Inside the newly created project, go to the **APIs & Services** dashboard by clicking on the menu (three horizontal lines) in the upper-left corner.
2. Click on **APIs & Services** > **Library**.
3. In the **API Library**, search for **YouTube Data API v3**.
4. Select **YouTube Data API v3** from the results and click **Enable**.

**3: Create API Credentials**

1. Go to **APIs & Services** > **Credentials** from the menu.
2. Click **Create Credentials** at the top of the page and select **API Key**.
3. Your new API key will appear. Copy this API key and store it securely.

**4: Restrict Your API Key (Optional but Recommended)**

1. After generating the API key, it's recommended to restrict it to specific websites or services to prevent unauthorized use.
2. In the **Credentials** page, click the **API Key** you just created to modify its settings.
3. Under **Application restrictions**, choose how you want to restrict the API key:
   - **HTTP Referrers**: If your application is a website, you can limit the API key to specific domain names.
   - **IP Addresses**: For backend services, you can restrict access by IP.
4. Under **API Restrictions**, select **YouTube Data API v3** to ensure the API key is only used for YouTube requests.
5. Click **Save** to apply the restrictions.

**5: Add API Key to Your Project**

Once you have your API key, you need to add it to your project:

- Copy and paste the api key into the config.yaml file of the frontend repository `chat_frontend/app/config.yaml`:
  ```bash
  youtube_api_key: "your_api_key_here"
  ```
## Project setting up 
1. Clone the repository
    ```bash
    git clone
    ```
2. Open a terminal, go to the cloned repository root path. Enter into terminal:
   ```bash
   cd llm_backend
   ./setup_and_run.sh 
   ```
3. Open a new terminal, go to the cloned repository root path. Enter into terminal:
    ```bash
    cd chat_frontend
    ./start.sh
    ```
4. **Once it is set up**, it will open automatically the user intarface otherwise go to http://localhost:8501

## Notes & Troubleshooting
1. GPU Usage

    Verify GPU usage: If you have a GPU, use `nvidia-smi` to monitor its usage during execution. The GPU should show utilization if properly configured.
    If the GPU is not utilized, ensure that CUDA and cuDNN are properly installed. Additionally, verify that the `CMAKE_ARGS` environment variable is set as required.

2. Numpy Version Conflicts

    If `numpy` is installed in a version `>= 2.0`.0, it may cause conflicts with `llama-cpp-python` and Langchain. The script automatically handles this by uninstalling numpy if needed, but verify using the following:
        
        python -c "import numpy; print(numpy__version__)"
        
3. Common Errors
    - **Environment Not Found**: If you encounter an error saying `EnvironmentNameNotFound`, ensure that the Conda environment was created successfully by running:
        ```bash
        conda info --envs
        ```
    - **CMake or Compiler Issues**: On Windows, ensure you have the correct version of `w64devkit` installed, and configure the `CMAKE_ARGS` properly if you see errors related to `CMAKE_C_COMPILER`.