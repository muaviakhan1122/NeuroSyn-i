import speech_recognition as sr # type: ignore
import webbrowser
import pyttsx3
import os
import datetime
import threading
import requests # type: ignore 
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog
import json
import google.generativeai as genai # type: ignore

# API Keys (Consider using environment variables for security)
CONFIG = {
    "newsapi": "0f8c1818fae645ffb632113d9d04aa74",
    "weather_api": "a93488f223194895ac045648250402",
    "genai_key": "AIzaSyBygYbUpztuT76GkpEigtIelEX_nJRBAkg"
}

# Configure AI Model
genai.configure(api_key=CONFIG["genai_key"])
model = genai.GenerativeModel("gemini-1.5-flash")

recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Global variables
conversation_history = []

def save_history():
    """Saves conversation history to a file."""
    with open("chat_history.json", "w") as file:
        json.dump(conversation_history, file)

def load_history():
    """Loads conversation history from a file."""
    global conversation_history
    try:
        with open("chat_history.json", "r") as file:
            conversation_history = json.load(file)
    except FileNotFoundError:
        conversation_history = []

# Load existing history
load_history()

class SmartAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Assistant")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Apply theme
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Define styles for dark mode
        self.style.configure("DarkButton", background="#333333", foreground="white")

        # Create Frames
        self.sidebar = ttk.Frame(root, width=120, relief="ridge")
        self.sidebar.pack(side="left", fill="y")

        self.chat_frame = ttk.Frame(root)
        self.chat_frame.pack(side="right", fill="both", expand=True)

        # Sidebar Buttons
        ttk.Button(self.sidebar, text="Google", command=self.open_google).pack(pady=10, padx=5)
        ttk.Button(self.sidebar, text="Weather", command=self.show_weather_dialog).pack(pady=10, padx=5)
        ttk.Button(self.sidebar, text="News", command=self.fetch_news).pack(pady=10, padx=5)
        ttk.Button(self.sidebar, text="Dark Mode", command=self.toggle_theme).pack(pady=10, padx=5)

        # Chat Display
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, state="disabled", height=20)
        self.chat_display.pack(pady=5, padx=10, fill="both", expand=True)

        # Input Area
        self.entry_frame = ttk.Frame(self.chat_frame)
        self.entry_frame.pack(fill="x", padx=10, pady=5)

        self.user_input = ttk.Entry(self.entry_frame, width=50)
        self.user_input.pack(side="left", fill="x", expand=True, padx=5)
        self.user_input.bind("<Return>", self.process_input)

        self.send_button = ttk.Button(self.entry_frame, text="Send", command=self.process_input)
        self.send_button.pack(side="left")

        self.mic_button = ttk.Button(self.entry_frame, text="🎤", command=self.listen_voice)
        self.mic_button.pack(side="left", padx=5)

        # Dark mode state
        self.dark_mode = False

    def open_google(self):
        """Open Google in the web browser."""
        webbrowser.open("https://google.com")
        self.display_message("AI: Opening Google.", "green")

    def show_weather_dialog(self):
        """Prompt the user for a city name to fetch weather information."""
        city = simpledialog.askstring("Input", "Enter the city name for weather information:")
        if city:
            self.fetch_weather(city)

    def display_message(self, message, color):
        """Display a message in the chat display."""
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, message + "\n", color)
        self.chat_display.tag_configure(color, foreground=color)
        self.chat_display.config(state="disabled")
        self.chat_display.yview(tk.END)

    def speak(self, text):
        """Speak the given text."""
        engine.say(text)
        engine.runAndWait()

    def get_response(self, text, is_voice=False):
        """Generate a response using the AI model."""
        global conversation_history
        conversation_history.append({"role": "user", "parts": [{"text": text}]})

        response = model.generate_content(text)

        if response and hasattr(response, 'text'):
            ai_response = response.text
            conversation_history.append({"role": "assistant", "parts": [{"text": ai_response}]})
            self.display_message("Assistant: " + ai_response, "green")
            if is_voice:
                self.speak(ai_response)  # Speak only if it's a voice command
            save_history()
        else:
            self.display_message("Assistant: I couldn't process that. Please try again.", "red")

    def process_input(self, event=None):
        """Process user input from the text entry."""
        command = self.user_input.get()
        if command:
            self.display_message("You: " + command, "blue")
            self.user_input.delete(0, tk.END)  # Clear the entry field
            self.get_response(command, is_voice=False)  # Process as text command

    def listen_voice(self):
        """Start listening for voice commands."""
        threading.Thread(target=self.listen, daemon=True).start()

    def listen(self):
        """Listens for a voice command and processes it."""
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                self.display_message("Listening for commands...", "orange")
                audio = recognizer.listen(source, timeout=5)

            command = recognizer.recognize_google(audio).lower()
            self.display_message(f"You: {command}", "blue")
            self.get_response(command, is_voice=True)  # Process the command as a voice command
        except sr.UnknownValueError:
            self.display_message("Sorry, I couldn't understand that.", "red")
            self.speak("Sorry, I couldn't understand that.")
        except sr.RequestError:
            self.display_message("Check your internet connection.", "red")
            self.speak("Check your internet connection.")
        except Exception as e:
            self.display_message(f"Error: {e}", "red")
            self.speak(f"Error: {e}")
    def process_command(self, command):
        """Handles user commands."""
        if "open google" in command:
            webbrowser.open("https://google.com")
            self.open_google()
        elif "open youtube" in command:
            webbrowser.open("https://youtube.com")
            self.display_message("AI: Opening YouTube.", "green")
            self.speak("Opening YouTube.")
        elif "open facebook" in command:
            webbrowser.open("https://facebook.com")
            self.display_message("AI: Opening Facebook.", "green")
            self.speak("Opening Facebook.")
        elif "news" in command:
            self.fetch_news()
            self.speak("Fetching the latest news.")
        elif "weather in" in command:
            city = command.replace("weather in", "").strip()
            self.fetch_weather(city)
            self.speak(f"Fetching weather information for {city}.")
        elif "play" in command:
            self.play_youtube(command.replace("play", "").strip())
            self.speak(f"Playing {command.replace('play', '').strip()} on YouTube.")
        elif "search" in command:
            self.search_google(command.replace("search", "").strip())
            self.speak(f"Searching Google for {command.replace('search', '').strip()}.")
        elif "restart" in command:
            self.display_message("AI: Restarting the system now.", "green")
            self.speak("Restarting the system now.")
            os.system("shutdown /r /t 1")
        elif "shutdown" in command:
            self.display_message("AI: Shutting down the system now.", "green")
            self.speak("Shutting down the system now.")
            os.system("shutdown /s /t 1")
        else:
            self.get_response(command)  # Pass the command to the AI model

    def fetch_news(self):
        """Fetches and displays the latest news headlines."""
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={CONFIG['newsapi']}"
        try:
            r = requests.get(url)
            r.raise_for_status()
            articles = r.json().get("articles", [])
            if articles:
                self.display_message("AI: Here are the latest news headlines:", "green")
                for article in articles[:5]:
                    self.display_message(f"AI: {article['title']}", "green")
            else:
                self.display_message("AI: No news found at the moment.", "red")
        except requests.RequestException:
            self.display_message("AI: I can't fetch news right now.", "red")

    def fetch_weather(self, city):
        """Fetches current weather conditions."""
        url = f"http://api.weatherapi.com/v1/current.json?key={CONFIG['weather_api']}&q={city}&aqi=no"
        try:
            response = requests.get(url)
            response.raise_for_status()
            weather_data = response.json()
            weather_info = f"The current temperature in {city} is {weather_data['current']['temp_c']} degrees Celsius with {weather_data['current']['condition']['text']}."
            self.display_message(f"AI: {weather_info}", "green")
        except requests.RequestException:
            self.display_message("AI: Unable to retrieve weather data.", "red")

    def play_youtube(self, query):
        """Plays a video on YouTube."""
        webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
        self.display_message(f"AI: Playing {query} on YouTube.", "green")

    def search_google(self, query):
        """Performs a Google search."""
        webbrowser.open(f"https://www.google.com/search?q={query}")
        self.display_message(f"AI: Searching Google for {query}.", "green")

    def toggle_theme(self):
        """Toggle between light and dark mode."""
        if self.dark_mode:
            # Switch to light mode
            self.root.configure(bg="white")
            self.chat_display.configure(bg="white", fg="black")
            self.sidebar.configure(bg="white")
            self.user_input.configure(bg="white", fg="black")
            self.send_button.configure(style="TButton")  # Reset to default style
            self.mic_button.configure(style="TButton")  # Reset to default style
            self.dark_mode = False 
        else:
            # Switch to dark mode
            self.root.configure(bg="#121212")  # Dark background for the main window
            self.chat_display.configure(bg="#121212", fg="white")  # Dark background for chat display
            self.sidebar.configure(bg="#1E1E1E")  # Dark background for sidebar
            self.user_input.configure(bg="#1E1E1E", fg="white")  # Dark background for input
            self.send_button.configure(style="DarkButton")  # Use a custom style for dark mode
            self.mic_button.configure(style="DarkButton")  # Use a custom style for dark mode
            self.dark_mode = True

# Load existing history
load_history()

# GUI Setup
root = tk.Tk()
app = SmartAssistantGUI(root)
root.protocol("WM_DELETE_WINDOW", lambda: (save_history(), root.destroy()))
root.mainloop()
