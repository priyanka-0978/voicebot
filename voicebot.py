import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import streamlit as st
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
import speech_recognition as sr
import pyttsx3
import threading
from dotenv import load_dotenv
import os

load_dotenv()  # loads variables from .env into environment
api_key = os.getenv("API_KEY")

# --- Global Variables ---
speech_thread = None
stop_flag = False
lock = threading.Lock()

# --- LLM Setup ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
    google_api_key=api_key  # Replace with your actual key
)
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)

# --- Speech Recognizer ---
recognizer = sr.Recognizer()

# --- TTS Function ---
def speak(text):
    global stop_flag
    try:
        local_engine = pyttsx3.init()
        local_engine.setProperty('rate', 170)
        voices = local_engine.getProperty('voices')
        local_engine.setProperty('voice', voices[1].id)

        if not stop_flag:
            local_engine.say(text)
            local_engine.runAndWait()

        local_engine.stop()

    except RuntimeError:
        pass

def stop_speaking():
    global stop_flag
    stop_flag = True
    try:
        local_engine = pyttsx3.init()
        local_engine.stop()
    except RuntimeError:
        pass

# --- Streamlit UI ---
st.set_page_config(page_title="🎙️ Voice AI Bot")
st.title("🎙️ Voice-Interactive AI Assistant")
st.markdown("""
- **Click "Start Speaking"** to begin a conversation with the AI.
- **Click "Stop Speaking"** to immediately halt the AI response.
""")


status = st.empty()  # Status display
response_placeholder = st.empty()  # Conversation display

# --- Start Speaking Button (At the Top) ---
if st.button("🎤 Start Speaking"):
    stop_flag = False  # Reset stop flag
    status.info("🤖 Responding...")  # Show responding status

    try:
        with sr.Microphone() as source:
            status.info("Adjusting for noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            status.info("Listening... Speak now.")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)

            user_input = recognizer.recognize_google(audio)

            # Update response placeholder with User & AI response together
            prompt = user_input + ", keep answer short and concise"
            response = conversation.run(prompt)

            response_placeholder.markdown(f"**You:** {user_input}\n\n**AI:** {response}")

            # Update status to "Speaking..." while AI is talking
            status.info("🗣️ Speaking...")

            # Stop any running speech thread first
            if speech_thread and speech_thread.is_alive():
                stop_speaking()
                speech_thread.join()

            speech_thread = threading.Thread(target=speak, args=(response,))
            speech_thread.start()

            # Wait for speech to finish before updating status
            speech_thread.join()
            status.success("✅ Done")

    except sr.WaitTimeoutError:
        status.error("⏳ Timeout. Please speak more quickly.")
    except sr.UnknownValueError:
        status.error("😕 Could not understand what you said.")
    except sr.RequestError:
        status.error("❌ Could not connect to speech service.")

# --- Stop Speaking Button (Always Visible at Bottom) ---
st.button("🛑 Stop Speaking", on_click=stop_speaking)
