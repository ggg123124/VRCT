# Installation and Setup

<cite>
**Referenced Files in This Document**   
- [install.bat](file://install.bat)
- [build.bat](file://build.bat)
- [build_cuda.bat](file://build_cuda.bat)
- [requirements.txt](file://requirements.txt)
- [requirements_cuda.txt](file://requirements_cuda.txt)
- [package.json](file://package.json)
- [vite.config.js](file://vite.config.js)
- [tauri.conf.json](file://src-tauri/tauri.conf.json)
- [config.py](file://src-python/config.py)
- [device_manager.py](file://src-python/device_manager.py)
- [utils.py](file://src-python/utils.py)
- [backend.spec](file://backend.spec)
- [backend_cuda.spec](file://backend_cuda.spec)
</cite>

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation Process](#installation-process)
3. [Configuration and Build Process](#configuration-and-build-process)
4. [Verification and Initial Launch](#verification-and-initial-launch)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [Security and Network Configuration](#security-and-network-configuration)

## System Requirements

VRCT requires a Windows operating system with specific Python dependencies and optional CUDA support for GPU acceleration. The application leverages the Tauri framework for its frontend and backend integration, requiring Node.js and npm for development and build processes.

The core system requirements include:
- **Operating System**: Windows 10 or later (64-bit)
- **Python**: Version 3.9 or higher for running the backend services and dependencies
- **Node.js**: Version 18 or higher for frontend development and package management
- **npm**: Package manager for JavaScript dependencies used in the UI components
- **CUDA**: Optional, version 12.8 for GPU acceleration of transcription and translation models

The application utilizes PyTorch for machine learning operations, with two separate dependency sets for CPU and GPU processing. The GPU-accelerated version requires NVIDIA graphics cards with CUDA support, specifically those from the RTX, Tesla, A100, or Quadro series for optimal performance.

**Section sources**
- [requirements.txt](file://requirements.txt#L1-L32)
- [requirements_cuda.txt](file://requirements_cuda.txt#L1-L33)
- [config.py](file://src-python/config.py#L8)
- [utils.py](file://src-python/utils.py#L9)

## Installation Process

The installation process for VRCT on Windows systems can be completed through automated batch scripts or manual dependency installation. Two primary methods are available: using the `install.bat` script for automated setup or manually installing dependencies through pip.

### Automated Installation with install.bat

The `install.bat` script provides a streamlined installation process that creates two separate virtual environments: one for CPU-based processing and another for GPU-accelerated processing. The script performs the following operations:

1. Removes existing virtual environments (.venv and .venv_cuda) if they exist
2. Creates a new virtual environment named .venv for CPU processing
3. Activates the virtual environment and upgrades pip
4. Installs all dependencies listed in requirements.txt
5. Creates a separate virtual environment named .venv_cuda for GPU processing
6. Activates the CUDA virtual environment and installs dependencies from requirements_cuda.txt

The batch script ensures that both CPU and GPU configurations are available, allowing users to switch between processing modes based on their hardware capabilities.

### Manual Dependency Installation

For users who prefer manual control over the installation process, dependencies can be installed directly using pip. This method requires creating virtual environments and installing packages from the provided requirements files.

To install CPU-only dependencies:
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

To install GPU-accelerated dependencies:
```bash
python -m venv .venv_cuda
source .venv_cuda/Scripts/activate
pip install -r requirements_cuda.txt
```

The requirements.txt file contains essential packages including torch, faster-whisper, ctranslate2, and various audio processing libraries. The requirements_cuda.txt file includes the same packages but with an additional CUDA index URL for GPU-accelerated PyTorch installation.

**Section sources**
- [install.bat](file://install.bat#L1-L25)
- [requirements.txt](file://requirements.txt#L1-L32)
- [requirements_cuda.txt](file://requirements_cuda.txt#L1-L33)

## Configuration and Build Process

The configuration and build process for VRCT involves setting up the Tauri framework, managing frontend dependencies through package.json, and executing build scripts for both CPU and GPU versions.

### Tauri Framework Configuration

The Tauri framework is configured through the tauri.conf.json file, which defines application settings, window properties, and security configurations. Key configuration parameters include:

- **Application Metadata**: Product name (VRCT), version (3.3.1), and identifier (com.vrct.app)
- **Window Settings**: Dimensions (450x220), minimum size (400x200), transparency, and borderless decoration
- **Build Configuration**: Development URL (http://localhost:1420) and frontend distribution directory
- **Security Settings**: Content security policy and capability references
- **Bundle Configuration**: Target platform (NSIS installer), publisher information, and icon resources

The configuration also specifies external binaries and resource bundling, including the VRCT-sidecar binary and plugin directories.

### Frontend Configuration with Vite

The frontend build process is managed by Vite, configured through vite.config.js. This configuration file sets up development server parameters, build options, and module resolution aliases. Key aspects include:

- **Development Server**: Port 1420 with strict port binding and WebSocket-based hot module replacement
- **Build Output**: Dist directory for compiled assets with source map generation
- **Module Resolution**: Aliases for various UI components and utilities to simplify imports
- **Plugin Configuration**: Integration with React, SCSS preprocessing, and YAML file handling

### Build Process

The build process is executed through two batch scripts: build.bat for CPU builds and build_cuda.bat for GPU-accelerated builds. These scripts activate the appropriate virtual environment and use PyInstaller to package the application.

The build.bat script:
1. Activates the .venv virtual environment
2. Executes PyInstaller with backend.spec configuration
3. Outputs the compiled binary to src-tauri/bin directory
4. Cleans temporary files and suppresses verbose logging

The build_cuda.bat script follows the same process but uses the .venv_cuda environment and backend_cuda.spec configuration file.

Alternative build methods are available through npm scripts defined in package.json, including:
- `dev`: Development build with Python backend compilation
- `build`: Production build with cleanup and Tauri packaging
- `release`: Complete release build with ZIP packaging

**Section sources**
- [tauri.conf.json](file://src-tauri/tauri.conf.json#L1-L60)
- [vite.config.js](file://vite.config.js#L1-L135)
- [build.bat](file://build.bat#L1-L2)
- [build_cuda.bat](file://build_cuda.bat#L1-L2)
- [package.json](file://package.json#L1-L63)

## Verification and Initial Launch

After installation and configuration, several verification steps ensure proper setup and functionality of VRCT on Windows systems.

### Audio Device Detection

The application automatically detects available audio devices through the device_manager.py module. This component uses PyAudioWPatch and pycaw to enumerate microphone and speaker devices, including WASAPI loopback devices for speaker audio capture.

To verify audio device detection:
1. Launch VRCT and navigate to the audio configuration section
2. Check that microphone hosts and devices are properly listed
3. Verify speaker devices, including loopback options for audio capture
4. Confirm default input and output devices are correctly identified

The device manager implements a monitoring system that detects device changes and updates the UI accordingly. This is particularly important for users who frequently connect or disconnect audio peripherals.

### Model Downloads

VRCT automatically downloads necessary machine learning models during initial launch. The application uses Hugging Face Hub for model distribution, with progress tracked through the download_models component in the UI.

Key models include:
- Whisper transcription models for speech-to-text conversion
- CTranslate2 optimized models for efficient translation
- Language-specific models for transcription and translation

The application caches downloaded models to prevent redundant downloads on subsequent launches.

### Initial Launch Process

The initial launch sequence follows these steps:
1. Application startup through Tauri framework initialization
2. Backend Python process initialization
3. Configuration loading from config.json
4. Model download and cache verification
5. Audio device enumeration and default selection
6. WebSocket and OSC server initialization
7. Main window rendering with overlay integration

During the first launch, users should expect a longer startup time due to model downloads and cache initialization. Subsequent launches will be significantly faster as resources are cached locally.

**Section sources**
- [device_manager.py](file://src-python/device_manager.py#L1-L529)
- [config.py](file://src-python/config.py#L1-L800)
- [utils.py](file://src-python/utils.py#L92-L132)

## Troubleshooting Guide

Common setup issues and their solutions are documented to assist users in resolving installation and configuration problems.

### Missing DLLs and Dependency Issues

Missing DLL errors typically occur when required system libraries are not available. Solutions include:

- Install Microsoft Visual C++ Redistributable packages
- Ensure Python and Node.js are properly installed and accessible in PATH
- Verify that all pip packages installed successfully without errors
- Reinstall the application using administrator privileges

For CUDA-specific issues:
- Verify NVIDIA GPU drivers are up to date
- Confirm CUDA 12.8 is properly installed
- Check that the GPU is supported (RTX, Tesla, A100, or Quadro series)
- Ensure sufficient VRAM is available for model loading

### Audio Permission Errors

Audio permission issues prevent VRCT from accessing microphone or speaker devices. Resolution steps:

- Grant microphone and audio capture permissions in Windows Settings
- Check that no other applications are exclusively using the audio devices
- Verify that the correct audio host (e.g., Windows Audio Session) is selected
- Restart the audio service if devices are not detected

The application requires both input (microphone) and loopback (speaker) audio access for full functionality. Some audio interfaces may require specific drivers or configurations to enable loopback recording.

### GPU Acceleration Problems

GPU acceleration issues can manifest as slow performance or fallback to CPU processing. Troubleshooting steps:

- Verify CUDA installation with `nvidia-smi` command
- Check that the GPU meets minimum requirements
- Ensure the .venv_cuda environment is being used for GPU builds
- Confirm that PyTorch CUDA version matches the installed CUDA toolkit
- Monitor GPU memory usage during operation

If GPU acceleration is not working, the application will automatically fall back to CPU processing, though with reduced performance for transcription and translation tasks.

**Section sources**
- [device_manager.py](file://src-python/device_manager.py#L5-L23)
- [config.py](file://src-python/config.py#L10-L15)
- [utils.py](file://src-python/utils.py#L8-L11)

## Security and Network Configuration

Proper security and network configuration is essential for VRCT's communication features and overall system stability.

### Security Considerations

During installation, several security aspects should be considered:
- The application requires network access for model downloads and API integrations
- User authentication keys for translation services (DeepL, Google, OpenAI) should be stored securely
- The application creates firewall exceptions for WebSocket and OSC communication
- Third-party dependencies are sourced from trusted repositories (PyPI, npm)

The Tauri framework provides built-in security features, including content security policy configuration and capability-based access control. The application uses a capability file (vrct_capability.json) to define permitted operations.

### Firewall Configuration

VRCT uses network communication for several features:
- WebSocket server for real-time data exchange
- OSC (Open Sound Control) for integration with VRChat and other applications
- API calls to translation services (DeepL, Google, OpenAI)

The application may require firewall exceptions to function properly. Key ports and protocols:
- WebSocket: Default port 1420 (configurable)
- OSC: Configurable IP address and port (default 9000)
- API calls: HTTPS (port 443) for external services

Users may need to allow VRCT through Windows Defender Firewall when prompted during first launch. For enterprise environments, administrators should configure appropriate firewall rules to allow these communications.

Network validation can be performed using command-line tools:
```bash
# Test WebSocket connectivity
telnet localhost 1420

# Verify external connectivity
ping google.com

# Check if port is available
netstat -an | findstr :1420
```

**Section sources**
- [tauri.conf.json](file://src-tauri/tauri.conf.json#L25-L28)
- [config.py](file://src-python/config.py#L692-L707)
- [utils.py](file://src-python/utils.py#L70-L82)