# Appendix

<cite>
**Referenced Files in This Document**   
- [config.py](file://src-python/config.py)
- [languages.yml](file://src-python/models/translation/languages/languages.yml)
- [transcription_languages.py](file://src-python/models/transcription/transcription_languages.py)
- [HotkeysEntry.jsx](file://src-ui/views/app/config_page/setting_section/setting_box/_components/hotkeys_entry/HotkeysEntry.jsx)
- [package.json](file://package.json)
- [Cargo.toml](file://src-tauri/Cargo.toml)
- [requirements.txt](file://requirements.txt)
- [en.yml](file://locales/en.yml)
</cite>

## Table of Contents
1. [Configuration File Reference](#configuration-file-reference)
2. [Supported Languages](#supported-languages)
3. [Keyboard Shortcuts](#keyboard-shortcuts)
4. [Third-Party Licenses and Attributions](#third-party-licenses-and-attributions)
5. [Glossary of Technical Terms](#glossary-of-technical-terms)
6. [External Resources](#external-resources)

## Configuration File Reference

This section provides a comprehensive reference for all settings available in the VRCT application configuration system. The configuration is managed through the `config.py` file which uses a descriptor-based system to handle property validation, serialization, and persistence.

### General Settings
- **ENABLE_TRANSLATION**: Enables or disables the translation functionality. Type: boolean. Default: `False`.
- **ENABLE_TRANSCRIPTION_SEND**: Controls whether voice input is transcribed and sent to chat. Type: boolean. Default: `False`.
- **ENABLE_TRANSCRIPTION_RECEIVE**: Enables transcription of audio from speakers (Speaker2Log). Type: boolean. Default: `False`.
- **ENABLE_FOREGROUND**: Keeps the application window on top of other windows. Type: boolean. Default: `False`.
- **CONVERT_MESSAGE_TO_ROMAJI**: Shows romanized Japanese text on hover when enabled. Type: boolean. Default: `False`.
- **CONVERT_MESSAGE_TO_HIRAGANA**: Displays hiragana transliteration of Japanese text. Type: boolean. Default: `False`.
- **MAIN_WINDOW_SIDEBAR_COMPACT_MODE**: Enables compact mode for the main window sidebar. Type: boolean. Default: `False`.

### Interface Settings
- **TRANSPARENCY**: Controls main window transparency level. Type: integer. Range: 0-100.
- **UI_SCALING**: Scales the overall UI size. Type: integer. Range: 50-200.
- **TEXTBOX_UI_SCALING**: Adjusts message log font size relative to UI size. Type: integer. Range: 50-200.
- **MESSAGE_BOX_RATIO**: Sets the ratio between message input box and log display. Type: number. Range: 0.1-1.0.
- **SEND_MESSAGE_BUTTON_TYPE**: Determines visibility and behavior of send button. Type: string. Options: "show", "hide", "show_and_disable_enter_key".
- **SHOW_RESEND_BUTTON**: Displays resend button on hover over sent messages. Type: boolean. Default: `False`.
- **FONT_FAMILY**: Specifies the font family used in the interface. Type: string.
- **UI_LANGUAGE**: Sets the application interface language. Type: string. Options: "en", "ja", "ko", "zh-Hant", "zh-Hans".

### Audio Input/Output Settings
- **MIC_THRESHOLD**: Sensitivity threshold for microphone activation. Type: integer. Range: 0-2000.
- **MIC_AUTOMATIC_THRESHOLD**: Enables automatic adjustment of mic sensitivity. Type: boolean. Default: `False`.
- **MIC_RECORD_TIMEOUT**: Maximum duration of silence before ending recording. Type: integer. Range: 0-10.
- **MIC_PHRASE_TIMEOUT**: Time between phrases before processing transcription. Type: integer. Range: 0-10.
- **MIC_MAX_PHRASES**: Minimum number of words required before sending transcription. Type: integer. Range: 0-100.
- **SPEAKER_THRESHOLD**: Sensitivity threshold for speaker audio detection. Type: integer. Range: 0-4000.
- **SPEAKER_AUTOMATIC_THRESHOLD**: Enables automatic speaker sensitivity adjustment. Type: boolean. Default: `False`.

### Translation Settings
- **SELECTED_TRANSLATION_ENGINES**: Maps translation tabs to specific engines. Type: dict.
- **CTRANSLATE2_WEIGHT_TYPE**: Selects model size for CTranslate2 engine. Type: string. Options: "small", "large".
- **WHISPER_WEIGHT_TYPE**: Chooses Whisper model for speech recognition. Type: string.
- **SELECTED_PLAMO_MODEL**: Specifies which Plamo model to use. Type: string.
- **SELECTED_GEMINI_MODEL**: Selects Gemini model version. Type: string.
- **SELECTED_OPENAI_MODEL**: Specifies OpenAI model to use. Type: string.
- **SELECTED_LMSTUDIO_MODEL**: Chooses LMStudio model. Type: string.
- **SELECTED_OLLAMA_MODEL**: Selects Ollama model. Type: string.

### Device Settings
- **AUTO_MIC_SELECT**: Automatically selects microphone device. Type: boolean. Default: `True`.
- **AUTO_SPEAKER_SELECT**: Automatically selects speaker device. Type: boolean. Default: `True`.
- **SELECTED_MIC_HOST**: Specifies audio driver/host for microphone. Type: string.
- **SELECTED_MIC_DEVICE**: Selects specific microphone device. Type: string.
- **SELECTED_SPEAKER_DEVICE**: Chooses speaker/audio output device. Type: string.
- **SELECTED_TRANSLATION_COMPUTE_DEVICE**: Specifies compute device for translation. Type: dict.
- **SELECTED_TRANSCRIPTION_COMPUTE_DEVICE**: Selects compute device for transcription. Type: dict.

### Overlay Settings
- **OVERLAY_SMALL_LOG**: Enables small overlay display. Type: boolean. Default: `False`.
- **OVERLAY_LARGE_LOG**: Enables large overlay display. Type: boolean. Default: `False`.
- **OVERLAY_SHOW_ONLY_TRANSLATED_MESSAGES**: Shows only translated messages in overlay. Type: boolean. Default: `False`.
- **OVERLAY_SMALL_LOG_SETTINGS**: Configuration for small overlay position and appearance. Type: dict.
- **OVERLAY_LARGE_LOG_SETTINGS**: Configuration for large overlay position and appearance. Type: dict.

### Network Settings
- **WEBSOCKET_SERVER**: Enables WebSocket server functionality. Type: boolean. Default: `False`.
- **OSC_IP_ADDRESS**: IP address for OSC communication. Type: string. Default: "127.0.0.1".
- **OSC_PORT**: Port number for OSC communication. Type: integer. Range: 1000-65535. Default: 9000.
- **WEBSOCKET_HOST**: Host address for WebSocket server. Type: string. Default: "127.0.0.1".
- **WEBSOCKET_PORT**: Port for WebSocket server. Type: integer. Range: 1000-65535. Default: 8765.

**Section sources**
- [config.py](file://src-python/config.py#L531-L800)

## Supported Languages

The VRCT application supports multiple languages for both transcription (speech-to-text) and translation through various backend engines. This section details the language capabilities across different systems.

### Transcription Languages
The application uses Whisper and Google services for speech recognition with support for numerous languages and regional variants:

- **English**: Supported with multiple regional variants including US, UK, Australia, Canada, India, and others.
- **Japanese**: Full support for Japanese language transcription.
- **Korean**: Complete support for Korean language.
- **Chinese**: Both Simplified (Mandarin) and Traditional (Taiwanese) variants supported.
- **European Languages**: Comprehensive support for major European languages including Spanish, French, German, Italian, Portuguese, Russian, Dutch, Polish, Swedish, and more.
- **Asian Languages**: Support for Hindi, Arabic, Turkish, Thai, Vietnamese, Indonesian, Hebrew, and others.
- **Other Languages**: Additional support for languages such as Arabic, Czech, Greek, Hungarian, Romanian, and Ukrainian.

Each language typically includes multiple regional variants where applicable, allowing users to select the most appropriate dialect for their needs.

### Translation Languages by Engine

#### CTranslate2
Supports bidirectional translation between:
- Major languages: English, Chinese (Simplified/Traditional), German, Spanish, Russian, Korean, French, Japanese, Portuguese, Turkish, Polish
- Additional languages: Catalan, Dutch, Arabic, Swedish, Italian, Indonesian, Hindi, Finnish, Hebrew, Ukrainian, Greek, Malay, Czech, Romanian, Danish, Hungarian, Tamil, Norwegian, Thai, Urdu, Croatian, Bulgarian, Lithuanian, and many others (over 100 total)

#### DeepL
- Source and target languages: Arabic, Bulgarian, Czech, Danish, German, Greek, English, Spanish, Estonian, Finnish, French, Irish, Croatian, Hungarian, Indonesian, Italian, Japanese, Korean, Lithuanian, Latvian, Maltese, Norwegian, Dutch, Polish, Portuguese, Romanian, Russian, Slovak, Slovenian, Swedish, Turkish, Ukrainian, Chinese (Simplified/Traditional)

#### Google Translate
Extensive language support including:
- Asian: Japanese, Chinese (Simplified/Traditional), Korean, Hindi, Thai, Vietnamese, Indonesian, Mongolian
- European: English, Russian, French, German, Spanish, Portuguese, Italian, Dutch, Polish, Czech, Hungarian, Estonian, Bulgarian, Danish, Finnish, Romanian, Swedish, Slovenian, Persian/Farsi, Serbian, Croatian, Slovak, Albanian, Lithuanian, Latvian, Macedonian, Ukrainian, Belarusian
- Middle Eastern: Arabic, Hebrew
- African: Swahili, Zulu, Xhosa, Afrikaans, Amharic, Tigrinya, Oromo, Somali, Kinyarwanda, Yoruba
- Pacific: Hawaiian, Samoan, Maori, Hmong, Cebuano, Javanese, Sundanese

#### Other Translation Engines
- **Bing**: Similar language coverage to Google with additional support for Klingon and Queretaro Otomi
- **Papago**: Focus on Asian languages (German, English, Spanish, French, Hindi, Indonesian, Italian, Japanese, Korean, Portuguese, Russian, Thai, Vietnamese, Chinese)
- **Plamo_API**: English, Japanese, Korean, French, German, Spanish, Portuguese, Russian, Italian, Dutch, Polish, Turkish, Arabic, Hindi, Thai, Vietnamese, Indonesian, Malay, Filipino, Swedish, Finnish, Danish, Norwegian, Romanian, Czech, Hungarian, Greek, Hebrew, Chinese
- **Gemini_API**: Arabic, Bengali, Bulgarian, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, German, Greek, Hebrew, Hindi, Hungarian, Indonesian, Italian, Japanese, Korean, Latvian, Lithuanian, Norwegian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swedish, Thai, Turkish, Ukrainian, Vietnamese
- **OpenAI_API**: Comprehensive multilingual support covering African, Asian, European, Middle Eastern, and Pacific languages

**Section sources**
- [languages.yml](file://src-python/models/translation/languages/languages.yml#L1-L772)
- [transcription_languages.py](file://src-python/models/transcription/transcription_languages.py#L1-L735)

## Keyboard Shortcuts

The VRCT application provides configurable keyboard shortcuts for quick access to core functionality. These can be customized through the application settings interface.

### Available Shortcuts
- **Toggle VRCT Visibility**: Toggles the visibility of the main application window. Default: `Ctrl+Shift+V`
- **Toggle Translation**: Enables or disables translation functionality. Default: `Ctrl+Shift+T`
- **Toggle Voice2Chatbox**: Toggles transcription and sending of voice input to chat. Default: `Ctrl+Shift+C`
- **Toggle Speaker2Log**: Toggles transcription of audio from speakers. Default: `Ctrl+Shift+S`

### Shortcut Management
Shortcuts are implemented using the Tauri global shortcut plugin, allowing them to work even when the application is minimized. The system automatically registers and unregisters shortcuts based on application state (ready, updating, available).

Users can customize these shortcuts through the Hotkeys configuration section in the settings menu. Each shortcut can be set to a combination of modifier keys (Ctrl, Alt, Shift) and a primary key. The application prevents conflicts with system-level shortcuts and common browser shortcuts (F5, F12, Ctrl+R).

**Section sources**
- [HotkeysEntry.jsx](file://src-ui/views/app/config_page/setting_section/setting_box/_components/hotkeys_entry/HotkeysEntry.jsx)
- [GlobalHotKeyController.jsx](file://src-ui/views/app/_app_controllers/GlobalHotKeyController.jsx)
- [KeyEventController.jsx](file://src-ui/views/app/_app_controllers/KeyEventController.jsx)

## Third-Party Licenses and Attributions

This section details the third-party dependencies used in the VRCT application along with their licensing information and attributions.

### Core Dependencies
- **faster-whisper**: An optimized implementation of OpenAI's Whisper model for faster inference. Used for speech recognition and transcription. License: MIT
- **ctranslate2**: A fast inference engine for Transformer models. Used for efficient translation processing. License: Apache 2.0
- **Tauri**: Framework for building desktop applications using web technologies. Provides the application shell and system integration. License: Apache 2.0

### Python Dependencies
- **torch**: PyTorch deep learning framework. Used for neural network operations and GPU acceleration. License: BSD 3-Clause
- **transformers**: Hugging Face Transformers library. Provides access to various AI models. License: Apache 2.0
- **deepl**: Official DeepL API client. Enables integration with DeepL translation service. License: MIT
- **python-osc**: OSC (Open Sound Control) protocol implementation. Used for VRChat integration. License: MIT
- **PyAudioWPatch**: Audio input/output library with WASAPI loopback support. License: MIT
- **websockets**: WebSocket protocol implementation. Used for real-time communication. License: BSD 2-Clause
- **huggingface_hub**: Interface to Hugging Face model repository. License: Apache 2.0
- **SpeechRecognition**: Speech recognition library with multiple backend support. License: BSD

### JavaScript/Node Dependencies
- **@tauri-apps/api**: Tauri API bindings for JavaScript. License: Apache 2.0
- **@tauri-apps/plugin-global-shortcut**: Global keyboard shortcut functionality. License: Apache 2.0
- **@tauri-apps/plugin-fs**: File system access plugin. License: Apache 2.0
- **react**: JavaScript library for building user interfaces. License: MIT
- **i18next**: Internationalization framework. License: MIT
- **js-yaml**: YAML parser and serializer. License: MIT
- **semver**: Semantic versioning utilities. License: ISC

### Additional Tools
- **PyInstaller**: Converts Python applications to standalone executables. License: GPL 2.0
- **Vite**: Frontend build tool. License: MIT
- **Rust/Cargo**: Tauri is built with Rust, which provides memory safety and performance. License: MIT/Apache 2.0

All dependencies are included in compliance with their respective licenses. The application distributes only the necessary components and provides proper attribution to all original authors and projects.

**Section sources**
- [requirements.txt](file://requirements.txt#L1-L32)
- [package.json](file://package.json#L1-L63)
- [Cargo.toml](file://src-tauri/Cargo.toml#L1-L34)

## Glossary of Technical Terms

This glossary defines key technical terms used throughout the VRCT application and documentation.

- **Transcription**: The process of converting spoken audio into written text. In VRCT, this applies to both microphone input (Voice2Chatbox) and speaker audio (Speaker2Log).
- **Translation**: The process of converting text from one language to another. VRCT supports multiple translation engines and models.
- **Compute Device**: Hardware used for AI processing, typically CPU or GPU. The application can utilize different devices for transcription and translation tasks.
- **Whisper**: OpenAI's automatic speech recognition system used as the primary engine for speech-to-text conversion.
- **CTranslate2**: Optimized inference engine for Transformer models, used for fast and efficient translation.
- **OSC (Open Sound Control)**: Network protocol used to communicate with VRChat, enabling text display in-game.
- **WebSocket**: Protocol providing full-duplex communication channels over a single TCP connection, used for real-time data exchange.
- **VAD (Voice Activity Detection)**: Technology that detects the presence of human speech in an audio signal, used to determine when to start/stop recording.
- **Loopback Recording**: Technique for capturing audio output from applications, used to transcribe speech heard through speakers.
- **Model Quantization**: Process of reducing the precision of neural network weights to improve inference speed and reduce memory usage.
- **Inference**: The process of using a trained machine learning model to make predictions or generate outputs from new data.
- **Backend**: The Python-based server component of VRCT that handles AI processing, audio capture, and network communication.
- **Frontend**: The user interface component built with React and Tauri that provides the visual interface and user interaction.
- **Overlay**: Transparent window that displays text over other applications, used to show transcriptions and translations in VRChat.
- **Hotkey**: Keyboard shortcut that triggers specific application functions without requiring interaction with the user interface.
- **Token**: Unit of text used by language models for processing. Translation and transcription quality can depend on token limits.
- **Latency**: Delay between speech input and text output. Lower latency provides more responsive communication.
- **Real-time Processing**: System capability to process and deliver results with minimal delay, essential for natural conversation flow.
- **API (Application Programming Interface)**: Set of protocols and tools for building software applications, used to integrate with external services like DeepL or Google Translate.
- **GPU Acceleration**: Use of graphics processing units to speed up AI computations, significantly improving performance for large models.

**Section sources**
- [config.py](file://src-python/config.py)
- [en.yml](file://locales/en.yml)

## External Resources

This section provides links to external documentation, APIs, and resources that are relevant to the VRCT application.

### VRChat Integration
- **VRChat OSC Documentation**: [https://docs.vrchat.com/docs/osc](https://docs.vrchat.com/docs/osc) - Official documentation for VRChat's OSC implementation, detailing message formats and parameters.
- **VRChat Creator Community**: [https://creator.vrchat.com/](https://creator.vrchat.com/) - Resources for VRChat developers and content creators.
- **VRChat API Documentation**: [https://vrchat.com/api](https://vrchat.com/api) - Web API for VRChat services.

### Translation Services
- **DeepL API Documentation**: [https://www.deepl.com/docs-api](https://www.deepl.com/docs-api) - Comprehensive documentation for DeepL's translation API, including authentication and usage limits.
- **Google Cloud Translation API**: [https://cloud.google.com/translate/docs](https://cloud.google.com/translate/docs) - Documentation for Google's translation service with details on supported languages and pricing.
- **OpenAI API Documentation**: [https://platform.openai.com/docs](https://platform.openai.com/docs) - Complete guide to OpenAI's API, including language models and authentication.
- **Ollama Documentation**: [https://ollama.com/library](https://ollama.com/library) - Information about locally running large language models.
- **LMStudio Documentation**: [https://lmstudio.ai/docs](https://lmstudio.ai/docs) - Guide to using LMStudio for local AI models.

### Technical References
- **Open Sound Control Specification**: [https://opensoundcontrol.stanford.edu/spec-1_0.html](https://opensoundcontrol.stanford.edu/spec-1_0.html) - Official OSC protocol specification.
- **WebSocket Protocol**: [https://datatracker.ietf.org/doc/html/rfc6455](https://datatracker.ietf.org/doc/html/rfc6455) - RFC specification for WebSocket.
- **Whisper GitHub Repository**: [https://github.com/openai/whisper](https://github.com/openai/whisper) - Source code and documentation for OpenAI's Whisper speech recognition system.
- **CTranslate2 Documentation**: [https://opennmt.net/CTranslate2/](https://opennmt.net/CTranslate2/) - Official documentation for the CTranslate2 inference engine.
- **Tauri Framework Documentation**: [https://tauri.app/v1/guides/](https://tauri.app/v1/guides/) - Comprehensive guides for building applications with Tauri.

### Community and Support
- **VRCT GitHub Repository**: [https://github.com/misyaguziya/VRCT](https://github.com/misyaguziya/VRCT) - Source code repository and issue tracker for the VRCT application.
- **VRCT Documentation**: [https://mzsoftware.notion.site/VRCT-Documents-be79b7a165f64442ad8f326d86c22246](https://mzsoftware.notion.site/VRCT-Documents-be79b7a165f64442ad8f326d86c22246) - Official documentation and user guides.
- **Hugging Face Model Hub**: [https://huggingface.co/models](https://huggingface.co/models) - Repository of pre-trained machine learning models used by various components.

**Section sources**
- [en.yml](file://locales/en.yml#L749)
- [config.py](file://src-python/config.py#L747-L751)