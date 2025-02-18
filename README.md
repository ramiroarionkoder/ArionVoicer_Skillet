## VoiceRecognitionApp Documentation

### Overview
The `VoiceRecognitionApp` is a Streamlit-based application that uses the Vosk speech recognition engine for transcribing spoken input and Amazon Polly for text-to-speech synthesis. The app allows users to select a language model and process voice inputs, recognizing names with high accuracy even in accented speech.

### Dependencies
The following dependencies are required:
- `streamlit`: Web-based UI framework.
- `os`, `json`, `queue`: Standard Python libraries for file handling, JSON processing, and managing data queues.
- `vosk`: Open-source offline speech recognition engine.
- `sounddevice`: Captures real-time audio input.
- `boto3`: AWS SDK for Python, used for Amazon Polly (text-to-speech) and SNS (commented out for future use).
- `fuzzywuzzy`: For future fuzzy string matching (currently commented out).
- `botocore.exceptions`: Handles AWS credential errors.

### Project Setup
1. Install the required dependencies:
```download ES and BR models from https://alphacephei.com/vosk/models```
```extract the models inside models/ folder and rename it, adjust on the code```
```pip install uv```
```uv lock```
```uv sync```
```streamlit run main_skilletz.py```


### Class: `VoiceRecognitionApp`
#### `__init__(self)`
- Initializes AWS Polly client using a `boto3.Session` with profile `akbot`.
- Loads Vosk language models (`pt-BR`, `es-ES`).
- Loads name grammar files for recognition.
- Sets the default model and grammar to Spanish (`es-ES`).

#### `load_vosk_model(model_path)`
- **Parameters:** `model_path` (str) - Path to the Vosk model directory.
- **Returns:** `vosk.Model` object.
- Checks if the model exists and loads it; otherwise, raises an error.

#### `load_grammar(file_path)`
- **Parameters:** `file_path` (str) - Path to the grammar file.
- **Returns:** JSON-encoded list of words.
- Reads a list of names from a text file and converts it to JSON format.

#### `recognize_speech(self)`
- Uses `sounddevice` to capture live audio.
- Feeds audio into Vosk for speech recognition.
- Returns recognized text.

#### `synthesize_speech(self, text, slow=False)`
- **Parameters:** `text` (str) - Input text, `slow` (bool) - Use standard engine for slower speech.
- **Returns:** Binary audio stream from Amazon Polly.
- Selects a voice from AWS Polly based on the selected language.
- Converts English prompts into the chosen language.
- Synthesizes speech using AWS Polly.

#### `run(self)`
- Streamlit-based UI.
- Allows language selection and runs speech recognition.
- Plays back recognized speech using Polly.
- Future implementation: SMS confirmation using AWS SNS.

### Running the App
Run the script with:
```sh
streamlit run script.py
```

### Future Enhancements
- Fuzzy name matching with `fuzzywuzzy`.
- SMS verification using AWS SNS.
- Support for additional languages.
- Models for other languages: https://alphacephei.com/vosk/models
- Confluence docs: https://arionkoder.atlassian.net/wiki/spaces/AK/pages/1165000733/ArionVoicer+Documentation

### Authors
- [Aislan Diego](diego@arionkoder.com)
