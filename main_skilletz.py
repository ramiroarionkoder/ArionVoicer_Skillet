import streamlit as st
import os
import json
import queue
import vosk
import sounddevice as sd
import boto3
import numpy as np
from fuzzywuzzy import fuzz
from botocore.exceptions import NoCredentialsError

class VoiceRecognitionApp:
    """
    A class to represent a voice recognition application using Vosk and AWS Polly.
    remove code
    """

    def __init__(self):
        """
        Initialize the VoiceRecognitionApp with AWS Polly client and Vosk models.
        """
        # For future implementations
        self.language_choice = None
        session = boto3.Session()
        self.polly_client = session.client("polly", region_name="us-east-1")

        # Set my models path
        self.br_model = self.load_vosk_model(os.path.join("models", "pt-BR"))
        self.es_model = self.load_vosk_model(os.path.join("models", "es-ES"))
        self.it_model = self.load_vosk_model(os.path.join("models", "it-IT"))  # Italian model

        # default models
        self.model = self.es_model

        # Load my custom names
        self.br_names = self.load_grammar("models/br_names.txt")
        self.es_names = self.load_grammar("models/es_names.txt")
        self.it_names = self.load_grammar("models/it_names.txt")  # Italian names

        # Load the default names
        self.grammar = self.es_names

        self.sample_rate = 16000

    @staticmethod
    def load_vosk_model(model_path):
        """
        Load the Vosk model from the specified path.

        Args:
            model_path (str): Path to the Vosk model directory.

        Returns:
            vosk.Model: Loaded Vosk model.
        """
        if not os.path.exists(model_path):
            print(f"Models not found in {model_path}")
            st.error("Models not found")
            st.stop()
        return vosk.Model(model_path)

    @staticmethod
    def load_grammar(file_path):
        """
        Load grammar from a file containing a list of words.

        Args:
            file_path (str): Path to the file containing the word list.

        Returns:
            str: JSON string representing the grammar.
        """
        if not os.path.exists(file_path):
            st.error(f"Names files {file_path} not found!")
            st.stop()
        with open(file_path, 'r') as file:
            words = file.read().splitlines()
        return json.dumps(words)  # Correct format

    def recognize_speech(self, sample_rate=16000, block_size=8000):
        """
        Record and transcribe speech using multiple Vosk models with custom grammar.

        Args:
            sample_rate (int): Sample rate for audio recording
            block_size (int): Block size for audio processing

        Returns:
            str: Recognized text from the speech.
        """
        q = queue.Queue(maxsize=1)

        def callback(indata, frames, time, status):
            if status:
                st.error(status)
            q.put(bytes(indata))

        # Initialize recognizer
        with sd.RawInputStream(samplerate=sample_rate, blocksize=block_size, dtype='int16',
                               channels=1, callback=callback):
            message_placeholder = st.empty()
            message_placeholder.write("🎤 Listening... Speak now")  # Mensaje temporal
            # self.msg_listening = "Listening... Speak now"
            # st.write(f"""{self.msg_listening}""")
            rec = vosk.KaldiRecognizer(self.model, sample_rate, self.grammar)
            rec.energy_threshold = 300  # Ajusta este valor según el ruido ambiental
            rec.dynamic_energy_threshold = True  # Permite ajustes automatizados

            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    message_placeholder.empty()
                    result = json.loads(rec.Result())
                    return result.get("text", "")

    def synthesize_speech(self, text, slow=False) -> bytes:
        """
        Synthesize speech using AWS Polly.

        Args:
            text (str): Text to be synthesized.
            slow (bool): Whether to use slow mode for speech synthesis.

        Returns:
            bytes: Audio data in bytes.
        """
        try:
            # Get available voices for the specified language
            voices_response = self.polly_client.describe_voices(LanguageCode=self.language_choice)
            voices = voices_response.get("Voices", [])

            if not voices:
                raise ValueError(f"No voices found for language: {self.language_choice}")

            engine = "standard"

            # Select the first voice that supports the specified engine
            selected_voice = None
            for voice in voices:
                if "neural" in voice.get("SupportedEngines", []):
                    selected_voice = voice["Id"]
                    engine = "neural"
                    break

            # If no neural voice is found, fall back to standard
            if not selected_voice:
                print(f"Neural engine not available for {self.language_choice}. Using standard.")
                selected_voice = voices[0]["Id"]
                engine = "standard"

            # Synthesize speech
            if self.language_choice == "pt-BR":
                text = text.replace("Did you say", "Você disse")
            elif self.language_choice == "es-ES":
                text = text.replace("Did you say", "Dijiste")
            elif self.language_choice == "it-IT":
                text = text.replace("Did you say", "Hai detto")

            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat="mp3",
                VoiceId=selected_voice,
                Engine=engine if not slow else "standard"
            )
            return response["AudioStream"].read()
        except Exception as e:
            print(f"Polly Error: {e}")

    def update_grammar(self, new_text):
        """
        Update the grammar file with new text for model improvement.

        Args:
            new_text (str): New text to add to the grammar
        """
        if self.language_choice == "es-ES":
            grammar_file = "models/es_names.txt"
        elif self.language_choice == "it-IT":
            grammar_file = "models/it_names.txt"
        else:
            grammar_file = "models/br_names.txt"

        # Read existing grammar
        with open(grammar_file, 'r') as file:
            existing_words = set(file.read().splitlines())

        # Add new text if it's not already present
        if new_text.strip().lower() not in {word.lower() for word in existing_words}:
            with open(grammar_file, 'a') as file:
                file.write(f"\n{new_text.strip()}")

            # Reload grammar
            if self.language_choice == "es-ES":
                self.grammar = self.load_grammar("models/es_names.txt")
            elif self.language_choice == "it-IT":
                self.grammar = self.load_grammar("models/it_names.txt")
            else:
                self.grammar = self.load_grammar("models/br_names.txt")
            return True
        return True

    def reset_session(self):
        """
        Reset all session state variables to their initial values
        """
        # First, store any values we need to preserve
        language_choice = getattr(st.session_state, 'language_choice', 'es-ES')

        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        # Restore preserved values and set initial states
        st.session_state.language_choice = language_choice
        st.session_state.current_cycle = 0
        st.session_state.recognition_active = False
        st.session_state.show_manual_input = False
        st.session_state.manual_submitted = False

    def run(self):
        """
        Run the Streamlit app for voice recognition and speech synthesis.
        """
        st.title("ArionVoicer - Special Voice Recognition")
        st.write("Recognizing names accurately, even with accents!")

        # Initialize session states if not exists
        if 'current_cycle' not in st.session_state:
            st.session_state.current_cycle = 0
        if 'recognition_active' not in st.session_state:
            st.session_state.recognition_active = False
        if 'show_manual_input' not in st.session_state:
            st.session_state.show_manual_input = False
        if 'manual_submitted' not in st.session_state:
            st.session_state.manual_submitted = False

        self.language_choice = st.selectbox("Select language model", ["es-ES", "pt-BR", "it-IT"], index=0)
        st.session_state.language_choice = self.language_choice

        speak_slower_msg = """
            **Try one of the following options:**
            1. Speak more slowly
            2. Say the last name in the context of a sentence, for example: *'I was playing with {Name LastName}'*
            3. Change the base language according to the origin of the last name
            """

        if self.language_choice == "pt-BR" and self.model != self.br_model:
            self.model = self.br_model
            self.grammar = self.br_names
        elif self.language_choice == "es-ES" and self.model != self.es_model:
            self.model = self.es_model
            self.grammar = self.es_names
        elif self.language_choice == "it-IT" and self.model != self.it_model:
            self.model = self.it_model
            self.grammar = self.it_names

        # Define recognition cycles with different parameters
        recognition_cycles = [
            {"sample_rate": 16000, "block_size": 2048},
            {"sample_rate": 32000, "block_size": 4096},
            {"sample_rate": 44100, "block_size": 8192}
        ]

        # Place Start Recognition and Reset buttons side by side
        col1, col2 = st.columns(2)
        start_recognition = col1.button("Start Recognition", key=f"start_{st.session_state.current_cycle}")
        reset_recognition = col2.button("Reset Recognition", key="reset")

        if reset_recognition:
            self.reset_session()

        if start_recognition:
            st.session_state.recognition_active = True
            st.session_state.show_manual_input = False
            st.session_state.current_cycle = 0
            st.rerun()

        if st.session_state.show_manual_input:
            # Manual input after all attempts failed
            st.error("Voice recognition was not successful after 3 attempts.")
            st.warning("Please enter your last name manually below:")

            # Create columns for better layout
            col1, col2 = st.columns([3, 1])
            with col1:
                manual_text = st.text_input("Enter the correct last name (SMS):", key="manual_input")
            with col2:
                submit_button = st.button("Submit", key="submit_manual")

            if submit_button and manual_text:
                st.success(f"Last Name recorded: {manual_text}")

                # Update grammar with the new text
                if self.update_grammar(manual_text):
                    st.info("Model grammar has been updated with the new name to improve future recognition.")

                # Reset session and refresh page
                self.reset_session()

        elif st.session_state.recognition_active:
            current_cycle = st.session_state.current_cycle

            if current_cycle < len(recognition_cycles):
                params = recognition_cycles[current_cycle]

                # Show message for subsequent attempts
                if current_cycle > 0:
                    st.write(f"Attempt {current_cycle + 1} of {len(recognition_cycles)}")
                    st.warning(speak_slower_msg)
                    # Display current recognition parameters
                    st.info(f"""Recognition Parameters:
                    - Cycle: {current_cycle + 1}
                    - Sample Rate: {params['sample_rate']} Hz
                    - Block Size: {params['block_size']}""")

                recognized_text = self.recognize_speech(
                    sample_rate=params["sample_rate"],
                    block_size=params["block_size"]
                )

                # Take last words of text to be the last name
                words = recognized_text.split()
                last_name = " ".join(words[-1:]) if len(words) >= 1 else recognized_text

                # Display results in a formatted box
                st.write("Recognition Results:")
                st.code(f"""Recognized Text: {recognized_text}
Recognized Last Name: {last_name}
Parameters Used:
    - Sample Rate: {params['sample_rate']} Hz
    - Block Size: {params['block_size']}
    - Recognition Cycle: {current_cycle + 1} of {len(recognition_cycles)}""")

                # Confirmation buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, that's correct", key=f"confirm_{current_cycle}"):
                        st.success(f"Great! Successfully recognized: {last_name}")
                        self.reset_session()
                with col2:
                    if st.button("No, try again", key=f"retry_{current_cycle}"):
                        if current_cycle == len(recognition_cycles) - 1:
                            # This was the last cycle, show manual input
                            st.session_state.show_manual_input = True
                            st.session_state.recognition_active = False
                        else:
                            # Move to next cycle
                            st.session_state.current_cycle += 1
                            # st.rerun()

if __name__ == "__main__":
    app = VoiceRecognitionApp()
    app.run()
