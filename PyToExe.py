#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import shlex
import webbrowser
import shutil
import ctypes
import subprocess
import importlib
import importlib.util
import GPUtil
import winsound
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QCheckBox, QPlainTextEdit, QMessageBox, QLabel,
    QHBoxLayout, QVBoxLayout, QGroupBox, QComboBox, QProgressBar, QMenu, QAction,
    QTabWidget, QSpinBox, QDoubleSpinBox, QTextEdit, QSplitter, QInputDialog
)

try:
    import psutil
except Exception:
    psutil = None

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
        "description": ""
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

class PluginManager:
    def __init__(self, plugins_dir="plugins"):
        self.plugins_dir = plugins_dir
        self.plugins = {}
        os.makedirs(plugins_dir, exist_ok=True)
    
    def load_plugins(self):
        for file in os.listdir(self.plugins_dir):
            if file.endswith(".py") and not file.startswith("_"):
                try:
                    plugin_name = file[:-3]
                    spec = importlib.util.spec_from_file_location(plugin_name, os.path.join(self.plugins_dir, file))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.plugins[plugin_name] = module
                    print(f"[Plugin] تم تحميل الإضافة: {plugin_name}")
                except Exception as e:
                    print(f"[Plugin] فشل تحميل الإضافة {file}: {e}")
    
    def execute_hook(self, hook_name, *args, **kwargs):
        results = {}
        for name, plugin in self.plugins.items():
            if hasattr(plugin, hook_name):
                try:
                    result = getattr(plugin, hook_name)(*args, **kwargs)
                    results[name] = result
                except Exception as e:
                    print(f"[Plugin] فشل تنفيذ الهوك {hook_name} في {name}: {e}")
        return results

def quote(p: str) -> str:
    if not p:
        return p
    if os.name != "nt":
        return shlex.quote(p)
    if " " in p or "(" in p or ")" in p:
        return f'"{p}"'
    return p

def is_admin() -> bool:
    try:
        if os.name == "nt":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False

def find_python_interpreters() -> List[str]:
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
    
    virtual_envs = find_virtual_environments()
    candidates.extend(virtual_envs)
    
    return candidates

def find_virtual_environments() -> List[str]:
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

    def _emit_sys_usage(self):
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
                        self._emit_sys_usage()
                rc = p.wait()
                if rc != 0:
                    ok = False
                    self.line.emit(f"[ERROR] انتهت العملية برمز {rc}")
                    break
            except FileNotFoundError:
                ok = False
                self.line.emit("[ERROR] الأمر غير موجود")
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
                    self.line.emit(f"[INFO] تشغيل الملف الناتج: {exe_path}")
                    if os.name == "nt":
                        os.startfile(exe_path)
                    else:
                        subprocess.Popen([exe_path])
                else:
                    self.line.emit("[WARN] لم يتم العثور على الملف الناتج للتشغيل")
            except Exception as e:
                self.line.emit(f"[ERROR] فشل تشغيل الملف الناتج: {e}")
        
        self.done.emit(ok)

class PyInstallerExtras:
    def __init__(self, presets_dir="presets"):
        self.presets_dir = presets_dir
        os.makedirs(presets_dir, exist_ok=True)

    def analyze_missing_imports(self, script_path: str) -> List[str]:
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
            print(f"[Analyzer] فشل التحليل: {e}")
        finally:
            for d in ("build", "__pycache__"):
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
            spec_file = os.path.splitext(os.path.basename(script_path))[0] + ".spec"
            if os.path.isfile(spec_file):
                os.remove(spec_file)

        return list(missing)

    def advanced_dependency_analysis(self, script_path: str) -> Dict[str, Any]:
        analysis_result = {
            "missing_imports": [],
            "large_files": [],
            "suspicious_imports": [],
            "performance_issues": [],
            "recommendations": []
        }
        
        missing = self.analyze_missing_imports(script_path)
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

    def build_with_upx(self, cmd: List[str], upx_dir: str) -> List[str]:
        if upx_dir and os.path.isdir(upx_dir):
            cmd.extend(["--upx-dir", upx_dir])
        return cmd

    def save_preset(self, name: str, data: Dict) -> str:
        path = os.path.join(self.presets_dir, f"{name}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Preset] فشل حفظ الإعداد: {e}")
        return path

    def load_preset(self, name: str) -> Dict:
        path = os.path.join(self.presets_dir, f"{name}.json")
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"[Preset] فشل تحميل الإعداد: {e}")
            return {}

    def list_presets(self) -> List[str]:
        files = [f[:-5] for f in os.listdir(self.presets_dir) if f.endswith(".json")]
        return files

    def delete_preset(self, name: str):
        path = os.path.join(self.presets_dir, f"{name}.json")
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[Preset] فشل الحذف: {e}")

    def copy_to_clipboard(self, text: str):
        try:
            import ctypes
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
            print(f"[Clipboard] فشل النسخ: {e}")

