import os
import threading
import speech_recognition as sr
import random
from gtts import gTTS
from dotenv import load_dotenv
from playsound3 import playsound
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
import tkinter as tk

load_dotenv()

# --- Constants ---
DARK_RED = "#a11a22"
WHITE = "#FFFFFF"
LIGHT_GRAY = "#CCCCCC"

# --- Core Functions ---
def speak(text):
    """Converts text to speech and plays it."""
    try:
        tts = gTTS(text=text, lang='en')
        with open("response.mp3", "wb") as f:
            tts.write_to_fp(f)
        playsound("response.mp3")
        os.remove("response.mp3")
    except Exception as e:
        print(f"Error in speak function: {e}")

def listen(app_instance):
    """Listens for voice input and returns the recognized text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        app_instance.update_status("Listening...")
        r.pause_threshold = 1.5
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=20)
        except sr.WaitTimeoutError:
            app_instance.update_status("I didn't hear anything. Let's try that again.")
            return None
    try:
        app_instance.update_status("Processing...")
        query = r.recognize_google(audio, language='en-us')
        app_instance.update_status(f"Heard: \"{query}\"")
        return query
    except Exception:
        speak("I'm sorry, I didn't quite catch that. Could you please repeat?")
        return listen(app_instance)

# --- Main Application Class ---
class ClaimApp:
    def __init__(self, root):
        self.root = root
        self.questions = {
            "Your Full Name": "To begin, what is your full name?",
            "Contact Phone": "What is a good contact phone number for you?",
            "Date & Time of Accident": "What was the date and approximate time of the accident?",
            "Location of Accident": "Where did the accident happen? Please be as specific as you can.",
            "Your Vehicle": "What is the year, make, and model of your vehicle?",
            "Other Vehicle": "Now, regarding the other vehicle involved, what was its make, model, and color?",
            "Other Driver's Name": "What was the name of the other driver, if you were able to get it?",
            "Police Report": "Was a police report filed? If so, do you have the report number?",
            "Description of Incident": "Finally, in your own words, please describe how the accident occurred."
        }
        self.claim_data = {}
        
        # --- Style Configuration ---
        self.style = ttk.Style()
        self.style.configure('.', background=DARK_RED, foreground=WHITE, font=("Helvetica", 13))
        self.style.configure('TFrame', background=DARK_RED)
        self.style.configure('TLabel', background=DARK_RED, foreground=WHITE)
        self.style.configure('secondary.TLabel', foreground=LIGHT_GRAY)
        self.style.configure('info.TLabel', foreground=LIGHT_GRAY, font=("Helvetica", 12, "italic"))
        self.style.configure('TSeparator', background=LIGHT_GRAY)
        # Custom button style with white border
        self.style.configure('primary.TButton', background=DARK_RED, foreground=WHITE, borderwidth=2)
        self.style.map('primary.TButton', bordercolor=[('!active', WHITE), ('active', WHITE)], background=[('active', '#b82a35')])
        
        self.root.configure(background=DARK_RED)
        self.main_frame = ttk.Frame(self.root, padding=(40, 20), style='TFrame')
        self.main_frame.pack(expand=True, fill=BOTH)
        
        self.show_start_screen()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _create_header(self, parent_frame):
        header_frame = ttk.Frame(parent_frame, style='TFrame')
        header_frame.pack(pady=(10, 20))
        ttk.Label(header_frame, text="STATE FARM", font=("Helvetica", 36, "bold")).pack()
        ttk.Separator(parent_frame).pack(fill=X, pady=(0, 20))

    def show_start_screen(self):
        self.clear_frame()
        self.claim_data = {}
        self._create_header(self.main_frame)
        
        ttk.Label(self.main_frame, text="Your Voice-Powered Car Accident Claim Assistant", font=("Helvetica", 18)).pack(pady=(0, 25))
        
        questions_container = ttk.Frame(self.main_frame, style='TFrame')
        questions_container.pack(fill=BOTH, expand=YES)

        self.question_labels = {}
        for key in self.questions.keys():
            q_frame = ttk.Frame(questions_container, style='TFrame')
            q_frame.pack(fill=X, pady=7, anchor=W)
            icon = ttk.Label(q_frame, text="◎", font=("Helvetica", 16))
            icon.pack(side=LEFT, padx=(0, 15))
            label = ttk.Label(q_frame, text=f"{key}", font=("Helvetica", 13, "bold"), width=25, anchor=W)
            label.pack(side=LEFT)
            self.question_labels[key] = {'icon': icon, 'label': label}
        self.update_question_ui()

        self.status_var = tk.StringVar(value="When you're ready, click 'Start New Claim' to begin.")
        ttk.Label(self.main_frame, textvariable=self.status_var, style="info.TLabel", wraplength=700).pack(pady=20, side=BOTTOM, fill=X)
        
        self.start_button = ttk.Button(self.main_frame, text="Start New Claim", style="primary.TButton", command=self.start_threaded_process)
        self.start_button.pack(side=BOTTOM, ipady=15, fill=X, pady=10)
    
    def show_summary_screen(self):
        self.clear_frame()
        self._create_header(self.main_frame)
        
        ttk.Label(self.main_frame, text="Claim Summary for Review", font=("Helvetica", 18, "bold"), style='secondary.TLabel').pack(pady=(0, 20), anchor=W)

        # Container for the text and buttons
        summary_container = ttk.Frame(self.main_frame, style='TFrame')
        summary_container.pack(fill=BOTH, expand=YES)

        # Use ScrolledText for a copyable summary
        self.summary_text = ScrolledText(summary_container, padding=15, autohide=True, state="disabled")
        self.summary_text.pack(fill=BOTH, expand=YES, pady=(0, 15))
        
        # Style the inner text widget
        self.summary_text.text.configure(background=DARK_RED, foreground=WHITE, font=("Helvetica", 12), highlightthickness=0, borderwidth=0)

        # Generate and insert formatted summary
        summary_string = ""
        for key, value in self.claim_data.items():
            summary_string += f"--- {key.upper()} ---\n{value}\n\n"
        
        self.summary_text.text.config(state="normal")
        self.summary_text.text.delete("1.0", END)
        self.summary_text.text.insert("1.0", summary_string)
        self.summary_text.text.config(state="disabled")

        # Container for the bottom buttons
        button_container = ttk.Frame(summary_container, style='TFrame')
        button_container.pack(fill=X, side=BOTTOM, pady=(10, 0))

        copy_button = ttk.Button(button_container, text="Copy to Clipboard", style="primary.TButton", command=self.copy_summary)
        copy_button.pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        
        new_claim_button = ttk.Button(button_container, text="File Another Claim", style="primary.TButton", command=self.show_start_screen)
        new_claim_button.pack(side=LEFT, expand=True, fill=X, padx=(5, 0))

    def copy_summary(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.summary_text.text.get("1.0", END))
        self.update_status("Summary copied to clipboard!")

    def update_status(self, message):
        self.status_var.set(message)

    def update_question_ui(self, current_key=None):
        for key, items in self.question_labels.items():
            if key in self.claim_data:
                items['icon'].config(foreground="#28a745") # Success Green
                items['label'].config(foreground=LIGHT_GRAY)
            elif key == current_key:
                items['icon'].config(foreground="#ffc107") # Active Yellow
                items['label'].config(foreground=WHITE)
            else:
                items['icon'].config(foreground=LIGHT_GRAY)
                items['label'].config(foreground=LIGHT_GRAY)

    def run_claim_process(self):
        self.start_button.config(state=DISABLED)
        speak("Hello, and thank you for choosing State Farm. I'm here to help you start your car accident claim. I will ask you a series of questions. Please answer each one after the prompt.")
        
        confirmation_phrases = ["Okay.", "Got it.", "Thanks.", "Alright, noting that down."]
        
        for key, question in self.questions.items():
            self.update_question_ui(current_key=key)
            speak(question)
            answer = listen(self)
            if answer:
                self.claim_data[key] = answer.capitalize()
                if key != list(self.questions.keys())[-1]:
                    speak(random.choice(confirmation_phrases))
            else:
                self.update_status("Process cancelled. Please click 'Start New Claim' to try again.")
                self.start_button.config(state=NORMAL)
                return
            self.update_question_ui()
        
        self.update_status("Thank you for the information. Preparing your claim summary for review...")
        speak("That's all the information I need. Thank you. Please take a moment to review the summary on screen.")
        self.show_summary_screen()

    def start_threaded_process(self):
        threading.Thread(target=self.run_claim_process, daemon=True).start()

def main():
    root = ttk.Window(themename="darkly") # Use a dark base theme
    root.title("Voice Claim Assistant")
    root.geometry("850x800")
    app = ClaimApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
