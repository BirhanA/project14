# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty
from kivy.core.text import LabelBase
from plyer import storagepath
import os

# Register font
LabelBase.register(name="AbyssinicaSIL", fn_regular="fonts/AbyssinicaSIL-Regular.ttf")

# Detect platform
try:
    from jnius import autoclass
    from android.storage import primary_external_storage_path
    is_android = True
except ImportError:
    is_android = False

if not is_android:
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

    def on_pre_enter(self):
        self.load_lines()
        self.display_line(self.current_index)

    def load_lines(self):
        try:
            with open("line.txt", encoding='utf-8') as f:
                self.lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error loading lines: {e}")
            self.lines = []

    def display_line(self, index):
        if 0 <= index < len(self.lines):
            self.current_line = self.lines[index]
            self.ids.line_number_input.text = str(index + 1)
        else:
            self.current_line = ""
            self.ids.line_number_input.text = ""

    def go_to_line(self):
        try:
            index = int(self.ids.line_number_input.text) - 1
            if 0 <= index < len(self.lines):
                self.current_index = index
                self.display_line(self.current_index)
        except ValueError:
            print("Invalid line number entered.")

    def next_line(self):
        if self.current_index < len(self.lines) - 1:
            self.current_index += 1
            self.display_line(self.current_index)

    def prev_line(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_line(self.current_index)

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

                base_dir = os.path.join(primary_external_storage_path(), "LineRecordings", self.current_user)
                os.makedirs(base_dir, exist_ok=True)
                # Corrected line: Use base_dir instead of undefined user_dir
                self.audio_path = os.path.join(base_dir, f"{self.current_user}_line_{self.current_index + 1}.wav")

                self.temp_audio_path = self.audio_path.replace(".wav", ".3gp")

                self.recorder.setOutputFile(self.temp_audio_path)
                self.recorder.prepare()
                self.recorder.start()
                self.is_recording = True
                print("🎙️ Android recording started")
            except Exception as e:
                print(f"Android recording error: {e}")
        else:
            try:
                music_dir = storagepath.get_music_dir() or "."
                user_dir = os.path.join(music_dir, "LineRecordings", self.current_user)
                os.makedirs(user_dir, exist_ok=True)
                self.audio_path = os.path.join(user_dir, f"{self.current_user}_line_{self.current_index + 1}.wav")

                print(f"🎙️ Starting desktop recording: {self.audio_path}")
                self.recording = sd.rec(int(60 * self.fs), samplerate=self.fs, channels=self.channels, dtype='float32')
                self.is_recording = True
            except Exception as e:
                print(f"Desktop recording error: {e}")

    def stop_recording(self):
        if not self.is_recording:
            print("⚠️ Not currently recording.")
            return

        if is_android:
            try:
                self.recorder.stop()
                self.recorder.release()
                self.is_recording = False
                os.rename(self.temp_audio_path, self.audio_path)
                print(f"✅ Android recording saved to: {self.audio_path}")
            except Exception as e:
                print(f"Android stop recording error: {e}")
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
                print(f"Desktop stop recording error: {e}")

    def trim_silence(self, audio, threshold=0.01):
        abs_audio = np.abs(audio)
        if audio.ndim > 1:
            abs_audio = np.max(abs_audio, axis=1)
        non_silent = np.where(abs_audio > threshold)[0]
        return audio[non_silent[0]:non_silent[-1]+1] if non_silent.size else audio[:1]

    def save_recording(self):
        print("ℹ️ Recording is saved automatically on stop.")

    def change_settings(self):
        self.manager.current = 'login'

class LineApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LineApp().run()
