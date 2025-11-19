# Troubleshooting Setup

<cite>
**Referenced Files in This Document**   
- [requirements.txt](file://requirements.txt)
- [requirements_cuda.txt](file://requirements_cuda.txt)
- [install.bat](file://install.bat)
- [clean.py](file://clean.py)
- [task_kill.py](file://task_kill.py)
- [device_manager.py](file://src-python/device_manager.py)
- [config.py](file://src-python/config.py)
- [utils.py](file://src-python/utils.py)
- [controller.py](file://src-python/controller.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Virtual Environment and Dependency Issues](#virtual-environment-and-dependency-issues)
3. [Audio Device Management and Detection](#audio-device-management-and-detection)
4. [CUDA and GPU Compute Troubleshooting](#cuda-and-gpu-compute-troubleshooting)
5. [Process Management and Environment Reset](#process-management-and-environment-reset)
6. [Network and Communication Issues](#network-and-communication-issues)
7. [Diagnostic and Logging Tools](#diagnostic-and-logging-tools)
8. [Conclusion](#conclusion)

## Introduction
This document provides comprehensive troubleshooting guidance for common setup issues encountered when installing and configuring VRCT (Voice Recognition & Chat Translation). The guide addresses problems ranging from virtual environment creation failures and missing system DLLs to audio device enumeration errors and CUDA initialization issues. It details the inner workings of the device management system, explains how to resolve dependency conflicts, and provides step-by-step solutions for resetting the application state. The information is derived directly from the codebase and is designed to help users diagnose and fix problems efficiently, ensuring a smooth setup and operation of the VRCT application.

## Virtual Environment and Dependency Issues

VRCT relies on a complex set of Python dependencies, which are managed through virtual environments and requirement files. Common issues arise from missing system libraries, dependency conflicts, and corrupted installations.

The project uses two primary requirement files: `requirements.txt` and `requirements_cuda.txt`. The former contains standard dependencies, while the latter includes an additional CUDA-specific index URL for GPU-accelerated packages like PyTorch. The `install.bat` script automates the setup process by creating two virtual environments: `.venv` for CPU processing and `.venv_cuda` for CUDA-enabled GPU processing. This script first removes any existing environments, creates new ones, activates them, and installs the respective requirements with `--no-cache-dir --force-reinstall` to ensure a clean installation.

A frequent issue is the failure to create the virtual environment or install packages, often due to missing Microsoft Visual C++ Redistributable libraries. The error manifests as missing DLLs such as `MSVCP140.dll` or `VCRUNTIME140.dll`. The solution is to download and install the latest Microsoft Visual C++ Redistributable package from the official Microsoft website. This package provides the necessary runtime components for applications built with Visual Studio.

Dependency conflicts can also occur, particularly with packages installed from Git repositories (e.g., `SpeechRecognition @ git+https://...`). If an installation fails, it may be due to network issues or changes in the remote repository. In such cases, manually cloning the repository and installing from the local directory can be a workaround. For persistent issues, the `clean.py` script can be used to remove build artifacts, followed by a complete reinstallation using `install.bat`.

**Section sources**
- [requirements.txt](file://requirements.txt#L1-L32)
- [requirements_cuda.txt](file://requirements_cuda.txt#L1-L33)
- [install.bat](file://install.bat#L1-L25)
- [clean.py](file://clean.py#L1-L6)

## Audio Device Management and Detection

The core of VRCT's functionality is its ability to detect and monitor audio input and output devices. This is handled by the `DeviceManager` class in `device_manager.py`, which uses the `PyAudioWPatch` and `pycaw` libraries to enumerate and track audio endpoints.

The `DeviceManager` is implemented as a singleton and uses a two-phase initialization process. First, it is created with default "NoDevice" values to prevent import-time crashes. The `init()` method is then called to populate the device lists. The system groups microphone devices by their host API (e.g., Windows WASAPI, MME) and stores them in a dictionary. Speaker devices are collected as a list of loopback devices, which are virtual devices that capture the audio output of other applications.

The detection process involves querying the PyAudio library for all available host APIs and their associated devices. For each host, it iterates through the devices and checks if they have input channels (for microphones) or are loopback devices (for speakers). The default devices are determined by querying the system's default input and output devices. If any step fails (e.g., due to missing libraries), the system gracefully falls back to the default "NoDevice" state, preventing the entire application from crashing.

A common error is "No input device found," which can occur for several reasons. The most frequent cause is that the application lacks the necessary permissions to access the microphone. On Windows, users must ensure that microphone access is enabled in the system privacy settings. Another cause is that the audio host API is not properly configured. The `DeviceManager` uses WASAPI for loopback recording, which requires exclusive mode to be disabled in the audio device's advanced properties.

The system also features a monitoring thread that can detect device changes in real-time. If `comtypes` and `pycaw` are available, it uses Windows' COM API to register for device change notifications. When a device is added, removed, or the default device changes, a callback is triggered, and the device lists are refreshed. If COM is not available, it falls back to periodic polling. This monitoring can be started with `startMonitoring()` and stopped with `stopMonitoring()`.

**Section sources**
- [device_manager.py](file://src-python/device_manager.py#L1-L529)
- [controller.py](file://src-python/controller.py#L1113-L1136)

## CUDA and GPU Compute Troubleshooting

CUDA initialization failures are a common hurdle for users attempting to leverage GPU acceleration for faster transcription and translation. The root cause is typically related to driver compatibility, incorrect PyTorch installation, or insufficient VRAM.

The application determines the compute mode during initialization in the `config.py` file. The `COMPUTE_MODE` is set to "cuda" if `torch.cuda.is_available()` returns `True`, otherwise it falls back to "cpu". This check is performed in the `init_config()` method of the `Config` class. If CUDA is not available, the application will run on the CPU, which is significantly slower but more universally compatible.

For CUDA to work, three components must be correctly installed and compatible: the NVIDIA GPU driver, the CUDA toolkit, and the PyTorch package. The `requirements_cuda.txt` file specifies a CUDA 12.8 index URL for PyTorch, which means the user's GPU driver must be compatible with CUDA 12.8. Users with older GPUs may need to install a different version of PyTorch that matches their driver version.

A frequent error is `CUDA out of memory`, which occurs when the GPU does not have enough VRAM to load the selected model. The application includes a `detectVRAMError()` method in the `model.py` file that catches these exceptions and notifies the user. The solution is to either select a smaller model, change the compute type to a lower-precision format (e.g., from `float16` to `int8`), or disable GPU acceleration entirely by setting the compute device to "cpu".

The `utils.py` file contains the `getComputeDeviceList()` function, which queries the system for all available compute devices and their supported compute types. It applies specific restrictions based on the GPU model. For example, GTX series cards are restricted to `float32` to avoid compatibility issues, while RTX, Tesla, and A100 cards support a full range of compute types. The `getBestComputeType()` function then selects the optimal compute type based on the device's capabilities and the user's preferences.

**Section sources**
- [config.py](file://src-python/config.py#L771-L772)
- [utils.py](file://src-python/utils.py#L92-L171)
- [model.py](file://src-python/model.py#L177-L183)

## Process Management and Environment Reset

When VRCT encounters persistent issues, the most effective solution is often to reset the application state by killing running processes and rebuilding the environment. The project provides two scripts, `task_kill.py` and `clean.py`, to facilitate this process.

The `task_kill.py` script is designed to forcefully terminate the `VRCT-sidecar.exe` process, which is a separate executable that may continue running in the background even after the main application is closed. This script uses the `subprocess.run()` function with the `taskkill` command and the `/F` (force) flag to ensure the process is terminated. This is crucial for resolving issues related to port conflicts or locked files, as a lingering sidecar process can prevent the main application from starting correctly.

The `clean.py` script removes build and distribution directories that can become corrupted. It uses the `shutil.rmtree()` function to delete the `build`, `dist`, `src-tauri\bin`, and `src-tauri\target` directories. These directories are created during the build process and can sometimes contain stale or incompatible files that interfere with a fresh installation. Running `clean.py` before a reinstallation ensures a completely clean slate.

The recommended troubleshooting workflow for a corrupted environment is as follows: first, run `task_kill.py` to ensure no VRCT processes are running. Next, run `clean.py` to remove any build artifacts. Then, manually delete the `.venv` and `.venv_cuda` directories if they exist. Finally, re-run the `install.bat` script to create fresh virtual environments and install all dependencies. This sequence of steps resolves the vast majority of setup issues related to environment corruption.

**Section sources**
- [task_kill.py](file://task_kill.py#L1-L12)
- [clean.py](file://clean.py#L1-L6)
- [install.bat](file://install.bat#L1-L25)

## Network and Communication Issues

VRCT uses WebSocket and OSC (Open Sound Control) protocols for communication with other applications, such as VRChat. Issues with these communication channels are often caused by port conflicts, firewall blocking, or permission issues.

The application checks for WebSocket server availability using the `isAvailableWebSocketServer()` function in `utils.py`. This function attempts to bind a TCP socket to the specified host and port. If the bind operation succeeds, the port is available; if it fails, the port is likely in use by another process or blocked by the firewall. The default WebSocket port is defined in the `config.py` file and can be changed by the user if a conflict is detected.

Firewall blocking is a common cause of connection failures, especially on Windows. The Windows Defender Firewall may block the application's network access by default. Users should ensure that VRCT is allowed through the firewall for both private and public networks. This can be configured in the Windows Security settings under "Firewall & network protection."

Permission issues can also arise, particularly when the application attempts to write to its configuration or log files. If the application is installed in a protected directory (e.g., `Program Files`), it may not have write permissions. The solution is to run the application as an administrator or to install it in a user-writable directory, such as the user's home folder.

For OSC communication, the IP address and port must be correctly configured to match the receiving application (e.g., VRChat). The `OSC_IP_ADDRESS` and `OSC_PORT` are stored in the `config.py` file. A common mistake is using the wrong IP address; users should ensure they are using the correct local IP address of their machine, not `localhost` or `127.0.0.1`, when communicating across a network.

**Section sources**
- [utils.py](file://src-python/utils.py#L70-L82)
- [config.py](file://src-python/config.py#L692-L707)

## Diagnostic and Logging Tools

VRCT provides several built-in tools for diagnosing issues, including structured logging, stdout inspection, and safe mode launches. These tools are essential for identifying the root cause of problems when they occur.

The application uses a dual-logging system with two log files: `process.log` and `error.log`. The `process.log` file contains structured JSON messages that log the application's status, endpoints, and data. Each message includes a `status` code, an `endpoint` identifier, and a `data` payload. This log is invaluable for tracking the flow of data through the application. The `error.log` file captures full Python traceback information for any unhandled exceptions, providing detailed context for debugging.

The `printLog()` and `printResponse()` functions in `utils.py` are used to write to the `process.log` and emit messages to stdout. By monitoring the stdout output, users can see real-time information about the application's state. For example, if the audio device detection fails, a message with `status: 400` and `endpoint: error_device` will be printed, along with a descriptive message.

A "safe mode" launch can be achieved by temporarily disabling certain features. For instance, users can disable CUDA acceleration by setting `COMPUTE_MODE` to "cpu" in the configuration, or disable audio device monitoring by not calling `startMonitoring()`. This allows the application to start with minimal dependencies, helping to isolate the source of a problem. Once the application is running in a stable state, features can be re-enabled one by one to identify the culprit.

The `controller.py` file contains numerous response functions that are called when specific events occur. For example, `progressBarMicEnergy()` is called to report the microphone energy level, and if no device is detected, it sends an error message. By examining the code in `controller.py`, users can understand the exact conditions under which different error messages are generated, which is crucial for effective troubleshooting.

**Section sources**
- [utils.py](file://src-python/utils.py#L184-L291)
- [controller.py](file://src-python/controller.py#L154-L186)

## Conclusion
This troubleshooting guide has covered the most common setup issues for VRCT, from dependency management and audio device detection to CUDA initialization and network communication. By understanding the underlying mechanisms, such as the `DeviceManager`'s use of `PyAudioWPatch` and `pycaw`, or the `config.py` file's role in determining compute mode, users can diagnose and resolve problems more effectively. The key to successful troubleshooting is a systematic approach: start by checking logs and stdout, use the provided scripts to reset the environment, and isolate the problem by disabling features. With this knowledge, users can ensure a smooth and reliable experience with VRCT.