def get_script_paths(ui) -> list:
    if ui.modeCombo.currentIndex() == 0:
        path = ui.entryLine.text().strip()
        return [path] if path else []
    else:
        return [ui.entryList.item(i).text() for i in range(ui.entryList.count())]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("From Python To Executable v3.0.0 (Arabic) © Mohammed Al-Baqer")
        self.resize(1200, 800)
        self.icon_path = r"icon\icon.png" if os.path.isfile(r"icon\icon.png") else None
        self.shield_icon = r"icon\Adminisrtator.ico" if os.path.isfile(r"icon\Adminisrtator.ico") else self.icon_path
        if self.icon_path:
            self.setWindowIcon(QIcon(self.icon_path))

        self.thread = None
        self.worker = None
        self.settings = {}
        self.plugin_manager = PluginManager(PLUGINS_DIR)
        self.load_settings()
        self.create_backup()

        self.create_menus()
        self.create_main_ui()
        self.setAcceptDrops(True)
        self._apply_settings_to_ui()
        self.ui_timer = QTimer()
        self.ui_timer.setInterval(1000)
        self.ui_timer.timeout.connect(self._update_sys_usage_label)
        self.ui_timer.start()
        self._indeterminate = False
        self.apply_theme()
        
        try:
            self.plugin_manager.load_plugins()
        except Exception as e:
            print(f"[Plugin] فشل تحميل الإضافات: {e}")

    def load_settings(self):
        if os.path.isfile(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = DEFAULT_SETTINGS.copy()
        else:
            self.settings = DEFAULT_SETTINGS.copy()

    def create_backup(self):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"settings_backup_{timestamp}.json")
        try:
            shutil.copy2(SETTINGS_FILE, backup_file)
        except Exception:
            pass

    def save_settings(self):
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

    def _apply_settings_to_ui(self):
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

    def reset_settings(self):
        reply = QMessageBox.question(self, "إعادة التعيين", "هل تريد إعادة الإعدادات إلى الوضع الافتراضي؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings = DEFAULT_SETTINGS.copy()
            try:
                if os.path.isfile(SETTINGS_FILE):
                    os.remove(SETTINGS_FILE)
            except Exception:
                pass
            self._apply_settings_to_ui()
            QMessageBox.information(self, "تم", "تمت إعادة التعيين للإعدادات الافتراضية.")

    def analyze_missing_modules(self):
        self.extra = PyInstallerExtras()
        script_paths = get_script_paths(self)

        if not script_paths:
            QMessageBox.warning(self, "تحليل", "رجاءً اختر ملف أو سكربتات أولاً.")
            return

        all_missing = []
        for script in script_paths:
            missing = self.extra.analyze_missing_imports(script)
            if missing:
                all_missing.extend(missing)

        if all_missing:
            QMessageBox.information(
                self,
                "نتائج التحليل",
                f"الموديولات المفقودة:\n{', '.join(set(all_missing))}"
            )
        else:
            QMessageBox.information(self, "نتائج التحليل", "لم يتم العثور على موديولات مفقودة.")

    def advanced_dependency_analysis(self):
        self.extra = PyInstallerExtras()
        script_paths = get_script_paths(self)

        if not script_paths:
            QMessageBox.warning(self, "تحليل", "رجاءً اختر ملف أو سكربتات أولاً.")
            return

        results = []
        for script in script_paths:
            analysis = self.extra.advanced_dependency_analysis(script)
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

    def generate_build_report(self, duration: float, output_path: str):
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

    def code_audit(self):
        script_paths = get_script_paths(self)
        if not script_paths:
            QMessageBox.warning(self, "التدقيق", "رجاءً اختر ملف أو سكربتات أولاً.")
            return

        audit_results = {
            "large_files": [],
            "suspicious_imports": [],
            "performance_issues": [],
            "security_issues": []
        }

        for script in script_paths:
            analysis = self.extra.advanced_dependency_analysis(script)
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

    def create_menus(self):
        menubar = self.menuBar()
        
        fileMenu = menubar.addMenu("الملف")
        action_new = QAction("مشروع جديد", self)
        action_new.setShortcut("Ctrl+N")
        fileMenu.addAction(action_new)
        
        action_reset = QAction("إعادة تعيين الإعدادات", self)
        action_reset.triggered.connect(self.reset_settings)
        fileMenu.addAction(action_reset)
        
        action_exit = QAction("خروج", self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.close)
        fileMenu.addAction(action_exit)

        buildMenu = menubar.addMenu("البناء")
        action_build = QAction("بدء البناء", self)
        action_build.setShortcut("Ctrl+B")
        action_build.triggered.connect(self.start_build)
        buildMenu.addAction(action_build)
        
        action_spec = QAction("توليد ملف .spec فقط", self)
        action_spec.triggered.connect(self.generate_spec_only)
        buildMenu.addAction(action_spec)

        toolsMenu = menubar.addMenu("أدوات")
        action_clean = QAction("تنظيف كامل (build, dist, spec)", self)
        action_clean.triggered.connect(self.full_clean)
        toolsMenu.addAction(action_clean)

        self.action_analyze = QAction("تحليل الموديولات المفقودة", self)
        self.action_analyze.triggered.connect(self.analyze_missing_modules)
        toolsMenu.addAction(self.action_analyze)
        
        action_advanced_analyze = QAction("تحليل متقدم للتبعيات", self)
        action_advanced_analyze.triggered.connect(self.advanced_dependency_analysis)
        toolsMenu.addAction(action_advanced_analyze)
        
        action_audit = QAction("تدقيق الكود", self)
        action_audit.triggered.connect(self.code_audit)
        toolsMenu.addAction(action_audit)

        viewMenu = menubar.addMenu("المظهر")
        self.action_toggle_theme = QAction("تبديل الوضع (داكن/فاتح)", self)
        self.action_toggle_theme.triggered.connect(self.toggle_theme)
        viewMenu.addAction(self.action_toggle_theme)
        
        action_dark = QAction("الوضع الداكن", self)
        action_dark.triggered.connect(lambda: self.set_theme("dark"))
        viewMenu.addAction(action_dark)
        
        action_light = QAction("الوضع الفاتح", self)
        action_light.triggered.connect(lambda: self.set_theme("light"))
        viewMenu.addAction(action_light)

        # اختيار مظهر لون مخصص
        action_custom = QAction("مظهر مخصص…", self)
        action_custom.triggered.connect(self.choose_custom_theme)
        viewMenu.addAction(action_custom)


        settingsMenu = menubar.addMenu("الإعدادات")
        action_plugins = QAction("إدارة الإضافات", self)
        action_plugins.triggered.connect(self.manage_plugins)
        settingsMenu.addAction(action_plugins)
        
        action_templates = QAction("القوالب", self)
        action_templates.triggered.connect(self.manage_templates)
        settingsMenu.addAction(action_templates)

        helpMenu = menubar.addMenu("مساعدة")
        action_check_updates = QAction("تحقق من التحديثات", self)
        action_check_updates.triggered.connect(self.check_updates)
        helpMenu.addAction(action_check_updates)
        
        action_docs = QAction("الوثائق", self)
        action_docs.triggered.connect(self.show_documentation)
        helpMenu.addAction(action_docs)

        WebDev = QAction("زيارة موقعي", self)
        WebDev.triggered.connect(self.VistWebSite)
        helpMenu.addAction(WebDev)

        GoWebProgram = QAction("موقع البرنامج", self)
        GoWebProgram.triggered.connect(self.WebSiteProgram)
        helpMenu.addAction(GoWebProgram)
        
        action_about = QAction("حول البرنامج", self)
        action_about.triggered.connect(self.about_program)
        helpMenu.addAction(action_about)

        Policies = menubar.addMenu("السياسات")

        Privacy_Policy = QAction("سياسة الخصوصية", self)
        Privacy_Policy.triggered.connect(self.Privacy_Policy)
        Policies.addAction(Privacy_Policy)

        Terms_of_Use = QAction("سياسة الأستخدام", self)
        Terms_of_Use.triggered.connect(self.Terms_of_Use)
        Policies.addAction(Terms_of_Use)

        License_Agreement = QAction("أتفاقية الترخيص", self)
        License_Agreement.triggered.connect(self.License_Agreement)
        Policies.addAction(License_Agreement)

        Code_of_Conduct = QAction("قواعد السلوك", self)
        Code_of_Conduct.triggered.connect(self.Code_of_Conduct)
        Policies.addAction(Code_of_Conduct)

        Contribution_Policy = QAction("سياسة المساهمة", self)
        Contribution_Policy.triggered.connect(self.Contribution_Policy)
        Policies.addAction(Contribution_Policy)


    def create_main_ui(self):
        cw = QWidget(self)
        self.setCentralWidget(cw)
        
        main_layout = QHBoxLayout(cw)
        splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.setup_left_panel(left_layout)
        self.setup_right_panel(right_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)

    def setup_left_panel(self, layout):
        tab_widget = QTabWidget()
        
        basic_tab = self.create_basic_tab()
        advanced_tab = self.create_advanced_tab()
        security_tab = self.create_security_tab()
        resources_tab = self.create_resources_tab()
        
        tab_widget.addTab(basic_tab, "أساسي")
        tab_widget.addTab(advanced_tab, "متقدم")
        tab_widget.addTab(security_tab, "الأمان")
        tab_widget.addTab(resources_tab, "الموارد")
        
        layout.addWidget(tab_widget)

    def create_basic_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("الوضع:"))
        self.modeCombo = QComboBox()
        self.modeCombo.addItems(["ملف واحد (Single)", "عدّة ملفات (Batch)"])
        self.modeCombo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.modeCombo)
        mode_layout.addStretch(1)
        layout.addLayout(mode_layout)
        
        entry_layout = QHBoxLayout()
        self.entryLine = QLineEdit()
        self.entryBtn = QPushButton("اختيار الملف الرئيسي…")
        self.entryBtn.clicked.connect(self.pick_entry)
        entry_layout.addWidget(QLabel("الملف الرئيسي:"))
        entry_layout.addWidget(self.entryLine)
        entry_layout.addWidget(self.entryBtn)
        entryBox = QGroupBox("المدخل (Single)")
        entryBox.setLayout(entry_layout)
        layout.addWidget(entryBox)
        
        self.entryList = QListWidget()
        self.addEntryBtn = QPushButton("إضافة سكربت…")
        self.addEntryBtn.clicked.connect(self.add_entry)
        self.remEntryBtn = QPushButton("حذف المحدد")
        self.remEntryBtn.clicked.connect(self.remove_entry)
        elBtns = QHBoxLayout()
        elBtns.addWidget(self.addEntryBtn)
        elBtns.addWidget(self.remEntryBtn)
        entryListBox = QGroupBox("مدخلات متعددة (Batch)")
        v = QVBoxLayout()
        v.addWidget(self.entryList)
        v.addLayout(elBtns)
        entryListBox.setLayout(v)
        layout.addWidget(entryListBox)
        
        options_group = QGroupBox("الخيارات الأساسية")
        options_layout = QVBoxLayout()
        self.oneFileChk = QCheckBox("بناء ملف واحد -F (موصى به)")
        self.consoleChk = QCheckBox("إظهار الكونسول (Console)")
        self.cleanChk = QCheckBox("تنظيف قبل البناء --clean")
        options_layout.addWidget(self.oneFileChk)
        options_layout.addWidget(self.consoleChk)
        options_layout.addWidget(self.cleanChk)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addWidget(QLabel("تستطيع سحب الملفات و أفلاتها على الصيغ المطلوبة منها (.py, .ico, .manifest, .pfx, .p12)"))
        layout.addStretch(1)
        
        return widget

    def create_advanced_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        build_system_layout = QHBoxLayout()
        build_system_layout.addWidget(QLabel("نظام البناء:"))
        self.buildSystemCombo = QComboBox()
        self.buildSystemCombo.addItems(["PyInstaller  تجميع شامل", "cx_Freeze  تجميع تقليدي", "Nuitka         C مترجم لغة", "PyOxidizer  Rustمدمج بـ"])
        build_system_layout.addWidget(self.buildSystemCombo)
        layout.addLayout(build_system_layout)
        
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("المنصة:"))
        self.platformCombo = QComboBox()
        self.platformCombo.addItems(["Windows 32-bit (win32)", "Windows 64-bit (win64)", "Linux", "macOS"])
        platform_layout.addWidget(self.platformCombo)
        layout.addLayout(platform_layout)
        
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("القالب:"))
        self.templateCombo = QComboBox()
        self.templateCombo.addItems([
            "تطبيق واجهة رسومية (GUI)",
            "تطبيق وحدة التحكم (CLI)", 
            "تطبيق خدمة (Service)",
            "تطبيق ويب (Web)",
            "مخصص (Custom)"
        ])
        template_layout.addWidget(self.templateCombo)
        layout.addLayout(template_layout)
        
        interp_layout = QHBoxLayout()
        self.interpCombo = QComboBox()
        found = find_python_interpreters()
        for p in found:
            self.interpCombo.addItem(p)
        self.interpCombo.setEditable(True)
        interp_layout.addWidget(QLabel("مفسّر Python:"))
        interp_layout.addWidget(self.interpCombo)
        layout.addLayout(interp_layout)
        
        virtual_env_layout = QHBoxLayout()
        self.virtualEnvCombo = QComboBox()
        virtual_envs = find_virtual_environments()
        for env in virtual_envs:
            self.virtualEnvCombo.addItem(env)
        self.virtualEnvCombo.setEditable(True)
        virtual_env_layout.addWidget(QLabel("البيئة الافتراضية:"))
        virtual_env_layout.addWidget(self.virtualEnvCombo)
        layout.addLayout(virtual_env_layout)
        
        optimization_group = QGroupBox("خيارات التحسين")
        optimization_layout = QVBoxLayout()
        self.optimizeChk = QCheckBox("تفعيل تحسينات الأداء --optimize")
        self.stripChk = QCheckBox("إزالة المعلومات غير الضرورية --strip")
        self.noPreferRedirectChk = QCheckBox("تعطيل إعادة التوجيه --no-prefer-redirect")
        optimization_layout.addWidget(self.optimizeChk)
        optimization_layout.addWidget(self.stripChk)
        optimization_layout.addWidget(self.noPreferRedirectChk)
        optimization_group.setLayout(optimization_layout)
        layout.addWidget(optimization_group)
        
        version_group = QGroupBox("معلومات الإصدار")
        version_layout = QVBoxLayout()
        version_info_layout = QHBoxLayout()
        self.versionEdit = QLineEdit()
        self.versionEdit.setText("1.0.0")
        version_info_layout.addWidget(QLabel("الإصدار:"))
        version_info_layout.addWidget(self.versionEdit)
        version_layout.addLayout(version_info_layout)
        
        company_layout = QHBoxLayout()
        self.companyEdit = QLineEdit()
        company_layout.addWidget(QLabel("الشركة:"))
        company_layout.addWidget(self.companyEdit)
        version_layout.addLayout(company_layout)
        
        copyright_layout = QHBoxLayout()
        self.copyrightEdit = QLineEdit()
        copyright_layout.addWidget(QLabel("حقوق النشر:"))
        copyright_layout.addWidget(self.copyrightEdit)
        version_layout.addLayout(copyright_layout)
        
        description_layout = QHBoxLayout()
        self.descriptionEdit = QLineEdit()
        description_layout.addWidget(QLabel("الوصف:"))
        description_layout.addWidget(self.descriptionEdit)
        version_layout.addLayout(description_layout)
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        

        layout.addStretch(1)
        return widget

    def create_security_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        security_group = QGroupBox("خيارات الأمان")
        security_layout = QVBoxLayout()
        self.obfuscateChk = QCheckBox("تشويش الكود (Obfuscation)")
        self.antiDebugChk = QCheckBox("الحماية من التصحيح (Anti-Debug)")
        self.packerChk = QCheckBox("استخدام ملفات مضغوطة (Packer)")
        security_layout.addWidget(self.obfuscateChk)
        security_layout.addWidget(self.antiDebugChk)
        security_layout.addWidget(self.packerChk)
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)
        
        signing_group = QGroupBox("التوقيع الرقمي")
        signing_layout = QVBoxLayout()
        cert_layout = QHBoxLayout()
        self.certFileEdit = QLineEdit()
        self.certFileBtn = QPushButton("اختيار...")
        self.certFileBtn.clicked.connect(self.pick_certificate)
        cert_layout.addWidget(QLabel("شهادة التوقيع:"))
        cert_layout.addWidget(self.certFileEdit)
        cert_layout.addWidget(self.certFileBtn)
        signing_layout.addLayout(cert_layout)
        
        cert_pass_layout = QHBoxLayout()
        self.certPassEdit = QLineEdit()
        self.certPassEdit.setEchoMode(QLineEdit.Password)
        cert_pass_layout.addWidget(QLabel("كلمة مرور الشهادة:"))
        cert_pass_layout.addWidget(self.certPassEdit)
        signing_layout.addLayout(cert_pass_layout)
        
        timestamp_layout = QHBoxLayout()
        self.timestampCombo = QComboBox()
        self.timestampCombo.addItems([
            "http://timestamp.digicert.com",
            "http://timestamp.comodoca.com",
            "http://timestamp.globalsign.com"
        ])
        timestamp_layout.addWidget(QLabel("خادم الطابع الزمني:"))
        timestamp_layout.addWidget(self.timestampCombo)
        signing_layout.addLayout(timestamp_layout)
        signing_group.setLayout(signing_layout)
        layout.addWidget(signing_group)
        
        layout.addStretch(1)
        return widget

    def create_resources_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        files_group = QGroupBox("ملفات موارد إضافية (--add-data)")
        files_layout = QVBoxLayout()
        self.filesList = QListWidget()
        files_buttons = QHBoxLayout()
        self.addFileBtn = QPushButton("إضافة ملف…")
        self.addFileBtn.clicked.connect(self.add_file)
        self.remFileBtn = QPushButton("حذف المحدد")
        self.remFileBtn.clicked.connect(self.remove_file)
        files_buttons.addWidget(self.addFileBtn)
        files_buttons.addWidget(self.remFileBtn)
        files_layout.addWidget(self.filesList)
        files_layout.addLayout(files_buttons)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        folders_group = QGroupBox("مجلدات موارد إضافية (--add-data)")
        folders_layout = QVBoxLayout()
        self.foldersList = QListWidget()
        folders_buttons = QHBoxLayout()
        self.addFolderBtn = QPushButton("إضافة مجلد…")
        self.addFolderBtn.clicked.connect(self.add_folder)
        self.remFolderBtn = QPushButton("حذف المحدد")
        self.remFolderBtn.clicked.connect(self.remove_folder)
        folders_buttons.addWidget(self.addFolderBtn)
        folders_buttons.addWidget(self.remFolderBtn)
        folders_layout.addWidget(self.foldersList)
        folders_layout.addLayout(folders_buttons)
        folders_group.setLayout(folders_layout)
        layout.addWidget(folders_group)
        
        resource_management = QGroupBox("إدارة الموارد")
        resource_layout = QVBoxLayout()
        compression_layout = QHBoxLayout()
        self.compressionCombo = QComboBox()
        self.compressionCombo.addItems(["بدون ضغط", "ضغط عادي", "ضغط عالي"])
        compression_layout.addWidget(QLabel("ضغط الموارد:"))
        compression_layout.addWidget(self.compressionCombo)
        resource_layout.addLayout(compression_layout)
        
        self.encryptionChk = QCheckBox("تشفير الموارد")
        resource_layout.addWidget(self.encryptionChk)
        resource_management.setLayout(resource_layout)
        layout.addWidget(resource_management)
        
        layout.addStretch(1)
        return widget

    def setup_right_panel(self, layout):
        output_group = QGroupBox("الإخراج")
        output_layout = QVBoxLayout()
        out_path_layout = QHBoxLayout()
        self.outLine = QLineEdit()
        self.outBtn = QPushButton("مكان الإخراج…")
        self.outBtn.clicked.connect(self.pick_output)
        out_path_layout.addWidget(QLabel("مجلد الإخراج:"))
        out_path_layout.addWidget(self.outLine)
        out_path_layout.addWidget(self.outBtn)
        output_layout.addLayout(out_path_layout)
        
        icon_layout = QHBoxLayout()
        self.iconLine = QLineEdit()
        self.iconBtn = QPushButton("اختيار أيقونة…")
        self.iconBtn.clicked.connect(self.pick_icon)
        icon_layout.addWidget(QLabel("الأيقونة:"))
        icon_layout.addWidget(self.iconLine)
        icon_layout.addWidget(self.iconBtn)
        output_layout.addLayout(icon_layout)
        
        manifest_layout = QHBoxLayout()
        self.manifestLine = QLineEdit()
        self.manifestBtn = QPushButton("اختيار ملف manifest…")
        self.manifestBtn.clicked.connect(self.pick_manifest)
        manifest_layout.addWidget(QLabel("الملف التجسيدي:"))
        manifest_layout.addWidget(self.manifestLine)
        manifest_layout.addWidget(self.manifestBtn)
        output_layout.addLayout(manifest_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        imports_group = QGroupBox("الاستيرادات والإعدادات المتقدمة")
        imports_layout = QVBoxLayout()
        hidden_layout = QHBoxLayout()
        self.hiddenImportsLine = QLineEdit()
        hidden_layout.addWidget(QLabel("الاستيرادات المخفية (مفصولة بفاصلة):"))
        hidden_layout.addWidget(self.hiddenImportsLine)
        imports_layout.addLayout(hidden_layout)
        
        exclude_layout = QHBoxLayout()
        self.excludeModulesLine = QLineEdit()
        exclude_layout.addWidget(QLabel("الموديولات المستبعدة (مفصولة بفاصلة):"))
        exclude_layout.addWidget(self.excludeModulesLine)
        imports_layout.addLayout(exclude_layout)
        
        uac_layout = QHBoxLayout()
        self.uacChk = QCheckBox("طلب صلاحيات المدير Administrator (--uac-admin)")
        uac_layout.addWidget(self.uacChk)
        imports_layout.addLayout(uac_layout)
        
        key_layout = QHBoxLayout()
        self.keyLine = QLineEdit()
        key_layout.addWidget(QLabel("مفتاح التشفير:"))
        key_layout.addWidget(self.keyLine)
        imports_layout.addLayout(key_layout)
        imports_group.setLayout(imports_layout)
        layout.addWidget(imports_group)
        
        build_control = QGroupBox("التحكم في البناء")
        build_layout = QVBoxLayout()
        build_buttons = QHBoxLayout()
        self.buildBtn = QPushButton("بدء البناء")
        if self.shield_icon and os.path.isfile(self.shield_icon):
            self.buildBtn.setIcon(QIcon(self.shield_icon))
        self.buildBtn.clicked.connect(self.start_build)
        self.cancelBtn = QPushButton("إلغاء")
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
        self.runAfterChk = QCheckBox("تشغيل الناتج بعد البناء")
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
        self.cmdPreview.setPlaceholderText("معاينة أوامر البناء ستظهر هنا…")
        cmd_layout.addWidget(QLabel("معاينة الأوامر:"))
        cmd_layout.addWidget(self.cmdPreview)
        logs_tab.addTab(cmd_tab, "معاينة الأوامر")
        
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("سجل عملية البناء…")
        log_layout.addWidget(QLabel("سجل البناء:"))
        log_layout.addWidget(self.log)
        logs_tab.addTab(log_tab, "سجل البناء")
        
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        self.reportText = QPlainTextEdit()
        self.reportText.setReadOnly(True)
        self.reportText.setPlaceholderText("تقرير البناء سيظهر هنا…")
        report_layout.addWidget(QLabel("تقرير البناء:"))
        report_layout.addWidget(self.reportText)
        logs_tab.addTab(report_tab, "التقارير")
        
        layout.addWidget(logs_tab)
        
        action_buttons = QHBoxLayout()
        self.saveLogBtn = QPushButton("حفظ السجل")
        self.saveLogBtn.clicked.connect(self.save_log_to_file)
        self.openDistBtn = QPushButton("فتح مجلد الإخراج")
        self.openDistBtn.clicked.connect(self.open_output_folder)
        self.openBuildBtn = QPushButton("فتح مجلد build")
        self.openBuildBtn.clicked.connect(self.open_build_folder)
        self.testOutputBtn = QPushButton("اختبار الناتج")
        self.testOutputBtn.clicked.connect(self.test_output)
        action_buttons.addWidget(self.saveLogBtn)
        action_buttons.addWidget(self.openDistBtn)
        action_buttons.addWidget(self.openBuildBtn)
        action_buttons.addWidget(self.testOutputBtn)
        layout.addLayout(action_buttons)

    def pick_certificate(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختيار شهادة التوقيع", "", "Certificate Files (*.pfx *.p12)")
        if path:
            self.certFileEdit.setText(os.path.abspath(path))

    def test_output(self):
        output_dir = self.outLine.text().strip() or os.path.abspath("output")
        if not os.path.isdir(output_dir):
            QMessageBox.warning(self, "اختبار", "مجلد الإخراج غير موجود.")
            return
        
        exe_files = []
        for file in os.listdir(output_dir):
            if file.endswith(".exe") or (os.name != "nt" and os.access(os.path.join(output_dir, file), os.X_OK)):
                exe_files.append(file)
        
        if not exe_files:
            QMessageBox.warning(self, "اختبار", "لم يتم العثور على ملفات قابلة للتنفيذ.")
            return
        
        if len(exe_files) == 1:
            exe_path = os.path.join(output_dir, exe_files[0])
            self.run_executable(exe_path)
        else:
            file, ok = QInputDialog.getItem(self, "اختيار ملف للاختبار", "اختر الملف للاختبار:", exe_files, 0, False)
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
            QMessageBox.warning(self, "اختبار", f"فشل تشغيل الملف: {e}")

    def manage_plugins(self):
        QMessageBox.information(self, "الإضافات", "نظام الإضافات مفعل. ضع ملفات الإضافات في مجلد 'plugins'")

    def manage_templates(self):
        QMessageBox.information(self, "القوالب", "يمكنك اختيار قالب من القائمة المنسدلة في علامة التبويب المتقدم")

    def show_documentation(self):
        webbrowser.open("https://github.com/wsl-iq/Python-Executable/wiki")

    def VistWebSite(self):
        webbrowser.open("https://wsl-iq.github.io/")

    def WebSiteProgram(self):
        webbrowser.open("https://wsl-iq.github.io/Python-Executable/")

    def about_program(self):
        about_text = """
From Python To Executable v3.0.0 (بالعربية)

أقوى أداة لتحويل برامج Python إلى ملفات تنفيذية
تم تطوير هذا البرنامج بواسطة محمد الباقر

المميزات:
• تحويل ملفات Python إلى EXE
• دعم البناء الفردي والجماعي
• تحليل تلقائي للتبعيات
• خيارات أمان متقدمة
• نظام إضافات قابل للتوسيع
• واجهة مستخدم متطورة
• تقارير مفصلة عن البناء

الشروط:
• للاستخدام الشخصي والتجاري
• يمنع استخدام البرنامج لأغراض ضارة
• يرجى احترام حقوق الملكية الفكرية
"""
        QMessageBox.about(self, "حول البرنامج", about_text)

    def Privacy_Policy(self):
        Privacy_Policy_txt = '''
• أحترم خصوصيتك، والبرنامج يعمل محلياً داخل جهازك فقط.
• لا يُجمع أو يُخزَّن أي بيانات خارج جهاز المستخدم.
• كل العمليات الناتجة تُخزَّن محلياً وتبقى تحت سيطرتك التامة.
• باستخدامك البرنامج، أنت تدرك أنه لا يشارك أي بيانات.
• بياناتك محفوظة داخل جهازك دائماً وبأمان كامل ومضمون.
'''
        QMessageBox.about(self, "سياسة الخصوصية", Privacy_Policy_txt)

    def Terms_of_Use(self):
        Terms_of_Use_txt = '''
• يُسمح باستخدام البرنامج فقط للأغراض الشخصية أو التعليمية.
• يُسمح بالتعديل شرط ذكر حقوق المطوّر عند النشر.
• استخدامك للبرنامج يعني موافقتك الكاملة على هذه الشروط.
'''
        QMessageBox.about(self, "سياسة الأستخدام", Terms_of_Use_txt)

    def License_Agreement(self):
        License_Agreement_txt = '''
• هذا البرنامج مرخّص للاستخدام الشخصي وغير التجاري .
• لا يُسمح ببيع البرنامج لأنهُ مجاني بالكامل من قبل المطور .
• جميع الحقوق محفوظة © 2025
'''
        QMessageBox.about(self, "أتفاقية الترخيص", License_Agreement_txt)

    def Code_of_Conduct(self):
        Code_of_Conduct_txt = '''
• يُتوقع من المستخدمين احترام البرنامج وتجنّب إساءة استخدامه مطلقاً.
• يُمنع القيام بتصرفات تُعطل النظام أو تنتهك حقوق الآخرين.
• استخدام البرنامج يعني الالتزام بالسلوك المسؤول والاحترام الدائم.
'''
        QMessageBox.about(self, "قواعد السلوك", Code_of_Conduct_txt)

    def Contribution_Policy(self):
        Contribution_Policy_txt = '''
• نرحّب بالمساهمات والملاحظات من المستخدمين والمطوّرين الآخرين دائماً.
• يجب أن تكون المقترحات بنّاءة ومحترمة وخالية من أي ضرر.
• باستخدام البرنامج، توافق على تعديل المساهمات لتحسين الأداء العام.
'''
        QMessageBox.about(self, "سياسة المساهمة", Contribution_Policy_txt)
      

    def set_theme(self, theme):
        self.settings["theme"] = theme
        self.apply_theme()
        self.save_settings()

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
        self.save_settings()

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
            self.save_settings()
            self.settings["custom_color"] = {"r": r, "g": g, "b": b}
            self.save_settings()

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
        self.save_settings()

    def _on_mode_changed(self, idx: int):
        single = idx == 0
        self.entryLine.setEnabled(single)
        self.entryBtn.setEnabled(single)
        self.entryList.setEnabled(not single)
        self.addEntryBtn.setEnabled(not single)
        self.remEntryBtn.setEnabled(not single)

    def pick_entry(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختيار الملف الرئيسي", "", "Python (*.py)")
        if path:
            self.entryLine.setText(os.path.abspath(path))

    def add_entry(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "اختيار سكربتات", "", "Python (*.py)")
        for p in paths:
            if p:
                self.entryList.addItem(os.path.abspath(p))

    def remove_entry(self):
        for item in self.entryList.selectedItems():
            self.entryList.takeItem(self.entryList.row(item))

    def add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "اختيار ملفات موارد", "", "All Files (*.*)")
        for p in paths:
            if p:
                self.filesList.addItem(os.path.abspath(p))

    def remove_file(self):
        for item in self.filesList.selectedItems():
            self.filesList.takeItem(self.filesList.row(item))

    def add_folder(self):
        path = QFileDialog.getExistingDirectory(self, "اختيار مجلد موارد")
        if path:
            self.foldersList.addItem(os.path.abspath(path))

    def remove_folder(self):
        for item in self.foldersList.selectedItems():
            self.foldersList.takeItem(self.foldersList.row(item))

    def pick_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختيار أيقونة", "", "Icon (*.ico)")
        if path:
            self.iconLine.setText(os.path.abspath(path))

    def pick_manifest(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختيار Manifest", "", "Manifest (*.manifest)")
        if path:
            self.manifestLine.setText(os.path.abspath(path))

    def pick_output(self):
        path = QFileDialog.getExistingDirectory(self, "اختيار مجلد الإخراج")
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
        self.save_settings()

        python_exec = self.interpCombo.currentText().strip() or None
        if python_exec:
            if not shutil.which(os.path.basename(python_exec)) and not os.path.isfile(python_exec):
                if QMessageBox.question(self, "مفسّر Python", f"المسار المحدد للمفسر غير موجود:\n{python_exec}\n\nهل تريد المتابعة مع مفسر النظام؟", QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
                    return
                python_exec = None

        if shutil.which("pyinstaller") is None:
            QMessageBox.critical(self, "PyInstaller غير موجود", "تعذر العثور على PyInstaller. ثبّت الحزمة بالأمر:\n\n    pip install pyinstaller\n\nثم أعد المحاولة.")
            return

        cmds = self._make_commands(generate_spec_only=False)
        if not cmds:
            QMessageBox.warning(self, "لا يوجد مدخلات", "حدّد سكربت رئيسي أو أضف سكربتات في وضع Batch.")
            return

        missing = []
        for c in cmds:
            entry = c[-1]
            if not os.path.isfile(entry):
                missing.append(entry)
        if missing:
            QMessageBox.warning(self, "ملفات مفقودة", "الملفات التالية غير موجودة:\n" + "\n".join(missing))
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
        self._append_log("[INFO] تم إلغاء العملية بواسطة المستخدم.")

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
            self.sysUsageLabel.setText(f"CPU: {cpu:.0f}%  RAM: {mem:.0f}%")
            self._update_sys_usage_graph(cpu, mem, disk, gpu)

            

    def _update_sys_usage_label(self):
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
            self._append_log("[SUCCESS] انتهى البناء بدون أخطاء.")
            QMessageBox.information(self, "تم", "انتهى البناء بدون أخطاء. الملفات داخل مجلد الإخراج المحدد.")
            
            self.save_log_to_file(prompt=False)
            
            try:
                if os.name == "nt":
                    winsound.MessageBeep()
                else:
                    print("\a")
            except Exception:
                pass
            
            if QMessageBox.question(self, "فتح مجلد الإخراج", "هل ترغب في فتح مجلد الإخراج الآن؟", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.open_output_folder()
        else:
            self._append_log("[WARN] انتهى البناء لكن مع أخطاء. راجع السجل.")
            QMessageBox.warning(self, "انتهى مع مشاكل", "تحقق من السجل لمعرفة تفاصيل الخطأ.")

    def save_log_to_file(self, prompt=True):
        default = os.path.abspath("build_log.txt")
        if prompt:
            path, _ = QFileDialog.getSaveFileName(self, "حفظ السجل كملف", default, "Text Files (*.txt)")
            if not path:
                return
        else:
            path = default
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log.toPlainText())
            QMessageBox.information(self, "حفظ السجل", f"تم حفظ السجل في: {path}")
        except Exception as e:
            QMessageBox.warning(self, "حفظ السجل", f"فشل حفظ السجل: {e}")

    def open_output_folder(self):
        outdir = self.outLine.text().strip() or os.path.abspath("output")
        if os.path.isdir(outdir):
            try:
                if os.name == "nt":
                    os.startfile(outdir)
                else:
                    subprocess.call(["xdg-open", outdir])
            except Exception as e:
                QMessageBox.warning(self, "فتح المجلد", f"فشل فتح المجلد: {e}")
        else:
            QMessageBox.warning(self, "مجلد الإخراج غير موجود", f"لم يتم العثور على مجلد الإخراج: {outdir}")

    def open_build_folder(self):
        build_dir = os.path.join(os.getcwd(), "build")
        if os.path.isdir(build_dir):
            try:
                if os.name == "nt":
                    os.startfile(build_dir)
                else:
                    subprocess.call(["xdg-open", build_dir])
            except Exception as e:
                QMessageBox.warning(self, "فتح المجلد", f"فشل فتح المجلد: {e}")
        else:
            QMessageBox.warning(self, "مجلد build غير موجود", f"لم يتم العثور على مجلد build في: {build_dir}")

    def clean_output_folder(self):
        outdir = self.outLine.text().strip() or os.path.abspath("output")
        if os.path.isdir(outdir):
            reply = QMessageBox.question(self, "حذف مجلد الإخراج", f"هل تريد حذف المجلد:\n{outdir} ?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    shutil.rmtree(outdir)
                    QMessageBox.information(self, "تم", "تم حذف مجلد الإخراج.")
                except Exception as e:
                    QMessageBox.warning(self, "فشل", f"فشل حذف المجلد: {e}")
        else:
            QMessageBox.information(self, "غير موجود", "مجلد الإخراج غير موجود.")

    def full_clean(self):
        reply = QMessageBox.question(self, "تنظيف كامل", "سيتم حذف مجلدات build و dist وكل ملفات .spec في المجلد الحالي. هل تريد المتابعة؟", QMessageBox.Yes | QMessageBox.No)
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
        QMessageBox.information(self, "تم", "تم التنظيف الكامل (إن وُجد شيء).")

    def generate_spec_only(self):
        cmds = self._make_commands(generate_spec_only=True)
        if not cmds:
            QMessageBox.warning(self, "لا يوجد مدخلات", "حدّد سكربت رئيسي أو أضف سكربتات في وضع Batch.")
            return
        preview = "\n\n".join(" ".join(map(quote, c)) for c in cmds)
        self.cmdPreview.setPlainText(preview)
        
        for cmd in cmds:
            try:
                subprocess.check_call(cmd, cwd=os.getcwd())
                self._append_log(f"[INFO] تم توليد ملف .spec باستخدام: {' '.join(cmd)}")
            except Exception as e:
                QMessageBox.warning(self, "فشل التوليد", f"خلال توليد .spec حدث خطأ: {e}")
                return
        QMessageBox.information(self, "تم", "تم توليد ملفات .spec بنجاح.")

    def check_updates(self):
        url = "https://github.com/wsl-iq/Python-Executable/blob/main/version.txt"
        try:
            webbrowser.open(url)
            QMessageBox.information(self, "تحقق من التحديثات", "تم فتح صفحة التحديث في المتصفح. ضع ملف version.txt بنفس السجل لعرض الإصدار.")
        except Exception as e:
            QMessageBox.warning(self, "فشل التحقق", f"تعذر فتح صفحة التحديث: {e}")

    def about_dev(self):
        QMessageBox.information(self, "حول المطور", "تم تطوير هذا البرنامج بواسطة محمد الباقر.\n\nمن شروط الترخيص عدم استخدام هذا البرنامج لأغراض ضارة أو غير قانونية.")

    def closeEvent(self, event):
        try:
            self.save_settings()
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