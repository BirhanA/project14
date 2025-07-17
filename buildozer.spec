[app]

# (str) Title of your application
title = Audio Recorder

# (str) Package name
package.name = recorder

# (str) Package domain (needed for android/ios packaging)
# IMPORTANT: Change this from org.test to a unique domain (e.g., com.yourusername.recorder)
# even for private apps, to avoid potential conflicts or issues in the future.
package.domain = org.ownuse

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
# Added 'ttf', 'json', 'txt' extensions for common data/asset types
source.include_exts = py,png,jpg,kv,atlas,ttf,json,txt

# (list) List of inclusions using pattern matching
# Example: source.include_patterns = assets/*,data/*
# Keep empty if all relevant files are in source.dir or specified via include_exts
source.include_patterns =

# (list) Source files to exclude (let empty to not exclude anything)
# Excludes common temporary or configuration files that are not needed in the APK
source.exclude_exts = pyc,pyo,bak

# (list) List of directory to exclude (let empty to not exclude anything)
# Excludes Buildozer's own directories, test folders, and virtual environments
source.exclude_dirs = tests, bin, venv, .buildozer, __pycache__

# (list) List of exclusions using pattern matching
# Do not prefix with './'
# Adds common exclusions like license files, version control data, and macOS specific files
source.exclude_patterns = license,images/*/*.jpg,*.log,.git/*,.gitignore,.DS_Store

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
# Ensure all necessary libraries for audio recording and UI are included.
requirements = python3,kivy,kivymd,pillow,plyer,sounddevice,numpy,cffi,libffi

# (str) Presplash of the application
presplash.filename = %(source.dir)s/soundrecorder.png 

# (str) Icon of the application
# Path to your application's icon file (e.g., in the project root)
icon.filename = %(source.dir)s/Recorder.png

# (list) Supported orientations
# Valid options are: landscape, portrait, portrait-reverse or landscape-reverse
orientation = landscape

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
# IMPORTANT: RECORD_AUDIO for microphone access.
# WRITE_EXTERNAL_STORAGE for older Android versions to save files (pre-API 29).
# READ_MEDIA_AUDIO for Android 10+ (API 29+) to access audio media files.
# INTERNET for potential network use (e.g., if any part of your app needs online access).
android.permissions = android.permission.RECORD_AUDIO, android.permission.WRITE_EXTERNAL_STORAGE, android.permission.READ_MEDIA_AUDIO, android.permission.INTERNET

# (int) Target Android API, should be as high as possible.
# Targeting Android 14 (API 34) for modern compatibility.
android.api = 34

# (int) Minimum API your APK / AAB will support.
# Compatible with Android 5.0 Lollipop (API 21).
android.minapi = 23

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
# android.ndk_api = 21

# (bool) If True, then automatically accept SDK license agreements. This is intended for automation only.
android.accept_sdk_license = True

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# Building for modern ARM architectures.
android.archs = arm64-v8a, armeabi-v7a

#android.add_assets = /fonts

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

#
# Python for android (p4a) specific
#

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

#
# Buildozer specific settings
#
[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# Using an absolute path within the GitHub Actions workspace to avoid permission issues.
build_dir = /github/workspace/.buildozer_output

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# IMPORTANT: Commented out to avoid the "Output directory does not exist" error.
# The APK will be generated inside build_dir. Use an 'upload-artifact' step
# in your GitHub Actions workflow to retrieve it from there.
# bin_dir = /github/workspace/bin_output
