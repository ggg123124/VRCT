# VR Overlay Usage

<cite>
**Referenced Files in This Document**   
- [overlay.py](file://src-python/models/overlay/overlay.py)
- [overlay_image.py](file://src-python/models/overlay/overlay_image.py)
- [osc.py](file://src-python/models/osc/osc.py)
- [controller.py](file://src-python/controller.py)
- [model.py](file://src-python/model.py)
- [config.py](file://src-python/config.py)
- [Vr.jsx](file://src-ui/views/app/config_page/setting_section/setting_box/vr/Vr.jsx)
- [overlay.md](file://src-python/docs/details/overlay.md)
- [osc.md](file://src-python/docs/details/osc.md)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [VR Overlay Modes](#vr-overlay-modes)
3. [Appearance Settings](#appearance-settings)
4. [OSC Communication Setup](#osc-communication-setup)
5. [Python Backend Components](#python-backend-components)
6. [Customization Examples](#customization-examples)
7. [Troubleshooting](#troubleshooting)
8. [Conclusion](#conclusion)

## Introduction
The VRCT application provides comprehensive VR overlay functionality that renders translated messages in virtual reality through OpenVR overlays and synchronizes with VRChat via the OSC (Open Sound Control) protocol. This system enables users to view real-time translations of conversations directly within their VR environment, enhancing cross-language communication in virtual spaces. The overlay system supports multiple display modes with different use cases, allowing for flexible positioning, scaling, and transparency adjustments. The integration with VRChat is achieved through OSC communication, which transmits typing indicators and chat messages between the application and the VR platform. This documentation details the architecture, configuration, and usage of these features, providing guidance for users and developers to effectively utilize and customize the VR overlay system.

**Section sources**
- [overlay.md](file://src-python/docs/details/overlay.md#L1-L200)

## VR Overlay Modes
The VRCT application implements two distinct overlay modes: small and large, each designed for specific use cases within VR environments. The small overlay mode is optimized for single-line messages and is typically positioned on the HMD (Head-Mounted Display) for quick reference during gameplay. This mode is ideal for displaying brief translated messages without obstructing the user's field of view. The large overlay mode, on the other hand, supports multi-line message logs and is designed to be attached to the left hand controller, allowing users to view conversation history by naturally looking at their hand. This mode displays a scrolling log of recent messages with timestamps, showing both original messages and their translations in a structured format.

The overlay system uses OpenVR to create and manage these overlays, with each mode having independent settings for position, rotation, scaling, and opacity. The small overlay has a fixed width of 3840 pixels and height of 92 pixels with a font size of 92, while the large overlay has a width of 960 pixels with variable font sizes (30 for large text, 20 for small text). Both modes support automatic fading, where messages are displayed for a configurable duration before gradually fading out. The overlay positioning is managed through transformation matrices that account for the user's head and hand tracking data, ensuring the overlays remain properly oriented in 3D space regardless of the user's movements.

```mermaid
graph TD
A[VR Overlay System] --> B[Small Overlay Mode]
A --> C[Large Overlay Mode]
B --> D[Single-line Messages]
B --> E[HMD Positioning]
B --> F[Quick Reference]
C --> G[Multi-line Message Log]
C --> H[Left Hand Controller]
C --> I[Conversation History]
D --> J[Translation Display]
E --> K[Non-obstructive Viewing]
F --> L[Gameplay Integration]
G --> M[Scrolling Log]
H --> N[Natural Hand Position]
I --> O[Context Preservation]
```

**Diagram sources **
- [overlay.py](file://src-python/models/overlay/overlay.py#L85-L388)
- [overlay_image.py](file://src-python/models/overlay/overlay_image.py#L60-L733)

**Section sources**
- [overlay.py](file://src-python/models/overlay/overlay.py#L85-L388)
- [overlay_image.py](file://src-python/models/overlay/overlay_image.py#L60-L733)
- [overlay.md](file://src-python/docs/details/overlay.md#L1-L200)

## Appearance Settings
The appearance of VR overlays in VRCT can be extensively customized through the application's settings interface, allowing users to adjust position, scale, transparency, and other visual properties. The overlay positioning system uses a 3D coordinate system where X, Y, and Z values control the horizontal, vertical, and depth placement of the overlay relative to the tracking device. Rotation parameters (X, Y, Z) allow for fine-tuning the overlay's orientation in degrees. Users can select between three tracking options: HMD (head-mounted display), LeftHand, or RightHand, which determines which tracked device the overlay follows in VR space.

The scaling of overlays is controlled by the UI scaling parameter, which adjusts the physical size of the overlay in meters. The small overlay has a default scaling of 1.0, while the large overlay has a default scaling of 0.25, making it appear smaller in the virtual environment despite its larger pixel dimensions. Transparency is managed through the opacity setting, which accepts values from 0.0 (completely transparent) to 1.0 (completely opaque). The overlay system also supports automatic fading, with configurable display duration and fadeout duration parameters that control how long messages remain visible before gradually disappearing.

The visual appearance of the overlays is further customized through UI settings that define the background color, text color, and corner radius. The small overlay uses a dark gray background (RGB: 41, 42, 45) with light gray text (RGB: 223, 223, 223), while the large overlay uses similar colors with additional color coding for different message types (send in blue, receive in purple, timestamps in gray). Both overlays feature rounded corners with a configurable radius and a subtle outline for better visibility against various backgrounds.

```mermaid
flowchart TD
A[Appearance Settings] --> B[Position]
A --> C[Scale]
A --> D[Transparency]
A --> E[Visual Style]
B --> B1[X Position]
B --> B2[Y Position]
B --> B3[Z Position]
B --> B4[Rotation X]
B --> B5[Rotation Y]
B --> B6[Rotation Z]
B --> B7[Tracker Selection]
C --> C1[UI Scaling]
D --> D1[Opacity]
D --> D2[Display Duration]
D --> D3[Fadeout Duration]
E --> E1[Background Color]
E --> E2[Text Color]
E --> E3[Corner Radius]
E --> E4[Outline]
B7 --> F[HMD]
B7 --> G[LeftHand]
B7 --> H[RightHand]
```

**Diagram sources **
- [overlay.py](file://src-python/models/overlay/overlay.py#L179-L231)
- [Vr.jsx](file://src-ui/views/app/config_page/setting_section/setting_box/vr/Vr.jsx#L1-L200)

**Section sources**
- [overlay.py](file://src-python/models/overlay/overlay.py#L179-L231)
- [config.py](file://src-python/config.py#L947-L990)
- [Vr.jsx](file://src-ui/views/app/config_page/setting_section/setting_box/vr/Vr.jsx#L1-L200)

## OSC Communication Setup
The VRCT application establishes communication with VRChat through the OSC (Open Sound Control) protocol, enabling bidirectional data exchange for chat messages and user status. To enable OSC communication, users must configure the target IP address and port number in the application settings. By default, the application connects to localhost (127.0.0.1) on port 9000, which is the standard configuration for VRChat running on the same machine. For networked setups, users can specify the IP address of the machine running VRChat to enable cross-device communication.

The OSC system in VRCT is managed by the OSCHandler class, which handles both message sending and receiving. When the target address is localhost, the application automatically enables OSCQuery functionality, which advertises available endpoints and allows VRChat to discover and interact with the application. This enables advanced features like reading the MuteSelf parameter from VRChat to synchronize microphone muting states. The application sends OSC messages to two primary endpoints: /chatbox/typing to indicate when a message is being composed, and /chatbox/input to submit the final message for display in VRChat.

To verify the OSC connection status, the application provides real-time feedback through the UI, indicating whether the connection to VRChat is active. Users can test the connection by sending sample messages through the configuration interface. The OSC system automatically handles connection errors and will attempt to re-establish communication if the connection is lost. For security and performance reasons, OSCQuery functionality is automatically disabled when connecting to remote addresses, as it requires opening additional network ports that may not be accessible or desirable in networked configurations.

```mermaid
sequenceDiagram
participant VRCT as VRCT Application
participant OSC as OSC Protocol
participant VRChat as VRChat
VRCT->>OSC : Configure IP : 127.0.0.1, Port : 9000
OSC->>VRCT : Connection Established
VRCT->>OSC : sendTyping(true)
OSC->>VRChat : /chatbox/typing [true]
VRChat-->>OSC : Typing Indicator Activated
OSC-->>VRCT : Confirmation
VRCT->>OSC : sendMessage("Hello World")
OSC->>VRChat : /chatbox/input ["Hello World", True, True]
VRChat-->>OSC : Message Displayed
OSC-->>VRCT : Confirmation
VRCT->>OSC : sendTyping(false)
OSC->>VRChat : /chatbox/typing [false]
VRChat-->>OSC : Typing Indicator Deactivated
```

**Diagram sources **
- [osc.py](file://src-python/models/osc/osc.py#L40-L241)
- [osc.md](file://src-python/docs/details/osc.md#L117-L218)

**Section sources**
- [osc.py](file://src-python/models/osc/osc.py#L40-L241)
- [controller.py](file://src-python/controller.py#L347-L356)
- [osc.md](file://src-python/docs/details/osc.md#L117-L218)

## Python Backend Components
The VR overlay functionality in VRCT is powered by several key Python backend components that work together to render translated messages and manage OSC communication. The core of the overlay system is the Overlay class in overlay.py, which manages OpenVR overlays for multiple sizes. This class handles the initialization of the OpenVR system, creation of overlay handles, and management of the rendering loop. It provides methods to update the overlay image, position, opacity, and other visual properties, as well as to control the overlay's lifecycle (starting, stopping, and restarting).

The OverlayImage class in overlay_image.py is responsible for generating the actual image content displayed in the overlays. This class manages font loading for multiple languages (Japanese, Korean, Chinese, etc.) using Noto Sans fonts, and handles the creation of text images with proper formatting and layout. It supports advanced features like ruby text (furigana) for Japanese text, rendering both hiragana and romaji transliterations above kanji characters. The class also manages message history for the large overlay mode, maintaining a log of recent messages with timestamps and message types.

The OSC communication is handled by the OSCHandler class in osc.py, which provides a thin wrapper around the python-osc library. This class manages the UDP client for sending messages to VRChat and can optionally run an OSC server with OSCQuery support for receiving messages from VRChat. It handles the formatting of OSC messages for the /chatbox/typing and /chatbox/input endpoints, and provides methods to query VRChat parameters like the MuteSelf state when OSCQuery is available.

These components are orchestrated by the Model class in model.py, which initializes and manages instances of the overlay, OSC handler, and other system components. The Controller class in controller.py acts as an intermediary between the UI and the model, handling user actions and updating the system state accordingly. Configuration settings are managed by the Config class in config.py, which provides a centralized location for all application settings, including overlay parameters and OSC connection details.

```mermaid
classDiagram
class Overlay {
+system : Any
+overlay : Any
+handle : Dict[str, Any]
+settings : Dict[str, Dict[str, Any]]
+lastUpdate : Dict[str, float]
+fadeRatio : Dict[str, float]
+init() : None
+startOverlay() : None
+shutdownOverlay() : None
+updateImage(img : Image, size : str) : None
+updatePosition(x_pos : float, y_pos : float, z_pos : float, x_rotation : float, y_rotation : float, z_rotation : float, tracker : str, size : str) : None
+updateOpacity(opacity : float, size : str) : None
+updateUiScaling(ui_scaling : float, size : str) : None
+mainloop() : None
}
class OverlayImage {
+LANGUAGES : Dict[str, str]
+message_log : List[dict]
+root_path : str
+_font_cache : Dict[tuple, ImageFont]
+__init__(root_path : Optional[str]) : None
+createOverlayImageSmallLog(message : str, your_language : str, translation : List[str], target_language : List[str]) : Image
+createOverlayImageLargeLog(message_type : str, message : str, your_language : str, translation : List[str], target_language : List[str]) : Image
+getUiSizeSmallLog() : dict
+getUiSizeLargeLog() : dict
+getUiColorSmallLog() : dict
+getUiColorLargeLog() : dict
}
class OSCHandler {
+osc_ip_address : str
+osc_port : int
+osc_parameter_muteself : str
+osc_parameter_chatbox_typing : str
+osc_parameter_chatbox_input : str
+udp_client : SimpleUDPClient
+osc_server : Optional[ThreadingOSCUDPServer]
+osc_query_service : Optional[OSCQueryService]
+dict_filter_and_target : Dict[str, Callable]
+__init__(ip_address : str, port : int) : None
+setOscIpAddress(ip_address : str) : None
+setOscPort(port : int) : None
+sendTyping(flag : bool) : None
+sendMessage(message : str, notification : bool) : None
+getOSCParameterMuteSelf() : Optional[bool]
+receiveOscParameters() : None
+oscServerStop() : None
}
class Model {
+overlay : Overlay
+overlay_image : OverlayImage
+osc_handler : OSCHandler
+translator : Translator
+init() : None
+ensure_initialized() : None
+createOverlayImageSmallLog(message : str, your_language : str, translation : List[str], target_language : List[str]) : Image
+createOverlayImageLargeLog(message_type : str, message : str, your_language : str, translation : List[str], target_language : List[str]) : Image
+updateOverlaySmallLog(image : Image) : None
+updateOverlayLargeLog(image : Image) : None
+oscSendMessage(message : str) : None
}
class Controller {
+run : Callable[[int, str, Any], None]
+micMessage(result : dict) : None
+speakerMessage(result : dict) : None
+chatMessage(data) : dict
+messageFormatter(message_type : str, translation : List[str], original_message : str) : str
}
class Config {
+OVERLAY_SMALL_LOG : bool
+OVERLAY_LARGE_LOG : bool
+OVERLAY_SMALL_LOG_SETTINGS : dict
+OVERLAY_LARGE_LOG_SETTINGS : dict
+OVERLAY_SHOW_ONLY_TRANSLATED_MESSAGES : bool
+OSC_IP_ADDRESS : str
+OSC_PORT : int
+SEND_MESSAGE_TO_VRC : bool
}
Overlay --> Model : "used by"
OverlayImage --> Model : "used by"
OSCHandler --> Model : "used by"
Model --> Controller : "used by"
Config --> Model : "configuration"
Controller --> Model : "controls"
```

**Diagram sources **
- [overlay.py](file://src-python/models/overlay/overlay.py#L85-L388)
- [overlay_image.py](file://src-python/models/overlay/overlay_image.py#L12-L733)
- [osc.py](file://src-python/models/osc/osc.py#L40-L241)
- [model.py](file://src-python/model.py#L81-L200)
- [controller.py](file://src-python/controller.py#L11-L800)
- [config.py](file://src-python/config.py#L1-L200)

**Section sources**
- [overlay.py](file://src-python/models/overlay/overlay.py#L85-L388)
- [overlay_image.py](file://src-python/models/overlay/overlay_image.py#L12-L733)
- [osc.py](file://src-python/models/osc/osc.py#L40-L241)
- [model.py](file://src-python/model.py#L81-L200)
- [controller.py](file://src-python/controller.py#L11-L800)
- [config.py](file://src-python/config.py#L1-L200)

## Customization Examples
The VRCT application provides several ways to customize overlay appearance and handle overlay visibility during gameplay. Users can modify the visual style of overlays by adjusting parameters such as opacity, scaling, and position through the configuration interface. For example, to make the small overlay more discreet during intense gameplay, users can reduce its opacity to 0.5 and position it at the periphery of their vision by adjusting the X and Y coordinates. The large overlay can be configured to appear only when needed by setting a longer display duration and enabling the fadeout effect, allowing messages to gradually disappear after being read.

Programmatic customization is also possible through the Python API. Developers can modify overlay settings by accessing the configuration parameters directly. For instance, to change the small overlay to follow the right hand controller instead of the HMD, the tracker setting can be updated:

```python
config.OVERLAY_SMALL_LOG_SETTINGS["tracker"] = "RightHand"
```

Similarly, the display behavior can be customized by adjusting the display_duration and fadeout_duration parameters. To keep messages visible indefinitely, the fadeout_duration can be set to 0:

```python
config.OVERLAY_LARGE_LOG_SETTINGS["fadeout_duration"] = 0
```

The application also supports conditional overlay visibility based on gameplay context. Through the controller logic, overlays can be automatically hidden during specific game events or when the user is engaged in activities that require full visual attention. This is achieved by temporarily disabling the overlay rendering loop and restoring it when appropriate. The message formatting can also be customized through the SEND_MESSAGE_FORMAT_PARTS configuration, allowing users to add prefixes, suffixes, and separators to control how original messages and translations are combined in the output.

```mermaid
flowchart TD
A[Customization Examples] --> B[Appearance Adjustments]
A --> C[Behavior Modifications]
A --> D[Conditional Visibility]
B --> B1[Reduce Opacity to 0.5]
B --> B2[Reposition to Periphery]
B --> B3[Change Tracker to RightHand]
B --> B4[Adjust Scaling Factor]
C --> C1[Set Display Duration to 10s]
C --> C2[Disable Fadeout Effect]
C --> C3[Modify Message Formatting]
C --> C4[Change Font Colors]
D --> D1[Hide During Combat]
D --> D2[Show Only Translated Messages]
D --> D3[Auto-hide After Reading]
D --> D4[Context-aware Positioning]
B1 --> E[Less Intrusive]
B2 --> E
C1 --> F[Prolonged Visibility]
C2 --> F
D1 --> G[Gameplay Integration]
D2 --> G
```

**Diagram sources **
- [config.py](file://src-python/config.py#L947-L990)
- [overlay.py](file://src-python/models/overlay/overlay.py#L226-L231)
- [controller.py](file://src-python/controller.py#L374-L398)

**Section sources**
- [config.py](file://src-python/config.py#L947-L990)
- [overlay.py](file://src-python/models/overlay/overlay.py#L226-L231)
- [controller.py](file://src-python/controller.py#L374-L398)

## Troubleshooting
Common issues with VR overlays in VRCT typically fall into three categories: overlay visibility problems, message formatting errors, and OSC connection failures. For overlay visibility issues where the overlay does not appear, the first step is to verify that the overlay feature is enabled in the configuration settings. Users should check that both the small and large overlay options are toggled on in the VR settings panel. If the overlay is still not visible, they should ensure that SteamVR is running and properly tracking their HMD and controllers. Restarting the overlay system through the application's restart function can resolve initialization issues that may prevent the overlay from appearing.

Message formatting problems, such as text appearing as boxes or incorrect character rendering, are usually related to font loading issues. The application uses Noto Sans fonts for Japanese, Korean, and Chinese characters, and missing or corrupted font files can cause display problems. Users should verify that the font directory exists and contains the required .ttf files. Clearing the font cache by restarting the application can resolve issues with corrupted font loading. For translation formatting issues, users should check that the source and target languages are correctly configured and that the translation engine is functioning properly.

OSC connection failures can be diagnosed by checking the connection status indicator in the application UI. If the connection is not established, users should verify that VRChat is running and that the OSC settings in VRChat match those in VRCT (typically port 9000). Firewall settings may block OSC traffic, so users should ensure that UDP port 9000 is allowed through their firewall. For localhost connections, users can test the connection by pinging 127.0.0.1 to verify network connectivity. If using OSCQuery features, users should note that these are only available when connecting to localhost and will be disabled for remote connections.

```mermaid
flowchart TD
A[Troubleshooting] --> B[Overlay Not Appearing]
A --> C[Message Formatting Issues]
A --> D[OSC Connection Failures]
B --> B1[Check Overlay Enabled]
B --> B2[Verify SteamVR Running]
B --> B3[Confirm Device Tracking]
B --> B4[Restart Overlay System]
B --> B5[Check OpenVR Initialization]
C --> C1[Verify Font Files Exist]
C --> C2[Check Language Settings]
C --> C3[Clear Font Cache]
C --> C4[Validate Translation Engine]
C --> C5[Inspect Text Encoding]
D --> D1[Check Connection Status]
D --> D2[Verify VRChat OSC Settings]
D --> D3[Test Network Connectivity]
D --> D4[Check Firewall Rules]
D --> D5[Validate IP Address and Port]
D --> D6[Test with Sample Message]
B1 --> E[Settings Issue]
B2 --> F[SteamVR Issue]
C1 --> G[Font Issue]
C2 --> H[Configuration Issue]
D2 --> I[VRChat Configuration]
D4 --> J[Network Issue]
```

**Diagram sources **
- [overlay.py](file://src-python/models/overlay/overlay.py#L232-L242)
- [osc.py](file://src-python/models/osc/osc.py#L103-L144)
- [controller.py](file://src-python/controller.py#L254-L265)

**Section sources**
- [overlay.py](file://src-python/models/overlay/overlay.py#L232-L242)
- [osc.py](file://src-python/models/osc/osc.py#L103-L144)
- [controller.py](file://src-python/controller.py#L254-L265)

## Conclusion
The VR overlay system in VRCT provides a robust solution for displaying translated messages in virtual reality environments through OpenVR overlays synchronized with VRChat via OSC protocol. The dual overlay mode system—small for quick reference and large for conversation history—offers flexibility for different use cases and gameplay scenarios. The comprehensive appearance settings allow users to customize position, scale, transparency, and visual style to suit their preferences and minimize visual obstruction. The OSC communication system enables seamless integration with VRChat, supporting both message transmission and status synchronization.

The Python backend components are well-structured, with clear separation of concerns between overlay management, image generation, and OSC communication. This modular design facilitates maintenance and future enhancements. The system handles common issues gracefully, with built-in error logging and recovery mechanisms. For optimal performance, users should ensure their system meets the requirements for OpenVR and maintain proper configuration of both VRCT and VRChat settings.

Future improvements could include additional overlay positioning options, more sophisticated message filtering, and enhanced customization of the visual appearance. The current system provides a solid foundation for real-time translation in VR, significantly improving cross-language communication in virtual environments.

**Section sources**
- [overlay.md](file://src-python/docs/details/overlay.md#L1-L776)
- [osc.md](file://src-python/docs/details/osc.md#L1-L218)