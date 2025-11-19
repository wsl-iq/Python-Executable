#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025 
# Developer : Mohammed Al-Baqer

import os
from pyclbr import Class
import sys
import time
import json
import shlex
import traceback
import webbrowser
import shutil
import ctypes
import subprocess
import importlib
import importlib.util
import GPUtil
import psutil
import ctypes
import struct
import shlex
import winsound
import tempfile
from collections import deque
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from matplotlib.figure import Figure
from plyer import notification
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QCoreApplication, QProcess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QCheckBox, QPlainTextEdit, QMessageBox, QLabel,
    QHBoxLayout, QVBoxLayout, QGroupBox, QComboBox, QProgressBar, QMenu, QAction,
    QTabWidget, QSpinBox, QDoubleSpinBox, QTextEdit, QSplitter, QInputDialog
)


SETTINGS_FILE = "settings.json"
LOG_FILE = "log.txt"
BACKUP_DIR = "backups"
PLUGINS_DIR = "plugins"
PRESETS_DIR = "presets"
DEFAULT_SETTINGS = {
    "onefile": True,
    "noconsole": False,
    "clean": True,
    "last_output": os.path.abspath("output"),
    "last_icon": "",
    "last_manifest": "",
    "last_entries": [],
    "last_files": [],
    "last_folders": [],
    "python_interpreter": "",
    "advanced": {
        "hidden_imports": [],
        "exclude_modules": [],
        "uac_admin": False,
        "key": "",
        "optimize": False,
        "strip": False,
        "no_prefer_redirect": False,
        "obfuscate": False,
        "anti_debug": False,
        "packer": False
    },
    "version_info": {
        "version": "1.0.0",
        "company": "",
        "copyright": "",
        "description": "",
        "website": ""
    },
    "security": {
        "sign_certificate": "",
        "cert_password": "",
        "timestamp_server": "http://timestamp.digicert.com"
    },
    "build_system": "PyInstaller",
    "platform": "win32",
    "theme": "light",
    "language": "ar",
    "virtual_env": "",
    "template": "مخصص (Custom)",
    "resource_compression": "normal",
    "resource_encryption": False,
    "ide_integration": {
        "vscode": False,
        "pycharm": False
    }
}

PATHSEP = ";" if os.name == "nt" else ":"

class LanguageManager:
    def __init__(self, settings_path="settings.json", languages_dir="languages"):
        self.languages_dir = languages_dir
        self.settings_path = settings_path
        self.current_language = "ar"
        self.translations = {}
        os.makedirs(self.languages_dir, exist_ok=True)
        self.SaveLoadLanguages()
    
    def SaveLoadLanguages(self):
        try:
            if not os.path.exists(self.settings_path):
                print("[Language] settings.json Not Found so using default language (ar)")
                return self.LoadLanguages("ar")

            with open(self.settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

            lang_code = settings.get("language", "ar")
            
            if isinstance(lang_code, list):
                lang_code = lang_code[0] if lang_code else "ar"
                
            if not isinstance(lang_code, str):
                lang_code = "ar"

            return self.LoadLanguages(lang_code)
            
        except Exception as e:
            print(f"[Language] Error loading language from settings: {e}")
            return self.LoadLanguages("ar")

    def LoadLanguages(self, lang_code: str):
        lang_file = os.path.join(self.languages_dir, f"{lang_code}.json")
        try:
            if not os.path.exists(lang_file):
                print(f"[Language] Language file {lang_code}.json not found, using default language (ar)")
                lang_file = os.path.join(self.languages_dir, "ar.json")

            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)

            self.current_language = lang_code
            
            S = "\033[0m"        # Reset
            R = "\033[91;1m"     # Red
            G = "\033[92;1m"     # Green
            B = "\033[94;1m"     # Blue
            Y = "\033[93;1m"     # Yellow
            C = "\033[96;1m"     # Cyan
            M = "\033[95;1m"     # Magenta
            W = "\033[97;1m"     # White
            D = "\033[90;1m"     # Grey
            P = "\033[38;5;198m" # Pink
            O = "\033[38;5;202m" # Orange
            
            print(f"[Language] Language loaded -> {lang_code}\n")
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{C}From Python To Executable\n{Y}Developer {W}: {O}Mohammed Al-Baqer\n{B}Instagram {W}: {P}@wsl.iq{W}")

            if not self.translations.get("ui"):
                self.translations["ui"] = {
                    "title": "عنوان",
                    "message": "رسالة",
                    "button": "زر",
                    "entry": "مدخل",
                    "checkbox": "خانة اختيار",
                    "combobox": "قائمة منسدلة",
                    "radiobutton": "زر اختيار",
                    "error": "خطأ",
                    "success": "نجاح",
                    "info": "معلومات"
                }
            return True
        except Exception as e:
            print(f"[Language] Error loading language {lang_code}: {e}")
            return False

    def get(self, key: str, default: str = None) -> str:
        return self.translations.get(key, default or key)

    def tr(self, key: str, *args) -> str:
        keys = key.split('.')
        value = self.translations
        try:
            for k in keys:
                value = value[k]
            text = value
        except (KeyError, TypeError):
            text = key
        
        if args:
            try:
                text = text.format(*args)
            except Exception:
                pass
        return text

    def AvailableLanguges(self) -> List[str]:
        languages = []
        for file in os.listdir(self.languages_dir):
            if file.endswith(".json"):
                languages.append(file[:-5])
        return sorted(languages)

class PluginManager:
    def __init__(self, plugins_dir="plugins"):
        self.plugins_dir = plugins_dir
        self.plugins = {}
        os.makedirs(plugins_dir, exist_ok=True)
    
    def LoadPlugins(self):
        for file in os.listdir(self.plugins_dir):
            if file.endswith(".py") and not file.startswith("_"):
                try:
                    plugin_name = file[:-3]
                    spec = importlib.util.spec_from_file_location(plugin_name, os.path.join(self.plugins_dir, file))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.plugins[plugin_name] = module
                    print(f"[Plugin] Loaded: {plugin_name}")
                except Exception as e:
                    print(f"[Plugin] Failed to load plugin {file}: {e}")

    def ExecuteHook(self, hook_name, *args, **kwargs):
        results = {}
        for name, plugin in self.plugins.items():
            if hasattr(plugin, hook_name):
                try:
                    result = getattr(plugin, hook_name)(*args, **kwargs)
                    results[name] = result
                except Exception as e:
                    print(f"[Plugin] Failed to execute hook {hook_name} in {name}: {e}")
        return results

def quote(p: str) -> str:
    if not p:
        return p
    if os.name != "nt":
        return shlex.quote(p)
    if " " in p or "(" in p or ")" in p:
        return f'"{p}"'
    return p

def Administrator() -> bool:
    try:
        if os.name == "nt":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False

def FindPythonInterpreters() -> List[str]:
    candidates = []
    for name in ("python", "python3", "py"):
        path = shutil.which(name)
        if path and path not in candidates:
            candidates.append(path)
    
    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        pf_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        for base in (program_files, pf_x86):
            for root, dirs, files in os.walk(base):
                for f in files:
                    if f.lower().startswith("python") and f.lower().endswith(".exe"):
                        p = os.path.join(root, f)
                        if p not in candidates:
                            candidates.append(p)
                break
    
    virtual_envs = FindVirtualEnvironments()
    candidates.extend(virtual_envs)
    
    return candidates

def FindVirtualEnvironments() -> List[str]:
    envs = []
    common_locations = [
        os.path.expanduser("~"),
        os.path.expanduser("~/.virtualenvs"),
        os.path.expanduser("~/Envs"),
        os.path.curdir
    ]
    
    for location in common_locations:
        if os.path.exists(location):
            for item in os.listdir(location):
                env_path = os.path.join(location, item)
                if os.path.isdir(env_path):
                    python_exe = None
                    if os.name == "nt":
                        python_exe = os.path.join(env_path, "Scripts", "python.exe")
                    else:
                        python_exe = os.path.join(env_path, "bin", "python")
                    
                    if python_exe and os.path.isfile(python_exe):
                        envs.append(python_exe)
    return envs

@dataclass
class BuildItem:
    entry_script: str

class BuildWorker(QObject):
    line = pyqtSignal(str)
    done = pyqtSignal(bool)
    progress = pyqtSignal(int)
    cpu_mem = pyqtSignal(float, float)

    def __init__(self, commands: List[List[str]], cwd: str, python_exec: Optional[str] = None, run_after=False):
        super().__init__()
        self.commands = commands
        self.cwd = cwd
        self._stopped = False
        self.python_exec = python_exec
        self.run_after = run_after

    def stop(self):
        self._stopped = True

    def EmitSysUsage(self):
        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent
                self.cpu_mem.emit(cpu, mem)
            except Exception:
                pass

    def run(self):
        ok = True
        for cmd in self.commands:
            if self._stopped:
                ok = False
                break
            display_cmd = " ".join(map(str, cmd))
            self.line.emit(f"\n=== تشغيل: {display_cmd}\n")
            try:
                with subprocess.Popen(
                    cmd,
                    cwd=self.cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                ) as p:
                    for out_line in p.stdout:
                        if self._stopped:
                            p.kill()
                            ok = False
                            break
                        text = out_line.rstrip("\n")
                        self.line.emit(text)
                        self.EmitSysUsage()
                rc = p.wait()
                if rc != 0:
                    ok = False
                    self.line.emit(f"[ERROR] The Process Ended with a code ! -> {rc}")
                    break
            except FileNotFoundError:
                ok = False
                self.line.emit("[ERROR] The command was not found")
                break
            except Exception as e:
                ok = False
                self.line.emit(f"[ERROR] {e}")
                break
        
        if ok and self.run_after and self.commands:
            try:
                output_dir = self.commands[0][self.commands[0].index("--distpath") + 1] if "--distpath" in self.commands[0] else "dist"
                entry_script = self.commands[0][-1]
                exe_name = os.path.splitext(os.path.basename(entry_script))[0] + (".exe" if os.name == "nt" else "")
                exe_path = os.path.join(output_dir, exe_name)
                
                if os.path.exists(exe_path):
                    self.line.emit(f"[INFO] Turning {exe_path}")
                    if os.name == "nt":
                        os.startfile(exe_path)
                    else:
                        subprocess.Popen([exe_path])
                else:
                    self.line.emit("[WARN] Not Found file run!")
            except Exception as e:
                self.line.emit(f"[ERROR] Failed to run the output file: {e}")
        
        self.done.emit(ok)

class PyInstallerExtras:
    def __init__(self, presets_dir="presets"):
        self.presets_dir = presets_dir
        os.makedirs(presets_dir, exist_ok=True)

    def AnalyzeMissingImports(self, script_path: str) -> List[str]:
        if not os.path.isfile(script_path):
            return []

        missing = set()
        cmd = ["pyinstaller", "--debug=imports", "--noconfirm", "--onefile", script_path]
        try:
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            ) as proc:
                for line in proc.stdout:
                    if "ModuleNotFoundError" in line:
                        mod_name = line.split("'")[-2]
                        missing.add(mod_name)
                    elif "WARNING" in line and "hidden import" in line.lower():
                        parts = line.split("'")
                        if len(parts) >= 2:
                            missing.add(parts[1])
        except Exception as e:
            print(f"[Analyzer] Failed to analyze: {e}")
        finally:
            for d in ("build", "__pycache__"):
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
            spec_file = os.path.splitext(os.path.basename(script_path))[0] + ".spec"
            if os.path.isfile(spec_file):
                os.remove(spec_file)

        return list(missing)

    def AdvancedDependencyAnalysis(self, script_path: str) -> Dict[str, Any]:
        analysis_result = {
            "missing_imports": [],
            "large_files": [],
            "suspicious_imports": [],
            "performance_issues": [],
            "recommendations": []
        }
        
        missing = self.AnalyzeMissingImports(script_path)
        analysis_result["missing_imports"] = missing
        
        script_dir = os.path.dirname(script_path)
        for root, dirs, files in os.walk(script_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) > 10 * 1024 * 1024:
                    analysis_result["large_files"].append(file_path)
        
        suspicious_keywords = ["os.system", "subprocess", "eval", "exec", "pickle", "marshal"]
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for keyword in suspicious_keywords:
                if keyword in content:
                    analysis_result["suspicious_imports"].append(keyword)
        
        performance_issues = ["time.sleep", "while True", "recursive"]
        for issue in performance_issues:
            if issue in content:
                analysis_result["performance_issues"].append(issue)
        
        if "tkinter" in content:
            analysis_result["recommendations"].append("نوصي باستخدام --noconsole لتطبيقات GUI")
        if "requests" in content or "urllib" in content:
            analysis_result["recommendations"].append("تأكد من إضافة شهادات SSL إذا كان التطبيق يتصل بالإنترنت")
        
        return analysis_result

    def BuildWithUPX(self, cmd: List[str], upx_dir: str) -> List[str]:
        if upx_dir and os.path.isdir(upx_dir):
            cmd.extend(["--upx-dir", upx_dir])
        return cmd

    def SavePreset(self, name: str, data: Dict) -> str:
        path = os.path.join(self.presets_dir, f"{name}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Preset] Failed to save preset: {e}")
        return path

    def LoadPreset(self, name: str) -> Dict:
        path = os.path.join(self.presets_dir, f"{name}.json")
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"[Preset] Failed to load preset: {e}")
            return {}

    def ListPresets(self) -> List[str]:
        files = [f[:-5] for f in os.listdir(self.presets_dir) if f.endswith(".json")]
        return files

    def DeletePreset(self, name: str):
        path = os.path.join(self.presets_dir, f"{name}.json")
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[Preset] Failed to delete preset: {e}")

    def CopyToClipboard(self, text: str):
        try:
            CF_UNICODETEXT = 13
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            hCd = ctypes.windll.kernel32.GlobalAlloc(0x2000, (len(text) + 1) * 2)
            lpCd = ctypes.windll.kernel32.GlobalLock(hCd)
            ctypes.cdll.msvcrt.wcscpy(lpCd, text)
            ctypes.windll.kernel32.GlobalUnlock(hCd)
            ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, hCd)
            ctypes.windll.user32.CloseClipboard()
        except Exception as e:
            print(f"[Clipboard] Failed to copy: {e}")

