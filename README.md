### Py to EXE Converter (with PyQt5 GUI)

### **Overview**
This project provides a **graphical tool built with PyQt5** that allows developers to easily convert their Python scripts (`.py`) into Windows executables (`.exe`).  
It integrates **PyInstaller** in the backend while offering a modern user interface to handle files, folders, and additional build options.

---

### **Features**
- **File Selection**:  
  - Convert a single `.py` file.  
  - Convert multiple `.py` files at once.  
  - Add complete folders containing scripts/resources.  

- **Build Options**:  
  - Enable/disable console window (GUI mode or CLI mode).  
  - Add a custom **icon** (`.ico`).  
  - Include a **manifest file** for advanced configuration.  

- **Output Management**:  
  - Automatically generates the `.exe` in an `output/` directory.  

---

### **Requirements**
- Python **3.8+**
- [PyInstaller](https://pyinstaller.org/)
- [PyQt5](https://pypi.org/project/PyQt5/)

**You can install them quickly with:**

```bash
pip install pyinstaller pyqt5
