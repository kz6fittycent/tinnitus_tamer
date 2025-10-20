# Tinnitus Tamer

Tinnitus Tamer is a Python application designed to provide relief for tinnitus sufferers by generating and mixing calming sounds, including white, pink, brown, wind, ocean, and waterfall noises. It features a customizable notch filter to target specific tinnitus frequencies, a modern One Dark Two theme, and system tray integration for background playback. The application was built with the aid of Grok, created by xAI.

## Features
- **Sound Mixing**: Blend white, pink, brown, wind, ocean, and waterfall sounds with adjustable volume sliders.
- **Notch Filter**: Apply a notch filter at a user-defined frequency (e.g., 4000 Hz) with adjustable Q factor to mask tinnitus.
- **Seamless Looping**: 60-second audio loops with 3-second crossfade for uninterrupted playback.
- **Persistent Settings**: Save and load volume, frequency, and Q settings across sessions using `QSettings`.
- **System Tray**: Minimize to system tray with options to restore or quit, including a notification on minimize.
- **Modern UI**: Styled with the One Dark Two theme (#282c34 background, #abb2bf text, #61afef accents) using PyQt6's `QPalette` and stylesheet.
- **Custom Icons**: 256x256 desktop icon and 32x32 tray icon (to be created with an ear and sound wave design).
- **About Dialog**: Accessible via Help > About, displaying version, MIT license, and Grok acknowledgment.
- **Snap Support**: Deployable as a Snap package with audio and desktop integration using `core24`.

## Installation

### Install the snap
```bash
sudo snap install tinnitustamer
```

### Prerequisites
- Python 3.10 or higher
- System dependencies (Ubuntu/Debian):
  ```bash
  sudo apt-get install python3-pip libasound2-dev libpulse-dev
  ```

### Install Dependencies
Clone the repository and install Python dependencies:
```bash
git clone https://github.com/<your-username>/tinnitus-tamer.git
cd tinnitus-tamer
pip install -r requirements.txt
```

## Usage
1. **Adjust Sounds**: Use sliders to mix white, pink, brown, wind, ocean, and waterfall sounds.
2. **Set Tinnitus Frequency**: Enter a frequency (Hz) in the input field (0 to disable the notch filter).
3. **Adjust Notch Q**: Use the Q slider to control the filter’s narrowness (higher = narrower).
4. **Play/Stop**: Click the Play/Stop button to control audio playback.
5. **Minimize to Tray**: Close the window to minimize to the system tray; double-click the tray icon to restore.
6. **About**: Access Help > About for version, license, and credits.


## License
MIT License

## Acknowledgments
- Built with the assistance of **Grok**, created by xAI.
- Inspired by the One Dark Two theme for Qt applications.
