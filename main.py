# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty, ListProperty # Added ListProperty
from kivy.core.text import LabelBase
from plyer import storagepath
import os
import traceback # Import traceback for detailed error logging

# Register font
LabelBase.register(name="AbyssinicaSIL", fn_regular="fonts/AbyssinicaSIL-Regular.ttf")

# Detect platform
try:
    from jnius import autoclass
    from android.storage import primary_external_storage_path
    from android.permissions import request_permissions, Permission # Import request_permissions and Permission
    is_android = True
except ImportError:
    is_android = False
    # For non-Android, import sounddevice and scipy.io.wavfile
    import sounddevice as sd
    from scipy.io.wavfile import write
    import numpy as np


class LoginScreen(Screen):
    def do_login(self, username, password):
        if username and password:
            self.manager.get_screen('main').current_user = username
            self.manager.current = 'main'

class MainScreen(Screen):
    current_line = StringProperty("")
    current_index = NumericProperty(0)
    current_user = StringProperty("")
    fs = 16000
    channels = 1
    recording = None
    is_recording = False
    audio_path = ""
    temp_audio_path = "" # Initialize temp_audio_path

    # New properties for file selection
    available_text_files = ListProperty([])
    # Default to the bundled line.txt, or a placeholder if it's not present
    selected_text_file = StringProperty("line.txt (bundled)") 
    text_files_base_dir = "" # Will store the path to the user's text files directory

    def on_pre_enter(self):
        """
        Called when the MainScreen is about to become active.
        Handles initial line loading and Android permission requests.
        """
        # Initial load of lines. This will load from bundled line.txt first.
        # If line.txt is not found, it will set an error message.
        self.load_lines()
        self.display_line(self.current_index)

        if is_android:
            # Request permissions on Android. File system access (setup/populate)
            # will happen AFTER permissions are granted in on_permission_callback.
            self.request_android_permissions()
        else:
            # For desktop, permissions are not an issue, so set up immediately.
            self.setup_text_files_directory()
            self.populate_text_file_spinner()

    def request_android_permissions(self):
        """Requests necessary Android permissions at runtime."""
        print("Requesting Android permissions...")
        permissions_to_request = [
            Permission.RECORD_AUDIO,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE # Needed for reading user text files
        ]
        request_permissions(permissions_to_request, self.on_permission_callback)

    def on_permission_callback(self, permissions, granted):
        """
        Callback method after Android permissions are requested.
        Only proceeds with file system operations if permissions are granted.
        """
        print(f"Permissions callback received. Permissions: {permissions}, Granted: {granted}")
        if all(granted):
            print("✅ All required permissions granted. Proceeding with file system setup.")
            self.setup_text_files_directory()
            self.populate_text_file_spinner()
            # After permissions and spinner populated, re-load the selected file.
            # This ensures user-selected files can be loaded if permissions were just granted.
            self.load_lines()
            self.display_line(self.current_index)
        else:
            print("❌ Not all required permissions were granted. File operations and recording may not work.")
            # Update UI to inform the user about permission issues
            self.lines = ["Permissions denied. Please grant storage and microphone permissions in app settings to use all features."]
            self.current_line = self.lines[0]
            self.current_index = 0
            # Update line number input to reflect the first line
            if self.ids: # Check if ids are available (might not be during initial setup)
                self.ids.line_number_input.text = "1" 
            self.available_text_files = ["Permissions Required"] # Update spinner to reflect state

    def setup_text_files_directory(self):
        """
        Defines and creates the directory where user-provided text files will be stored.
        This is called *after* permissions are confirmed on Android.
        """
        if is_android:
            # For Android, use a subfolder in primary external storage (e.g., /storage/emulated/0/RecorderTextFiles)
            self.text_files_base_dir = os.path.join(primary_external_storage_path(), "RecorderTextFiles")
        else:
            # For desktop, use a subfolder in the user's documents directory
            self.text_files_base_dir = os.path.join(storagepath.get_documents_dir() or ".", "RecorderTextFiles")
        
        try:
            os.makedirs(self.text_files_base_dir, exist_ok=True)
            print(f"Text files directory set to: {self.text_files_base_dir}")
        except Exception as e:
            print(f"Error creating text files directory: {e}")
            traceback.print_exc() # Print full traceback for debugging
            self.lines = [f"Error accessing storage for text files: {e}"]
            self.current_line = self.lines[0]

    def populate_text_file_spinner(self):
        """
        Scans the text files directory and populates the spinner with .txt files.
        Only attempts to list directory if it's set and accessible.
        """
        files = []
        files.append("line.txt (bundled)") # Always add the bundled line.txt as an option

        try:
            # Only attempt to list directory if text_files_base_dir is set and accessible
            if self.text_files_base_dir and os.path.exists(self.text_files_base_dir):
                for filename in os.listdir(self.text_files_base_dir):
                    if filename.lower().endswith(".txt"):
                        files.append(filename)
                self.available_text_files = sorted(list(set(files))) # Remove duplicates and sort
                print(f"Available text files for spinner: {self.available_text_files}")
            else:
                print("Text files base directory not set or not accessible yet (permissions pending?).")
                # Fallback message if directory is not ready/accessible
                self.available_text_files = ["Permissions Required / Directory not ready"] 
        except Exception as e:
            print(f"Error populating text file spinner: {e}")
            traceback.print_exc() # Print full traceback for debugging
            self.available_text_files = ["Error scanning files"] # Fallback

    def on_text_file_selected(self, text_file_name):
        """Called when a text file is selected from the spinner."""
        self.selected_text_file = text_file_name
        self.current_index = 0 # Reset to the first line of the new file
        self.load_lines()
        self.display_line(self.current_index)
        print(f"Selected text file: {self.selected_text_file}")

    def load_lines(self):
        """
        Loads lines from the currently selected text file.
        Handles loading from bundled assets or user-provided directory.
        """
        file_to_load = self.selected_text_file
        
        if file_to_load == "line.txt (bundled)":
            try:
                # Load from bundled assets (assuming line.txt is in the app's root/source.dir)
                with open("line.txt", encoding='utf-8') as f:
                    self.lines = [line.strip() for line in f if line.strip()]
                print(f"Loaded {len(self.lines)} lines from bundled line.txt")
            except Exception as e:
                print(f"Error loading bundled line.txt: {e}")
                traceback.print_exc()
                self.lines = ["Error: Could not load bundled line.txt. Ensure it's in your project root."]
                self.current_line = self.lines[0]
        elif self.text_files_base_dir and os.path.exists(self.text_files_base_dir): # Only try if base_dir is set and exists
            file_path = os.path.join(self.text_files_base_dir, file_to_load)
            try:
                with open(file_path, encoding='utf-8') as f:
                    self.lines = [line.strip() for line in f if line.strip()]
                print(f"Loaded {len(self.lines)} lines from {file_path}")
            except Exception as e:
                print(f"Error loading text file '{file_to_load}': {e}")
                traceback.print_exc()
                self.lines = [f"Error: Could not load {file_to_load}. Check file exists and permissions."]
                self.current_line = self.lines[0]
        else:
            # This case handles when a user file is selected but permissions/directory isn't ready
            self.lines = ["Permissions not granted or file directory not ready. Cannot load user files."]
            self.current_line = self.lines[0]
        
        if not self.lines: # Fallback if lines list is still empty after attempts
            self.lines = ["No lines available. Please add text files to the 'RecorderTextFiles' folder on your device's internal storage."]
            self.current_index = 0
            self.current_line = self.lines[0]


    def display_line(self, index):
        if 0 <= index < len(self.lines):
            self.current_line = self.lines[index]
            # Check if ids.line_number_input exists before accessing it
            if self.ids and 'line_number_input' in self.ids:
                self.ids.line_number_input.text = str(index + 1)
        else:
            self.current_line = ""
            if self.ids and 'line_number_input' in self.ids:
                self.ids.line_number_input.text = ""

    def go_to_line(self):
        try:
            index = int(self.ids.line_number_input.text) - 1
            if 0 <= index < len(self.lines):
                self.current_index = index
                self.display_line(self.current_index)
            else:
                print(f"Line number {index + 1} is out of bounds.")
        except ValueError:
            print("Invalid line number entered.")

    def next_line(self):
        if self.current_index < len(self.lines) - 1:
            self.current_index += 1
            self.display_line(self.current_index)
        else:
            print("Reached end of lines.")

    def prev_line(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_line(self.current_index)
        else:
            print("Reached beginning of lines.")

    def start_recording(self):
        if self.is_recording:
            print("⚠️ Already recording!")
            return

        if is_android:
            try:
                MediaRecorder = autoclass('android.media.MediaRecorder')
                self.recorder = MediaRecorder()
                self.recorder.setAudioSource(MediaRecorder.AudioSource.MIC)
                self.recorder.setOutputFormat(MediaRecorder.OutputFormat.THREE_GPP)
                self.recorder.setAudioEncoder(MediaRecorder.AudioEncoder.AMR_NB)

                # Define base directory for recordings within external storage
                # This will create a folder like /storage/emulated/0/LineRecordings/YourUsername/
                base_dir = os.path.join(primary_external_storage_path(), "LineRecordings", self.current_user)
                os.makedirs(base_dir, exist_ok=True)
                print(f"Attempting to create directory: {base_dir}")

                # Save as .3gp, which is the actual format MediaRecorder outputs
                self.audio_path = os.path.join(base_dir, f"{self.current_user}_line_{self.current_index + 1}.3gp")
                self.temp_audio_path = self.audio_path # No need for temp path if we save as .3gp directly

                self.recorder.setOutputFile(self.audio_path) # Use the .3gp path
                self.recorder.prepare()
                self.recorder.start()
                self.is_recording = True
                print(f"🎙️ Android recording started. Saving to: {self.audio_path}")
            except Exception as e:
                print(f"❌ Android recording error: {e}")
                traceback.print_exc() # Print full traceback for debugging
        else:
            try:
                music_dir = storagepath.get_music_dir() or "."
                user_dir = os.path.join(music_dir, "LineRecordings", self.current_user)
                os.makedirs(user_dir, exist_ok=True)
                self.audio_path = os.path.join(user_dir, f"{self.current_user}_line_{self.current_index + 1}.wav")

                print(f"🎙️ Starting desktop recording: {self.audio_path}")
                # Record for a fixed duration (e.g., 60 seconds) or until stop is pressed
                self.recording = sd.rec(int(60 * self.fs), samplerate=self.fs, channels=self.channels, dtype='float32')
                self.is_recording = True
            except Exception as e:
                print(f"❌ Desktop recording error: {e}")
                traceback.print_exc()

    def stop_recording(self):
        if not self.is_recording:
            print("⚠️ Not currently recording.")
            return

        if is_android:
            try:
                self.recorder.stop()
                self.recorder.release()
                self.is_recording = False
                # No os.rename needed if we saved as .3gp directly
                print(f"✅ Android recording stopped and saved to: {self.audio_path}")
            except Exception as e:
                print(f"❌ Android stop recording error: {e}")
                traceback.print_exc()
        else:
            try:
                sd.stop()
                self.is_recording = False
                if self.recording is not None:
                    trimmed = self.trim_silence(self.recording)
                    max_val = np.max(np.abs(trimmed))
                    scaled = np.int16(trimmed / max_val * 32767) if max_val > 0 else np.int16(trimmed)
                    write(self.audio_path, self.fs, scaled)
                    print(f"✅ Desktop recording saved to: {self.audio_path}")
                    self.recording = None
                else:
                    print("⚠️ No recording buffer found")
            except Exception as e:
                print(f"❌ Desktop stop recording error: {e}")
                traceback.print_exc()

    def trim_silence(self, audio, threshold=0.01):
        # This function is only used for desktop recording
        abs_audio = np.abs(audio)
        if audio.ndim > 1:
            abs_audio = np.max(abs_audio, axis=1)
        non_silent = np.where(abs_audio > threshold)[0]
        return audio[non_silent[0]:non_silent[-1]+1] if non_silent.size else audio[:1]

    def save_recording(self):
        # This function is called by a button, but recording is saved on stop.
        # You might want to add a message box here for user feedback.
        print("ℹ️ Recording is saved automatically when you stop it.")

    # Removed change_settings as it's replaced by file selection
    # def change_settings(self):
    #     self.manager.current = 'login'

class LineApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LineApp().run()
