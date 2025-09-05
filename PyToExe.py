#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025
# Custom License Based on MIT License
# Version        : 1.0.0
# Developer      : Mohammed Al-Baqer
# License        : Custom License Based on MIT License
# Language       : Arabic only (العربية فقط)
# Description    : From Python To Executable (Py to Exe) GUI Tool using PyQt5 and PyInstaller
# 

import os; os.system("cls" if os.name == "nt" else "clear")
import sys; sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import time
import shlex
import webbrowser
import shutil
import subprocess
from dataclasses import dataclass
from typing import List
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QCheckBox, QPlainTextEdit, QMessageBox, QLabel,
    QHBoxLayout, QVBoxLayout, QGroupBox, QComboBox
)

PATHSEP = ";" if os.name == "nt" else ":"

def quote(p: str) -> str:
    """ضع اقتباس للمسارات التي تحتوي مسافات."""
    if not p:
        return p
    if os.name != "nt":
        return shlex.quote(p)
    if " " in p or "(" in p or ")" in p:
        return f'"{p}"'
    return p

@dataclass
class BuildItem:
    entry_script: str

class BuildWorker(QObject):
    line = pyqtSignal(str)
    done = pyqtSignal(bool)

    def __init__(self, commands: List[List[str]], cwd: str) -> None:
        super().__init__()
        self.commands = commands
        self.cwd = cwd
        self._stopped = False

    def stop(self):
        self._stopped = True

    def run(self):
        ok = True
        for cmd in self.commands:
            if self._stopped:
                ok = False
                break
            self.line.emit("\n=== Running: {}\n".format(" ".join(cmd)))
            try:
                with subprocess.Popen(
                    cmd,
                    cwd=self.cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                ) as p:
                    for out_line in p.stdout:
                        self.line.emit(out_line.rstrip("\n"))
                rc = p.wait()
                if rc != 0:
                    ok = False
                    self.line.emit(f"[ERROR] Command exited with code {rc}")
                    break
            except FileNotFoundError:
                ok = False
                self.line.emit("[ERROR] لم يتم العثور على الأمر (تأكد من تثبيت PyInstaller وأضافته للمسار PATH)")
                if QMessageBox.question(self, "تثبيت PyInstaller", "هل ترغب في تثبيت PyInstaller الآن؟", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
                    QMessageBox.information(self, "تثبيت PyInstaller", "تم تثبيت PyInstaller بنجاح.")
                break
            except Exception as e:
                ok = False
                self.line.emit(f"[ERROR] {e}")
                break
        self.done.emit(ok)

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Copyright © 2025 Mohammed Al-Baqer -> (From Python To Executable)")
        self.resize(400, 500)

        self.setWindowIcon(QIcon("icon.png") if os.path.isfile("icon.png") else QIcon.fromTheme("application-x-executable"))
        self.setWindowIcon(QIcon.fromTheme("application-x-executable"))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        if os.path.isfile("icon.png"):
            self.setWindowIcon(QIcon("icon.png"))
        elif os.path.isfile("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
        else:
            self.setWindowIcon(QIcon.fromTheme("application-x-executable"))
        def AboutDeveloper():
            QMessageBox.information(self, "حول المطور", "تم تطوير هذا البرنامج بواسطة محمد الباقر." \
            "\n\nالموقع الرسمي: https://wsl-iq.github.io/" \
            "\n\n من شروط الترخيص عدم استخدام هذا البرنامج لأغراض ضارة أو غير قانونية." \
            "\n\nباستخدام هذا البرنامج، فإنك توافق على شروط الترخيص.")
        aboutDevAction = self.menuBar().addAction("حول المطور")
        aboutDevAction.triggered.connect(AboutDeveloper)
        
        def AboutLicense():
            QMessageBox.information(self, "الترخيص",\
            "\n\nلا توجد أي ضمانات مقدمة مع هذا البرنامج، ويُستخدم على مسؤولة المستخدم الخاصة." \
            "\n\nباستخدام هذا البرنامج، فإنك توافق على شروط هذه الرخصة.")
        licenseAction = self.menuBar().addAction("الترخيص")
        licenseAction.triggered.connect(AboutLicense)

        def Privacy():
            QMessageBox.information(self, "سياسة الخصوصية", "هذا التطبيق لا يجمع أو يخزن أي بيانات شخصية للمستخدم." \
            "\n\nيتم استخدام ملفات السجل فقط لأغراض التصحيح وتحسين التطبيق." \
            "\n\nلا يتم مشاركة أي بيانات مع أطراف ثالثة." \
            "\n\nباستخدام هذا التطبيق، فإنك توافق على هذه السياسة." \
            "\n\nإذا كانت لديك أي أسئلة، يرجى الاتصال بالمطور.")
        privacyAction = self.menuBar().addAction("سياسة الخصوصية")
        privacyAction.triggered.connect(Privacy)

        def Donate():
            webbrowser.open("https://wsl-iq.github.io/MASTERCARD/")
        donateAction = self.menuBar().addAction("الدعم و التبرع")
        donateAction.triggered.connect(Donate)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon.fromTheme("application-x-executable"))

        def website():
            webbrowser.open("https://wsl-iq.github.io/")
        webAction = self.menuBar().addAction("الموقع الرسمي")
        webAction.triggered.connect(website)

        cw = QWidget(self)
        self.setCentralWidget(cw) 

        self.modeCombo = QComboBox()
        self.modeCombo.addItems(["ملف واحد (Single)", "عدّة ملفات (Batch)"])
        self.modeCombo.currentIndexChanged.connect(self._on_mode_changed)

        self.entryLine = QLineEdit()
        self.entryBtn = QPushButton("اختيار الملف الرئيسي…")
        self.entryBtn.clicked.connect(self.pick_entry)

        entryLayout = QHBoxLayout()
        entryLayout.addWidget(QLabel("الملف الرئيسي:"))
        entryLayout.addWidget(self.entryLine)
        entryLayout.addWidget(self.entryBtn)
        entryBox = QGroupBox("المدخل (Single)")
        entryBox.setLayout(entryLayout)

        self.entryList = QListWidget()
        self.addEntryBtn = QPushButton("إضافة سكربت…")
        self.remEntryBtn = QPushButton("حذف المحدد")
        self.addEntryBtn.clicked.connect(self.add_entry)
        self.remEntryBtn.clicked.connect(self.remove_entry)

        elBtns = QHBoxLayout()
        elBtns.addWidget(self.addEntryBtn)
        elBtns.addWidget(self.remEntryBtn)
        entryListBox = QGroupBox("مدخلات متعددة (Batch)")
        v = QVBoxLayout()
        v.addWidget(self.entryList)
        v.addLayout(elBtns)
        entryListBox.setLayout(v)

        self.filesList = QListWidget()
        self.addFileBtn = QPushButton("إضافة ملف…")
        self.remFileBtn = QPushButton("حذف المحدد")
        self.addFileBtn.clicked.connect(self.add_file)
        self.remFileBtn.clicked.connect(self.remove_file)

        flBtns = QHBoxLayout()
        flBtns.addWidget(self.addFileBtn)
        flBtns.addWidget(self.remFileBtn)
        filesBox = QGroupBox("ملفات موارد إضافية (--add-data)")
        vf = QVBoxLayout()
        vf.addWidget(self.filesList)
        vf.addLayout(flBtns)
        filesBox.setLayout(vf)

        self.foldersList = QListWidget()
        self.addFolderBtn = QPushButton("إضافة مجلد…")
        self.remFolderBtn = QPushButton("حذف المحدد")
        self.addFolderBtn.clicked.connect(self.add_folder)
        self.remFolderBtn.clicked.connect(self.remove_folder)

        fdBtns = QHBoxLayout()
        fdBtns.addWidget(self.addFolderBtn)
        fdBtns.addWidget(self.remFolderBtn)
        foldersBox = QGroupBox("مجلدات موارد إضافية (--add-data)")
        vfd = QVBoxLayout()
        vfd.addWidget(self.foldersList)
        vfd.addLayout(fdBtns)
        foldersBox.setLayout(vfd)

        self.oneFileChk = QCheckBox("بناء ملف واحد -F (موصى به)")
        self.oneFileChk.setChecked(True)
        self.consoleChk = QCheckBox("إظهار الكونسول (Console)")
        self.consoleChk.setChecked(False)
        self.cleanChk = QCheckBox("تنظيف قبل البناء --clean")
        self.cleanChk.setChecked(True)

        self.iconLine = QLineEdit()
        self.iconBtn = QPushButton("اختيار أيقونة .ico…")
        self.iconBtn.clicked.connect(self.pick_icon)

        icoLayout = QHBoxLayout()
        icoLayout.addWidget(QLabel("الأيقونة:"))
        icoLayout.addWidget(self.iconLine)
        icoLayout.addWidget(self.iconBtn)

        self.manifestLine = QLineEdit()
        self.manifestBtn = QPushButton("اختيار ملف .manifest…")
        self.manifestBtn.clicked.connect(self.pick_manifest)

        manLayout = QHBoxLayout()
        manLayout.addWidget(QLabel("Manifest:"))
        manLayout.addWidget(self.manifestLine)
        manLayout.addWidget(self.manifestBtn)

        self.outLine = QLineEdit(os.path.abspath("output"))
        self.outBtn = QPushButton("مكان الإخراج…")
        self.outBtn.clicked.connect(self.pick_output)

        outLayout = QHBoxLayout()
        outLayout.addWidget(QLabel("مجلد الإخراج (distpath):"))
        outLayout.addWidget(self.outLine)
        outLayout.addWidget(self.outBtn)

        optBox = QGroupBox("الخيارات")
        vo = QVBoxLayout()
        vo.addWidget(self.oneFileChk)
        vo.addWidget(self.consoleChk)
        vo.addWidget(self.cleanChk)
        vo.addLayout(icoLayout)
        vo.addLayout(manLayout)
        vo.addLayout(outLayout)
        optBox.setLayout(vo)

        self.buildBtn = QPushButton("بدء التحويل py → exe")
        self.buildBtn.clicked.connect(self.start_build)
        self.cancelBtn = QPushButton("إلغاء")
        self.cancelBtn.setEnabled(False)
        self.cancelBtn.clicked.connect(self.cancel_build)

        bb = QHBoxLayout()
        bb.addWidget(self.buildBtn)
        bb.addWidget(self.cancelBtn)

        self.cmdPreview = QPlainTextEdit()
        self.cmdPreview.setReadOnly(True)
        self.cmdPreview.setPlaceholderText("معاينة أوامر PyInstaller ستظهر هنا…")

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("سجل عملية البناء…")

        logBox = QGroupBox("السجل")
        vl = QVBoxLayout()
        vl.addWidget(self.cmdPreview)
        vl.addWidget(self.log)
        logBox.setLayout(vl)

        topRow = QHBoxLayout()
        topRow.addWidget(QLabel("الوضع:"))
        topRow.addWidget(self.modeCombo)
        topRow.addStretch(1)

        leftCol = QVBoxLayout()
        leftCol.addLayout(topRow)
        leftCol.addWidget(entryBox)
        leftCol.addWidget(entryListBox)
        leftCol.addWidget(filesBox)
        leftCol.addWidget(foldersBox)

        rightCol = QVBoxLayout()
        rightCol.addWidget(optBox)
        rightCol.addLayout(bb)
        rightCol.addWidget(logBox)

        root = QHBoxLayout(cw)
        root.addLayout(leftCol, 2)
        root.addLayout(rightCol, 3)

        self._on_mode_changed(0)
        self.thread: QThread | None = None
        self.worker: BuildWorker | None = None

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

    def _make_commands(self) -> List[List[str]]:
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

        cmds: List[List[str]] = []
        for e in entries:
            if not os.path.isfile(e):
                continue
            cmd = base_args + [e]
            cmds.append(cmd)
        return cmds

    def start_build(self):
        if not shutil.which("python") and not shutil.which("python3") and not shutil.which("py"):
            if QMessageBox.question(self, "Python غير موجود", "تعذر العثور على بيئة Python. هل ترغب في تنزيلها الآن؟", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                webbrowser.open("https://www.python.org/downloads/")
                if os.name == "nt" and shutil.which("winget"):
                    subprocess.call(["winget", "install", "Python"])
            return
         
        if shutil.which("pyinstaller") is None:
            QMessageBox.critical(self, "PyInstaller غير موجود", "تعذر العثور على PyInstaller. ثبّت الحزمة بالأمر:\n\n    pip install pyinstaller\n\nثم أعد المحاولة.")
            return

        cmds = self._make_commands()
        if not cmds:
            QMessageBox.warning(self, "لا يوجد مدخلات", "حدّد سكربت رئيسي أو أضف سكربتات في وضع Batch.")
            return

        preview = "\n\n".join(" ".join(map(quote, c)) for c in cmds)
        self.cmdPreview.setPlainText(preview)

        self.buildBtn.setEnabled(False)
        self.cancelBtn.setEnabled(True)
        self.log.clear()

        self.thread = QThread()
        self.worker = BuildWorker(commands=cmds, cwd=os.getcwd())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.line.connect(self._append_log)
        self.worker.done.connect(self._build_finished)
        self.thread.start()

    def cancel_build(self):
        if self.worker:
            self.worker.stop()
        if self.thread and self.thread.isRunning():
            pass
        self.buildBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)

    def _append_log(self, text: str):
        self.log.appendPlainText(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def _build_finished(self, ok: bool):
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
        self.worker = None
        self.buildBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        if ok:
            QMessageBox.information(self, "تم", "انتهى البناء بدون أخطاء الملفات داخل مجلد الإخراج المحدد.")
        else:
            QMessageBox.warning(self, "انتهى مع مشاكل", "تحقق من السجل لمعرفة تفاصيل الخطأ.")
        if QMessageBox.question(self, "فتح مجلد الإخراج", "هل ترغب في فتح مجلد الإخراج الآن؟", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            outdir = self.outLine.text().strip() or os.path.abspath("output")
            if os.path.isdir(outdir):
                os.startfile(outdir) if os.name == "nt" else subprocess.call(["xdg-open", outdir])
            else:
                QMessageBox.warning(self, "مجلد الإخراج غير موجود", f"لم يتم العثور على مجلد الإخراج: {outdir}")
                if os.name == "nt":
                    os.startfile(outdir)
                else:
                    subprocess.call(["xdg-open", outdir])

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    StartTime = time.time()
    Login = "log.txt"
    try:
        with open(Login, "a", encoding="utf-8") as log:
            log.write(f"[START] {time.ctime()}\n")
        print("[INFO] Log started.")
    except Exception as e:
        print(f"[ERROR] Could not write to log: {e}")

    try:
        main()
    except Exception as e:
        print(f"[ERROR] Unexpected error occurred: {e}")

    finally:
        EndTime = time.time()
        duration = EndTime - StartTime
        try:
            with open(Login, "a", encoding="utf-8") as log:
                log.write(f"[END] {time.ctime()} - Duration: {duration:.2f} seconds\n\n")
            print(f"[INFO] Session duration saved: {duration:.2f} seconds.")
        except Exception as e:
            with open(Login, "a", encoding="utf-8") as log:
                log.write(f"[ERROR] Failed to write session end to log: {e}\n")