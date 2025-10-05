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
from dataclasses import dataclass
from typing import List, Dict, Optional
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QCheckBox, QPlainTextEdit, QMessageBox, QLabel,
    QHBoxLayout, QVBoxLayout, QGroupBox, QComboBox, QProgressBar, QMenu, QAction
)

try:
    import psutil
except Exception:
    psutil = None

SETTINGS_FILE = "settings.json"
LOG_FILE = "log.txt"
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
        "key": ""
    },
    "theme": "light",
    "hide_console": False
}
PATHSEP = ";" if os.name == "nt" else ":"


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
    """ابحث عن مفسرات Python شائعة في PATH وبعض المسارات المعروفة."""
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
    return candidates

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
                self.line.emit("[ERROR] الأمر غير موجود (تأكد من تثبيت pyinstaller أو مفسر البايثون)")
                break
            except Exception as e:
                ok = False
                self.line.emit(f"[ERROR] {e}")
                break
        if ok and self.run_after and self.commands:
            try:
                self.line.emit("[INFO] تنفيذ الملف الناتج إن وُجد...")
            except Exception:
                pass
        self.done.emit(ok)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("From Python To Executable — v2.0 © Mohammed Al-Baqer")
        self.resize(820, 620)
        self.icon_path = "icon.ico" if os.path.isfile("icon.ico") else None
        self.shield_icon = "shield.ico" if os.path.isfile("shield.ico") else self.icon_path
        if self.icon_path:
            self.setWindowIcon(QIcon(self.icon_path))
        
        self.thread: Optional[QThread] = None
        self.worker: Optional[BuildWorker] = None
        self.settings: Dict = {}
        self.load_settings()
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

    def create_menus(self):
        menubar = self.menuBar()
        
        fileMenu = menubar.addMenu("الملف")
        action_reset = QAction("إعادة تعيين الإعدادات", self)
        action_reset.triggered.connect(self.reset_settings)
        fileMenu.addAction(action_reset)
        action_exit = QAction("خروج", self)
        action_exit.triggered.connect(self.close)
        fileMenu.addAction(action_exit)

        toolsMenu = menubar.addMenu("أدوات")
        action_spec = QAction("توليد ملف .spec فقط", self)
        action_spec.triggered.connect(self.generate_spec_only)
        toolsMenu.addAction(action_spec)
        action_clean = QAction("تنظيف كامل (build, dist, spec)", self)
        action_clean.triggered.connect(self.full_clean)
        toolsMenu.addAction(action_clean)

        viewMenu = menubar.addMenu("المظهر")
        self.action_toggle_theme = QAction("تبديل الوضع (داكن/فاتح)", self)
        self.action_toggle_theme.triggered.connect(self.toggle_theme)
        viewMenu.addAction(self.action_toggle_theme)

        helpMenu = menubar.addMenu("مساعدة")
        action_check_updates = QAction("تحقق من التحديثات", self)
        action_check_updates.triggered.connect(self.check_updates)
        helpMenu.addAction(action_check_updates)
        action_about = QAction("حول المطور", self)
        action_about.triggered.connect(self.about_dev)
        helpMenu.addAction(action_about)

    def create_main_ui(self):
        cw = QWidget(self)
        self.setCentralWidget(cw)
        root = QHBoxLayout(cw)

        leftCol = QVBoxLayout()
        
        topRow = QHBoxLayout()
        topRow.addWidget(QLabel("الوضع:"))
        self.modeCombo = QComboBox()
        self.modeCombo.addItems(["ملف واحد (Single)", "عدّة ملفات (Batch)"])
        self.modeCombo.currentIndexChanged.connect(self._on_mode_changed)
        topRow.addWidget(self.modeCombo)
        topRow.addStretch(1)
        leftCol.addLayout(topRow)

        entryLayout = QHBoxLayout()
        self.entryLine = QLineEdit()
        self.entryBtn = QPushButton("اختيار الملف الرئيسي…")
        self.entryBtn.clicked.connect(self.pick_entry)
        entryLayout.addWidget(QLabel("الملف الرئيسي:"))
        entryLayout.addWidget(self.entryLine)
        entryLayout.addWidget(self.entryBtn)
        entryBox = QGroupBox("المدخل (Single)")
        entryBox.setLayout(entryLayout)
        leftCol.addWidget(entryBox)

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
        leftCol.addWidget(entryListBox)

        self.filesList = QListWidget()
        self.addFileBtn = QPushButton("إضافة ملف…")
        self.addFileBtn.clicked.connect(self.add_file)
        self.remFileBtn = QPushButton("حذف المحدد")
        self.remFileBtn.clicked.connect(self.remove_file)
        flBtns = QHBoxLayout()
        flBtns.addWidget(self.addFileBtn)
        flBtns.addWidget(self.remFileBtn)
        filesBox = QGroupBox("ملفات موارد إضافية (--add-data)")
        vf = QVBoxLayout()
        vf.addWidget(self.filesList)
        vf.addLayout(flBtns)
        filesBox.setLayout(vf)
        leftCol.addWidget(filesBox)

        self.foldersList = QListWidget()
        self.addFolderBtn = QPushButton("إضافة مجلد…")
        self.addFolderBtn.clicked.connect(self.add_folder)
        self.remFolderBtn = QPushButton("حذف المحدد")
        self.remFolderBtn.clicked.connect(self.remove_folder)
        fdBtns = QHBoxLayout()
        fdBtns.addWidget(self.addFolderBtn)
        fdBtns.addWidget(self.remFolderBtn)
        foldersBox = QGroupBox("مجلدات موارد إضافية (--add-data)")
        vfd = QVBoxLayout()
        vfd.addWidget(self.foldersList)
        vfd.addLayout(fdBtns)
        foldersBox.setLayout(vfd)
        leftCol.addWidget(foldersBox)

        leftCol.addWidget(QLabel("تستطيع سحب ملفات .py و .ico وإفلاتها مباشرة على النافذة."))

        rightCol = QVBoxLayout()

        optBox = QGroupBox("الخيارات")
        vo = QVBoxLayout()
        self.oneFileChk = QCheckBox("بناء ملف واحد -F (موصى به)")
        self.consoleChk = QCheckBox("إظهار الكونسول (Console)")
        self.cleanChk = QCheckBox("تنظيف قبل البناء --clean")
        vo.addWidget(self.oneFileChk)
        vo.addWidget(self.consoleChk)
        vo.addWidget(self.cleanChk)

        icoLayout = QHBoxLayout()
        self.iconLine = QLineEdit()
        self.iconBtn = QPushButton("اختيار أيقونة .ico…")
        self.iconBtn.clicked.connect(self.pick_icon)
        icoLayout.addWidget(QLabel("الأيقونة:"))
        icoLayout.addWidget(self.iconLine)
        icoLayout.addWidget(self.iconBtn)
        vo.addLayout(icoLayout)

        manLayout = QHBoxLayout()
        self.manifestLine = QLineEdit()
        self.manifestBtn = QPushButton("اختيار ملف .manifest…")
        self.manifestBtn.clicked.connect(self.pick_manifest)
        manLayout.addWidget(QLabel("Manifest:"))
        manLayout.addWidget(self.manifestLine)
        manLayout.addWidget(self.manifestBtn)
        vo.addLayout(manLayout)

        outLayout = QHBoxLayout()
        self.outLine = QLineEdit()
        self.outBtn = QPushButton("مكان الإخراج…")
        self.outBtn.clicked.connect(self.pick_output)
        outLayout.addWidget(QLabel("مجلد الإخراج (distpath):"))
        outLayout.addWidget(self.outLine)
        outLayout.addWidget(self.outBtn)
        vo.addLayout(outLayout)
        optBox.setLayout(vo)
        rightCol.addWidget(optBox)

        interpLayout = QHBoxLayout()
        self.interpCombo = QComboBox()
        found = find_python_interpreters()
        for p in found:
            self.interpCombo.addItem(p)
        self.interpCombo.setEditable(True)
        interpLayout.addWidget(QLabel("مفسّر Python:"))
        interpLayout.addWidget(self.interpCombo)
        rightCol.addLayout(interpLayout)

        advBox = QGroupBox("خيارات متقدمة (Advanced)")
        advLayout = QVBoxLayout()
        
        hiLayout = QHBoxLayout()
        self.hiddenImportsLine = QLineEdit()
        hiLayout.addWidget(QLabel("hidden-import (فصل بعلامة ,):"))
        hiLayout.addWidget(self.hiddenImportsLine)
        advLayout.addLayout(hiLayout)
        
        exLayout = QHBoxLayout()
        self.excludeModulesLine = QLineEdit()
        exLayout.addWidget(QLabel("exclude-module (فصل بعلامة ,):"))
        exLayout.addWidget(self.excludeModulesLine)
        advLayout.addLayout(exLayout)
        
        self.uacChk = QCheckBox("طلب صلاحيات Admin عبر --uac-admin")
        advLayout.addWidget(self.uacChk)
        
        kLayout = QHBoxLayout()
        self.keyLine = QLineEdit()
        kLayout.addWidget(QLabel("key (لتشفير الكود):"))
        kLayout.addWidget(self.keyLine)
        advLayout.addLayout(kLayout)
        
        advBox.setLayout(advLayout)
        advBox.setVisible(False)
        rightCol.addWidget(advBox)

        self.toggleAdvBtn = QPushButton("إظهار خيارات متقدمة")
        self.toggleAdvBtn.clicked.connect(lambda: self._toggle_advanced(advBox))
        rightCol.addWidget(self.toggleAdvBtn)

        self.buildBtn = QPushButton("بدء التحويل py → exe")
        if self.shield_icon and os.path.isfile(self.shield_icon):
            self.buildBtn.setIcon(QIcon(self.shield_icon))
        self.buildBtn.clicked.connect(self.start_build)
        self.cancelBtn = QPushButton("إلغاء")
        self.cancelBtn.setEnabled(False)
        self.cancelBtn.clicked.connect(self.cancel_build)
        bb = QHBoxLayout()
        bb.addWidget(self.buildBtn)
        bb.addWidget(self.cancelBtn)
        rightCol.addLayout(bb)

        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        rightCol.addWidget(self.progressBar)
        self.sysUsageLabel = QLabel("CPU: -%  RAM: -%")
        rightCol.addWidget(self.sysUsageLabel)

        self.cmdPreview = QPlainTextEdit()
        self.cmdPreview.setReadOnly(True)
        self.cmdPreview.setPlaceholderText("معاينة أوامر PyInstaller ستظهر هنا…")
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("سجل عملية البناء…")
        logBox = QGroupBox("السجل")
        vl = QVBoxLayout()
        vl.addWidget(QLabel("معاينة الأوامر:"))
        vl.addWidget(self.cmdPreview)
        vl.addWidget(QLabel("سجل الحدث:"))
        vl.addWidget(self.log)
        
        logsBtns = QHBoxLayout()
        self.saveLogBtn = QPushButton("حفظ السجل")
        self.saveLogBtn.clicked.connect(self.save_log_to_file)
        self.openDistBtn = QPushButton("فتح مجلد الإخراج")
        self.openDistBtn.clicked.connect(self.open_output_folder)
        self.openBuildBtn = QPushButton("فتح مجلد build")
        self.openBuildBtn.clicked.connect(self.open_build_folder)
        self.runAfterChk = QCheckBox("تشغيل الناتج بعد النجاح")
        logsBtns.addWidget(self.saveLogBtn)
        logsBtns.addWidget(self.openDistBtn)
        logsBtns.addWidget(self.openBuildBtn)
        logsBtns.addWidget(self.runAfterChk)
        vl.addLayout(logsBtns)
        logBox.setLayout(vl)
        rightCol.addWidget(logBox)

        bottomBtns = QHBoxLayout()
        self.cleanOutputBtn = QPushButton("حذف مجلد الإخراج")
        self.cleanOutputBtn.clicked.connect(self.clean_output_folder)
        self.resetBtn = QPushButton("إعادة تعيين إلى الافتراضي")
        self.resetBtn.clicked.connect(self.reset_settings)
        bottomBtns.addWidget(self.cleanOutputBtn)
        bottomBtns.addWidget(self.resetBtn)
        rightCol.addLayout(bottomBtns)

        # تجميع الواجهة
        root.addLayout(leftCol, 2)
        root.addLayout(rightCol, 3)

    def _toggle_advanced(self, advBox):
        advBox.setVisible(not advBox.isVisible())
        self.toggleAdvBtn.setText("إخفاء خيارات متقدمة" if advBox.isVisible() else "إظهار خيارات متقدمة")

    def load_settings(self):
        if os.path.isfile(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = DEFAULT_SETTINGS.copy()
        else:
            self.settings = DEFAULT_SETTINGS.copy()

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
            "key": self.keyLine.text().strip()
        }
        
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "حفظ الإعدادات", f"فشل حفظ الإعدادات: {e}")

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
        
        python_interpreter = self.settings.get("python_interpreter", "")
        if python_interpreter:
            index = self.interpCombo.findText(python_interpreter)
            if index >= 0:
                self.interpCombo.setCurrentIndex(index)
            else:
                self.interpCombo.setEditText(python_interpreter)

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
        args: List[str] = []
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

        base_args: List[str] = ["pyinstaller", "--distpath", outdir]
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

        cmds: List[List[str]] = []
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

    def _on_cpu_mem(self, cpu: float, mem: float):
        self.sysUsageLabel.setText(f"CPU: {cpu:.0f}%  RAM: {mem:.0f}%")

    def _update_sys_usage_label(self):
        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent
                self.sysUsageLabel.setText(f"CPU: {cpu:.0f}%  RAM: {mem:.0f}%")
            except Exception:
                pass

    def _build_finished(self, ok: bool):
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
        self.worker = None
        self.buildBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(100 if ok else 0)
        self._indeterminate = False

        if ok:
            self._append_log("[SUCCESS] انتهى البناء بدون أخطاء.")
            QMessageBox.information(self, "تم", "انتهى البناء بدون أخطاء. الملفات داخل مجلد الإخراج المحدد.")
            
            self.save_log_to_file(prompt=False)
            
            try:
                if os.name == "nt":
                    import winsound
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
        reply = QMessageBox.question(self, "تنظيف كامل", "سيتم حذف مجلدات build وdist وكل ملفات .spec في المجلد الحالي. هل تريد المتابعة؟", QMessageBox.Yes | QMessageBox.No)
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

    def apply_dark_theme(self):
        app = QApplication.instance()
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 48))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 48))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(45, 45, 48))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(10, 132, 255))
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