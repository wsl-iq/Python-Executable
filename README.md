### **Executable to Python converter**

---

### **About**

- **This project provides a graphical tool built with `PyQt5` that allows developers to easily convert their Python scripts `(.py)` into Windows executables `(.exe)`.**
 - **It integrates PyInstaller in the backend while offering a modern user interface to handle files, folders, and additional build options.**

 ---

### **what Features?**

---

**Version `3.0.0`**

- **settings json**
- **light theme**
- **interpreter choice**
- **psutil monitor `CPU` + `RAM`**
- **advanced PyInstaller options**
- **drag & drop**
- **log export**
- **generate `.spec`**
- **open folders**
- **reset defaults**
- **sound notify**
- **chacking in Update**
- **Request admin privileges radio button**

---

### **1- Plugin System**
- **Extensible plugin system**
- **Dynamic plugin loading from the `plugins` folder**
- **Implement various hooks**
```Python
class PluginManager:
    def load_plugins(self): ...
    def execute_hook(self, hook_name, *args, **kwargs): ...
```


### **2-Virtual Environment Management**
- **Automatic discovery of virtual environments**
- **Support for `venv`, `virtualenv`, and `conda`**
- **Integration with various Python interpreters**
```Python
def find_virtual_environments() -> List[str]:
```

### **3- Advanced Optimization Options**
- **PyInstaller performance enhancements (`--optimize`).**
- **Debug information stripping (`--strip`).**
- **Redirect preference control (stdout/stderr/file).**

```Python
self.optimizeChk = QCheckBox("Enable performance optimizations --optimize")
self.stripChk = QCheckBox("Remove unnecessary information --strip")
self.redirectCombo = QComboBox()
self.redirectCombo.addItems(["No Redirect", "Redirect stdout", "Redirect stderr", "Redirect to File"])
```

### **4- Digital Signature System**
- **Executable file signing capability.**
- **PFX/P12 certificate support.**
- **Timestamp server integration for validation.**

```Python
self.certFileEdit = QLineEdit()   # Signature certificate (.pfx/.p12)
self.certPassEdit = QLineEdit()   # Certificate password
self.timestampCombo = QComboBox() # Timestamp servers
self.timestampCombo.addItems(["None", "http://timestamp.digicert.com", "http://timestamp.verisign.com"])
```

### **5- Ready-made Templates**
- **Pre-configured application templates.**
- **Different configurations for various app types.**
- **Easy customization of template settings.**

```Python
self.templateCombo = QComboBox()
self.templateCombo.addItems([
    "GUI Application",
    "Console Application",
    "Service Application",
    "Web Application",
    "Custom"
])
```

### **6- Advanced Dependency Analyzer**
- **In-depth dependency analysis.**
- **Large file detection and warnings.**
- **Suspicious import detection and smart recommendations.**

```Python
def advanced_dependency_analysis(self, script_path: str) -> Dict[str, Any]:
    # analyze imports, hiddenimports, and large package footprints
    ...
```

### **7- Version Information System**
- **Application metadata management.**
- **Version info integration into build.**
- **Company and developer details fields.**

```Python
version_group = QGroupBox("Version Information")
self.versionEdit = QLineEdit()    # Version number
self.companyEdit = QLineEdit()    # Company name
self.copyrightEdit = QLineEdit()  # Copyright info
```

### **8- Advanced Security Options**
- **Reverse engineering protection options.**
- **Anti-debugging features.**
- **Code obfuscation and packer support.**

```Python
self.obfuscateChk = QCheckBox("Code Obfuscation")
self.antiDebugChk = QCheckBox("Anti-Debug Protection")
self.packerChk = QCheckBox("Use Packer Files")
```

### **9- Multi-Platform Support**
- **Build for multiple operating systems.**
- **Platform-specific configuration presets.**
- **Cross-platform compatibility checks.**

```Python
self.platformCombo = QComboBox()
self.platformCombo.addItems([
    "Windows (win32)",
    "Windows 64-bit (win64)",
    "Linux",
    "macOS"
])
```

### **10- Integrated Reporting System**
- **Detailed build reports and logs.**
- **Performance statistics and analysis.**
- **Output artifact inspection.**

```Python
def generate_build_report(self, duration: float, output_path: str):
    # compile build metadata, size, warnings, and timing
    ...
```

### **11- Advanced User Interface**
- **Organized tabbed interface for sections.**
- **Splitter layout management for resizable panes.**
- **Enhanced user experience and accessibility.**

```Python
tab_widget = QTabWidget()
tab_widget.addTab(basic_tab, "Basic")
tab_widget.addTab(advanced_tab, "Advanced")
tab_widget.addTab(security_tab, "Security")
```