def GetScriptPaths(ui) -> list:
    if ui.modeCombo.currentIndex() == 0:
        path = ui.entryLine.text().strip()
        return [path] if path else []
    else:
        return [ui.entryList.item(i).text() for i in range(ui.entryList.count())]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = {}
        self.LoadSettings()

        self.lang_manager = LanguageManager()
        self.lang_manager.LoadLanguages("ar")
        self.setWindowTitle(self.lang_manager.tr("app_title", "From Python To Executable v3.1.0"))
        self.resize(1200, 800)
        self.icon_path = r"icon\icon.png" if os.path.isfile(r"icon\icon.png") else None
        self.shield_icon = r"icon\run.ico" if os.path.isfile(r"icon\run.ico") else self.icon_path
        if self.icon_path:
            self.setWindowIcon(QIcon(self.icon_path))
            
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.info_label.setStyleSheet("background-color: rgba(255, 255, 255, 0.8); border: 1px solid #ccc; padding: 5px;")
        self.info_label.setMinimumHeight(100)

        self.interval_ms = 1000
        self.settings = {}
        self.thread = None
        self.worker = None
        self._indeterminate = False

        self.LoadSettings()
        self.CreateBackup()
        
        self.lang_manager = LanguageManager()
        self.LoadLanguagesFromSettings()
        
        self.__CreateMenus__()
        self.CreateMenusGUI()
        self.setAcceptDrops(True)
        self.__ApplySettingsGUI__()
        
        self.ui_timer = QTimer()
        self.ui_timer.setInterval(1000)
        self.ui_timer.timeout.connect(self.__UpdateSysLabelUsing__)
        self.ui_timer.start()
        
        self.apply_theme()
        
        try:
            self.plugin_manager = PluginManager(PLUGINS_DIR)
            self.plugin_manager.LoadPlugins()
        except Exception as e:
            print(f"[Plugin] Failed to load plugins: {e}")
            
    def RestartApplication(self):
        exe_path = os.path.abspath(sys.argv[0])
        bat_path = os.path.join(tempfile.gettempdir(), "restart_pytoexe.bat")
        with open(bat_path, "w", encoding="utf-8") as bat:
            bat.write(f"""@echo off
    timeout /t 1 >nul
    start "" "{exe_path}"
    exit
    """)

        os.startfile(bat_path)
        QCoreApplication.quit()


        
    def ChangeLanguage(self, lang_code: str):
        if self.lang_manager.LoadLanguages(lang_code):
            self.settings["language"] = lang_code
            self.SaveSettings()
            self.RefreshGUI()

            msg = {
                "ar": "تم تغيير اللغة إلى (العربية)",
                "en": "Language changed to (English)",
                "fr": "La langue a été changée en (Français)",
                "ru": "Язык изменён на (Русский)",
                "zh": "语言已更改为 (中文)"
            }.get(lang_code, "Language changed.")

            restart_q = {
                "ar": "هل تريد إعادة تشغيل البرنامج الآن لتطبيق التغييرات؟",
                "en": "Do you want to restart now to apply changes?",
                "fr": "Voulez-vous redémarrer maintenant pour appliquer les modifications ?",
                "ru": "Хотите перезапустить сейчас?",
                "zh": "是否现在重新启动？"
            }.get(lang_code, "Restart now?")

            QMessageBox.information(self,
                                    self.lang_manager.tr("language", "اللغة"),
                                    msg)

            reply = QMessageBox.question(self,
                                        self.lang_manager.tr("language", "اللغة"),
                                        restart_q,
                                        QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.RestartApplication()

            
    def LoadLanguagesFromSettings(self):
        try:
            if not hasattr(self, 'settings') or not self.settings:
                self.LoadSettings()
                
            lang = self.settings.get("language", "ar")
            
            if isinstance(lang, list):
                lang = lang[0] if lang else "ar"
                
            if not isinstance(lang, str):
                lang = "ar"
                
            if not self.lang_manager.LoadLanguages(lang):
                print(f"[Language] Failed to load {lang}, using Arabic")
                self.lang_manager.LoadLanguages("ar")
                
        except Exception as e:
            print(f"[Language] Failed to load language from settings: {e}")
            self.lang_manager.LoadLanguages("ar")
            
    def RefreshGUI(self):
        self.ApplyLanguage()
        self.apply_theme()

    def ApplyLanguage(self):
        tr = self.lang_manager.tr        
        self.setWindowTitle(self.lang_manager.tr("app_title", "from Python To Executable v3.1.0"))
        self.UpdateMenusText()
        self.UpdateTextGUI()
    
    def UpdateMenusText(self):
        tr = self.lang_manager.tr
        self.menuBar().actions()[0].setText(tr("file_menu", "قائمة الملف"))
    
    def UpdateTextGUI(self):
        tr = self.lang_manager.tr
       
        if not hasattr(self, "tab_basic"):
            return
        self.tab_basic.setText(tr("tab_basic", "أساسي"))
        self.tab_advanced.setText(tr("tab_advanced", "متقدم"))
        self.tab_version.setText(tr("tab_version", "معلومات الإصدار"))
        self.tab_security.setText(tr("tab_security", "الأمان"))
        
        self.entryLabel.setText(tr("options_os_system", "خيارات نظام التشغيل"))
        
        self.modeCombo.setItemText(0, tr("single_file"))
        self.modeCombo.setItemText(1, tr("batch_files"))
        self.entryBtn.setText(tr("choose_file"))
        self.addEntryBtn.setText(tr("add_script"))
        self.remEntryBtn.setText(tr("remove_selected"))
        self.oneFileChk.setText(tr("one_file"))
        self.consoleChk.setText(tr("show_console"))
        self.cleanChk.setText(tr("clean_before"))
        self.buildSystemCombo.setItemText(0, tr("PyInstaller", "PyInstaller تجميع شامل"))
        self.buildSystemCombo.setItemText(1, tr("cx_Freeze", "cx_Freeze تجميع تقليدي"))
        self.buildSystemCombo.setItemText(2, tr("Nuitka", "Nuitka C مترجم لغة"))
        self.buildSystemCombo.setItemText(3, tr("PyOxidizer", "PyOxidizer Rustمدمج بـ"))
        self.platformCombo.setItemText(0, tr("Windows 32-bit (win32)", "Windows 32-bit (win32)"))
        self.platformCombo.setItemText(1, tr("Windows 64-bit (win64)", "Windows 64-bit (win64)"))
        self.platformCombo.setItemText(2, tr("Linux", "Linux"))
        self.platformCombo.setItemText(3, tr("macOS", "macOS"))
        self.templateCombo.setItemText(0, tr("Application (GUI)", "تطبيق واجهة رسومية (GUI)"))
        self.templateCombo.setItemText(1, tr("Application (CLI)", "تطبيق وحدة التحكم (CLI)"))
        self.templateCombo.setItemText(2, tr("Application (Service)", "تطبيق خدمة (Service)"))
        self.templateCombo.setItemText(3, tr("Application (Web)", "تطبيق ويب (Web)"))
        self.templateCombo.setItemText(4, tr("Custom (Custom)", "مخصص (Custom)"))
        self.optimizeChk.setText(tr("enable_optimizations"))
        self.stripChk.setText(tr("strip_info"))
        self.noPreferRedirectChk.setText(tr("disable_redirect"))
        self.obfuscateChk.setText(tr("obfuscation"))
        self.antiDebugChk.setText(tr("anti_debug"))
        self.packerChk.setText(tr("packer"))
        self.certFileBtn.setText(tr("choose_certificate"))
        self.certPassEdit.setPlaceholderText(tr("cert_password"))
        self.timestampCombo.setItemText(0, tr("http://timestamp.digicert.com", "http://timestamp.digicert.com"))
        self.timestampCombo.setItemText(1, tr("http://timestamp.comodoca.com", "http://timestamp.comodoca.com"))
        self.timestampCombo.setItemText(2, tr("http://timestamp.globalsign.com", "http://timestamp.globalsign.com"))
        self.addFileBtn.setText(tr("add_file"))
        self.remFileBtn.setText(tr("remove_file"))
        self.addFolderBtn.setText(tr("add_folder"))
        self.remFolderBtn.setText(tr("remove_folder"))
        self.compressionCombo.setItemText(0, tr("compression_levels.0", "بدون ضغط"))
        self.compressionCombo.setItemText(1, tr("compression_levels.1", "ضغط عادي"))
        self.compressionCombo.setItemText(2, tr("compression_levels.2", "ضغط عالي"))
        self.encryptionChk.setText(tr("encrypt_resources"))
        self.outBtn.setText(tr("choose_output"))
        self.iconBtn.setText(tr("choose_icon"))
        self.manifestBtn.setText(tr("choose_manifest"))
        self.buildBtn.setText(tr("start_build_button"))
        self.cancelBtn.setText(tr("cancel"))
        self.runAfterChk.setText(tr("run_after"))
        self.sysUsageLabel.setText(tr("sys_usage", "CPU: -%  RAM: -%"))
        self.cmdPreview.setPlaceholderText(tr("command_placeholder"))
        self.log.setPlaceholderText(tr("log_placeholder"))
        self.reportText.setPlaceholderText(tr("report_placeholder"))
        self.saveLogBtn.setText(tr("save_log"))
        self.openDistBtn.setText(tr("open_output"))
        self.openBuildBtn.setText(tr("open_build"))
        self.testOutputBtn.setText(tr("test_output"))
        self.setWindowTitle(tr("app_title"))
        try:
            QApplication.processEvents()
            self.repaint()
            mb = self.menuBar()
            if mb:
                mb.update()
        except Exception:
            pass

        try:
            menubar = self.menuBar()
            for action in menubar.actions():
                text = action.text().lower()
            if "language" in text or "اللغة" in text:
                action.setText(tr("language_menu", "اللغة"))
            if "file" in text or "الملف" in text:
                action.setText(tr("file_menu", "الملف"))
            if "build" in text or "البناء" in text:
                action.setText(tr("build_menu", "البناء"))
            if "tools" in text or "أدوات" in text:
                action.setText(tr("tools_menu", "أدوات"))
            if "view" in text or "المظهر" in text:
                action.setText(tr("view_menu", "المظهر"))
            if "settings" in text or "الإعدادات" in text:
                action.setText(tr("settings_menu", "الإعدادات"))
            if "help" in text or "مساعدة" in text:
                action.setText(tr("help_menu", "مساعدة"))
            if "about" in text or "حول" in text:
                action.setText(tr("about_menu", "حول"))
            if "exit" in text or "خروج" in text:
                action.setText(tr("exit_menu", "خروج"))
                action.triggered.connect(self.close)
        except Exception:
            pass
        
        try:
            addtab = addtab = self.tabWidget.widget(0)
            addtab.setTitle(tr("tab_basic", "أساسي", "Basic", "Basique", "Базовый", "基础"))
        except Exception:
            pass
        
        try:
            addtab = self.tabWidget.widget(1)
            addtab.setTitle(tr("tab_advanced", "متقدم", "Advanced", "Avancé", "Продвинутый", "高级"))
        except Exception:
            pass
        
        try:
            addtab = self.tabWidget.widget(2)
            addtab.setTitle(tr("tab_version", "معلومات الإصدار", "Version Info", "Infos de version", "Информация о версии", "版本信息"))
        except Exception:
            pass
        
        try:
            addtab = self.tabWidget.widget(3)
            addtab.setTitle(tr("tab_security", "الأمان", "Security", "Sécurité", "Безопасность", "安全"))
        except Exception:
            pass
        
        try:
            addtab = self.tabWidget.widget(4)
            addtab.setTitle(tr("tab_resources", "الموارد", "Resources", "Ressources", "Ресурсы", "资源"))
        except Exception:
            pass
        
        try:
            addtab = self.tabWidget.widget(5)
            addtab.setTitle(tr("tab_log", "السجل", "Log", "Journal", "Журнал", "日志"))
        except Exception:
            pass
        
        try: # entryLabel خيارات نظام التشغيل
            addtab = self.entryLabel
            addtab.setText(tr("options_os_system", "خيارات نظام التشغيل", "OS System Options", "Options du système d'exploitation", "Параметры ОС", "操作系统选项"))
        except Exception:
            pass

    def LoadSettings(self):
        if os.path.isfile(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"[Settings] Failed to load settings: {e}")
                self.settings = DEFAULT_SETTINGS.copy()
        else:
            self.settings = DEFAULT_SETTINGS.copy()

    def CreateBackup(self):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"settings_backup_{timestamp}.json")
        try:
            shutil.copy2(SETTINGS_FILE, backup_file)
        except Exception:
            pass

    def SaveSettings(self):
        self.settings["onefile"] = self.oneFileChk.isChecked()
        self.settings["noconsole"] = not self.consoleChk.isChecked()
        self.settings["clean"] = self.cleanChk.isChecked()
        self.settings["last_output"] = self.outLine.text().strip()
        self.settings["last_icon"] = self.iconLine.text().strip()
        self.settings["last_manifest"] = self.manifestLine.text().strip()
        self.settings["last_entries"] = [self.entryList.item(i).text() for i in range(self.entryList.count())]
        self.settings["last_files"] = [self.filesList.item(i).text() for i in range(self.filesList.count())]
        self.settings["last_folders"] = [self.foldersList.item(i).text() for i in range(self.foldersList.count())]
        self.settings["python_interpreter"] = self.interpCombo.currentText()
        self.settings["language"] = self.lang_manager.current_language
        
        self.settings["advanced"] = {
            "hidden_imports": [s.strip() for s in self.hiddenImportsLine.text().split(",") if s.strip()],
            "exclude_modules": [s.strip() for s in self.excludeModulesLine.text().split(",") if s.strip()],
            "uac_admin": self.uacChk.isChecked(),
            "key": self.keyLine.text().strip(),
            "optimize": self.optimizeChk.isChecked(),
            "strip": self.stripChk.isChecked(),
            "no_prefer_redirect": self.noPreferRedirectChk.isChecked(),
            "obfuscate": self.obfuscateChk.isChecked(),
            "anti_debug": self.antiDebugChk.isChecked(),
            "packer": self.packerChk.isChecked()
        }
        
        self.settings["version_info"] = {
            "version": self.versionEdit.text().strip(),
            "company": self.companyEdit.text().strip(),
            "copyright": self.copyrightEdit.text().strip(),
            "description": self.descriptionEdit.text().strip()
        }
        
        self.settings["security"] = {
            "sign_certificate": self.certFileEdit.text().strip(),
            "cert_password": self.certPassEdit.text().strip(),
            "timestamp_server": self.timestampCombo.currentText()
        }
        
        self.settings["build_system"] = self.buildSystemCombo.currentText()
        self.settings["platform"] = self.platformCombo.currentText()
        self.settings["virtual_env"] = self.virtualEnvCombo.currentText()
        self.settings["template"] = self.templateCombo.currentText()
        self.settings["resource_compression"] = self.compressionCombo.currentText()
        self.settings["resource_encryption"] = self.encryptionChk.isChecked()
        
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "حفظ الإعدادات", f"فشل حفظ الإعدادات: {e}")

    def __ApplySettingsGUI__(self):
        self.entryList.clear()
        for p in self.settings.get("last_entries", []):
            self.entryList.addItem(p)
            
        self.filesList.clear()
        for p in self.settings.get("last_files", []):
            self.filesList.addItem(p)
            
        self.foldersList.clear()
        for p in self.settings.get("last_folders", []):
            self.foldersList.addItem(p)
            
        self.outLine.setText(self.settings.get("last_output", os.path.abspath("output")))
        self.iconLine.setText(self.settings.get("last_icon", ""))
        self.manifestLine.setText(self.settings.get("last_manifest", ""))
        
        self.oneFileChk.setChecked(self.settings.get("onefile", True))
        self.consoleChk.setChecked(not self.settings.get("noconsole", False))
        self.cleanChk.setChecked(self.settings.get("clean", True))
        
        adv = self.settings.get("advanced", {})
        self.hiddenImportsLine.setText(", ".join(adv.get("hidden_imports", [])))
        self.excludeModulesLine.setText(", ".join(adv.get("exclude_modules", [])))
        self.uacChk.setChecked(adv.get("uac_admin", False))
        self.keyLine.setText(adv.get("key", ""))
        self.optimizeChk.setChecked(adv.get("optimize", False))
        self.stripChk.setChecked(adv.get("strip", False))
        self.noPreferRedirectChk.setChecked(adv.get("no_prefer_redirect", False))
        self.obfuscateChk.setChecked(adv.get("obfuscate", False))
        self.antiDebugChk.setChecked(adv.get("anti_debug", False))
        self.packerChk.setChecked(adv.get("packer", False))
        
        version_info = self.settings.get("version_info", {})
        self.versionEdit.setText(version_info.get("version", "1.0.0"))
        self.companyEdit.setText(version_info.get("company", ""))
        self.WebSiteEdit.setText(version_info.get("WebSite", ""))
        self.copyrightEdit.setText(version_info.get("copyright", ""))
        self.descriptionEdit.setText(version_info.get("description", ""))
        
        security = self.settings.get("security", {})
        self.certFileEdit.setText(security.get("sign_certificate", ""))
        self.certPassEdit.setText(security.get("cert_password", ""))
        timestamp_server = security.get("timestamp_server", "http://timestamp.digicert.com")
        index = self.timestampCombo.findText(timestamp_server)
        if index >= 0:
            self.timestampCombo.setCurrentIndex(index)
        
        build_system = self.settings.get("build_system", "PyInstaller")
        index = self.buildSystemCombo.findText(build_system)
        if index >= 0:
            self.buildSystemCombo.setCurrentIndex(index)
            
        platform = self.settings.get("platform", "win32")
        index = self.platformCombo.findText(platform)
        if index >= 0:
            self.platformCombo.setCurrentIndex(index)
            
        virtual_env = self.settings.get("virtual_env", "")
        if virtual_env:
            index = self.virtualEnvCombo.findText(virtual_env)
            if index >= 0:
                self.virtualEnvCombo.setCurrentIndex(index)
            else:
                self.virtualEnvCombo.setEditText(virtual_env)
                
        template = self.settings.get("template", "مخصص (Custom)")
        index = self.templateCombo.findText(template)
        if index >= 0:
            self.templateCombo.setCurrentIndex(index)
            
        compression = self.settings.get("resource_compression", "normal")
        index = self.compressionCombo.findText(compression)
        if index >= 0:
            self.compressionCombo.setCurrentIndex(index)
            
        self.encryptionChk.setChecked(self.settings.get("resource_encryption", False))
        
        python_interpreter = self.settings.get("python_interpreter", "")
        if python_interpreter:
            index = self.interpCombo.findText(python_interpreter)
            if index >= 0:
                self.interpCombo.setCurrentIndex(index)
            else:
                self.interpCombo.setEditText(python_interpreter)

    def ResetSettings(self):
        reply = QMessageBox.question(self, self.lang_manager.tr("reset_settings", "إعادة التعيين"), self.lang_manager.tr("reset_confirm", "هل تريد إعادة الإعدادات إلى الوضع الافتراضي؟"), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings = DEFAULT_SETTINGS.copy()
            try:
                if os.path.isfile(SETTINGS_FILE):
                    os.remove(SETTINGS_FILE)
            except Exception:
                pass
            self.__ApplySettingsGUI__()
            QMessageBox.information(self, self.lang_manager.tr("reset_complete", "تم"), self.lang_manager.tr("reset_complete", "تمت إعادة التعيين للإعدادات الافتراضية."))

    def __AnalyzeMissingModules__(self):
        self.extra = PyInstallerExtras()
        script_paths = GetScriptPaths(self)

        if not script_paths:
            QMessageBox.warning(self, self.lang_manager.tr("analyze", "تحليل"), self.lang_manager.tr("no_inputs", "رجاءً اختر ملف أو سكربتات أولاً."))
            return

        all_missing = []
        for script in script_paths:
            missing = self.extra.AnalyzeMissingImports(script)
            if missing:
                all_missing.extend(missing)

        if all_missing:
            QMessageBox.information(
                self,
                "نتائج التحليل",
                f"الموديولات المفقودة:\n{', '.join(set(all_missing))}"
            )
        else:
            QMessageBox.information(self, self.lang_manager.tr("analyze_results", "نتائج التحليل"), self.lang_manager.tr("no_missing_modules", "لم يتم العثور على موديولات مفقودة."))

    def AdvancedDependencyAnalysis(self):
        self.extra = PyInstallerExtras()
        script_paths = GetScriptPaths(self)

        if not script_paths:
            QMessageBox.warning(self, self.lang_manager.tr("advanced_analysis", "تحليل"), self.lang_manager.tr("no_inputs", "رجاءً اختر ملف أو سكربتات أولاً."))
            return

        results = []
        for script in script_paths:
            analysis = self.extra.AdvancedDependencyAnalysis(script)
            results.append((script, analysis))

        report = "نتائج التحليل المتقدم:\n\n"
        for script, analysis in results:
            report += f"الملف: {os.path.basename(script)}\n"
            report += f"الموديولات المفقودة: {', '.join(analysis['missing_imports']) if analysis['missing_imports'] else 'لا يوجد'}\n"
            report += f"الملفات الكبيرة: {len(analysis['large_files'])}\n"
            report += f"الاستيرادات المشبوهة: {', '.join(analysis['suspicious_imports']) if analysis['suspicious_imports'] else 'لا يوجد'}\n"
            report += f"مشاكل الأداء: {', '.join(analysis['performance_issues']) if analysis['performance_issues'] else 'لا يوجد'}\n"
            report += f"التوصيات: {', '.join(analysis['recommendations']) if analysis['recommendations'] else 'لا يوجد'}\n"
            report += "-" * 50 + "\n"

        QMessageBox.information(self, "التحليل المتقدم", report)

    def __GenerateBuildReport__(self, duration: float, output_path: str):
        report = {
            "build_time": f"{duration:.2f} ثانية",
            "timestamp": time.ctime(),
            "settings": self.settings,
            "output_size": "0 bytes",
            "dependencies": [],
            "optimizations": []
        }

        try:
            if os.path.exists(output_path):
                total_size = 0
                for root, dirs, files in os.walk(output_path):
                    for file in files:
                        total_size += os.path.getsize(os.path.join(root, file))
                report["output_size"] = f"{total_size / 1024 / 1024:.2f} MB"
        except Exception:
            pass

        if self.optimizeChk.isChecked():
            report["optimizations"].append("تحسينات الأداء")
        if self.stripChk.isChecked():
            report["optimizations"].append("إزالة المعلومات غير الضرورية")
        if self.obfuscateChk.isChecked():
            report["optimizations"].append("تشويش الكود")

        report_text = f"تقرير البناء\n{'='*30}\n"
        report_text += f"وقت البناء: {report['build_time']}\n"
        report_text += f"الطابع الزمني: {report['timestamp']}\n"
        report_text += f"حجم الإخراج: {report['output_size']}\n"
        report_text += f"التحسينات: {', '.join(report['optimizations']) if report['optimizations'] else 'لا يوجد'}\n"

        return report_text

    def CodeAudit(self):
        script_paths = GetScriptPaths(self)
        if not script_paths:
            QMessageBox.warning(self, self.lang_manager.tr("code_audit", "التدقيق"), self.lang_manager.tr("no_inputs", "رجاءً اختر ملف أو سكربتات أولاً."))
            return

        audit_results = {
            "large_files": [],
            "suspicious_imports": [],
            "performance_issues": [],
            "security_issues": []
        }

        for script in script_paths:
            analysis = self.extra.AdvancedDependencyAnalysis(script)
            audit_results["large_files"].extend(analysis["large_files"])
            audit_results["suspicious_imports"].extend(analysis["suspicious_imports"])
            audit_results["performance_issues"].extend(analysis["performance_issues"])
            audit_results["security_issues"].extend(analysis["suspicious_imports"])

        report = "نتائج تدقيق الكود:\n\n"
        report += f"الملفات الكبيرة (>10MB): {len(audit_results['large_files'])}\n"
        report += f"الاستيرادات المشبوهة: {', '.join(set(audit_results['suspicious_imports'])) if audit_results['suspicious_imports'] else 'لا يوجد'}\n"
        report += f"مشاكل الأداء: {', '.join(set(audit_results['performance_issues'])) if audit_results['performance_issues'] else 'لا يوجد'}\n"
        report += f"مشاكل الأمان: {', '.join(set(audit_results['security_issues'])) if audit_results['security_issues'] else 'لا يوجد'}\n"

        QMessageBox.information(self, "تدقيق الكود", report)

    def __CreateMenus__(self):
        menubar = self.menuBar()
            
        fileMenu = menubar.addMenu(self.lang_manager.tr("file_menu", "الملف", "File", "Fichier", "Файл", "文件"))
        action_new = QAction(self.lang_manager.tr("new_project", "مشروع جديد", "New Project", "Nouveau projet", "Новый проект", "新项目"), self)
        action_new.setShortcut("Ctrl+N")
        fileMenu.addAction(action_new)
        
        action_reset = QAction(self.lang_manager.tr("reset_settings", "إعادة تعيين الإعدادات", "Reset Settings", "Réinitialiser les paramètres", "Сброс настроек", "重置设置"), self)
        action_reset.triggered.connect(self.ResetSettings)
        fileMenu.addAction(action_reset)
        
        action_exit = QAction(self.lang_manager.tr("exit", "خروج", "Exit", "Quitter", "Выход", "退出"), self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.close)
        fileMenu.addAction(action_exit)

        buildMenu = menubar.addMenu(self.lang_manager.tr("build_menu", "البناء", "Build", "Construction", "Сборка", "构建"))
        action_build = QAction(self.lang_manager.tr("start_build", "بدء البناء", "Start Build", "Démarrer la construction", "Начать сборку", "开始构建"), self)
        action_build.setShortcut("Ctrl+B")
        action_build.triggered.connect(self.start_build)
        buildMenu.addAction(action_build)
        
        action_spec = QAction(self.lang_manager.tr("generate_spec_only", "توليد ملف .spec فقط", "Generate .spec File Only", "Générer uniquement le fichier .spec", "Генерировать только файл .spec", "仅生成 .spec 文件"), self)
        action_spec.triggered.connect(self.generate_spec_only)
        buildMenu.addAction(action_spec)

        toolsMenu = menubar.addMenu(self.lang_manager.tr("tools_menu", "أدوات", "Tools", "Outils", "Инструменты", "工具"))
        action_clean = QAction(self.lang_manager.tr("full_clean", "تنظيف كامل (build, dist, spec)", "Full Clean (build, dist, spec)", "Nettoyage complet (build, dist, spec)", "Полная очистка (build, dist, spec)", "完全清理（build、dist、spec）"), self)
        action_clean.triggered.connect(self.full_clean)
        toolsMenu.addAction(action_clean)

        self.action_analyze = QAction(self.lang_manager.tr("analyze_missing", "تحليل الموديولات المفقودة", "Analyze Missing Modules", "Analyser les modules manquants", "Анализ отсутствующих модулей", "分析缺失模块"), self)
        self.action_analyze.triggered.connect(self.__AnalyzeMissingModules__)
        toolsMenu.addAction(self.action_analyze)
        
        action_advanced_analyze = QAction(self.lang_manager.tr("advanced_analyze", "تحليل متقدم للتبعيات", "Advanced Dependency Analysis", "Analyse avancée des dépendances", "Расширенный анализ зависимостей", "高级依赖分析"), self)
        action_advanced_analyze.triggered.connect(self.AdvancedDependencyAnalysis)
        toolsMenu.addAction(action_advanced_analyze)
        
        action_audit = QAction(self.lang_manager.tr("code_audit", "تدقيق الكود", "Code Audit", "Audit de code", "Аудит кода", "代码审计"), self)
        action_audit.triggered.connect(self.CodeAudit)
        toolsMenu.addAction(action_audit)

        viewMenu = menubar.addMenu(self.lang_manager.tr("view_menu", "المظهر", "View", "Affichage", "Вид", "视图"))
        self.action_toggle_theme = QAction(self.lang_manager.tr("toggle_theme", "تبديل الوضع (داكن/فاتح)", "Toggle Theme (Dark/Light)", "Basculer le thème (Sombre/Clair)", "Переключить тему (Темная/Светлая)", "切换主题（深色/浅色）"), self)
        self.action_toggle_theme.triggered.connect(self.toggle_theme)
        viewMenu.addAction(self.action_toggle_theme)
        
        action_dark = QAction(self.lang_manager.tr("dark_theme", "الوضع الداكن", "Dark Theme", "Thème sombre", "Темная тема", "深色主题"), self)
        action_dark.triggered.connect(lambda: self.set_theme("dark"))
        viewMenu.addAction(action_dark)
        
        action_light = QAction(self.lang_manager.tr("light_theme", "الوضع الفاتح", "Light Theme", "Thème clair", "Светлая тема", "浅色主题"), self)
        action_light.triggered.connect(lambda: self.set_theme("light"))
        viewMenu.addAction(action_light)

        action_custom = QAction(self.lang_manager.tr("custom_theme", "مظهر مخصص…", "Custom Theme…", "Thème personnalisé…", "Пользовательская тема…", "自定义主题…"), self)
        action_custom.triggered.connect(self.choose_custom_theme)
        viewMenu.addAction(action_custom)


        settingsMenu = menubar.addMenu(self.lang_manager.tr("settings_menu", "الإعدادات", "Settings", "Paramètres", "Настройки", "设置"))
        action_plugins = QAction(self.lang_manager.tr("manage_plugins", "إدارة الإضافات", "Manage Plugins", "Gérer les plugins", "Управление плагинами", "管理插件"), self)
        action_plugins.triggered.connect(self.manage_plugins)
        settingsMenu.addAction(action_plugins)
        
        action_templates = QAction(self.lang_manager.tr("manage_templates", "القوالب", "Templates", "Modèles", "Шаблоны", "模板"), self)
        action_templates.triggered.connect(self.manage_templates)
        settingsMenu.addAction(action_templates)

        helpMenu = menubar.addMenu(self.lang_manager.tr("help_menu", "مساعدة", "Help", "Aide", "Помощь", "帮助"))
        action_check_updates = QAction(self.lang_manager.tr("check_updates", "تحقق من التحديثات", "Check for Updates", "Vérifier les mises à jour", "Проверить обновления", "检查更新"), self)
        action_check_updates.triggered.connect(self.check_updates)
        helpMenu.addAction(action_check_updates)
        
        action_docs = QAction(self.lang_manager.tr("documentation", "الوثائق", "Documentation", "Documentation", "Документация", "文档"), self)
        action_docs.triggered.connect(self.show_documentation)
        helpMenu.addAction(action_docs)

        WebDev = QAction(self.lang_manager.tr("visit_website", "زيارة موقعي", "Visit My Website", "Visiter mon site Web", "Посетить мой сайт", "访问我的网站"), self)
        WebDev.triggered.connect(self.VistWebSite)
        helpMenu.addAction(WebDev)

        GoWebProgram = QAction(self.lang_manager.tr("program_website", "موقع البرنامج", "Program Website", "Site du programme", "Веб-сайт программы", "程序网站"), self)
        GoWebProgram.triggered.connect(self.WebSiteProgram)
        helpMenu.addAction(GoWebProgram)
        
        action_about = QAction(self.lang_manager.tr("about_program", "حول البرنامج", "About Program", "À propos du programme", "О программе", "关于程序"), self)
        action_about.triggered.connect(self.about_program)
        helpMenu.addAction(action_about)

        Policies = menubar.addMenu(self.lang_manager.tr("policies_menu", "السياسات", "Policies", "Politiques", "Политики", "政策"))

        Privacy_Policy = QAction(self.lang_manager.tr("privacy_policy", "سياسة الخصوصية", "Privacy Policy", "Politique de confidentialité", "Политика конфиденциальности", "隐私政策"), self)
        Privacy_Policy.triggered.connect(self.Privacy_Policy)
        Policies.addAction(Privacy_Policy)

        Terms_of_Use = QAction(self.lang_manager.tr("terms_of_use", "سياسة الأستخدام", "Terms of Use", "Conditions d'utilisation", "Условия использования", "使用条款"), self)
        Terms_of_Use.triggered.connect(self.Terms_of_Use)
        Policies.addAction(Terms_of_Use)

        License_Agreement = QAction(self.lang_manager.tr("license_agreement", "أتفاقية الترخيص", "License Agreement", "Contrat de licence", "Лицензионное соглашение", "许可协议"), self)
        License_Agreement.triggered.connect(self.License_Agreement)
        Policies.addAction(License_Agreement)

        Code_of_Conduct = QAction(self.lang_manager.tr("code_of_conduct", "قواعد السلوك", "Code of Conduct", "Code de conduite", "Кодекс поведения", "行为准则"), self)
        Code_of_Conduct.triggered.connect(self.Code_of_Conduct)
        Policies.addAction(Code_of_Conduct)

        Contribution_Policy = QAction(self.lang_manager.tr("contribution_policy", "سياسة المساهمة", "Contribution Policy", "Politique de contribution", "Политика вклада", "贡献政策"), self)
        Contribution_Policy.triggered.connect(self.Contribution_Policy)
        Policies.addAction(Contribution_Policy)
        
        PyInstallerMenu = menubar.addMenu(self.lang_manager.tr("pyinstaller_menu", "PyInstaller قائمة", "Menu PyInstaller", "Menu PyInstaller", "Меню PyInstaller", "PyInstaller 菜单"))
        action_check_pyinstaller = QAction(self.lang_manager.tr("check_pyinstaller_updates", "التحقق من تحديثات PyInstaller", "Check PyInstaller Updates"), self)
        action_check_pyinstaller.triggered.connect(self.check_pyinstaller_updates)
        PyInstallerMenu.addAction(action_check_pyinstaller)
        
        
        languageMenu = menubar.addMenu(self.lang_manager.tr("language_menu", "اللغة", "Language", "Langue", "Язык", "语言"))    
        languages = self.lang_manager.AvailableLanguges()
        lang_names = {
            "ar": "العربية",
            "en": "English", 
            "fr": "Français",
            "ru": "Русский",
            "zh": "中文"
        }
        
        for lang_code in languages:
            action = QAction(lang_names.get(lang_code, lang_code), self)
            action.triggered.connect(lambda checked, code=lang_code: self.ChangeLanguage(code))
            languageMenu.addAction(action)

    def CreateMenusGUI(self):
        cw = QWidget(self)
        self.setCentralWidget(cw)
        
        main_layout = QHBoxLayout(cw)
        splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.__SetupLeftPanel__(left_layout)
        self.setup_right_panel(right_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)

    def __SetupLeftPanel__(self, layout):
        tab_widget = QTabWidget()
        
        basic_tab = self.__CreateBasicTAB__()
        advanced_tab = self.__CreateAdvancedTAB__()
        security_tab = self.__CreateSecurityTAB__()
        resources_tab = self.create_resources_tab()
        options_os_system = self.__CreateOSSystemOptionsTAB__()
        
        tab_widget.addTab(basic_tab, self.lang_manager.tr("tab_basic"))
        tab_widget.addTab(advanced_tab, self.lang_manager.tr("tab_advanced"))
        tab_widget.addTab(security_tab, self.lang_manager.tr("tab_security"))
        tab_widget.addTab(resources_tab, self.lang_manager.tr("tab_resources"))
        tab_widget.addTab(options_os_system, self.lang_manager.tr("options_os_system"))
        
        layout.addWidget(tab_widget)

    def __CreateBasicTAB__(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel(self.lang_manager.tr("mode")))
        self.modeCombo = QComboBox()

        self.modeCombo.addItems([self.lang_manager.tr("single_file", "ملف واحد"), self.lang_manager.tr("batch_files", "ملفات متعددة")])
        self.modeCombo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.modeCombo)
        mode_layout.addStretch(1)
        layout.addLayout(mode_layout)
        
        entry_layout = QHBoxLayout()
        self.entryLine = QLineEdit()
        self.entryBtn = QPushButton(self.lang_manager.tr("choose_file", "أختيار ملف…"))
        self.entryBtn.clicked.connect(self.pick_entry)
        entry_layout.addWidget(QLabel(self.lang_manager.tr("main_file", "الملف الرئيسي")))
        entry_layout.addWidget(self.entryLine)
        entry_layout.addWidget(self.entryBtn)
        entryBox = QGroupBox(self.lang_manager.tr("single_input", "المدخل (Single)"))
        entryBox.setLayout(entry_layout)
        layout.addWidget(entryBox)
        
        self.entryList = QListWidget()
        self.addEntryBtn = QPushButton(self.lang_manager.tr("add_script", "أضف سكربت"))
        self.addEntryBtn.clicked.connect(self.add_entry)
        self.remEntryBtn = QPushButton(self.lang_manager.tr("remove_selected", "إزالة المحدد"))
        self.remEntryBtn.clicked.connect(self.remove_entry)
        elBtns = QHBoxLayout()
        elBtns.addWidget(self.addEntryBtn)
        elBtns.addWidget(self.remEntryBtn)
        entryListBox = QGroupBox(self.lang_manager.tr("multiple_inputs", "مدخلات متعددة (Batch)"))
        v = QVBoxLayout()
        v.addWidget(self.entryList)
        v.addLayout(elBtns)
        entryListBox.setLayout(v)
        layout.addWidget(entryListBox)
        
        options_group = QGroupBox(self.lang_manager.tr("basic_options", "الخيارات الأساسية"))
        options_layout = QVBoxLayout()
        self.oneFileChk = QCheckBox(self.lang_manager.tr("one_file", "بناء ملف واحد -F (موصى به)"))
        self.consoleChk = QCheckBox(self.lang_manager.tr("show_console", "إظهار الكونسول (Console)"))
        self.cleanChk = QCheckBox(self.lang_manager.tr("clean_before", "تنظيف قبل البناء --clean"))
        options_layout.addWidget(self.oneFileChk)
        options_layout.addWidget(self.consoleChk)
        options_layout.addWidget(self.cleanChk)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addWidget(QLabel(self.lang_manager.tr("drag_drop_hint", "تستطيع سحب الملفات و أفلاتها على الصيغ المطلوبة منها (.py, .ico, .manifest, .pfx, .p12)")))
        layout.addStretch(1)
        
        return widget

    def __CreateAdvancedTAB__(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        build_system_layout = QHBoxLayout()
        build_system_layout.addWidget(QLabel(self.lang_manager.tr("build_system", "نظام البناء")))
        self.buildSystemCombo = QComboBox()
        self.buildSystemCombo.addItems(self.lang_manager.tr("build_systems", ["PyInstaller (All)", "cx_Freeze (Traditional)", "Nuitka (C/C++)", "PyOxidizer (Rust)", "Briefcase (Native)"]))
        build_system_layout.addWidget(self.buildSystemCombo)
        layout.addLayout(build_system_layout)
        
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel(self.lang_manager.tr("platform", "المنصة")))
        self.platformCombo = QComboBox()
        self.platformCombo.addItems(["Windows 32-bit (win32)", "Windows 64-bit (win64)", "Linux", "macOS"])
        platform_layout.addWidget(self.platformCombo)
        layout.addLayout(platform_layout)
        
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel(self.lang_manager.tr("template", "القالب")))
        self.templateCombo = QComboBox()
        templates = self.lang_manager.tr("templates")
        if isinstance(templates, list):
            self.templateCombo.addItems(templates)
        else:
            fallback_templates = [
                "تطبيق واجهة رسومية (GUI)",
                "تطبيق وحدة التحكم (CLI)",
                "تطبيق خدمة (Service)",
                "تطبيق ويب (Web)",
                "مخصص (Custom)"
            ]
            self.templateCombo.addItems(fallback_templates)
        template_layout.addWidget(self.templateCombo)
        layout.addLayout(template_layout)
        
        interp_layout = QHBoxLayout()
        self.interpCombo = QComboBox()
        found = FindPythonInterpreters()
        for p in found:
            self.interpCombo.addItem(p)
        self.interpCombo.setEditable(True)
        interp_layout.addWidget(QLabel(self.lang_manager.tr("python_interpreter", "مفسّر Python")))
        interp_layout.addWidget(self.interpCombo)
        layout.addLayout(interp_layout)
        
        
        virtual_env_layout = QHBoxLayout()
        self.virtualEnvCombo = QComboBox()
        self.virtualEnvCombo.setEditable(True)
        virtual_env_types = [
            "venv (Python built-in)",
            "virtualenv",
            "conda",
            "pipenv",
            "poetry",
            "rye",
            "pyenv",
            "wsl venv",
        ]
        virtual_envs = FindVirtualEnvironments()
        for env in virtual_envs:
            self.virtualEnvCombo.addItem(env)
        self.virtualEnvCombo.insertSeparator(self.virtualEnvCombo.count())
        self.virtualEnvCombo.addItems(virtual_env_types)
        virtual_env_layout.addWidget(QLabel(self.lang_manager.tr("virtual_env", "البيئة الافتراضية")))
        virtual_env_layout.addWidget(self.virtualEnvCombo)
        layout.addLayout(virtual_env_layout)

        
        optimization_group = QGroupBox(self.lang_manager.tr("optimization_options", "خيارات التحسين"))
        optimization_layout = QVBoxLayout()
        self.optimizeChk = QCheckBox(self.lang_manager.tr("enable_optimizations", "تفعيل تحسينات الأداء --optimize"))
        self.stripChk = QCheckBox(self.lang_manager.tr("strip_info", "إزالة المعلومات غير الضرورية --strip"))
        self.noPreferRedirectChk = QCheckBox(self.lang_manager.tr("disable_redirect", "تعطيل إعادة التوجيه --no-prefer-redirect"))
        optimization_layout.addWidget(self.optimizeChk)
        optimization_layout.addWidget(self.stripChk)
        optimization_layout.addWidget(self.noPreferRedirectChk)
        optimization_group.setLayout(optimization_layout)
        layout.addWidget(optimization_group)
        
        version_group = QGroupBox(self.lang_manager.tr("version_info", "معلومات الإصدار"))
        version_layout = QVBoxLayout()
        version_info_layout = QHBoxLayout()
        self.versionEdit = QLineEdit()
        self.versionEdit.setText("1.0.0")
        version_info_layout.addWidget(QLabel(self.lang_manager.tr("version", "الإصدار")))
        version_info_layout.addWidget(self.versionEdit)
        version_layout.addLayout(version_info_layout)
        
        company_layout = QHBoxLayout()
        self.companyEdit = QLineEdit()
        company_layout.addWidget(QLabel(self.lang_manager.tr("company", "الشركة")))
        company_layout.addWidget(self.companyEdit)
        version_layout.addLayout(company_layout)
        
        WebSite_layout = QHBoxLayout()
        self.WebSiteEdit = QLineEdit()
        self.WebSiteEdit.setPlaceholderText(self.lang_manager.tr("website", "https://example.com"))
        WebSite_layout.addWidget(QLabel(self.lang_manager.tr("website", "الرابط")))
        WebSite_layout.addWidget(self.WebSiteEdit)
        version_layout.addLayout(WebSite_layout) 
        
        copyright_layout = QHBoxLayout()
        self.copyrightEdit = QLineEdit()
        self.copyrightEdit.setPlaceholderText(self.lang_manager.tr("copyright", "Copyright © 2025"))
        copyright_layout.addWidget(QLabel(self.lang_manager.tr("copyright", "حقوق النشر")))
        copyright_layout.addWidget(self.copyrightEdit)
        version_layout.addLayout(copyright_layout)
        
        description_layout = QHBoxLayout()
        self.descriptionEdit = QLineEdit()
        description_layout.addWidget(QLabel(self.lang_manager.tr("description", "الوصف")))
        description_layout.addWidget(self.descriptionEdit)
        version_layout.addLayout(description_layout)
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        
        layout.addStretch(1)
        return widget
    
    def __CreateOSSystemOptionsTAB__(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.entryLabel = QLabel(self.lang_manager.tr("options_os_system", "خيارات نظام التشغيل"))
        self.entryLabel.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.entryLabel)

        disable_traceback_group = QGroupBox(self.lang_manager.tr("disable_windowed_traceback", "تعطيل رسالة الخطأ المنفصلة"))
        disable_traceback_layout = QVBoxLayout()
        self.disableWindowedTracebackChk = QCheckBox(self.lang_manager.tr("disable_windowed_traceback_checkbox", "--disable-windowed-traceback"))
        disable_traceback_desc = QLabel(self.lang_manager.tr("disable_windowed_traceback_desc", "عند تفعيله: سيتم عرض رسائل الأخطاء في الكونسول بدلاً من نافذة منفصلة (مفيد للتطبيقات التي تعمل بدون واجهة رسومية)"))
        disable_traceback_desc.setWordWrap(True)
        disable_traceback_desc.setStyleSheet("color: gray; font-size: 10px;")
        disable_traceback_layout.addWidget(self.disableWindowedTracebackChk)
        disable_traceback_layout.addWidget(disable_traceback_desc)
        disable_traceback_group.setLayout(disable_traceback_layout)
        layout.addWidget(disable_traceback_group)

        uac_admin_group = QGroupBox(self.lang_manager.tr("uac_admin_option", "صلاحيات المدير"))
        uac_admin_layout = QVBoxLayout()
        self.uacAdminChk = QCheckBox(self.lang_manager.tr("uac_admin_checkbox", "--uac-admin"))
        uac_admin_desc = QLabel(self.lang_manager.tr("uac_admin_desc", "عند تفعيله: سيطلب البرنامج صلاحيات المدير (Administrator) عند التشغيل على Windows"))
        uac_admin_desc.setWordWrap(True)
        uac_admin_desc.setStyleSheet("color: gray; font-size: 10px;")
        uac_admin_layout.addWidget(self.uacAdminChk)
        uac_admin_layout.addWidget(uac_admin_desc)
        uac_admin_group.setLayout(uac_admin_layout)
        layout.addWidget(uac_admin_group)

        uac_uiaccess_group = QGroupBox(self.lang_manager.tr("uac_uiaccess_option", "وصول واجهة المستخدم"))
        uac_uiaccess_layout = QVBoxLayout()
        self.uacUIAccessChk = QCheckBox(self.lang_manager.tr("uac_uiaccess_checkbox", "--uac-uiaccess"))
        uac_uiaccess_desc = QLabel(self.lang_manager.tr("uac_uiaccess_desc", "عند تفعيله: يسمح للبرنامج بالتحكم بنوافذ ذات صلاحيات أعلى على Windows (يتطلب توقيع رقمي)"))
        uac_uiaccess_desc.setWordWrap(True)
        uac_uiaccess_desc.setStyleSheet("color: gray; font-size: 10px;")
        uac_uiaccess_layout.addWidget(self.uacUIAccessChk)
        uac_uiaccess_layout.addWidget(uac_uiaccess_desc)
        uac_uiaccess_group.setLayout(uac_uiaccess_layout)
        layout.addWidget(uac_uiaccess_group)

        no_upx_group = QGroupBox(self.lang_manager.tr("no_upx_option", "تعطيل ضاغط UPX"))
        no_upx_layout = QVBoxLayout()
        self.noUpxChk = QCheckBox(self.lang_manager.tr("no_upx_checkbox", "--noupx"))
        no_upx_desc = QLabel(self.lang_manager.tr("no_upx_desc", "عند تفعيله: سيتم عدم استخدام أداة الضغط UPX على الملفات الثنائية (قد يؤدي إلى حجم ملف أكبر لكن أسرع في التشغيل)"))
        no_upx_desc.setWordWrap(True)
        no_upx_desc.setStyleSheet("color: gray; font-size: 10px;")
        no_upx_layout.addWidget(self.noUpxChk)
        no_upx_layout.addWidget(no_upx_desc)
        no_upx_group.setLayout(no_upx_layout)
        layout.addWidget(no_upx_group)

        strip_group = QGroupBox(self.lang_manager.tr("strip_option", "إزالة رموز التصحيح"))
        strip_layout = QVBoxLayout()
        self.stripSymbolsChk = QCheckBox(self.lang_manager.tr("strip_checkbox", "--strip"))
        strip_desc = QLabel(self.lang_manager.tr("strip_desc", "عند تفعيله: سيتم إزالة رموز التصحيح (Debug Symbols) من الملفات الثنائية (يقلل حجم الملف لكن يصعب تصحيح الأخطاء)"))
        strip_desc.setWordWrap(True)
        strip_desc.setStyleSheet("color: gray; font-size: 10px;")
        strip_layout.addWidget(self.stripSymbolsChk)
        strip_layout.addWidget(strip_desc)
        strip_group.setLayout(strip_layout)
        layout.addWidget(strip_group)

        bootloader_group = QGroupBox(self.lang_manager.tr("bootloader_signals_option", "تجاهل الإشارات (Signals)"))
        bootloader_layout = QVBoxLayout()
        self.bootloaderIgnoreSignalsChk = QCheckBox(self.lang_manager.tr("bootloader_signals_checkbox", "--bootloader-ignore-signals"))
        bootloader_desc = QLabel(self.lang_manager.tr("bootloader_signals_desc", "عند تفعيله: سيتم تجاهل إشارات النظام (مثل SIGTERM) في مرحلة التحميل الأولية (مفيد لتجنب إغلاق البرنامج بشكل مفاجئ)"))
        bootloader_desc.setWordWrap(True)
        bootloader_desc.setStyleSheet("color: gray; font-size: 10px;")
        bootloader_layout.addWidget(self.bootloaderIgnoreSignalsChk)
        bootloader_layout.addWidget(bootloader_desc)
        bootloader_group.setLayout(bootloader_layout)
        layout.addWidget(bootloader_group)

        layout.addStretch(1)
        return widget
        

    def __CreateSecurityTAB__(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        security_group = QGroupBox(self.lang_manager.tr("security_options", "خيارات الأمان"))
        security_layout = QVBoxLayout()
        self.obfuscateChk = QCheckBox(self.lang_manager.tr("obfuscation", "تشويش الكود (Obfuscation)"))
        self.antiDebugChk = QCheckBox(self.lang_manager.tr("anti_debug", "الحماية من التصحيح (Anti-Debug)"))
        self.packerChk = QCheckBox(self.lang_manager.tr("packer", "استخدام ملفات مضغوطة (Packer)"))
        security_layout.addWidget(self.obfuscateChk)
        security_layout.addWidget(self.antiDebugChk)
        security_layout.addWidget(self.packerChk)
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)
        
        signing_group = QGroupBox(self.lang_manager.tr("digital_signature", "التوقيع الرقمي"))
        signing_layout = QVBoxLayout()
        cert_layout = QHBoxLayout()
        self.certFileEdit = QLineEdit()
        self.certFileBtn = QPushButton(self.lang_manager.tr("choose_certificate", "اختيار..."))
        self.certFileBtn.clicked.connect(self.pick_certificate)
        cert_layout.addWidget(QLabel(self.lang_manager.tr("sign_certificate", "شهادة التوقيع")))
        cert_layout.addWidget(self.certFileEdit)
        cert_layout.addWidget(self.certFileBtn)
        signing_layout.addLayout(cert_layout)
        
        cert_pass_layout = QHBoxLayout()
        self.certPassEdit = QLineEdit()
        self.certPassEdit.setEchoMode(QLineEdit.Password)
        cert_pass_layout.addWidget(QLabel(self.lang_manager.tr("cert_password", "كلمة مرور الشهادة")))
        cert_pass_layout.addWidget(self.certPassEdit)
        signing_layout.addLayout(cert_pass_layout)
        
        timestamp_layout = QHBoxLayout()
        self.timestampCombo = QComboBox()
        self.timestampCombo.addItems([
            "http://timestamp.digicert.com",
            "http://timestamp.comodoca.com",
            "http://timestamp.globalsign.com",
            "http://timestamp.sectigo.com",
            "http://tsa.starfieldtech.com",
            "Nothing"
        ])
        timestamp_layout.addWidget(QLabel(self.lang_manager.tr("timestamp_server", "خادم الطابع الزمني")))
        timestamp_layout.addWidget(self.timestampCombo)
        signing_layout.addLayout(timestamp_layout)
        signing_group.setLayout(signing_layout)
        layout.addWidget(signing_group)
        if not self.certFileEdit.text():
            self.certFileEdit.setStyleSheet("border: 1px solid red;")
            self.certFileEdit.setFocus()
        layout.addStretch(1)
        return widget

    def create_resources_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        files_group = QGroupBox(self.lang_manager.tr("additional_files", "ملفات موارد إضافية (--add-data)"))
        files_layout = QVBoxLayout()
        self.filesList = QListWidget()
        files_buttons = QHBoxLayout()
        self.addFileBtn = QPushButton(self.lang_manager.tr("add_file", "إضافة ملف…"))
        self.addFileBtn.clicked.connect(self.add_file)
        self.remFileBtn = QPushButton(self.lang_manager.tr("remove_file", "حذف المحدد"))
        self.remFileBtn.clicked.connect(self.remove_file)
        self.chaning = QPushButton(self.lang_manager.tr("toggle_files_list", "تكبير / تصغير قائمة الملفات"))
        self.chaning.clicked.connect(self.__RestoreMinimize__)
        files_buttons.addWidget(self.chaning)
        files_buttons.addWidget(self.addFileBtn)
        files_buttons.addWidget(self.remFileBtn)
        files_layout.addWidget(self.filesList)
        files_layout.addLayout(files_buttons)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        folders_group = QGroupBox(self.lang_manager.tr("additional_folders", "مجلدات موارد إضافية (--add-data)"))
        folders_layout = QVBoxLayout()
        self.foldersList = QListWidget()
        folders_buttons = QHBoxLayout()
        self.addFolderBtn = QPushButton(self.lang_manager.tr("add_folder", "إضافة مجلد…"))
        self.addFolderBtn.clicked.connect(self.add_folder)
        self.remFolderBtn = QPushButton(self.lang_manager.tr("remove_folder", "حذف المحدد"))
        self.remFolderBtn.clicked.connect(self.remove_folder)
        folders_buttons.addWidget(self.addFolderBtn)
        folders_buttons.addWidget(self.remFolderBtn)
        folders_layout.addWidget(self.foldersList)
        folders_layout.addLayout(folders_buttons)
        folders_group.setLayout(folders_layout)
        layout.addWidget(folders_group)
        
        resource_management = QGroupBox(self.lang_manager.tr("resource_management", "إدارة الموارد"))
        resource_layout = QVBoxLayout()
        compression_layout = QHBoxLayout()
        self.compressionCombo = QComboBox()
        self.compressionCombo.addItems([self.lang_manager.tr("compression_levels", ["بدون ضغط", "ضغط عادي", "ضغط عالي"])[0],
                                        self.lang_manager.tr("compression_levels", ["بدون ضغط", "ضغط عادي", "ضغط عالي"])[1],
                                        self.lang_manager.tr("compression_levels", ["بدون ضغط", "ضغط عادي", "ضغط عالي"])[2]])
        compression_layout.addWidget(QLabel(self.lang_manager.tr("resource_compression", "ضغط الموارد")))
        compression_layout.addWidget(self.compressionCombo)
        resource_layout.addLayout(compression_layout)
        
        self.encryptionChk = QCheckBox(self.lang_manager.tr("encrypt_resources", "تشفير الموارد"))
        resource_layout.addWidget(self.encryptionChk)
        resource_management.setLayout(resource_layout)
        layout.addWidget(resource_management)
        
        layout.addStretch(1)
        return widget

    def setup_right_panel(self, layout):
        output_group = QGroupBox(self.lang_manager.tr("output_group", "الإخراج"))
        output_layout = QVBoxLayout()
        out_path_layout = QHBoxLayout()
        self.outLine = QLineEdit()
        self.outBtn = QPushButton(self.lang_manager.tr("pick_output", "مكان الإخراج"))
        self.outBtn.clicked.connect(self.pick_output)
        out_path_layout.addWidget(QLabel(self.lang_manager.tr("output_folder", "مجلد الإخراج")))
        out_path_layout.addWidget(self.outLine)
        out_path_layout.addWidget(self.outBtn)
        output_layout.addLayout(out_path_layout)
        
        icon_layout = QHBoxLayout()
        self.iconLine = QLineEdit()
        self.iconBtn = QPushButton(self.lang_manager.tr("choose_icon", "اختيار أيقونة…"))
        self.iconBtn.clicked.connect(self.pick_icon)
        icon_layout.addWidget(QLabel(self.lang_manager.tr("icon", "الأيقونة")))
        icon_layout.addWidget(self.iconLine)
        icon_layout.addWidget(self.iconBtn)
        output_layout.addLayout(icon_layout)
        
        manifest_layout = QHBoxLayout()
        self.manifestLine = QLineEdit()
        self.manifestBtn = QPushButton(self.lang_manager.tr("choose_manifest", "اختيار ملف manifest…"))
        self.manifestBtn.clicked.connect(self.pick_manifest)
        manifest_layout.addWidget(QLabel(self.lang_manager.tr("manifest", "الملف التجسيدي")))
        manifest_layout.addWidget(self.manifestLine)
        manifest_layout.addWidget(self.manifestBtn)
        output_layout.addLayout(manifest_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        imports_group = QGroupBox(self.lang_manager.tr("imports_settings", "الاستيرادات والإعدادات المتقدمة"))
        imports_layout = QVBoxLayout()
        hidden_layout = QHBoxLayout()
        self.hiddenImportsLine = QLineEdit()
        hidden_layout.addWidget(QLabel(self.lang_manager.tr("hidden_imports", "الاستيرادات المخفية (مفصولة بفاصلة)")))
        hidden_layout.addWidget(self.hiddenImportsLine)
        imports_layout.addLayout(hidden_layout)
        
        exclude_layout = QHBoxLayout()
        self.excludeModulesLine = QLineEdit()
        exclude_layout.addWidget(QLabel(self.lang_manager.tr("exclude_modules", "الموديولات المستبعدة (مفصولة بفاصلة)")))
        exclude_layout.addWidget(self.excludeModulesLine)
        imports_layout.addLayout(exclude_layout)
        
        uac_layout = QHBoxLayout()
        self.uacChk = QCheckBox(self.lang_manager.tr("request_admin", "طلب صلاحيات المدير Administrator (--uac-admin)"))
        self.iconAdmin = QIcon(r"icon\Adminisrtator.ico")
        self.uacChk.setIcon(self.iconAdmin)
        uac_layout.addWidget(self.uacChk)
        imports_layout.addLayout(uac_layout)

        
        key_layout = QHBoxLayout()
        self.keyLine = QLineEdit()
        key_layout.addWidget(QLabel(self.lang_manager.tr("encryption_key", "مفتاح التشفير")))
        key_layout.addWidget(self.keyLine)
        imports_layout.addLayout(key_layout)
        imports_group.setLayout(imports_layout)
        layout.addWidget(imports_group)
        
        build_control = QGroupBox(self.lang_manager.tr("build_control", "التحكم في البناء"))
        build_layout = QVBoxLayout()
        build_buttons = QHBoxLayout()
        self.buildBtn = QPushButton(self.lang_manager.tr("start_build_button", "بدء البناء"))
        if self.shield_icon and os.path.isfile(self.shield_icon):
            self.buildBtn.setIcon(QIcon(self.shield_icon))
        self.buildBtn.clicked.connect(self.start_build)
        self.cancelBtn = QPushButton(self.lang_manager.tr("cancel", "إلغاء"))
        self.cancelBtn.setEnabled(False)
        self.cancelBtn.clicked.connect(self.cancel_build)
        build_buttons.addWidget(self.buildBtn)
        build_buttons.addWidget(self.cancelBtn)
        build_layout.addLayout(build_buttons)
        
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        build_layout.addWidget(self.progressBar)
        
        system_layout = QHBoxLayout()
        self.sysUsageLabel = QLabel("CPU: -%  RAM: -%  Disk: -%  GPU: -%")
        self.runAfterChk = QCheckBox(self.lang_manager.tr("run_after", "تشغيل الناتج بعد البناء"))
        system_layout.addWidget(self.sysUsageLabel)
        system_layout.addWidget(self.runAfterChk)
        build_layout.addLayout(system_layout)
        build_control.setLayout(build_layout)
        layout.addWidget(build_control)
        
        logs_tab = QTabWidget()
        
        cmd_tab = QWidget()
        cmd_layout = QVBoxLayout(cmd_tab)
        self.cmdPreview = QPlainTextEdit()
        self.cmdPreview.setReadOnly(True)
        self.cmdPreview.setPlaceholderText(self.lang_manager.tr("command_placeholder", "معاينة أوامر البناء ستظهر هنا…"))
        cmd_layout.addWidget(QLabel(self.lang_manager.tr("command_preview", "معاينة الأوامر")))
        cmd_layout.addWidget(self.cmdPreview)
        logs_tab.addTab(cmd_tab, self.lang_manager.tr("command_preview", "معاينة الأوامر"))
        
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText(self.lang_manager.tr("log_placeholder", "سجل عملية البناء…"))
        log_layout.addWidget(QLabel(self.lang_manager.tr("build_log", "سجل البناء")))
        log_layout.addWidget(self.log)
        logs_tab.addTab(log_tab, self.lang_manager.tr("build_log", "سجل البناء:"))
        
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        self.reportText = QPlainTextEdit()
        self.reportText.setReadOnly(True)
        self.reportText.setPlaceholderText(self.lang_manager.tr("report_placeholder", "تقرير البناء سيظهر هنا…"))
        report_layout.addWidget(QLabel(self.lang_manager.tr("build_report", "تقرير البناء")))
        report_layout.addWidget(self.reportText)
        logs_tab.addTab(report_tab, self.lang_manager.tr("build_report", "التقارير"))
        
        class SysInfoWidget(QWidget):
            def __init__(self, lang_manager, parent=None, max_points=120, interval_ms=500):
                super().__init__(parent)

                self.lang_manager = lang_manager
                self.max_points = max_points
                self.interval_ms = interval_ms

                layout = QVBoxLayout(self)

                ctrl_layout = QHBoxLayout()
                self.pauseBtn = QPushButton(self.lang_manager.tr("pause", "إيقاف"))
                self.clearBtn = QPushButton(self.lang_manager.tr("clear", "مسح"))
                self.toggleViewBtn = QPushButton(self.lang_manager.tr("toggle_view", "تبديل العرض"))

                ctrl_layout.addWidget(self.pauseBtn)
                ctrl_layout.addWidget(self.clearBtn)
                ctrl_layout.addWidget(self.toggleViewBtn)
                ctrl_layout.addStretch(1)
                layout.addLayout(ctrl_layout)

                self.fig = Figure(figsize=(6, 3))
                self.canvas = FigureCanvas(self.fig)
                layout.addWidget(self.canvas)

                self._text_mode = False
                self.textView = QPlainTextEdit()
                self.textView.setReadOnly(True)
                self.textView.setPlaceholderText(self.lang_manager.tr("text_view_placeholder", "عرض نصي لمؤشرات النظام سيظهر هنا…"))
                layout.addWidget(self.textView)
                self.textView.hide()

                self.ax = self.fig.add_subplot(111)
                self.ax.set_title("")
                self.ax.set_xlabel("")
                self.ax.set_ylabel("")
                self.ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)

                self.xdata = deque(maxlen=self.max_points)
                self.cpu_data = deque(maxlen=self.max_points)
                self.ram_data = deque(maxlen=self.max_points)
                self.disk_data = deque(maxlen=self.max_points)
                self.gpu_data = deque(maxlen=self.max_points)
                self.wave_data = deque(maxlen=self.max_points)

                self.line_cpu, = self.ax.plot([], [], label="CPU %", color="tab:blue")
                self.line_ram, = self.ax.plot([], [], label="RAM %", color="tab:green")
                self.line_disk, = self.ax.plot([], [], label="Disk %", color="tab:orange")
                self.line_gpu, = self.ax.plot([], [], label="GPU %", color="tab:purple")
                self.line_wave, = self.ax.plot([], [], label="Test", color="tab:red", linestyle=":")

                self.ax.legend(loc="upper right", fontsize="small")

                self._running = True
                self._start_time = time.time()
                self._count = 0

                self.pauseBtn.clicked.connect(self._toggle_running)
                self.clearBtn.clicked.connect(self._clear_data)
                self.toggleViewBtn.clicked.connect(self._toggle_view)

                self.timer = QTimer(self)
                self.timer.setInterval(self.interval_ms)
                self.timer.timeout.connect(self._update)
                self.timer.start()

                self._text_view_timer = QTimer(self)
                self._text_view_timer.setInterval(self.interval_ms)
                self._text_view_timer.timeout.connect(self._update_text_view)
                self._text_view_timer.start()


            def _toggle_running(self):
                self._running = not self._running
                if self._running:
                    self.pauseBtn.setText(self.lang_manager.tr("pause", "إيقاف"))
                else:
                    self.pauseBtn.setText(self.lang_manager.tr("resume", "استئناف"))

            def _clear_data(self):
                self.xdata.clear()
                self.cpu_data.clear()
                self.ram_data.clear()
                self.disk_data.clear()
                self.gpu_data.clear()
                self.wave_data.clear()
                self._count = 0
                self._redraw()
                self._update_text_view()

            def _toggle_view(self):
                self._text_mode = not self._text_mode
                if self._text_mode:
                    self.canvas.hide()
                    self.textView.show()
                    self.toggleViewBtn.setText(self.lang_manager.tr("graph_view", "عرض بياني"))
                    self._update_text_view()
                else:
                    self.textView.hide()
                    self.canvas.show()
                    self.toggleViewBtn.setText(self.lang_manager.tr("text_view", "عرض نصي"))
                    self._redraw()


            def _safe_disk_usage_percent(self):
                try:
                    parent = self.parent()
                    path = os.sep
                    if parent is not None and hasattr(parent, "outLine"):
                        path = (parent.outLine.text().strip() or os.sep)
                    if not os.path.exists(path):
                        path = os.sep
                    if psutil:
                        du = psutil.disk_usage(path)
                        return float(du.percent)
                except Exception:
                    pass
                try:
                    if psutil:
                        return float(psutil.disk_usage(os.sep).percent)
                except Exception:
                    pass
                return 0.0

            def _sample_system(self):
                cpu = ram = disk = gpu = 0.0
                try:
                    if psutil:
                        cpu = psutil.cpu_percent(interval=None)
                        ram = psutil.virtual_memory().percent
                        disk = self._safe_disk_usage_percent()
                except Exception:
                    pass
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = max((g.load or 0.0) * 100.0 for g in gpus)
                except Exception:
                    pass
                return cpu, ram, disk, gpu

            def _update(self):
                if not self._running:
                    return
                cpu, ram, disk, gpu = self._sample_system()
                self._count += 1
                t = time.time() - self._start_time
                self.xdata.append(self._count)
                self.cpu_data.append(cpu)
                self.ram_data.append(ram)
                self.disk_data.append(disk)
                self.gpu_data.append(gpu)
                freq = 0.5
                wave = 50.0 * (1.0 + np.sin(2 * np.pi * freq * t))
                self.wave_data.append(wave)
                self._redraw()


            def _redraw(self):
                if not self.xdata:
                    return

                x = list(self.xdata)
                self.line_cpu.set_data(x, list(self.cpu_data))
                self.line_ram.set_data(x, list(self.ram_data))
                self.line_disk.set_data(x, list(self.disk_data))
                self.line_gpu.set_data(x, list(self.gpu_data))
                self.line_wave.set_data(x, list(self.wave_data))

                if x:
                    self.ax.set_xlim(max(0, x[0]), x[-1] + 1)

                all_vals = list(self.cpu_data) + list(self.ram_data) + list(self.disk_data) + list(self.gpu_data) + list(self.wave_data)
                if all_vals:
                    ymin = max(0, min(all_vals) - 5)
                    ymax = min(100, max(all_vals) + 5)
                    if ymin == ymax:
                        ymin = max(0, ymin - 1)
                        ymax = min(100, ymax + 1)
                    self.ax.set_ylim(ymin, ymax)

                self.fig.tight_layout()
                self.canvas.draw_idle()


            def _update_text_view(self):
                if not self._text_mode:
                    return

                try:
                    n = len(self.xdata)
                    lines = []
                    lines.append(f"ITEMS {n}  | End Update {time.strftime('%Y-%m-%d %H:%M:%S')}")

                    bar_width = 30
                    def make_bar(pct):
                        try:
                            p = max(0.0, min(100.0, float(pct)))
                        except Exception:
                            p = 0.0
                        filled = int(round((p / 100.0) * bar_width))
                        return "█" * filled + "░" * (bar_width - filled) + f" {p:5.1f}%"

                    if n > 0:
                        lines.append("Current Values")
                        cpu = self.cpu_data[-1] if self.cpu_data else 0.0
                        ram = self.ram_data[-1] if self.ram_data else 0.0
                        disk = self.disk_data[-1] if self.disk_data else 0.0
                        gpu = self.gpu_data[-1] if self.gpu_data else 0.0

                        lines.append(f"CPU:  {make_bar(cpu)}")
                        lines.append(f"RAM:  {make_bar(ram)}")
                        lines.append(f"DISK: {make_bar(disk)}")
                        lines.append(f"GPU:  {make_bar(gpu)}")
                    else:
                        lines.append("No data yet.")

                    last = min(1, n)
                    if last > 0:
                        lines.append(f"Last {last} samples")
                        start = max(0, n - last)
                        for idx, i in enumerate(range(start, n), start=1):
                            cpu = self.cpu_data[i] if i < len(self.cpu_data) else 0.0
                            ram = self.ram_data[i] if i < len(self.ram_data) else 0.0
                            disk = self.disk_data[i] if i < len(self.disk_data) else 0.0
                            gpu = self.gpu_data[i] if i < len(self.gpu_data) else 0.0
                            
                            lines.append(f"Sample {idx}:")
                            lines.append(f"  CPU:  {cpu:5.1f}%")
                            lines.append(f"  RAM:  {ram:5.1f}%")
                            lines.append(f"  DISK: {disk:5.1f}%")
                            lines.append(f"  GPU:  {gpu:5.1f}%")
                    else:
                        lines.append("No data yet.")

                    text = "\n".join(lines)
                    self.textView.setPlainText(text)
                    self.textView.verticalScrollBar().setValue(self.textView.verticalScrollBar().maximum())

                    try:
                        out_dir = None
                        try:
                            app_win = QApplication.instance().activeWindow()
                            if app_win is None:
                                app_win = self.parent() or (QApplication.instance().topLevelWidgets()[0] if QApplication.instance().topLevelWidgets() else None)
                            if app_win is not None and hasattr(app_win, "outLine"):
                                candidate = app_win.outLine.text().strip()
                                if candidate:
                                    out_dir = candidate
                        except Exception:
                            out_dir = None

                        if not out_dir:
                            out_dir = os.getcwd()
                        os.makedirs(out_dir, exist_ok=True)
                        fp = os.path.join(out_dir, "InfoItems.txt")
                        with open(fp, "w", encoding="utf-8") as fh:
                            fh.write(text)
                    except Exception:
                        pass

                except Exception as e:
                    self.textView.setPlainText(f"Error updating text display: {str(e)}")
                    logs_tab.addTab(SysInfoWidget(self.lang_manager, self), self.lang_manager.tr("sysinfo_tab", "معلومات النظام"))
        sysinfo_tab = SysInfoWidget(self.lang_manager, self)
        logs_tab.addTab(sysinfo_tab, self.lang_manager.tr("sysinfo_tab", "معلومات النظام"))
        layout.addWidget(logs_tab)

        action_buttons = QHBoxLayout()
        self.saveLogBtn = QPushButton(self.lang_manager.tr("save_log", "حفظ السجل"))
        self.saveLogBtn.clicked.connect(self.save_log_to_file)
        self.openDistBtn = QPushButton(self.lang_manager.tr("open_output_folder", "فتح مجلد الإخراج"))
        self.openDistBtn.clicked.connect(self.open_output_folder)
        self.openBuildBtn = QPushButton(self.lang_manager.tr("open_build_folder", "فتح مجلد build"))
        self.openBuildBtn.clicked.connect(self.open_build_folder)
        self.testOutputBtn = QPushButton(self.lang_manager.tr("test_output", "اختبار الناتج"))
        self.testOutputBtn.clicked.connect(self.test_output)
        action_buttons.addWidget(self.saveLogBtn)
        action_buttons.addWidget(self.openDistBtn)
        action_buttons.addWidget(self.openBuildBtn)
        action_buttons.addWidget(self.testOutputBtn)
        layout.addLayout(action_buttons)

    def pick_certificate(self):
        path, _ = QFileDialog.getOpenFileName(self, self.lang_manager.tr("pick_certificate", "اختيار شهادة التوقيع"), "", "Certificate Files (*.pfx *.p12)")
        if path:
            self.certFileEdit.setText(os.path.abspath(path))

    def test_output(self):
        output_dir = self.outLine.text().strip() or os.path.abspath("output")
        if not os.path.isdir(output_dir):
            QMessageBox.warning(self, self.lang_manager.tr("test_output", "اختبار"), self.lang_manager.tr("output_folder_not_found", "مجلد الإخراج غير موجود."))
            return
        
        exe_files = []
        for file in os.listdir(output_dir):
            if file.endswith(".exe") or (os.name != "nt" and os.access(os.path.join(output_dir, file), os.X_OK)):
                exe_files.append(file)
        
        if not exe_files:
            QMessageBox.warning(self, self.lang_manager.tr("test_output", "اختبار"), self.lang_manager.tr("no_executable_files_found", "لم يتم العثور على ملفات قابلة للتنفيذ."))
            return
        
        if len(exe_files) == 1:
            exe_path = os.path.join(output_dir, exe_files[0])
            self.run_executable(exe_path)
        else:
            file, ok = QInputDialog.getItem(self, self.lang_manager.tr("select_file_for_testing", "اختيار ملف للاختبار"), self.lang_manager.tr("choose_file_for_testing", "اختر الملف للاختبار:"), exe_files, 0, False)
            if ok and file:
                exe_path = os.path.join(output_dir, file)
                self.run_executable(exe_path)

    def run_executable(self, exe_path):
        try:
            if os.name == "nt":
                os.startfile(exe_path)
            else:
                subprocess.Popen([exe_path])
            self._append_log(f"[TEST] تم تشغيل الملف للاختبار: {exe_path}")
        except Exception as e:
            QMessageBox.warning(self, self.lang_manager.tr("test_output", "اختبار"), self.lang_manager.tr("failed_to_run_file", f"فشل تشغيل الملف: {e}"))

    def manage_plugins(self):
        QMessageBox.information(self, self.lang_manager.tr("plugins", "الإضافات"), self.lang_manager.tr("plugins_info", "نظام الإضافات مفعل. ضع ملفات الإضافات في مجلد 'plugins'"))

    def manage_templates(self):
        QMessageBox.information(self, self.lang_manager.tr("templates", "القوالب"), self.lang_manager.tr("templates_info", "يمكنك اختيار قالب من القائمة المنسدلة في علامة التبويب المتقدم"))

    def show_documentation(self):
        webbrowser.open("https://github.com/wsl-iq/Python-Executable/wiki")

    def VistWebSite(self):
        webbrowser.open("https://wsl-iq.github.io/")

    def WebSiteProgram(self):
        webbrowser.open("https://wsl-iq.github.io/Python-Executable/")

    def about_program(self):
        about_text = self.lang_manager.tr("about_program_text")
        QMessageBox.about(self, self.lang_manager.tr("about_program", "حول البرنامج"), about_text)

    def Privacy_Policy(self):
        Privacy_Policy_txt = self.lang_manager.tr("privacy_policy_text")
        QMessageBox.about(self, self.lang_manager.tr("privacy_policy", "سياسة الخصوصية"), Privacy_Policy_txt)


    def Terms_of_Use(self):
        Terms_of_Use_txt = self.lang_manager.tr("terms_of_use_text")
        QMessageBox.about(self, self.lang_manager.tr("terms_of_use", "سياسة الأستخدام"), Terms_of_Use_txt)

    def License_Agreement(self):
        License_Agreement_txt = self.lang_manager.tr("license_agreement_text")
        QMessageBox.about(self, self.lang_manager.tr("license_agreement", "أتفاقية الترخيص"), License_Agreement_txt)

    def Code_of_Conduct(self):
        Code_of_Conduct_txt = self.lang_manager.tr("code_of_conduct_text")
        QMessageBox.about(self, self.lang_manager.tr("code_of_conduct", "قواعد السلوك"), Code_of_Conduct_txt)

    def Contribution_Policy(self):
        Contribution_Policy_txt = self.lang_manager.tr("contribution_policy_text")
        QMessageBox.about(self, self.lang_manager.tr("contribution_policy", "سياسة المساهمة"), Contribution_Policy_txt)
    
    def check_pyinstaller_updates(self):
        try:
            import urllib.request, urllib.error, re
            raw_url = "https://api.github.com/repos/pyinstaller/pyinstaller/releases/latest"
            
            with urllib.request.urlopen(raw_url, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                remote_ver = data.get("tag_name", "").lstrip("v")
            
            if not remote_ver:
                raise ValueError(self.lang_manager.tr("invalid_remote_version", "لم يتم العثور على إصدار صالح"))
        except Exception as e:
            QMessageBox.warning(self, self.lang_manager.tr("check_failed", "فشل التحقق"), 
                              self.lang_manager.tr("failed_to_check_pyinstaller", f"تعذّر التحقق من تحديثات PyInstaller:\n{e}"))
            return

        try:
            result = subprocess.check_output(["pip", "show", "pyinstaller"], stderr=subprocess.DEVNULL)
            for line in result.decode("utf-8").splitlines():
                if line.startswith("Version:"):
                    local_ver = line.split(":", 1)[1].strip()
                    break
            else:
                local_ver = "0.0.0"
        except Exception:
            local_ver = "0.0.0"

        def parse_version(v: str):
            parts = re.findall(r"\d+", v)
            return tuple(int(p) for p in parts) if parts else (0,)

        try:
            rv = parse_version(remote_ver)
            lv = parse_version(local_ver)
        except Exception:
            QMessageBox.information(self, self.lang_manager.tr("check_updates", "تحقق من التحديثات"), 
                                  self.lang_manager.tr("failed_to_parse_versions", "تعذّر تحليل أرقام الإصدارات"))
            return

        if rv > lv:
            msg = f"يتوفر تحديث جديد لـ PyInstaller.\nالإصدار المثبت: {local_ver}\nالإصدار المتاح: {remote_ver}\n\nهل ترغب بتحديث PyInstaller الآن؟"
            if QMessageBox.question(self, self.lang_manager.tr("update_available", "تحديث متاح"), msg, 
                                   QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                try:
                    subprocess.check_call(["pip", "install", "--upgrade", "pyinstaller"])
                    QMessageBox.information(self, self.lang_manager.tr("done", "تم"), 
                                          self.lang_manager.tr("pyinstaller_updated", "تم تحديث PyInstaller بنجاح"))
                except Exception as e:
                    QMessageBox.warning(self, self.lang_manager.tr("failed", "فشل"), 
                                      self.lang_manager.tr("update_failed", f"فشل التحديث: {e}"))
        else:
            QMessageBox.information(self, self.lang_manager.tr("check_updates", "تحقق من التحديثات"), 
                                  self.lang_manager.tr("pyinstaller_up_to_date", f"PyInstaller محدث: {local_ver}"))
        

    def set_theme(self, theme):
        self.settings["theme"] = theme
        self.apply_theme()
        self.SaveSettings()

    def apply_dark_theme(self):
        app = QApplication.instance()
        try:
            app.setStyle("Fusion")
        except Exception:
            pass
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 48))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 48))
        palette.setColor(QPalette.ToolTipBase, QColor(60, 60, 60))
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(60, 60, 60))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(150, 150, 150))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(150, 150, 150))
        app.setPalette(palette)

    def apply_light_theme(self):
        app = QApplication.instance()
        app.setPalette(QApplication.style().standardPalette())

    def apply_theme(self):
        if self.settings.get("theme", "light") == "dark":
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def toggle_theme(self):
        if self.settings.get("theme", "light") == "light":
            self.settings["theme"] = "dark"
        else:
            self.settings["theme"] = "light"
        self.apply_theme()
        self.SaveSettings()

    def choose_custom_theme(self):
        color = QColorDialog.getColor()
        if color.isValid():
            app = QApplication.instance()
            r, g, b = color.red(), color.green(), color.blue()
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            contrast_text = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
            base = color
            base_light = color.lighter(120)   
            base_lighter = color.lighter(140)
            base_dark = color.darker(110)    
            base_darker = color.darker(150)
            highlight = base_dark
            link = base_lighter
            palette = QPalette()
            palette.setColor(QPalette.Window, base)
            palette.setColor(QPalette.WindowText, contrast_text)
            palette.setColor(QPalette.Base, base_light)
            palette.setColor(QPalette.AlternateBase, base_darker)
            palette.setColor(QPalette.ToolTipBase, base_lighter)
            palette.setColor(QPalette.ToolTipText, contrast_text)
            palette.setColor(QPalette.Text, contrast_text)
            palette.setColor(QPalette.Button, base_dark)
            palette.setColor(QPalette.ButtonText, contrast_text)
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Link, link)
            palette.setColor(QPalette.Highlight, highlight)
            palette.setColor(QPalette.HighlightedText, contrast_text)
            disabled_text = QColor(contrast_text)
            disabled_text.setAlpha(140)
            palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
            palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
            app.setPalette(palette)
            self.settings["theme"] = "custom"
            self.SaveSettings()
            self.settings["custom_color"] = {"r": r, "g": g, "b": b}
            self.SaveSettings()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.foldersList.addItem(os.path.abspath(path))
            elif path.lower().endswith(".py"):
                if self.modeCombo.currentIndex() == 0:
                    self.entryLine.setText(os.path.abspath(path))
                else:
                    self.entryList.addItem(os.path.abspath(path))
            elif path.lower().endswith(".ico"):
                self.iconLine.setText(os.path.abspath(path))
            elif path.lower().endswith(".pfx") or path.lower().endswith(".p12"):
                self.certFileEdit.setText(os.path.abspath(path))
        self.SaveSettings()

    def _on_mode_changed(self, idx: int):
        single = idx == 0
        self.entryLine.setEnabled(single)
        self.entryBtn.setEnabled(single)
        self.entryList.setEnabled(not single)
        self.addEntryBtn.setEnabled(not single)
        self.remEntryBtn.setEnabled(not single)

    def pick_entry(self):
        path, _ = QFileDialog.getOpenFileName(self, self.lang_manager.tr("pick_main_file", "اختيار الملف الرئيسي"), "", "Python (*.py)")
        if path:
            self.entryLine.setText(os.path.abspath(path))

    def add_entry(self):
        paths, _ = QFileDialog.getOpenFileNames(self, self.lang_manager.tr("pick_scripts", "اختيار سكربتات"), "", "Python (*.py)")
        for p in paths:
            if p:
                self.entryList.addItem(os.path.abspath(p))

    def remove_entry(self):
        for item in self.entryList.selectedItems():
            self.entryList.takeItem(self.entryList.row(item))

    def add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, self.lang_manager.tr("pick_resource_files", "اختيار ملفات موارد"), "", "All Files (*.*)")
        for p in paths:
            if p:
                self.filesList.addItem(os.path.abspath(p))
                
    def __RestoreMinimize__(self):
        if self.filesList.maximumHeight() <= 150:
            self.filesList.setMaximumHeight(400) 
            self.filesList.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.chaning.setText(self.lang_manager.tr("shrink_files_list", "تصغير قائمة الملفات"))
        else:
            self.filesList.setMaximumHeight(150)
            self.filesList.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.chaning.setText(self.lang_manager.tr("expand_files_list", "تكبير قائمة الملفات"))
    def remove_file(self):
        for item in self.filesList.selectedItems():
            self.filesList.takeItem(self.filesList.row(item))

    def add_folder(self):
        path = QFileDialog.getExistingDirectory(self, self.lang_manager.tr("pick_resource_folder", "اختيار مجلد موارد"))
        if path:
            self.foldersList.addItem(os.path.abspath(path))

    def remove_folder(self):
        for item in self.foldersList.selectedItems():
            self.foldersList.takeItem(self.foldersList.row(item))

    def pick_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, self.lang_manager.tr("choose_icon", "اختيار أيقونة"), "", "Icon (*.ico)")
        if path:
            self.iconLine.setText(os.path.abspath(path))

    def pick_manifest(self):
        path, _ = QFileDialog.getOpenFileName(self, self.lang_manager.tr("choose_manifest", "اختيار Manifest"), "", "Manifest (*.manifest)")
        if path:
            self.manifestLine.setText(os.path.abspath(path))

    def pick_output(self):
        path = QFileDialog.getExistingDirectory(self, self.lang_manager.tr("pick_output", "اختيار مجلد الإخراج"))
        if path:
            self.outLine.setText(os.path.abspath(path))

    def _collect_entries(self) -> List[str]:
        if self.modeCombo.currentIndex() == 0:
            e = self.entryLine.text().strip()
            return [e] if e else []
        else:
            return [self.entryList.item(i).text() for i in range(self.entryList.count())]

    def _build_add_data_args(self) -> List[str]:
        args = []
        for i in range(self.filesList.count()):
            src = self.filesList.item(i).text()
            dest = os.path.basename(src)
            spec = f"{src}{PATHSEP}{dest}"
            args.extend(["--add-data", spec])
        for i in range(self.foldersList.count()):
            src = self.foldersList.item(i).text()
            dest = os.path.basename(os.path.normpath(src))
            spec = f"{src}{PATHSEP}{dest}"
            args.extend(["--add-data", spec])
        return args

    def _make_commands(self, generate_spec_only=False) -> List[List[str]]:
        entries = self._collect_entries()
        outdir = self.outLine.text().strip() or os.path.abspath("output")
        os.makedirs(outdir, exist_ok=True)

        base_args = ["pyinstaller", "--distpath", outdir]
        if self.cleanChk.isChecked():
            base_args.append("--clean")
        if self.oneFileChk.isChecked():
            base_args.append("-F")
        if not self.consoleChk.isChecked():
            base_args.append("--noconsole")

        icon = self.iconLine.text().strip()
        if icon:
            base_args.extend(["--icon", icon])

        manifest = self.manifestLine.text().strip()
        if manifest:
            base_args.extend(["--manifest", manifest])

        base_args.extend(self._build_add_data_args())

        hidden = [s.strip() for s in self.hiddenImportsLine.text().split(",") if s.strip()]
        excl = [s.strip() for s in self.excludeModulesLine.text().split(",") if s.strip()]
        if hidden:
            for h in hidden:
                base_args.extend(["--hidden-import", h])
        if excl:
            for e in excl:
                base_args.extend(["--exclude-module", e])
        if self.uacChk.isChecked():
            base_args.append("--uac-admin")
        key = self.keyLine.text().strip()
        if key:
            base_args.extend(["--key", key])

        if self.optimizeChk.isChecked():
            base_args.append("--optimize")
        if self.stripChk.isChecked():
            base_args.append("--strip")
        if self.noPreferRedirectChk.isChecked():
            base_args.append("--no-prefer-redirect")

        cmds = []
        for e in entries:
            if not os.path.isfile(e):
                continue
            if generate_spec_only:
                cmd = ["pyi-makespec"] + base_args[1:] + [e]
            else:
                cmd = base_args + [e]
            cmds.append(cmd)
        return cmds

    def start_build(self):
        self.SaveSettings()

        python_exec = self.interpCombo.currentText().strip() or None
        if python_exec:
            if not shutil.which(os.path.basename(python_exec)) and not os.path.isfile(python_exec):
                if QMessageBox.question(self, self.lang_manager.tr("python_interpreter", "مفسّر Python"), f"{self.lang_manager.tr("interpreter_not_found", "المسار المحدد للمفسر غير موجود")}:\n{python_exec}\n\n{self.lang_manager.tr("continue_with_system_interpreter", "هل تريد المتابعة مع مفسر النظام؟")}", QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
                    return
                python_exec = None

        if shutil.which("pyinstaller") is None:
            QMessageBox.critical(self, self.lang_manager.tr("pyinstaller_not_found", "PyInstaller غير موجود"), self.lang_manager.tr("install_pyinstaller", "تعذر العثور على PyInstaller. ثبّت الحزمة بالأمر:\n\n    pip install pyinstaller\n\nثم أعد المحاولة."))
            return

        cmds = self._make_commands(generate_spec_only=False)
        if not cmds:
            QMessageBox.warning(self, self.lang_manager.tr("no_inputs", "لا يوجد مدخلات"), self.lang_manager.tr("specify_main_script_or_add_scripts_in_batch_mode", "حدّد سكربت رئيسي أو أضف سكربتات في وضع Batch."))
            return

        missing = []
        for c in cmds:
            entry = c[-1]
            if not os.path.isfile(entry):
                missing.append(entry)
        if missing:
            QMessageBox.warning(self, self.lang_manager.tr("missing_files", "ملفات مفقودة"), self.lang_manager.tr("the_following_files_are_missing", "الملفات التالية غير موجودة:\n") + "\n".join(missing))
            return

        preview = "\n\n".join(" ".join(map(quote, c)) for c in cmds)
        self.cmdPreview.setPlainText(preview)
        self.buildBtn.setEnabled(False)
        self.cancelBtn.setEnabled(True)
        self.log.clear()        
        self.thread = QThread()
        self.worker = BuildWorker(commands=cmds, cwd=os.getcwd(), python_exec=python_exec, run_after=self.runAfterChk.isChecked())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.line.connect(self._append_log)
        self.worker.progress.connect(self._set_progress)
        self.worker.cpu_mem.connect(self._on_cpu_mem)
        self.worker.done.connect(self._build_finished)
        self.thread.start()        
        self.progressBar.setRange(0, 0)
        self._indeterminate = True

    def cancel_build(self):
        if self.worker:
            self.worker.stop()
        self.buildBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self._indeterminate = False
        self._append_log("[INFO] Build cancelled by user.")

    def _append_log(self, text: str):
        self.log.appendPlainText(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"{time.ctime()} {text}\n")
        except Exception:
            pass

    def _set_progress(self, value: int):
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(value)
        self._indeterminate = False

    def _get_disk_usage(self) -> float:
        try:
            path = (self.outLine.text().strip() or os.sep)
            if not os.path.exists(path):
                path = os.sep
            du = psutil.disk_usage(path)
            return float(du.percent)
        except Exception:
            try:
                return float(psutil.disk_usage(os.sep).percent)
            except Exception:
                return 0.0

    def _get_gpu_usage(self) -> float:
        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                return 0.0
            return max((gpu.load or 0.0) * 100.0 for gpu in gpus)
        except Exception:
            pass
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL
            )
            lines = [l.strip() for l in out.decode(errors="ignore").splitlines() if l.strip()]
            if lines:
                vals = [float(l) for l in lines if l.replace('.', '', 1).isdigit()]
                if vals:
                    return max(vals)
        except Exception:
            pass
        return 0.0

    def _on_cpu_mem(self, cpu: float, mem: float):
        disk = self._get_disk_usage() if psutil else 0.0
        gpu = self._get_gpu_usage()
        try:
            self.sysUsageLabel.setText(f"CPU: {cpu:.0f}%  RAM: {mem:.0f}%  Disk: {disk:.0f}%  GPU: {gpu:.0f}%")
        except Exception:
            self.sysUsageLabel.setText(f"CPU: {cpu:.0f}%  RAM: {mem:.0f}%  Disk: {disk:.0f}%  GPU: {gpu:.0f}%")
            self._update_sys_usage_graph(cpu, mem, disk, gpu)
            if not self._indeterminate:
                self.progressBar.setRange(0, 100)
                self.progressBar.setValue(0)
                self._indeterminate = False
                self._update_sys_usage_graph(cpu, mem, disk, gpu)
                self.__UpdateSysLabelUsing__()
                self.progressBar.setRange(0, 100)
                self.progressBar.setValue(0)
                self._indeterminate = False

    def __UpdateSysLabelUsing__(self):
        if not psutil:
            return
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            disk = self._get_disk_usage()
            gpu = self._get_gpu_usage()
            self.sysUsageLabel.setText(f"CPU: {cpu:.0f}%  RAM: {mem:.0f}%  Disk: {disk:.0f}%  GPU: {gpu:.0f}%")
        except Exception:
            pass

    def _build_finished(self, ok: bool):
        if self.thread:
            try:
                self.thread.quit()
                self.thread.wait()
            except Exception:
                pass
            self.thread = None
        self.worker = None
        self.buildBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)

        self._indeterminate = False
        self.progressBar.setRange(0, 100)
        target = 100 if ok else 0
        current = self.progressBar.value()

        if current != target:
            step_up = 2
            step_down = 5

            def _animate():
                try:
                    v = self.progressBar.value()
                except Exception:
                    return
                if v < target:
                    v = min(target, v + step_up)
                    self.progressBar.setValue(v)
                    if v < target:
                        QTimer.singleShot(10, _animate)
                elif v > target:
                    v = max(target, v - step_down)
                    self.progressBar.setValue(v)
                    if v > target:
                        QTimer.singleShot(10, _animate)

            QTimer.singleShot(0, _animate)
        else:
            self.progressBar.setValue(target)

            try:
                if os.name == "nt":
                    try:
                        winsound.MessageBeep()
                    except Exception:
                        pass
                else:
                    print("\a")
            except Exception:
                pass

        if ok:
            self._append_log("[SUCCESS] Done building without errors.")
            QMessageBox.information(self, self.lang_manager.tr("done", "تم"), self.lang_manager.tr("build_finished_without_errors", "انتهى البناء بدون أخطاء. الملفات داخل مجلد الإخراج المحدد."))
            try:
                notification.notify(
                    icon=r"icon\PyCLI.ico" if os.path.isfile(r"icon\PyCLI.ico") else None,
                    title="From Python to Executable",
                    message=self.lang_manager.tr("build_success_message", "تم الأنتهاء من عملية البناء بنجاح."),
                    timeout=10
                )
            except Exception:
                pass
            
            self.save_log_to_file(prompt=False)
            
            try:
                if os.name == "nt":
                    winsound.MessageBeep()
                else:
                    print("\a")
            except Exception:
                pass
            
            if QMessageBox.question(self, self.lang_manager.tr("open_output_folder", "فتح مجلد الإخراج"), self.lang_manager.tr("open_output_folder_now", "هل ترغب في فتح مجلد الإخراج الآن؟"), QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.open_output_folder()
        else:
            self._append_log("[WARN] Finished building with errors. Check the log.")
            QMessageBox.warning(self, self.lang_manager.tr("finished_with_issues", "انتهى مع مشاكل"), self.lang_manager.tr("check_log_for_error_details", "تحقق من السجل لمعرفة تفاصيل الخطأ."))
    def save_log_to_file(self, prompt=True):
        default = os.path.abspath("build Tools.txt")
        if prompt:
            path, _ = QFileDialog.getSaveFileName(self, self.lang_manager.tr("save_log", "حفظ السجل كملف"), default, "Text Files (*.txt)")
            if not path:
                return
        else:
            path = default
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log.toPlainText())
            QMessageBox.information(self, self.lang_manager.tr("save_log", "حفظ السجل"), self.lang_manager.tr("log_saved_to", "تم حفظ السجل في: ") + path)
        except Exception as e:
            QMessageBox.warning(self, self.lang_manager.tr("save_log", "حفظ السجل"), self.lang_manager.tr("failed_to_save_log", "فشل حفظ السجل: ") + str(e))

    def open_output_folder(self):
        outdir = self.outLine.text().strip() or os.path.abspath("output")
        if os.path.isdir(outdir):
            try:
                if os.name == "nt":
                    os.startfile(outdir)
                else:
                    subprocess.call(["xdg-open", outdir])
            except Exception as e:
                QMessageBox.warning(self, self.lang_manager.tr("open_folder", "فتح المجلد"), self.lang_manager.tr("failed_to_open_folder", "فشل فتح المجلد: ") + str(e))
        else:
            QMessageBox.warning(self, self.lang_manager.tr("output_folder_not_found", "مجلد الإخراج غير موجود"), self.lang_manager.tr("output_folder_not_found_details", "لم يتم العثور على مجلد الإخراج: ") + outdir)

    def open_build_folder(self):
        build_dir = os.path.join(os.getcwd(), "build")
        if os.path.isdir(build_dir):
            try:
                if os.name == "nt":
                    os.startfile(build_dir)
                else:
                    subprocess.call(["xdg-open", build_dir])
            except Exception as e:
                QMessageBox.warning(self, self.lang_manager.tr("open_folder", "فتح المجلد"), self.lang_manager.tr("failed_to_open_folder", "فشل فتح المجلد: ") + str(e))
        else:
            QMessageBox.warning(self, self.lang_manager.tr("build_folder_not_found", "مجلد build غير موجود"), self.lang_manager.tr("build_folder_not_found_details", "لم يتم العثور على مجلد build في: ") + build_dir)

    def clean_output_folder(self):
        outdir = self.outLine.text().strip() or os.path.abspath("output")
        if os.path.isdir(outdir):
            reply = QMessageBox.question(self, self.lang_manager.tr("delete_output_folder", "حذف مجلد الإخراج"), self.lang_manager.tr("confirm_delete_output_folder", f"هل تريد حذف المجلد:\n{outdir} ?"), QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    shutil.rmtree(outdir)
                    QMessageBox.information(self, self.lang_manager.tr("done", "تم"), self.lang_manager.tr("output_folder_deleted", "تم حذف مجلد الإخراج."))
                except Exception as e:
                    QMessageBox.warning(self, self.lang_manager.tr("failed", "فشل"), self.lang_manager.tr("failed_to_delete_output_folder", "فشل حذف المجلد: ") + str(e))
        else:
            QMessageBox.information(self, self.lang_manager.tr("not_found", "غير موجود"), self.lang_manager.tr("output_folder_not_found", "مجلد الإخراج غير موجود."))
    def full_clean(self):
        reply = QMessageBox.question(self, self.lang_manager.tr("full_clean", "تنظيف كامل"), self.lang_manager.tr("full_clean_confirmation", "سيتم حذف مجلدات build و dist وكل ملفات .spec في المجلد الحالي. هل تريد المتابعة؟"), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        for d in ("build", "dist"):
            if os.path.isdir(d):
                try:
                    shutil.rmtree(d)
                except Exception:
                    pass
        for f in os.listdir("."):
            if f.endswith(".spec"):
                try:
                    os.remove(f)
                except Exception:
                    pass
        QMessageBox.information(self, self.lang_manager.tr("done", "تم"), self.lang_manager.tr("full_clean_done", "تم التنظيف الكامل (إن وُجد شيء)."))

    def generate_spec_only(self):
        cmds = self._make_commands(generate_spec_only=True)
        if not cmds:
            QMessageBox.warning(self, self.lang_manager.tr("no_inputs", "لا يوجد مدخلات"), self.lang_manager.tr("no_inputs_details", "حدّد سكربت رئيسي أو أضف سكربتات في وضع Batch."))
            return
        preview = "\n\n".join(" ".join(map(quote, c)) for c in cmds)
        self.cmdPreview.setPlainText(preview)
        
        for cmd in cmds:
            try:
                subprocess.check_call(cmd, cwd=os.getcwd())
                self._append_log(f"[INFO] .spec generated using: {' '.join(cmd)}")
            except Exception as e:
                QMessageBox.warning(self, self.lang_manager.tr("generation_failed", "فشل التوليد"), self.lang_manager.tr("generation_failed_details", f"خلال توليد .spec حدث خطأ: {e}"))
                return
        QMessageBox.information(self, self.lang_manager.tr("done", "تم"), self.lang_manager.tr("spec_files_generated", "تم توليد ملفات .spec بنجاح."))
    def check_updates(self):
        raw_url = "https://raw.githubusercontent.com/wsl-iq/Python-Executable/main/version.txt"
        project_page = "https://github.com/wsl-iq/Python-Executable"
        releases_page = project_page + "/releases"
        try:
            import urllib.request, urllib.error, re
            with urllib.request.urlopen(raw_url, timeout=8) as resp:
                remote_txt = resp.read().decode("utf-8", errors="ignore")
            remote_ver = ""
            for line in remote_txt.splitlines():
                line = line.strip()
                if line:
                    remote_ver = line
                    break
            if not remote_ver:
                raise ValueError(self.lang_manager.tr("invalid_remote_version", "لم يتم العثور على إصدار صالح في الملف البعيد."))
        except Exception as e:
            QMessageBox.warning(self, self.lang_manager.tr("check_failed", "فشل التحقق"), self.lang_manager.tr("failed_to_access_remote_version_file", f"تعذّر الوصول إلى ملف الإصدار البعيد:\n{e}\nسيتم فتح صفحة المشروع."))
            webbrowser.open(project_page)
            return

        try:
            local_path = os.path.join(os.path.dirname(__file__), "version.txt")
        except Exception:
            local_path = "version.txt"
        local_ver = None
        try:
            if os.path.isfile(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            local_ver = line
                            break
        except Exception:
            local_ver = None

        if not local_ver:
            m = re.search(r"v?(\d+(?:\.\d+)+)", self.windowTitle())
            local_ver = m.group(1) if m else "0.0.0"

        def parse_version(v: str):
            parts = re.findall(r"\d+", v)
            return tuple(int(p) for p in parts) if parts else (0,)

        try:
            rv = parse_version(remote_ver)
            lv = parse_version(local_ver)
        except Exception:
            QMessageBox.information(self, self.lang_manager.tr("check_updates", "تحقق من التحديثات"), self.lang_manager.tr("failed_to_parse_versions", "تعذّر تحليل أرقام الإصدارات."))
            return

        if rv > lv:
            msg = f"يتوفر تحديث جديد.\nالإصدار الحالي: {local_ver}\nالإصدار المتاح: {remote_ver}\n\nهل ترغب بفتح صفحة الإصدارات لتحميل التحديث؟"
            if QMessageBox.question(self, self.lang_manager.tr("update_available", "تحديث متاح"), msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                webbrowser.open(releases_page)
        else:
            QMessageBox.information(self, self.lang_manager.tr("check_updates", "تحقق من التحديثات"), self.lang_manager.tr("up_to_date", f"أنت تستخدم أحدث إصدار: {local_ver}"))

    def about_dev(self):
        QMessageBox.information(self, self.lang_manager.tr("about_dev", "حول المطور"), self.lang_manager.tr("about_dev_details", "تم تطوير هذا البرنامج بواسطة محمد الباقر.\n\nمن شروط الترخيص عدم استخدام هذا البرنامج لأغراض ضارة أو غير قانونية."))

    def closeEvent(self, event):
        try:
            self.SaveSettings()
        except Exception:
            pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    StartTime = time.time()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"[START] {time.ctime()}\n")
    except Exception:
        pass

    try:
        main()
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
    finally:
        EndTime = time.time()
        duration = EndTime - StartTime
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write(f"[END] {time.ctime()} - Duration: {duration:.2f} seconds\n\n")
        except Exception:
            pass
        try:
            import platform
            text = (
                f"Platform: {platform.platform()}\n"
                f"Python: {platform.python_version()}\n"
                f"Time: {time.ctime()}\n"
                f"Duration: {duration:.2f} seconds\n"
                f"User: {os.getlogin()}\n"
                f"Working Directory: {os.getcwd()}\n"
                f"Executable Path: {sys.executable}\n"
                f"Script: {os.path.abspath(__file__)}\n"
                f"Error: {e}\n"
                f"Traceback: {traceback.format_exc()}\n"
                f"keyboard Interrupt: {isinstance(e, KeyboardInterrupt)}\n"
                f"System Exit: {isinstance(e, SystemExit)}\n"
                f"OS Name: {os.name}\n"
                
            )
            fp = os.path.join(os.getcwd(), "Report-info-System.txt")
            with open(fp, "w", encoding="utf-8") as fh:
                fh.write(text)
            try:
                with open(LOG_FILE, "a", encoding="utf-8") as log:
                    log.write(f"[INFO] Saved file in {fp}\n")
            except Exception:
                pass
        except Exception:
            pass
        def FileFixingBugs():
            try:
                text = (
                    f"Platform: {platform.platform()}\n"
                    f"Python: {platform.python_version()}\n"
                    f"Time: {time.ctime()}\n"
                    f"Duration: {duration:.2f} seconds\n"
                    f"User: {os.getlogin()}\n"
                    f"Working Directory: {os.getcwd()}\n"
                    f"Executable Path: {sys.executable}\n"
                    f"Script: {os.path.abspath(__file__)}\n"
                    f"Error: {e}\n"
                    f"Traceback: {traceback.format_exc()}\n"
                    f"keyboard Interrupt: {isinstance(e, KeyboardInterrupt)}\n"
                    f"System Exit: {isinstance(e, SystemExit)}\n"
                    
                )
                fix_dir = os.path.join(os.getcwd(), "FixBug")
                os.makedirs(fix_dir, exist_ok=True)
                fp = os.path.join(fix_dir, "FixingBugs.txt")
                with open(fp, "w", encoding="utf-8") as fh:
                    fh.write(text)
                try:
                    with open(LOG_FILE, "a", encoding="utf-8") as log:
                        log.write(f"Copyright Mohammed Al-Baqer\n\n[INFO] Saved file in {fp}\n")
                except Exception:
                    pass
            except Exception:
                pass
        FileFixingBugs()

if os.name == "nt":

    def __Win64Bit__():
        return struct.calcsize("P") * 8 == 8 and ctypes.sizeof(ctypes.c_voidp) == 8

    def __dll__(path):
        if hasattr(ctypes, "windll"):
            try:
                kernel32 = ctypes.windll.kernel32
                if hasattr(kernel32, "AddDllDirectory"):
                    kernel32.AddDllDirectory(ctypes.c_wchar_p(path))
                else:
                    kernel32.SetDllDirectoryW(ctypes.c_wchar_p(path))
            except Exception:
                pass

    current_dir = os.path.dirname(os.path.abspath(__file__))
    dll_dir = os.path.join(current_dir, ".dll", "x64" if __Win64Bit__() else "x86")

    os.makedirs(dll_dir, exist_ok=True)

    __dll__(dll_dir)

    try:
        src_file = os.path.abspath(__file__)
        dst_dll = os.path.join(dll_dir, "FromPythonApp.dll")

        shutil.copy2(src_file, dst_dll)

        with open(os.path.join(dll_dir, "Build.txt"), "a", encoding="utf-8") as log:
            log.write(f"[✓] DLL: {dst_dll}\n")
    except Exception as e:
        print(f"[X] DLL: {e}")   
        
        
        
# check_log_for_error_detail