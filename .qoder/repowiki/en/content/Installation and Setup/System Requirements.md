# System Requirements

<cite>
**Referenced Files in This Document**   
- [requirements.txt](file://requirements.txt)
- [requirements_cuda.txt](file://requirements_cuda.txt)
- [package.json](file://package.json)
- [install.bat](file://install.bat)
- [config.py](file://src-python/config.py)
- [overlay.py](file://src-python/models/overlay/overlay.py)
- [utils.md](file://src-python/docs/utils.md)
- [config.md](file://src-python/docs/config.md)
</cite>

## Table of Contents
1. [Operating System Requirements](#operating-system-requirements)
2. [Python Runtime Environment](#python-runtime-environment)
3. [Node.js and Frontend Tooling](#nodejs-and-frontend-tooling)
4. [Core Python Dependencies](#core-python-dependencies)
5. [GPU and CUDA Requirements](#gpu-and-cuda-requirements)
6. [Frontend Dependencies](#frontend-dependencies)
7. [Memory, Storage, and Audio Requirements](#memory-storage-and-audio-requirements)
8. [Network Communication Requirements](#network-communication-requirements)
9. [System Readiness Validation](#system-readiness-validation)

## Operating System Requirements

VRCT requires Windows 10 or Windows 11 as the minimum operating system. The application is designed to leverage modern Windows audio APIs and VR integration features available in these operating systems. While the core functionality may work on earlier versions, full compatibility and optimal performance are guaranteed only on Windows 10 and 11.

The application utilizes Windows-specific audio capture technologies such as WASAPI (Windows Audio Session API) for loopback recording of speaker output, which is essential for transcribing audio from VRChat and other applications. This functionality is not available on older Windows versions or non-Windows operating systems.

**Section sources**
- [device_manager.md](file://src-python/docs/device_manager.md#L258-L306)
- [device_manager_zh.md](file://src-python/docs/device_manager_zh.md#L258-L284)

## Python Runtime Environment

VRCT requires Python 3.10 or higher to run. This requirement is due to the use of modern Python language features such as the match-case syntax, which was introduced in Python 3.10. The application will not function correctly on earlier Python versions.

The system uses a virtual environment setup for dependency management, with separate environments for CUDA and non-CUDA configurations. The installation process creates two virtual environments:
- `.venv` for CPU-only operation
- `.venv_cuda` for GPU-accelerated operation with CUDA support

The Python environment is managed through the `install.bat` script, which sets up the virtual environments and installs all required packages from the requirements files.

**Section sources**
- [config.md](file://src-python/docs/config.md#L74)
- [config_zh.md](file://src-python/docs/config_zh.md#L74)
- [install.bat](file://install.bat#L1-L25)

## Node.js and Frontend Tooling

The frontend development environment requires Node.js for building and running the user interface. The application uses a modern JavaScript toolchain with Vite as the build tool and Tauri for creating the desktop application wrapper.

The `package.json` file defines the complete frontend tooling setup, including development scripts for building the application with and without CUDA support. Key Node.js scripts include:
- `dev`: Builds the Python backend and runs the development UI
- `dev-cuda`: Builds the CUDA-enabled Python backend and runs the development UI
- `build`: Creates a production build of the application
- `build-cuda`: Creates a production build with CUDA support
- `release`: Packages the application into a distributable ZIP file

**Section sources**
- [package.json](file://package.json#L1-L63)

## Core Python Dependencies

The application relies on several critical Python packages for its core functionality, as specified in the `requirements.txt` file:

### Transcription and Translation Packages
- **torch==2.7.0**: Core machine learning framework used for CUDA detection and GPU acceleration
- **faster-whisper==1.1.1**: High-performance speech recognition engine for transcription
- **ctranslate2==4.6.0**: Optimized inference engine for fast translation processing
- **transformers==4.40.2**: Hugging Face transformers library for language models
- **SpeechRecognition**: Custom speech recognition package for audio processing

### VR and Overlay Packages
- **openvr==1.26.701**: Valve's OpenVR API for creating VR overlays in VRChat
- **Pillow==10.0.0**: Image processing library for creating overlay graphics

### Audio Processing Packages
- **PyAudioWPatch==0.2.12.6**: Audio interface library with WASAPI loopback support
- **pydub==0.25.1**: Audio manipulation library
- **pycaw==20240210**: Audio volume control for system audio

### Communication and Utility Packages
- **python-osc==1.9.0**: OSC (Open Sound Control) protocol implementation
- **websockets==15.0.1**: WebSocket server implementation for real-time communication
- **psutil==5.9.8**: System monitoring and process management
- **PyYAML==6.0.2**: Configuration file parsing

**Section sources**
- [requirements.txt](file://requirements.txt#L1-L32)
- [requirements_cuda.txt](file://requirements_cuda.txt#L1-L33)

## GPU and CUDA Requirements

VRCT supports GPU acceleration through CUDA for improved performance in transcription and translation tasks. The application can operate in both CPU-only and GPU-accelerated modes, with the latter providing significantly faster processing.

### CUDA Configuration
The application provides two separate dependency files:
- `requirements.txt`: For CPU-only operation
- `requirements_cuda.txt`: For GPU-accelerated operation with CUDA support

The CUDA version includes the same packages but with PyTorch configured for CUDA 12.8, enabling GPU acceleration.

### GPU Compute Capability
The application supports different compute types based on GPU architecture:
- **RTX, Tesla, A100, Quadro series**: Full compute type support including int8_bfloat16, bfloat16, float16, and int8
- **GTX series**: Limited compute types (excludes int8_bfloat16, bfloat16, float16, and int8)
- **Other GPUs**: Float32 only

The system automatically detects the GPU device and adjusts the available compute types accordingly. For optimal performance, an NVIDIA GPU with compute capability 6.0 or higher is recommended.

### Driver Requirements
To use CUDA acceleration, users must have up-to-date NVIDIA drivers installed that support CUDA 12.8. The application uses PyTorch's CUDA integration, which requires compatible drivers and a supported GPU.

**Section sources**
- [requirements_cuda.txt](file://requirements_cuda.txt#L1-L33)
- [utils.md](file://src-python/docs/utils.md#L254-L267)
- [config.md](file://src-python/docs/config.md#L75)
- [details/model.md](file://src-python/docs/details/model.md#L363)

## Frontend Dependencies

The frontend is built with a modern React-based stack using the following key dependencies:

### UI Framework
- **React 18.3.1**: Core UI library for building the user interface
- **@mui/material 7.0.2**: Material-UI components for consistent UI design
- **jotai 2.12.3**: State management library
- **i18next 25.0.1**: Internationalization and localization

### Tauri Plugins
- **@tauri-apps/api 2.5.0**: Core Tauri functionality
- **@tauri-apps/plugin-fs 2.2.1**: File system access
- **@tauri-apps/plugin-global-shortcut 2.2.0**: Global keyboard shortcuts
- **@tauri-apps/plugin-http 2.4.3**: HTTP client functionality
- **@tauri-apps/plugin-opener 2.2.6**: Opening URLs and files
- **@tauri-apps/plugin-shell 2.2.1**: Shell command execution

### Development Tools
- **Vite 6.3.4**: Build tool and development server
- **@vitejs/plugin-react 4.4.1**: Vite plugin for React
- **@rollup/plugin-yaml 4.1.2**: YAML file processing

**Section sources**
- [package.json](file://package.json#L27-L62)

## Memory, Storage, and Audio Requirements

### Memory Requirements
- **Minimum**: 8GB RAM
- **Recommended**: 16GB RAM or higher

The application's memory usage varies significantly based on the selected models and processing mode. GPU acceleration can reduce CPU memory usage by offloading computation to VRAM, but requires sufficient GPU memory for model loading.

### Storage Requirements
- **Minimum**: 10GB free disk space
- **Recommended**: 20GB free disk space

Additional storage is required for:
- Model files (several GB depending on selected models)
- Application logs
- Temporary processing files
- Cache data

### Audio Device Requirements
The application requires appropriate audio devices for both input and output processing:

#### Microphone Input
- Any standard microphone or headset with microphone
- Support for the system's default audio input device
- Sample rates up to 48kHz supported

#### Speaker Loopback
- **Critical Requirement**: Ability to capture system audio output
- On Windows, this typically requires a "Stereo Mix" or "What U Hear" device
- Alternatively, the application can use WASAPI loopback if available
- Required for transcribing audio from VRChat and other applications

The application automatically detects available audio devices and provides configuration options for selecting input sources.

**Section sources**
- [device_manager.md](file://src-python/docs/device_manager.md#L258-L306)
- [details/transcription_recorder.md](file://src-python/docs/details/transcription_recorder.md#L277-L293)

## Network Communication Requirements

### WebSocket Communication
The application includes a WebSocket server for real-time communication with other components. Key configuration options:
- **WebSocket Host**: Configurable IP address (default: 127.0.0.1)
- **WebSocket Port**: Configurable port number (default: 8765)
- The server enables bidirectional communication for real-time data exchange

### OSC (Open Sound Control) Communication
The application supports OSC for integration with VRChat and other applications:
- **OSC IP Address**: Configurable destination IP (default: 127.0.0.1)
- **OSC Port**: Configurable destination port (default: 9000)
- Used for sending transcription and translation results to VRChat

### Antivirus and Firewall Considerations
Antivirus software and firewalls may interfere with WebSocket and OSC communication. Users may need to:
- Add VRCT to antivirus exclusions
- Allow VRCT through the Windows Firewall
- Configure firewall rules to permit UDP traffic on the OSC port
- Configure firewall rules to permit WebSocket connections on the specified port

If OSC communication is blocked due to IP address restrictions, certain features may be automatically disabled with appropriate notifications to the user.

**Section sources**
- [test_endpoints.py](file://src-python/test_endpoints.py#L426-L440)
- [test_client.py](file://src-python/test_client.py#L833-L836)
- [_useBackendErrorHandling.js](file://src-ui/logics/_useBackendErrorHandling.js#L189-L219)
- [websocket_server.md](file://src-python/docs/details/websocket_server.md#L361-L532)

## System Readiness Validation

Users can validate their system readiness using the following commands:

### Python Environment Validation
```bash
python -c "import torch; print(f'PyTorch available: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

This command verifies that Python is correctly installed and can access the required packages, particularly PyTorch and CUDA support.

### Node.js Environment Validation
```bash
npm run dev
```

This command attempts to build and run the application in development mode, which will reveal any issues with the Node.js environment or frontend dependencies.

### Dependency Installation Verification
The installation process can be verified by running:
```bash
npm run setup-python
```

This executes the `install.bat` script which sets up the virtual environments and installs all Python dependencies.

### CUDA-Specific Validation
For systems with CUDA support, users can verify GPU acceleration with:
```bash
python -c "import torch; print(f'CUDA devices: {torch.cuda.device_count()}'); [print(f'Device {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())]"
```

This command lists all available CUDA devices and their names, confirming that the GPU is properly detected and accessible.

**Section sources**
- [install.bat](file://install.bat#L1-L25)
- [config.py](file://src-python/config.py#L8)
- [package.json](file://package.json#L7)