### **12- Backup System**
- **Automatic backup creation for settings.**
- **Settings preservation and easy restoration.**
- **Versioned backups with timestamps.**

```Python
def create_backup(self):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file = f"settings_backup_{timestamp}.json"
    # save current settings to backup_file
    ...
```

### **13- Output Testing System**
- **Built-in output testing and validation.**
- **Direct execution from interface with sandboxing.**
- **Automatic error detection and reporting.**

```Python
def test_output(self):
    # run basic tests on the generated executable
    ...

def run_executable(self, exe_path):
    # execute with selected parameters and capture output
    ...
```

### **14- Advanced Resource Management**
- **Resource compression options for smaller builds.**
- **File encryption capabilities for bundled resources.**
- **Memory efficiency management and tuning.**

```Python
self.compressionCombo = QComboBox()
self.compressionCombo.addItems(["No Compression", "Normal Compression", "High Compression"])
self.encryptionChk = QCheckBox("Encrypt Resources")
```

### **15- IDE Integration**
- **VS Code and PyCharm integration support.**
- **Custom IDE launch and configuration.**
- **One-click open project in preferred IDE.**

```Python
# settings example
"ide_integration": {
    "vscode": False,
    "pycharm": False
}
```

### **16- Code Audit System**
- **Automated security scanning and quality checks.**
- **Static analysis and vulnerability detection.**
- **Actionable suggestions and fix hints.**

```Python
def code_audit(self):
    # run linters, security checks, and produce a report
    ...
```

### **17- Multi-Build System Support**
- **Support multiple packers/build systems.**
- **Fallbacks and compatibility layers.**
- **User-selectable build backend.**

```Python
self.buildSystemCombo = QComboBox()
self.buildSystemCombo.addItems([
    "PyInstaller",
    "cx_Freeze",
    "Nuitka",
    "PyOxidizer"
])
```

### **18- Help and Documentation System**
- **Comprehensive, searchable documentation.**
- **Program information and user guide access.**
- **Contextual help and tooltips.**

```Python
def show_documentation(self):
    # open local/docs or remote docs page
    ...

def about_program(self):
    # display about dialog with version and authors
    ...
```

### **19- Advanced Logging System**
- **Detailed logging with levels and filters.**
- **Command preview before execution.**
- **Build reports and exportable logs.**

```Python
logs_tab = QTabWidget()
logs_tab.addTab(cmd_tab, "Command Preview")
logs_tab.addTab(log_tab, "Build Log")
logs_tab.addTab(report_tab, "Reports")
```

### **20- Visual Enhancements**
- **Dark/Light theme support and custom color schemes.**
- **Attractive and accessible user interface.**
- **Runtime theme switching and persistence.**

```Python
def apply_dark_theme(self):
    # apply stylesheet for dark mode
    ...

def apply_light_theme(self):
    # apply stylesheet for light mode
    ...
```

---

- **Converting files from `(.Py)` format to `(.exe)` format.**
- **Convert multiple files at once `(.py)`.**
- **Add entire `folders` containing texts/resources.**

---
### **Options**
- **Enable/disable console window (`GUI` mode or `CLI` mode).**
- **Add a custom icon `(.ico)`.**
- **Include a `(.manifest)` file for advanced configuration.**

---

### **OUTPUT**

- **Automatically creates in the directory Folder `output`.**

```
output\
┗─> file.exe
```

---

### **Installation**

- **Download Version Python 3.9+**
- [![Download Python](https://img.shields.io/badge/Download-Python-blue?logo=python&logoColor=white)](https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe)

- **Requirements**
- **[PyInstaller](https://pyinstaller.org/)**
- **[PyQt5](https://pypi.org/project/PyQt5/)**

- **install Packages Python `pip`.**

```
$ pip install pyinstaller pyqt5
```
### **OR**

```
$ pip install -r requirements.txt
```

### **OR**

```
$ setup.bat
```

---

### **Run**

```
Ppython PyToExe.py
```

---

### **See the instructions**

- **[CODE OF CONDUCT](https://github.com/wsl-iq/Python-Executable/blob/main/CODE_OF_CONDUCT.md)**

- **[CONTRIBUTING](https://github.com/wsl-iq/Python-Executable/blob/main/CONTRIBUTING.md)**
- **[MIT License](https://github.com/wsl-iq/Python-Executable/blob/main/LICENSE)**

---

### **My WebSite**
- **[wsl-iq.github.io](https://wsl-iq.github.io/)**
- **[From Python To Executable](https://wsl-iq.github.io/Python-Executable/)**

---

### **Download**
**[Python Executable 32/64 Bit]()**

**[Python Executable MSI]()**

**[PythonExecutable Later V1 , V2]()**

---

### **Languages**

| Arabic (العربية) | English |
|------------------|---------|
|✅               |❌ **SOON**|

---


