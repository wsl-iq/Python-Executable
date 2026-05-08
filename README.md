# Python Executable – PyToExe Converter

<div align="center">

![GitHub release (latest by date)](https://img.shields.io/github/v/release/wsl-iq/Python-Executable?color=blue&label=Latest)
![GitHub all releases](https://img.shields.io/github/downloads/wsl-iq/Python-Executable/total?color=green&label=Total%20Downloads)
![GitHub Repo stars](https://img.shields.io/github/stars/wsl-iq/Python-Executable)
![GitHub issues](https://img.shields.io/github/issues/wsl-iq/Python-Executable)
![License](https://img.shields.io/github/license/wsl-iq/Python-Executable)
![Platform](https://img.shields.io/badge/platform-Windows-blue)

</div>

---

## Table of Contents

1. [About](#about)
2. [Features (v3.2.0)](#features)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [User Interface & Workflow](#user-interface--workflow)
6. [Options Explained](#options-explained)
7. [Output Structure](#output-structure)
8. [System Monitor](#system-monitor)
9. [Multi‑language Support](#multi-language-support)
10. [Download](#download)
11. [Contributing & License](#contributing--license)

---

## About

PyToExe is a modern desktop application built with **PyQt5** that provides a graphical interface to convert Python scripts (`.py`) into standalone Windows executables (`.exe`).  
It uses **PyInstaller** as its backend engine while removing the need for command‑line interaction.  
The tool is designed for developers who want a fast, clean and reliable way to distribute their Python programs to end‑users without requiring a Python installation.

---

## Features

**Version `3.2.0`** introduces multiple new capabilities and improvements:

### Conversion Core
- **Single or batch conversion** – add multiple `.py` files and process them in one session.
- **One‑file / one‑folder output** – choose between a single executable or a folder containing the executable and all dependencies.
- **Console window toggle** – build a CLI application (console visible) or a GUI application (console hidden).
- **Custom icon** – attach a `.ico` file to give your executable a professional appearance.
- **Manifest file support** – include a `.manifest` for advanced Windows configuration (DPI awareness, execution level, etc.).
- **Version info embedding** – attach a version information file (`.txt` or direct input) so that the `.exe` shows details like company name, file version, copyright, etc.
- **UPX compression** – optionally compress the final executable using UPX to reduce file size significantly.

### Extended PyInstaller Control
- **Add data files and folders** – bundle external resources (images, config files, DLLs, etc.) with the application.
- **Add extra paths** – define additional search directories for imports.
- **Hidden imports** – manually specify modules that PyInstaller fails to detect automatically.
- **Generate `.spec` file** – save the current configuration as a reusable PyInstaller spec file for later fine‑tuning.

### User Interface & Productivity
- **Drag & Drop** – add files and folders directly from Windows Explorer.
- **Detailed file information panel** – see size, modification date, and path of selected scripts before building.
- **Progress animation** – a visual indicator shows that the build is ongoing, with live log output.
- **Advanced PyInstaller options text field** – directly pass any custom PyInstaller flags not covered by the GUI.
- **System monitor** – view real‑time CPU, RAM, and (if available) GPU usage during the build process.
- **Settings persistence** – all preferences are saved automatically in a `settings.json` file.
- **Light theme** – a clean, modern light interface alongside the default dark look.
- **Reset defaults** – revert all settings to the original state with one click.
- **Log export** – save the full conversion log to a text file for debugging or record‑keeping.
- **Sound notification** – be alerted with a sound when the build finishes.
- **Open output folder** – quickly jump to the directory containing the generated `.exe`.
- **Check for updates** – inside the tool, verify if a newer version is available online.

### Administration & Compatibility
- **Request administrator privileges** – a radio button to embed a manifest that asks for admin rights when the `.exe` is launched.
- **Python interpreter selection** – choose which Python installation to use if multiple versions are installed.
- **Windows 32/64‑bit support** – pre‑built executables available for both architectures.

---

## Installation

### Requirements
- **Python 3.9 or higher**
- **PyInstaller** – executable builder
- **PyQt5** – graphical toolkit

### Step 1 – Install Python
Download and install Python 3.9+ from the official website:  
[![Download Python](https://img.shields.io/badge/Download-Python-blue?logo=python&logoColor=white)](https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe)  
*Make sure to check “Add Python to PATH” during installation.*

### Step 2 – Get the Project
Clone the repository or download the source code from [GitHub](https://github.com/wsl-iq/Python-Executable).

### Step 3 – Install Dependencies
Open a terminal inside the project folder and run **one** of the following:

```bash
pip install pyinstaller pyqt5
pip install -r requirements.txt
setup.bat
```

---

### Quick Start
1. Navigate to the project folder.
2. Launch the application:

`python PyToExe.py`

3. **The main window appears.**
    - Add one or more `.py` files using the Add Files button or by dragging them from Explorer.
    - Configure options **(icon, console visibility, output mode, etc.)**.
    - **Click Convert and wait for the process to finish.**
4. The final executable(s) will be placed inside the automatically created `output` folder.

---

### **User Interface & Workflow**
- The interface is organised into logical sections for clarity:
    - File List – displays all selected scripts, with an information panel showing size and date.
    - Options Panel – contains checkboxes, input fields, and file pickers for every build parameter.

    - Advanced Options – a free‑text field for custom PyInstaller flags.
    - System Monitor – live resource usage (CPU, RAM, GPU) visible at the bottom or side.
    - Log Area – real‑time output of PyInstaller’s build process.
    - Action Buttons – Convert, Reset, Export Log, Open Output, Check for Updates.
**Every setting you change is automatically saved to `settings.json` and restored on the next launch.**

---

### System Monitor
- While a conversion is running, a dedicated panel displays:

- CPU usage (overall system percentage)
- RAM usage (used vs total)
- GPU load (if a ✅ NVIDIA/AMD card and drivers are present)
**This helps you understand the resource impact during heavy builds and ensures your system is not overloaded.**

---

### Contributing & License
- We welcome contributions of any kind – code, translations, documentation, bug reports.
- Please read our contribution guidelines and code of conduct before opening a pull request.

**Code of Conduct**
**Contributing Guide**
**MIT License**

---

| Language              | Status   |
|-----------------------|----------|
| العربية              | ✅       |
| English              | ✅       |
| Français             | ✅       |
| Deutsch              | ✅       |
| Español              | ✅       |
| Italiano             | ✅       |
| Русский              | ✅       |
| 中文                 | ✅       |
| 日本語               | ✅         |
| 한국어               | ✅         |
| हिंदी                  | ✅         |
| کوردی               | ✅         |
| فارسی               | ✅         |
| Español              | ✅         |
| اردو                 | ✅         |
| Português            | ✅         |
| Türkçe               | ✅         |
| עברית               | ✅         |
| Português            | ✅         |
| Nederlands           | ✅         |

