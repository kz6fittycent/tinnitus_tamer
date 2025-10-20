#!/usr/bin/env python3

import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile
import pygame
import tempfile
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QSlider, QLabel, QPushButton, QLineEdit, QHBoxLayout,
                            QMenu, QStyle, QSystemTrayIcon, QMenuBar, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPalette, QColor
from PyQt6.QtCore import QSettings

class TinnitusTamer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tinnitus Tamer")
        self.setGeometry(100, 100, 400, 500)  # Reduced height to minimize bottom padding
        
        # Settings for persistence
        self.settings = QSettings("xAI", "TinnitusTamer")
        
        # Initialize pygame mixer with explicit parameters
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=4096)
            pygame.mixer.init()
            print("Pygame mixer initialized successfully")
        except Exception as e:
            print(f"Failed to initialize pygame mixer: {e}")
        
        # Variables (load from settings)
        self.white_vol = self.settings.value("white_vol", 0.5, float)
        self.pink_vol = self.settings.value("pink_vol", 0.0, float)
        self.brown_vol = self.settings.value("brown_vol", 0.0, float)
        self.wind_vol = self.settings.value("wind_vol", 0.0, float)
        self.ocean_vol = self.settings.value("ocean_vol", 0.0, float)
        self.waterfall_vol = self.settings.value("waterfall_vol", 0.0, float)
        self.master_vol = self.settings.value("master_vol", 0.5, float)
        self.tinnitus_freq = self.settings.value("tinnitus_freq", 4000.0, float)
        self.notch_q = self.settings.value("notch_q", 30.0, float)
        self.playing = False
        self.sound = None
        self.tmpfile = None
        
        # GUI setup
        self.init_ui()
        
        # Tray icon setup
        base_path = os.path.dirname(os.path.abspath(__file__))
        tray_icon_path = os.path.join(base_path, "icons", "tt_systray.png")
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(tray_icon_path):
            self.tray_icon.setIcon(QIcon(tray_icon_path))
        else:
            print(f"Tray icon not found at {tray_icon_path}, using default")
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setVisible(True)
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # Tray menu
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        self.tray_icon.setContextMenu(tray_menu)

    def init_ui(self):
        # Menu bar
        menubar = self.menuBar()
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)  # Equal padding on all sides
        
        # Apply One Dark Two theme via QPalette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(40, 44, 52))  # #282c34
        palette.setColor(QPalette.WindowText, QColor(171, 178, 191))  # #abb2bf
        palette.setColor(QPalette.Base, QColor(33, 37, 43))  # #21252b
        palette.setColor(QPalette.AlternateBase, QColor(40, 44, 52))  # #282c34
        palette.setColor(QPalette.Text, QColor(171, 178, 191))  # #abb2bf
        palette.setColor(QPalette.Button, QColor(40, 44, 52))  # #282c34
        palette.setColor(QPalette.ButtonText, QColor(171, 178, 191))  # #abb2bf
        palette.setColor(QPalette.Highlight, QColor(97, 175, 239))  # #61afef
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))  # #ffffff
        palette.setColor(QPalette.Light, QColor(59, 66, 82))  # #3b4252
        palette.setColor(QPalette.Mid, QColor(44, 49, 60))  # #2c313c
        palette.setColor(QPalette.Dark, QColor(33, 37, 43))  # #21252b
        palette.setColor(QPalette.Shadow, QColor(30, 34, 40))  # #1e2228
        self.setPalette(palette)
        
        # Custom stylesheet for One Dark Two
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #282c34;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #3b4252;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #61afef;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #61afef;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid #528bff;
            }
            QPushButton {
                background-color: #61afef;
                color: #ffffff;
                padding: 8px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #528bff;
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid #3b4252;
                border-radius: 4px;
                background-color: #21252b;
                color: #abb2bf;
            }
            QLineEdit:focus {
                border: 1px solid #61afef;
            }
            QLabel {
                color: #abb2bf;
            }
            QMenuBar {
                background-color: #282c34;
                color: #abb2bf;
            }
            QMenuBar::item {
                background-color: #282c34;
                color: #abb2bf;
            }
            QMenuBar::item:selected {
                background-color: #61afef;
                color: #ffffff;
            }
            QMenu {
                background-color: #282c34;
                color: #abb2bf;
                border: 1px solid #3b4252;
            }
            QMenu::item:selected {
                background-color: #61afef;
                color: #ffffff;
            }
        """)
        
        # Sliders and labels
        self.add_slider(layout, "White Noise Volume", 0, 100, int(self.white_vol * 100), self.update_white_vol)
        self.add_slider(layout, "Pink Noise Volume", 0, 100, int(self.pink_vol * 100), self.update_pink_vol)
        self.add_slider(layout, "Brown Noise Volume", 0, 100, int(self.brown_vol * 100), self.update_brown_vol)
        self.add_slider(layout, "Wind Volume", 0, 100, int(self.wind_vol * 100), self.update_wind_vol)
        self.add_slider(layout, "Ocean Waves Volume", 0, 100, int(self.ocean_vol * 100), self.update_ocean_vol)
        self.add_slider(layout, "Waterfall Volume", 0, 100, int(self.waterfall_vol * 100), self.update_waterfall_vol)
        self.add_slider(layout, "Master Volume", 0, 100, int(self.master_vol * 100), self.update_master_vol)
        
        # Tinnitus frequency input
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Tinnitus Frequency (Hz, 0 to disable):")
        self.freq_input = QLineEdit(str(self.tinnitus_freq))
        self.freq_input.textChanged.connect(self.update_freq)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_input)
        layout.addLayout(freq_layout)
        
        # Notch Q slider
        self.add_slider(layout, "Notch Q (higher = narrower)", 1, 100, int(self.notch_q), self.update_notch_q)
        
        # Play/Stop button
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)
        layout.addWidget(self.play_button)

    def show_about_dialog(self):
        about_text = """
        <h2>Tinnitus Tamer</h2>
        <p>Version: 1.0</p>
        <p>A Qt application for tinnitus relief with customizable sound mixing (white, pink, brown, wind, ocean, waterfall).</p>
        <p>This application was built with the aid of Grok, created by xAI.</p>
        <p><b>License: MIT License</b></p>
        <p>Copyright (c) 2025 James Tigert - kz6fittycent</p>
        <p>Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:</p>
        <p>The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.</p>
        <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.</p>
        """
        QMessageBox.about(self, "About Tinnitus Tamer", about_text)

    def add_slider(self, layout, label, min_val, max_val, default, callback):
        slider_layout = QHBoxLayout()
        slider_label = QLabel(label)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)
        slider.valueChanged.connect(callback)
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(slider)
        layout.addLayout(slider_layout)

    def update_white_vol(self, value):
        self.white_vol = value / 100.0
        self.settings.setValue("white_vol", self.white_vol)
        self.update_sound()

    def update_pink_vol(self, value):
        self.pink_vol = value / 100.0
        self.settings.setValue("pink_vol", self.pink_vol)
        self.update_sound()

    def update_brown_vol(self, value):
        self.brown_vol = value / 100.0
        self.settings.setValue("brown_vol", self.brown_vol)
        self.update_sound()

    def update_wind_vol(self, value):
        self.wind_vol = value / 100.0
        self.settings.setValue("wind_vol", self.wind_vol)
        self.update_sound()

    def update_ocean_vol(self, value):
        self.ocean_vol = value / 100.0
        self.settings.setValue("ocean_vol", self.ocean_vol)
        self.update_sound()

    def update_waterfall_vol(self, value):
        self.waterfall_vol = value / 100.0
        self.settings.setValue("waterfall_vol", self.waterfall_vol)
        self.update_sound()

    def update_master_vol(self, value):
        self.master_vol = value / 100.0
        self.settings.setValue("master_vol", self.master_vol)
        if self.sound:
            self.sound.set_volume(self.master_vol)
            print(f"Master volume set to {self.master_vol}")

    def update_freq(self, text):
        try:
            self.tinnitus_freq = float(text) if text else 0.0
            self.settings.setValue("tinnitus_freq", self.tinnitus_freq)
            self.update_sound()
        except ValueError:
            self.tinnitus_freq = 0.0
            print("Invalid frequency input, defaulting to 0")

    def update_notch_q(self, value):
        self.notch_q = float(value)
        self.settings.setValue("notch_q", self.notch_q)
        self.update_sound()

    def generate_noise(self):
        fs = 44100
        duration = 60  # Longer duration for less frequent looping
        overlap = 3  # Overlap in seconds for crossfade
        N_raw = int((duration + overlap) * fs)

        # Generate base noises
        def generate_white(N):
            return np.random.randn(N)

        def generate_colored(beta, N, fs):
            white = generate_white(N)
            fft_white = np.fft.rfft(white)
            freqs = np.fft.rfftfreq(N, 1/fs)
            freqs[freqs == 0] = 1e-10  # Avoid division by zero
            magnitude = 1 / (freqs ** (beta / 2))
            colored_fft = fft_white * magnitude
            colored = np.fft.irfft(colored_fft)
            colored -= np.mean(colored)  # Remove DC offset
            std = np.std(colored)
            if std > 1e-10:
                colored /= std  # Normalize to unit variance
            return colored

        # Additional sound generators
        def generate_wind(N, fs):
            brown = generate_colored(2, N, fs)
            b, a = signal.butter(2, 500 / (fs / 2), 'low')
            wind = signal.filtfilt(b, a, brown)
            wind -= np.mean(wind)
            std = np.std(wind)
            if std > 1e-10:
                wind /= std
            return wind

        def generate_ocean(N, fs):
            pink = generate_colored(1, N, fs)
            t = np.arange(N) / fs
            modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t)  # slow swell
            ocean = pink * modulation
            ocean -= np.mean(ocean)
            std = np.std(ocean)
            if std > 1e-10:
                ocean /= std
            return ocean

        def generate_waterfall(N, fs):
            pink = generate_colored(1, N, fs)
            white = generate_colored(0, N, fs)
            waterfall = 0.7 * pink + 0.3 * white
            b, a = signal.butter(2, 200 / (fs / 2), 'high')
            waterfall = signal.filtfilt(b, a, waterfall)
            waterfall -= np.mean(waterfall)
            std = np.std(waterfall)
            if std > 1e-10:
                waterfall /= std
            return waterfall

        white = generate_colored(0, N_raw, fs) * self.white_vol
        pink = generate_colored(1, N_raw, fs) * self.pink_vol
        brown = generate_colored(2, N_raw, fs) * self.brown_vol
        wind = generate_wind(N_raw, fs) * self.wind_vol
        ocean = generate_ocean(N_raw, fs) * self.ocean_vol
        waterfall = generate_waterfall(N_raw, fs) * self.waterfall_vol

        mix = white + pink + brown + wind + ocean + waterfall
        if np.abs(mix).max() > 0:
            mix /= np.abs(mix).max()

        # Apply notch filter if frequency is set
        if self.tinnitus_freq > 0:
            w0 = self.tinnitus_freq / (fs / 2.0)
            b, a = signal.iirnotch(w0, self.notch_q)
            mix = signal.filtfilt(b, a, mix)

        # Create seamless loop with crossfade
        L = int(duration * fs)
        O_samples = int(overlap * fs)
        loop_mix = mix[:L].copy()
        next_segment = mix[L : L + O_samples]
        fade_out = np.linspace(1, 0, O_samples)
        fade_in = np.linspace(0, 1, O_samples)
        loop_mix[-O_samples:] *= fade_out
        loop_mix[-O_samples:] += next_segment * fade_in

        # Convert to int16
        loop_mix = (loop_mix * 32767).astype(np.int16)
        return loop_mix, fs

    def toggle_play(self):
        if self.playing:
            self.stop_sound()
            self.play_button.setText("Play")
            self.playing = False
            print("Sound stopped")
        else:
            self.play_sound()
            self.play_button.setText("Stop")
            self.playing = True
            print("Sound started")

    def play_sound(self):
        self.stop_sound()  # Ensure clean state
        noise, fs = self.generate_noise()
        
        # Create temporary WAV file
        self.tmpfile = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        try:
            wavfile.write(self.tmpfile.name, fs, noise)
            print(f"WAV file created: {self.tmpfile.name}")
            
            # Load and play sound
            self.sound = pygame.mixer.Sound(self.tmpfile.name)
            self.sound.set_volume(self.master_vol)
            self.sound.play(loops=-1)
            print("Sound playing")
        except Exception as e:
            print(f"Error playing sound: {e}")
        finally:
            # Clean up the file after loading
            if os.path.exists(self.tmpfile.name):
                os.unlink(self.tmpfile.name)
                print(f"Temporary file deleted: {self.tmpfile.name}")
            self.tmpfile = None

    def update_sound(self):
        if self.playing:
            # Fade out current sound to avoid pop
            if self.sound:
                self.sound.fadeout(100)  # 100ms fadeout for smoother transition
            self.play_sound()
            print("Sound updated")

    def stop_sound(self):
        if self.sound:
            self.sound.fadeout(100)  # Smooth fadeout
            self.sound = None
        if self.tmpfile and os.path.exists(self.tmpfile.name):
            os.unlink(self.tmpfile.name)
            print(f"Temporary file deleted: {self.tmpfile.name}")
            self.tmpfile = None

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Tinnitus Tamer",
            "Minimized to system tray. Double-click to restore.",
            QSystemTrayIcon.Information,
            2000
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Ensure consistent base style
    base_path = os.path.dirname(os.path.abspath(__file__))
    desktop_icon_path = os.path.join(base_path, "icons", "tinnitus_tamer.png")
    if os.path.exists(desktop_icon_path):
        app.setWindowIcon(QIcon(desktop_icon_path))
    else:
        print(f"Desktop icon not found at {desktop_icon_path}")
    window = TinnitusTamer()
    window.show()
    sys.exit(app.exec_())
