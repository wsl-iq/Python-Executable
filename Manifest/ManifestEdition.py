import sys, os, threading, codecs, xml.dom.minidom, re, zipfile, tempfile, shutil
from datetime import datetime
from PyQt5.QtCore import Qt, QRegularExpression, pyqtSignal, QSettings, QSize, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QThread, QObject, QCoreApplication, QProcess, QEvent
from PyQt5.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QIcon, QTextDocument, QTextOption, QColor, QKeySequence, QPalette, QPainter, QTextCursor, QPixmap, QCloseEvent, QBrush
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, 
    QFileDialog, QMessageBox, QPushButton, QLabel, QToolBar, QWidget, QAction, 
    QLineEdit, QStyle, QSpacerItem, QSizePolicy, QShortcut, QComboBox, QSpinBox, 
    QDoubleSpinBox, QTabWidget, QMenu, QCheckBox, QToolButton, QProgressBar, 
    QSplitter, QTextEdit, QListWidget, QListWidgetItem, QFrame, QTreeWidget, 
    QTreeWidgetItem, QGroupBox, QInputDialog, QColorDialog, QFontDialog
)

# تكوينات البرنامج
CONFIG = {
    'dark_bg': '#1e1e1e',
    'dark_sidebar': '#252526',
    'dark_text': '#d4d4d4',
    'light_bg': '#ffffff',
    'light_text': '#000000',
    'backup_interval': 300000,  # 5 دقائق
    'max_recent_files': 10,
    'auto_save_interval': 60000,  # دقيقة واحدة
    'tree_update_delay': 100
}

MANIFEST_TAGS = {
    "assembly": ["manifestVersion"],
    "assemblyIdentity": ["name","version","processorArchitecture","publicKeyToken","language","type"],
    "description": [],
    "trustInfo": [],
    "security": [],
    "requestedPrivileges": [],
    "requestedExecutionLevel": ["level","uiAccess"],
    "compatibility": [],
    "application": [],
    "windowsSettings": [],
    "dpiAware": [],
    "dpiAwareness": [],
    "dependency": [],
    "dependentAssembly": [],
    "file": ["name","hashalgorithm","hash"],
    "comInterfaceExternalProxyStub": [],
    "noInherit": [],
    "list": [],
    "uiAccess": [],
    "ms_compatibility": [],
    "ms_asmv2": [],
    "ms_windowsSettings": [],
}

MANIFEST_COMMON_ATTRS = ["xmlns","xmlns:asmv3","xmlns:asmv2","xmlns:asmv1","xmlns:asm","xmlns:ms_asmv2","xmlns:ms_windowsSettings","publicKeyToken","processorArchitecture","version","name","type","language","uiAccess","level"]

class TreeBuilderThread(QThread):
    """خيط منفصل لبناء شجرة XML"""
    tree_built = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.xml_text = ""
        
    def build_tree(self, xml_text):
        self.xml_text = xml_text
        self.start()
        
    def run(self):
        try:
            if not self.xml_text or not self.xml_text.strip():
                self.tree_built.emit(None)
                return
            dom = xml.dom.minidom.parseString(self.xml_text.encode('utf-8', 'ignore'))
            self.tree_built.emit(dom)
        except Exception:
            self.tree_built.emit(None)

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.update_formats()
        
    def update_formats(self):
        if self.is_dark:
            self.formats = {
                'keyword': self._fmt(QColor(197, 134, 192), QFont.Bold),
                'operator': self._fmt(QColor(255, 215, 0)),
                'brace': self._fmt(QColor(255, 255, 255)),
                'defclass': self._fmt(QColor(86, 156, 214), QFont.Bold),
                'string': self._fmt(QColor(206, 145, 120)),
                'string2': self._fmt(QColor(206, 145, 120)),
                'comment': self._fmt(QColor(106, 153, 85), italic=True),
                'self': self._fmt(QColor(78, 201, 176), QFont.Bold),
                'numbers': self._fmt(QColor(181, 206, 168)),
                'import': self._fmt(QColor(86, 156, 214), QFont.Bold),
                'decorator': self._fmt(QColor(220, 220, 170)),
            }
        else:
            self.formats = {
                'keyword': self._fmt(QColor(0, 0, 255), QFont.Bold),
                'operator': self._fmt(QColor(136, 0, 0)),
                'brace': self._fmt(QColor(0, 0, 0)),
                'defclass': self._fmt(QColor(79, 118, 172), QFont.Bold),
                'string': self._fmt(QColor(163, 21, 21)),
                'string2': self._fmt(QColor(163, 21, 21)),
                'comment': self._fmt(QColor(0, 128, 0), italic=True),
                'self': self._fmt(QColor(135, 0, 135), QFont.Bold),
                'numbers': self._fmt(QColor(0, 128, 128)),
                'import': self._fmt(QColor(79, 118, 172), QFont.Bold),
                'decorator': self._fmt(QColor(102, 102, 0)),
            }
            
        self.keywords = [
            'and', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'exec', 'finally',
            'for', 'from', 'global', 'if', 'import', 'in',
            'is', 'lambda', 'not', 'or', 'pass', 'print',
            'raise', 'return', 'try', 'while', 'yield',
            'None', 'True', 'False', 'async', 'await'
        ]
        
    def _fmt(self, color, weight=QFont.Normal, italic=False):
        f = QTextCharFormat()
        f.setForeground(color)
        f.setFontWeight(weight)
        f.setFontItalic(italic)
        return f
        
    def set_dark_mode(self, dark):
        self.is_dark = dark
        self.update_formats()
        self.rehighlight()
        
    def highlightBlock(self, text):
        self._highlight_multiline_comments(text)
        self._highlight_keywords(text)
        self._highlight_functions_classes(text)
        self._highlight_self(text)
        self._highlight_numbers(text)
        self._highlight_strings(text)
        self._highlight_single_line_comments(text)
        self._highlight_operators(text)
        
    def _highlight_multiline_comments(self, text):
        self.setCurrentBlockState(0)
        start_index = 0
        
        if self.previousBlockState() != 1:
            start_index = text.find('"""')
            if start_index == -1:
                start_index = text.find("'''")
                
        while start_index >= 0:
            end_index = text.find('"""', start_index + 3)
            if end_index == -1:
                end_index = text.find("'''", start_index + 3)
                
            if end_index == -1:
                self.setFormat(start_index, len(text) - start_index, self.formats['comment'])
                self.setCurrentBlockState(1)
                break
            else:
                comment_length = end_index - start_index + 3
                self.setFormat(start_index, comment_length, self.formats['comment'])
                start_index = text.find('"""', end_index + 3)
                if start_index == -1:
                    start_index = text.find("'''", end_index + 3)
                    
    def _highlight_keywords(self, text):
        for keyword in self.keywords:
            pattern = r'\b' + keyword + r'\b'
            regex = QRegularExpression(pattern)
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.formats['keyword'])
                
    def _highlight_functions_classes(self, text):
        def_pattern = r'\b(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
        regex = QRegularExpression(def_pattern)
        it = regex.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(1), match.capturedLength(1), self.formats['keyword'])
            self.setFormat(match.capturedStart(2), match.capturedLength(2), self.formats['defclass'])
            
    def _highlight_self(self, text):
        self_pattern = r'\b(self|cls)\b'
        regex = QRegularExpression(self_pattern)
        it = regex.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.formats['self'])
            
    def _highlight_numbers(self, text):
        num_pattern = r'\b[0-9]+\b'
        regex = QRegularExpression(num_pattern)
        it = regex.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.formats['numbers'])
            
    def _highlight_strings(self, text):
        string_pattern = r'("[^"\\]*(\\.[^"\\]*)*")|(\'[^\'\\]*(\\.[^\'\\]*)*\')'
        regex = QRegularExpression(string_pattern)
        it = regex.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.formats['string'])
            
    def _highlight_single_line_comments(self, text):
        comment_index = text.find('#')
        if comment_index >= 0:
            in_string = False
            for j in range(comment_index):
                if text[j] in '"\'':
                    in_string = not in_string
            if not in_string:
                self.setFormat(comment_index, len(text) - comment_index, self.formats['comment'])
                
    def _highlight_operators(self, text):
        operators = ['=', '==', '!=', '<', '>', '<=', '>=', '\+', '-', '\*', '/', '//', '%', '\*\*', '\+=', '-=', '\*=', '/=', '%=', '&', '\|', '\^', '~', '<<', '>>']
        for op in operators:
            op_pattern = r'(' + op + r')'
            regex = QRegularExpression(op_pattern)
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.formats['operator'])

class ManifestHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.error_lines = set()
        self.update_formats()
        
    def update_formats(self):
        if self.is_dark:
            self.formats = {
                "tag": self._fmt(QColor("#569cd6"), QFont.DemiBold),
                "attr": self._fmt(QColor("#9cdcfe")),
                "value": self._fmt(QColor("#ce9178")),
                "comment": self._fmt(QColor("#6a9955"), italic=True),
                "doctype": self._fmt(QColor("#4ec9b0"), QFont.DemiBold),
                "pi": self._fmt(QColor("#d4d4d4")),
                "variable": self._fmt(QColor("#d7ba7d")),
                "error": self._fmt(QColor("#f48771"), background=QColor("#5a1d1d")),
            }
        else:
            self.formats = {
                "tag": self._fmt(QColor("#1f4b99"), QFont.DemiBold),
                "attr": self._fmt(QColor("#7f2aac")),
                "value": self._fmt(QColor("#aa5500")),
                "comment": self._fmt(QColor("#008000"), italic=True),
                "doctype": self._fmt(QColor("#00695c"), QFont.DemiBold),
                "pi": self._fmt(QColor("#616161")),
                "variable": self._fmt(QColor("#8b4513")),
                "error": self._fmt(QColor("#b71c1c"), background=QColor("#ffcdd2")),
            }
            
        self.rules = []
        self.comment_start = QRegularExpression(r"<!--")
        self.comment_end = QRegularExpression(r"-->")
        self.rules.append((QRegularExpression(r"</?[A-Za-z_][A-Za-z0-9._:-]*"), "tag"))
        self.rules.append((QRegularExpression(r"/>"), "tag"))
        self.rules.append((QRegularExpression(r">"), "tag"))
        self.rules.append((QRegularExpression(r"\b[A-Za-z_][A-Za-z0-9._:-]*(?=\s*=)"), "attr"))
        self.rules.append((QRegularExpression(r"\"[^\"<>]*\""), "value"))
        self.rules.append((QRegularExpression(r"<!DOCTYPE[^>]*>"), "doctype"))
        self.rules.append((QRegularExpression(r"<\?xml[^>]*\?>"), "pi"))
        self.rules.append((QRegularExpression(r"%[A-Za-z_][A-Za-z0-9_]*%"), "variable"))
        
    def _fmt(self, color, weight=QFont.Normal, italic=False, background=None):
        f = QTextCharFormat()
        f.setForeground(color)
        f.setFontWeight(weight)
        f.setFontItalic(italic)
        if background:
            f.setBackground(background)
        return f
        
    def set_dark_mode(self, dark):
        self.is_dark = dark
        self.update_formats()
        self.rehighlight()
        
    def set_error_lines(self, lines):
        self.error_lines = set(lines)
        self.rehighlight()
        
    def clear_errors(self):
        self.error_lines.clear()
        self.rehighlight()
        
    def highlightBlock(self, text):
        # تظليل الأخطاء أولاً
        block_number = self.currentBlock().blockNumber()
        if block_number in self.error_lines:
            self.setFormat(0, len(text), self.formats["error"])
            
        self.setCurrentBlockState(0)
        start_idx = 0
        
        if self.previousBlockState() != 1:
            start_match = self.comment_start.match(text)
            start_idx = start_match.capturedStart() if start_match.hasMatch() else -1
        else:
            start_idx = 0
            
        while start_idx >= 0:
            end_match = self.comment_end.match(text, start_idx)
            end_idx = end_match.capturedEnd() if end_match.hasMatch() else -1
            if end_idx == -1:
                self.setFormat(start_idx, len(text) - start_idx, self.formats["comment"])
                self.setCurrentBlockState(1)
                break
            else:
                length = end_idx - start_idx
                self.setFormat(start_idx, length, self.formats["comment"])
                start_match = self.comment_start.match(text, end_idx)
                start_idx = start_match.capturedStart() if start_match.hasMatch() else -1
                
        if self.currentBlockState() != 1:
            for pattern, key in self.rules:
                it = pattern.globalMatch(text)
                while it.hasNext():
                    m = it.next()
                    self.setFormat(m.capturedStart(), m.capturedLength(), self.formats[key])

class CodeEditor(QPlainTextEdit):
    request_rebuild_tree = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # إلغاء ترقيم الأسطر نهائياً - إزالة كل ما يتعلق بـ line_number_area
        # لا يوجد line_number_area ولا أي إشارات مرتبطة به
        
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        # ضبط المسافة للعلامة التبويب
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        
        self.is_dark = False
        self._rebuild_delay = QTimer(self)
        self._rebuild_delay.setSingleShot(True)
        self._rebuild_delay.timeout.connect(self.request_rebuild_tree.emit)
        
        self._completer_popup = QListWidget()
        self._completer_popup.setWindowFlags(Qt.Popup)
        self._completer_popup.itemClicked.connect(self._insert_completion)
        self._complete_mode = None
        self._last_tag = ""
        self._last_attrs = []
        self.error_lines = []
        
        # تعيين لون الخلفية
        self.setStyleSheet("QPlainTextEdit { background-color: %s; }" % 
                          (CONFIG['dark_bg'] if self.is_dark else CONFIG['light_bg']))
        
        # إزالة الهوامش - لا يوجد ترقيم للأسطر
        self.setViewportMargins(0, 0, 0, 0)
        
    def highlight_current_line(self):
        """تظليل السطر الحالي"""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(70, 70, 100, 80) if self.is_dark else QColor(255, 255, 200, 80)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        self.setExtraSelections(extra_selections)
        
    def set_dark_mode(self, dark):
        """تغيير الوضع"""
        self.is_dark = dark
        self.highlight_current_line()
        
        # تحديث لون الخلفية
        bg_color = CONFIG['dark_bg'] if dark else CONFIG['light_bg']
        self.setStyleSheet(f"QPlainTextEdit {{ background-color: {bg_color}; }}")
        
    def keyPressEvent(self, event):
        """معالجة أحداث لوحة المفاتيح"""
        # معالجة المفاتيح الخاصة
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_enter_key(event)
            return
            
        if event.key() == Qt.Key_Tab:
            self.insertPlainText(' ' * 4)
            return
            
        if event.key() == Qt.Key_Backtab:
            self._handle_backtab()
            return
            
        if event.text() == ">":
            super().keyPressEvent(event)
            self._auto_close_tag()
            self._maybe_show_completion()
            return
            
        if event.text() == "<":
            super().keyPressEvent(event)
            self._show_tag_completion()
            return
            
        if event.text() == " ":
            super().keyPressEvent(event)
            self._show_attr_completion()
            return
            
        if event.key() in (Qt.Key_Escape,):
            self._completer_popup.hide()
            super().keyPressEvent(event)
            return
            
        # معالجة المفاتيح العادية
        super().keyPressEvent(event)
        
        # إظهار الاقتراحات
        if event.text().isalnum() or event.text() in ['_', ':', '-']:
            self._maybe_show_completion()
            
    def _handle_enter_key(self, event):
        """معالجة مفتاح Enter"""
        cursor = self.textCursor()
        line = cursor.block().text()
        indent = len(line) - len(line.lstrip())
        
        # تنفيذ الإدخال
        super().keyPressEvent(event)
        
        # إضافة المسافات
        if indent > 0:
            self.insertPlainText(' ' * indent)
            
    def _handle_backtab(self):
        """معالجة Shift+Tab"""
        cursor = self.textCursor()
        pos = cursor.position()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 4)
        
        if cursor.selectedText() == '    ':
            cursor.removeSelectedText()
        else:
            cursor.clearSelection()
            cursor.setPosition(pos)
            self.setTextCursor(cursor)
            
    def _current_tag_context(self):
        """الحصول على سياق الوسم الحالي"""
        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()
        
        start = text.rfind("<", 0, pos)
        if start == -1:
            return "", []
            
        end = text.find(">", start, pos)
        chunk = text[start:pos] if end == -1 or end >= pos else text[start:end]
        
        match = re.match(r"<\s*([A-Za-z_][\w\.\-:]*)", chunk)
        if not match:
            return "", []
            
        tag = match.group(1).split(":")[-1]
        attrs = re.findall(r'([A-Za-z_][\w\.\-:]*)\s*=', chunk)
        clean = [a.split(":")[-1] for a in attrs]
        
        return tag, clean
        
    def _show_list_at_cursor(self, items):
        """عرض قائمة الاقتراحات"""
        if not items:
            self._completer_popup.hide()
            return
            
        self._completer_popup.clear()
        for item in items:
            QListWidgetItem(item, self._completer_popup)
            
        cr = self.cursorRect()
        pos = self.mapToGlobal(cr.bottomRight())
        self._completer_popup.move(pos)
        self._completer_popup.setMinimumWidth(220)
        self._completer_popup.show()
        
    def _insert_completion(self, item):
        """إدراج الاقتراح المحدد"""
        text = item.text()
        cursor = self.textCursor()
        
        word = self._current_word_under_cursor()
        if word:
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(word))
            cursor.removeSelectedText()
            
        if self._complete_mode == "tag":
            cursor.insertText(text)
        elif self._complete_mode == "attr":
            cursor.insertText(text + '=""')
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            
        self.setTextCursor(cursor)
        self._completer_popup.hide()
        
    def _current_word_under_cursor(self):
        """الحصول على الكلمة تحت المؤشر"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        return cursor.selectedText()
        
    def _show_tag_completion(self):
        """عرض اقتراحات الوسوم"""
        self._complete_mode = "tag"
        items = sorted(set(list(MANIFEST_TAGS.keys())))
        self._show_list_at_cursor(items)
        
    def _show_attr_completion(self):
        """عرض اقتراحات السمات"""
        tag, attrs = self._current_tag_context()
        if not tag:
            self._completer_popup.hide()
            return
            
        self._complete_mode = "attr"
        base = set(MANIFEST_COMMON_ATTRS)
        base.update(MANIFEST_TAGS.get(tag, []))
        remain = sorted([a for a in base if a not in attrs])
        self._show_list_at_cursor(remain)
        
    def _maybe_show_completion(self):
        """إظهار الاقتراحات إذا كان مناسباً"""
        tag, attrs = self._current_tag_context()
        if tag and (self._last_tag != tag or set(attrs) != set(self._last_attrs)):
            self._last_tag, self._last_attrs = tag, attrs
            self._show_attr_completion()
            
    def _auto_close_tag(self):
        """إغلاق الوسم تلقائياً"""
        cursor = self.textCursor()
        text = self.toPlainText()
        pos = cursor.position()
        
        left = text.rfind("<", 0, pos)
        if left == -1:
            return
            
        seg = text[left:pos]
        if seg.endswith("/"):
            return
            
        match = re.match(r"<\s*([A-Za-z_][\w\.\-:]*)[^>/]*>$", seg)
        if not match:
            return
            
        name = match.group(1).split(":")[-1]
        tail = text[pos:pos+1]
        
        if tail and tail[0] == "<":
            return
            
        closing = f"</{name}>"
        cursor.insertText(closing)
        cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(closing))
        self.setTextCursor(cursor)
        
    def set_error_lines(self, lines):
        """تعيين أسطر الأخطاء - يمكن استخدامها للتظليل"""
        self.error_lines = lines

class FindReplaceBar(QWidget):
    find_next = pyqtSignal(str, bool, bool)
    find_prev = pyqtSignal(str, bool, bool)
    replace_one = pyqtSignal(str, str, bool, bool)
    replace_all = pyqtSignal(str, str, bool, bool)
    find_in_all_tabs = pyqtSignal(str, bool, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5,2,5,2)
        
        layout.addWidget(QLabel("بحث:"))
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("النص المطلوب البحث عنه...")
        layout.addWidget(self.find_edit)
        
        self.btn_prev = QPushButton("السابق")
        self.btn_next = QPushButton("التالي")
        layout.addWidget(self.btn_prev)
        layout.addWidget(self.btn_next)
        
        layout.addWidget(QLabel("استبدال:"))
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("النص البديل...")
        layout.addWidget(self.replace_edit)
        
        self.btn_replace = QPushButton("استبدال")
        self.btn_replace_all = QPushButton("استبدال الكل")
        layout.addWidget(self.btn_replace)
        layout.addWidget(self.btn_replace_all)
        
        self.case_check = QCheckBox("مطابقة الحالة")
        self.regex_check = QCheckBox("تعبير نمطي")
        layout.addWidget(self.case_check)
        layout.addWidget(self.regex_check)
        
        self.btn_find_all = QPushButton("بحث في الكل")
        layout.addWidget(self.btn_find_all)
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(22,22)
        layout.addWidget(self.btn_close)
        
        self.btn_prev.clicked.connect(self._prev)
        self.btn_next.clicked.connect(self._next)
        self.btn_replace.clicked.connect(self._rep)
        self.btn_replace_all.clicked.connect(self._rep_all)
        self.btn_find_all.clicked.connect(self._find_all)
        self.find_edit.textChanged.connect(lambda _: self._auto())
        self.btn_close.clicked.connect(self.hide)
        
        self.setVisible(False)
        
    def show_bar(self):
        self.setVisible(True)
        self.find_edit.setFocus()
        self.find_edit.selectAll()
        
    def _auto(self):
        text = self.find_edit.text()
        if text:
            self.find_next.emit(text, self.case_check.isChecked(), self.regex_check.isChecked())
            
    def _next(self):
        self.find_next.emit(self.find_edit.text(), self.case_check.isChecked(), self.regex_check.isChecked())
        
    def _prev(self):
        self.find_prev.emit(self.find_edit.text(), self.case_check.isChecked(), self.regex_check.isChecked())
        
    def _rep(self):
        self.replace_one.emit(self.find_edit.text(), self.replace_edit.text(), self.case_check.isChecked(), self.regex_check.isChecked())
        
    def _rep_all(self):
        self.replace_all.emit(self.find_edit.text(), self.replace_edit.text(), self.case_check.isChecked(), self.regex_check.isChecked())
        
    def _find_all(self):
        self.find_in_all_tabs.emit(self.find_edit.text(), self.case_check.isChecked(), self.regex_check.isChecked())

class ModernTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.close_tab)
        
    def close_tab(self, index):
        widget = self.widget(index)
        if hasattr(widget, 'editor_tab'):
            if widget.editor_tab.check_save_before_close():
                self.removeTab(index)
                widget.deleteLater()
        else:
            self.removeTab(index)
            widget.deleteLater()

class EditorTab(QWidget):
    content_changed = pyqtSignal()
    
    def __init__(self, main_window, dark=False, font_name="Courier New", font_size=11):
        super().__init__()
        self.main_window = main_window
        self.file_path = ""
        self.original_content = ""
        self.is_modified = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.editor = CodeEditor()
        font = QFont(font_name, font_size)
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        
        self.highlighter = ManifestHighlighter(self.editor.document())
        self.editor.set_dark_mode(dark)
        self.highlighter.set_dark_mode(dark)
        
        layout.addWidget(self.editor)
        
        self.editor.textChanged.connect(self._on_changed)
        self.editor.request_rebuild_tree.connect(self.content_changed)
        
    def set_content(self, text):
        self.editor.blockSignals(True)
        self.editor.setPlainText(text)
        self.editor.blockSignals(False)
        self.original_content = text
        self.is_modified = False
        
    def _on_changed(self):
        self.is_modified = (self.editor.toPlainText() != self.original_content)
        
    def check_save_before_close(self):
        if self.is_modified:
            ret = QMessageBox.question(self, "حفظ الملف", 
                                      "توجد تعديلات غير محفوظة. هل تريد حفظ الملف قبل الإغلاق؟",
                                      QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if ret == QMessageBox.Cancel:
                return False
            if ret == QMessageBox.Yes:
                return self.save_file()
        return True
        
    def save_file(self):
        if self.file_path:
            try:
                with codecs.open(self.file_path, "w", encoding="utf-8", errors="strict") as f:
                    f.write(self.editor.toPlainText())
                self.original_content = self.editor.toPlainText()
                self.is_modified = False
                return True
            except Exception as e:
                QMessageBox.critical(self, "خطأ في الحفظ", str(e))
                return False
        else:
            return self.main_window.save_file_as()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("محرر XML المتقدم - الإصدار 4.0")
        self.setWindowIcon(self._get_standard_icon(QStyle.SP_FileIcon))
        self.resize(1400, 900)
        
        self.settings = QSettings("XML-Editor", "Professional")
        self.file_history = self.settings.value("file_history", []) or []
        self.current_encoding = "utf-8"
        self.auto_save_timer = QTimer(self)
        self.tree_builder = TreeBuilderThread()
        self.tree_builder.tree_built.connect(self._display_tree)
        self.validation_timer = QTimer(self)
        
        # إعداد الواجهة الرئيسية
        self._setup_ui()
        self._connect_signals()
        
        self.add_new_tab()
        self._start_timers()
        
        self.setAcceptDrops(True)
        
    def _get_standard_icon(self, standard_icon):
        return self.style().standardIcon(standard_icon)
        
    def _create_text_icon(self, text):
        """إنشاء أيقونة نصية بسيطة"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)
        
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)
        
        # شريط الأدوات الرئيسي
        self.toolbar = self._build_main_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # شريط الأدوات الإضافي
        self.extra_toolbar = self._build_extra_toolbar()
        main_layout.addWidget(self.extra_toolbar)
        
        # شريط البحث
        self.findbar = FindReplaceBar()
        main_layout.addWidget(self.findbar)
        
        # المقسم الرئيسي
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter, 1)
        
        # اللوحة اليسرى (شجرة XML والملفات الحديثة)
        self.left_panel = self._build_left_panel()
        self.main_splitter.addWidget(self.left_panel)
        
        # المنطقة الوسطى (التبويبات)
        self.tabs = ModernTabWidget()
        self.main_splitter.addWidget(self.tabs)
        
        # اللوحة اليمنى (معلومات وإحصائيات)
        self.right_panel = self._build_right_panel()
        self.main_splitter.addWidget(self.right_panel)
        
        # ضبط نسب المقسم
        self.main_splitter.setSizes([250, 800, 250])
        
        # شريط الحالة
        self.status = self._build_statusbar()
        main_layout.addWidget(self.status)
        
        # قائمة الملفات الحديثة
        self.recent_files_menu = QMenu("ملفات حديثة", self)
        self._update_recent_files_menu()
        
    def _build_main_toolbar(self):
        toolbar = QToolBar("شريط الأدوات الرئيسي")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        
        # ملف
        self.act_new = QAction(self._get_standard_icon(QStyle.SP_FileIcon), "جديد", self)
        self.act_new.setShortcut("Ctrl+N")
        
        self.act_open = QAction(self._get_standard_icon(QStyle.SP_DialogOpenButton), "فتح", self)
        self.act_open.setShortcut("Ctrl+O")
        
        self.act_save = QAction(self._get_standard_icon(QStyle.SP_DialogSaveButton), "حفظ", self)
        self.act_save.setShortcut("Ctrl+S")
        
        self.act_save_as = QAction(self._get_standard_icon(QStyle.SP_FileIcon), "حفظ باسم", self)
        self.act_save_as.setShortcut("Ctrl+Shift+S")
        
        toolbar.addAction(self.act_new)
        toolbar.addAction(self.act_open)
        toolbar.addAction(self.act_save)
        toolbar.addAction(self.act_save_as)
        toolbar.addSeparator()
        
        # تحرير
        self.act_undo = QAction(self._get_standard_icon(QStyle.SP_ArrowBack), "تراجع", self)
        self.act_undo.setShortcut("Ctrl+Z")
        
        self.act_redo = QAction(self._get_standard_icon(QStyle.SP_ArrowForward), "إعادة", self)
        self.act_redo.setShortcut("Ctrl+Y")
        
        self.act_find = QAction(self._get_standard_icon(QStyle.SP_FileDialogContentsView), "بحث", self)
        self.act_find.setShortcut("Ctrl+F")
        
        toolbar.addAction(self.act_undo)
        toolbar.addAction(self.act_redo)
        toolbar.addAction(self.act_find)
        toolbar.addSeparator()
        
        # أدوات XML
        self.act_validate = QAction(self._get_standard_icon(QStyle.SP_DialogApplyButton), "تحقق", self)
        self.act_validate.setShortcut("F5")
        
        self.act_format = QAction(self._get_standard_icon(QStyle.SP_BrowserReload), "تنسيق", self)
        self.act_format.setShortcut("Ctrl+Shift+F")
        
        self.act_minify = QAction(self._get_standard_icon(QStyle.SP_FileDialogDetailedView), "تصغير", self)
        
        toolbar.addAction(self.act_validate)
        toolbar.addAction(self.act_format)
        toolbar.addAction(self.act_minify)
        toolbar.addSeparator()
        
        # عرض
        self.act_theme = QAction(self._get_standard_icon(QStyle.SP_ComputerIcon), "الوضع الداكن", self)
        self.act_theme.setCheckable(True)
        self.act_theme.setChecked(self.settings.value("theme", "light") == "dark")
        
        self.act_wrap = QAction(self._get_standard_icon(QStyle.SP_FileDialogListView), "التفاف النص", self)
        self.act_wrap.setCheckable(True)
        
        toolbar.addAction(self.act_theme)
        toolbar.addAction(self.act_wrap)
        
        return toolbar
        
    def _build_extra_toolbar(self):
        toolbar = QToolBar("شريط الأدوات الإضافي")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        
        # أزرار إضافية
        self.act_collapse_all = QAction("طي الكل", self)
        self.act_expand_all = QAction("توسيع الكل", self)
        self.act_copy_path = QAction("نسخ المسار", self)
        self.act_toggle_comment = QAction("تعليق", self)
        self.act_show_whitespace = QAction("إظهار الفراغات", self)
        self.act_show_whitespace.setCheckable(True)
        
        self.act_show_endl = QAction("إظهار نهاية السطر", self)
        self.act_show_endl.setCheckable(True)
        
        self.act_readonly = QAction("قفل", self)
        self.act_readonly.setCheckable(True)
        
        self.act_compare = QAction("مقارنة", self)
        self.act_export_json = QAction("تصدير JSON", self)
        self.act_stats = QAction("إحصائيات", self)
        self.act_reload = QAction("إعادة تحميل", self)
        self.act_open_folder = QAction("فتح المجلد", self)
        self.act_copy_xpath = QAction("نسخ XPath", self)
        self.act_debug = QAction("وضع المطور", self)
        self.act_debug.setCheckable(True)
        
        # إضافة الأزرار
        for action in [self.act_collapse_all, self.act_expand_all, self.act_copy_path,
                      self.act_toggle_comment, self.act_show_whitespace, self.act_show_endl,
                      self.act_readonly, self.act_compare, self.act_export_json,
                      self.act_stats, self.act_reload, self.act_open_folder,
                      self.act_copy_xpath, self.act_debug]:
            toolbar.addAction(action)
            
        toolbar.addSeparator()
        
        # إعدادات الخط
        toolbar.addWidget(QLabel("الخط:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Courier New", "Consolas", "Monaco", "DejaVu Sans Mono", 
                                  "Source Code Pro", "Fira Code", "Cascadia Code", "Arial", "Times New Roman"])
        self.font_combo.setCurrentText(self.settings.value("editor_font", "Courier New"))
        toolbar.addWidget(self.font_combo)
        
        toolbar.addWidget(QLabel("الحجم:"))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 28)
        self.font_size.setValue(int(self.settings.value("font_size", 11)))
        toolbar.addWidget(self.font_size)
        
        # ترميز الملف
        toolbar.addWidget(QLabel("الترميز:"))
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["UTF-8", "UTF-16", "ANSI", "ASCII"])
        self.encoding_combo.setCurrentText("UTF-8")
        toolbar.addWidget(self.encoding_combo)
        
        return toolbar
        
    def _build_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # شجرة XML
        tree_group = QGroupBox("هيكل XML")
        tree_layout = QVBoxLayout(tree_group)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["العناصر"])
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        tree_layout.addWidget(self.tree)
        layout.addWidget(tree_group)
        
        # الملفات الحديثة
        recent_group = QGroupBox("ملفات حديثة")
        recent_layout = QVBoxLayout(recent_group)
        self.recent_list = QListWidget()
        recent_layout.addWidget(self.recent_list)
        layout.addWidget(recent_group)
        
        return panel
        
    def _build_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # إحصائيات الملف
        stats_group = QGroupBox("إحصائيات")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        search_group = QGroupBox("نتائج البحث")
        search_layout = QVBoxLayout(search_group)
        
        self.search_results = QListWidget()
        search_layout.addWidget(self.search_results)
        
        layout.addWidget(search_group)
        
        return panel
        
    def _build_statusbar(self):
        status_bar = QFrame()
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(6, 2, 6, 2)
        
        self.st_pos = QLabel("السطر: 1, العمود: 1")
        self.st_enc = QLabel("UTF-8")
        self.st_size = QLabel("0 حرف")
        self.st_state = QLabel("محفوظ")
        self.st_xml_status = QLabel("XML صحيح")
        
        layout.addWidget(self.st_pos)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.st_enc)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.st_size)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.st_xml_status)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(self.st_state)
        
        status_bar.setFrameStyle(QFrame.StyledPanel)
        return status_bar
        
    def _connect_signals(self):
        self.act_new.triggered.connect(self.add_new_tab)
        self.act_open.triggered.connect(self.open_file_dialog)
        self.act_save.triggered.connect(self.save_file)
        self.act_save_as.triggered.connect(self.save_file_as)
        
        self.act_undo.triggered.connect(lambda: self._with_editor(lambda e: e.undo()))
        self.act_redo.triggered.connect(lambda: self._with_editor(lambda e: e.redo()))
        self.act_find.triggered.connect(self.toggle_find)
        
        self.act_validate.triggered.connect(self.validate_xml)
        self.act_format.triggered.connect(self.format_xml)
        self.act_minify.triggered.connect(self.minify_xml)
        
        self.act_theme.triggered.connect(self.toggle_theme)
        self.act_wrap.triggered.connect(self.toggle_wrap)
        
        self.act_collapse_all.triggered.connect(lambda: self.tree.collapseAll())
        self.act_expand_all.triggered.connect(lambda: self.tree.expandAll())
        self.act_copy_path.triggered.connect(self._copy_current_path)
        self.act_toggle_comment.triggered.connect(self._toggle_comment)
        self.act_stats.triggered.connect(self._update_stats)
        self.act_reload.triggered.connect(self._reload_current_file)
        self.act_readonly.triggered.connect(self._toggle_readonly)
        
        self.font_combo.currentTextChanged.connect(self.change_font)
        self.font_size.valueChanged.connect(self.change_font_size)
        self.encoding_combo.currentTextChanged.connect(self._change_encoding)
        
        self.tabs.currentChanged.connect(lambda: self._refresh_status())
        self.tabs.currentChanged.connect(lambda: self._rebuild_tree_from_editor())
        
        self.findbar.find_next.connect(self.find_text)
        self.findbar.find_prev.connect(self.find_text_backward)
        self.findbar.replace_one.connect(self.replace_text)
        self.findbar.replace_all.connect(self.replace_all_text)
        self.findbar.find_in_all_tabs.connect(self._find_in_all_tabs)
        
        self.tree.itemClicked.connect(self._jump_to_tree_item)
        self.recent_list.itemClicked.connect(self._open_recent_file)
        
        self.validation_timer.timeout.connect(self.validate_xml)
        
    def _start_timers(self):
        self.backup_timer = QTimer(self)
        self.backup_timer.timeout.connect(self._auto_backup)
        self.backup_timer.start(CONFIG['backup_interval'])
        
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(CONFIG['auto_save_interval'])
        
        self.validation_timer.start(2000)
        
    def _with_editor(self, func):
        tab = self.current_tab()
        if tab:
            func(tab.editor)
            self._refresh_status()
            
    def add_new_tab(self, file_path="", content=""):
        dark = self.act_theme.isChecked()
        tab = EditorTab(self, dark=dark, font_name=self.font_combo.currentText(), font_size=self.font_size.value())
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tab)
        
        file_name = os.path.basename(file_path) if file_path else "مستند جديد"
        index = self.tabs.addTab(container, file_name)
        self.tabs.setCurrentIndex(index)
        
        container.editor_tab = tab
        
        if content:
            tab.set_content(content)
            
        tab.file_path = file_path
        tab.editor.cursorPositionChanged.connect(self._refresh_status)
        tab.content_changed.connect(self._on_tab_content_changed)
        
        self._refresh_status()
        self._rebuild_tree_from_editor()
        
        return tab
        
    def _on_tab_content_changed(self):
        self._rebuild_tree_from_editor()
        
    def current_tab(self):
        widget = self.tabs.currentWidget()
        return getattr(widget, 'editor_tab', None) if widget else None
        
    def get_editor(self):
        tab = self.current_tab()
        return tab.editor if tab else None
        
    def change_font(self, font_name):
        for i in range(self.tabs.count()):
            tab = getattr(self.tabs.widget(i), 'editor_tab', None)
            if tab:
                font = tab.editor.font()
                font.setFamily(font_name)
                tab.editor.setFont(font)
        self.settings.setValue("editor_font", font_name)
        
    def change_font_size(self, size):
        for i in range(self.tabs.count()):
            tab = getattr(self.tabs.widget(i), 'editor_tab', None)
            if tab:
                font = tab.editor.font()
                font.setPointSize(size)
                tab.editor.setFont(font)
        self.settings.setValue("font_size", size)
        
    def _change_encoding(self, encoding):
        self.current_encoding = encoding.lower()
        self.st_enc.setText(encoding)
        
    def apply_theme(self, mode):
        is_dark = (mode == "dark")
        palette = QPalette()
        
        if is_dark:
            palette.setColor(QPalette.Window, QColor(CONFIG['dark_bg']))
            palette.setColor(QPalette.WindowText, QColor(CONFIG['dark_text']))
            palette.setColor(QPalette.Base, QColor(37, 37, 38))
            palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
            palette.setColor(QPalette.ToolTipBase, QColor(CONFIG['dark_bg']))
            palette.setColor(QPalette.ToolTipText, QColor(CONFIG['dark_text']))
            palette.setColor(QPalette.Text, QColor(CONFIG['dark_text']))
            palette.setColor(QPalette.Button, QColor(62, 62, 64))
            palette.setColor(QPalette.ButtonText, QColor(CONFIG['dark_text']))
            palette.setColor(QPalette.Highlight, QColor(14, 99, 156))
            palette.setColor(QPalette.HighlightedText, QColor(CONFIG['dark_text']))
            QApplication.setPalette(palette)
            
            self.act_theme.setIcon(self._get_standard_icon(QStyle.SP_DriveCDIcon))
            self.act_theme.setText("الوضع الفاتح")
        else:
            QApplication.setPalette(QApplication.style().standardPalette())
            self.act_theme.setIcon(self._get_standard_icon(QStyle.SP_ComputerIcon))
            self.act_theme.setText("الوضع الداكن")
            
        for i in range(self.tabs.count()):
            tab = getattr(self.tabs.widget(i), 'editor_tab', None)
            if tab:
                tab.editor.set_dark_mode(is_dark)
                tab.highlighter.set_dark_mode(is_dark)
                
        self.settings.setValue("theme", mode)
        
    def toggle_theme(self):
        self.apply_theme("dark" if self.act_theme.isChecked() else "light")
        
    def toggle_wrap(self):
        editor = self.get_editor()
        if not editor:
            return
        editor.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere if self.act_wrap.isChecked() else QTextOption.NoWrap)
        
    def toggle_find(self):
        if self.findbar.isVisible():
            self.findbar.hide()
        else:
            self.findbar.show_bar()
            
    def find_text(self, text, case_sensitive=False, use_regex=False):
        editor = self.get_editor()
        if not editor or not text:
            return
            
        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
            
        if use_regex:
            pattern = QRegularExpression(text)
            if not case_sensitive:
                pattern.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            cursor = editor.document().find(pattern, editor.textCursor())
        else:
            cursor = editor.document().find(text, editor.textCursor(), flags)
            
        if not cursor.isNull():
            editor.setTextCursor(cursor)
        else:
            QMessageBox.information(self, "بحث", "لم يتم العثور على النص المطلوب")
            
    def find_text_backward(self, text, case_sensitive=False, use_regex=False):
        editor = self.get_editor()
        if not editor or not text:
            return
            
        flags = QTextDocument.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
            
        if use_regex:
            pattern = QRegularExpression(text)
            if not case_sensitive:
                pattern.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            cursor = editor.document().find(pattern, editor.textCursor(), flags)
        else:
            cursor = editor.document().find(text, editor.textCursor(), flags)
            
        if not cursor.isNull():
            editor.setTextCursor(cursor)
        else:
            QMessageBox.information(self, "بحث", "لم يتم العثور على النص المطلوب")
            
    def replace_text(self, find_text, replace_text, case_sensitive=False, use_regex=False):
        editor = self.get_editor()
        if not editor:
            return
            
        cursor = editor.textCursor()
        if cursor.hasSelection() and (cursor.selectedText() == find_text or use_regex):
            cursor.insertText(replace_text)
            
        self.find_text(find_text, case_sensitive, use_regex)
        
    def replace_all_text(self, find_text, replace_text, case_sensitive=False, use_regex=False):
        editor = self.get_editor()
        if not editor:
            return
            
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        editor.setTextCursor(cursor)
        
        count = 0
        while True:
            if use_regex:
                pattern = QRegularExpression(find_text)
                if not case_sensitive:
                    pattern.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
                found = editor.document().find(pattern, editor.textCursor())
            else:
                flags = QTextDocument.FindFlags()
                if case_sensitive:
                    flags |= QTextDocument.FindCaseSensitively
                found = editor.document().find(find_text, editor.textCursor(), flags)
                
            if found.isNull():
                break
                
            cursor = found
            cursor.insertText(replace_text)
            editor.setTextCursor(cursor)
            count += 1
            
        QMessageBox.information(self, "استبدال", f"تم استبدال {count} نتيجة")
        
    def _find_in_all_tabs(self, text, case_sensitive, use_regex):
        self.search_results.clear()
        results = []
        
        for i in range(self.tabs.count()):
            tab = getattr(self.tabs.widget(i), 'editor_tab', None)
            if tab:
                content = tab.editor.toPlainText()
                lines = content.split('\n')
                tab_name = self.tabs.tabText(i)
                
                for j, line in enumerate(lines):
                    if (use_regex and re.search(text, line, 0 if case_sensitive else re.IGNORECASE)) or \
                       (not use_regex and ((case_sensitive and text in line) or text.lower() in line.lower())):
                        results.append(f"{tab_name} - سطر {j+1}: {line[:50]}...")
                        
        for result in results:
            self.search_results.addItem(result)
            
        QMessageBox.information(self, "بحث", f"تم العثور على {len(results)} نتيجة")
        
    def validate_xml(self):
        editor = self.get_editor()
        if not editor:
            return
            
        text = editor.toPlainText().strip()
        tab = self.current_tab()
        
        if not text:
            self.st_xml_status.setText("ملف فارغ")
            self.st_xml_status.setStyleSheet("color: gray;")
            if hasattr(editor, 'set_error_lines'):
                editor.set_error_lines([])
            if tab:
                tab.highlighter.clear_errors()
            return
            
        try:
            xml.dom.minidom.parseString(text)
            self.st_xml_status.setText("XML صحيح")
            self.st_xml_status.setStyleSheet("color: green;")
            
            # مسح تظليل الأخطاء
            if hasattr(editor, 'set_error_lines'):
                editor.set_error_lines([])
            if tab:
                tab.highlighter.clear_errors()
                
        except Exception as e:
            self.st_xml_status.setText("خطأ في XML")
            self.st_xml_status.setStyleSheet("color: red;")
            
            error_msg = str(e)
            line_match = re.search(r'line (\d+)', error_msg)
            if line_match:
                error_line = int(line_match.group(1)) - 1
                if hasattr(editor, 'set_error_lines'):
                    editor.set_error_lines([error_line])
                if tab:
                    tab.highlighter.set_error_lines([error_line])
                    
    def format_xml(self):
        editor = self.get_editor()
        if not editor:
            return
            
        text = editor.toPlainText().strip()
        if not text:
            return
            
        try:
            parsed = xml.dom.minidom.parseString(text)
            formatted = parsed.toprettyxml(indent="  ")
            formatted = "\n".join([line for line in formatted.split("\n") if line.strip()])
            editor.setPlainText(formatted)
        except Exception as e:
            QMessageBox.warning(self, "خطأ في التنسيق", f"فشل تنسيق الملف:\n{str(e)}")
            
    def minify_xml(self):
        editor = self.get_editor()
        if not editor:
            return
            
        try:
            text = editor.toPlainText()
            text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
            text = re.sub(r'>\s+<', '><', text)
            text = re.sub(r'\s+', ' ', text)
            editor.setPlainText(text.strip())
        except Exception as e:
            QMessageBox.warning(self, "خطأ في التصغير", f"فشل تصغير الملف:\n{str(e)}")
            
    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "فتح ملف", "", 
                                               "ملفات XML (*.xml);;جميع الملفات (*)")
        if path:
            self.load_file_async(path)
            
    def load_file_async(self, path):
        if not os.path.isfile(path):
            QMessageBox.warning(self, "تحذير", "مسار الملف غير صحيح")
            return
            
        for i in range(self.tabs.count()):
            tab = getattr(self.tabs.widget(i), 'editor_tab', None)
            if tab and tab.file_path == path:
                self.tabs.setCurrentIndex(i)
                return
                
        def worker():
            try:
                with open(path, 'rb') as fb:
                    raw = fb.read()
                    
                for enc in ['utf-8-sig', 'utf-16', 'utf-16le', 'utf-16be', 'utf-8']:
                    try:
                        text = raw.decode(enc)
                        if text.strip():
                            return enc, text, None
                    except:
                        pass
                        
                try:
                    return 'utf-8', raw.decode('utf-8', 'replace'), None
                except:
                    return 'latin-1', raw.decode('latin-1', 'replace'), None
                    
            except Exception as e:
                return None, None, e
                
        def done(result):
            enc, text, error = result
            if error:
                QMessageBox.critical(self, "خطأ", str(error))
                return
                
            tab = self.add_new_tab(path, text)
            tab.file_path = path
            self.current_encoding = enc or "utf-8"
            self.encoding_combo.setCurrentText(self.current_encoding.upper())
            
            self._add_to_recent_files(path)
            
            self._rename_current_tab(os.path.basename(path))
            self._refresh_status()
            self._update_stats()
            
        threading.Thread(target=lambda: done(worker()), daemon=True).start()
        
    def _add_to_recent_files(self, path):
        if path in self.file_history:
            self.file_history.remove(path)
        self.file_history.insert(0, path)
        self.file_history = self.file_history[:CONFIG['max_recent_files']]
        self.settings.setValue("file_history", self.file_history)
        self._update_recent_files_menu()
        self._update_recent_list()
        
    def _update_recent_files_menu(self):
        self.recent_files_menu.clear()
        for path in self.file_history:
            action = QAction(os.path.basename(path), self)
            action.setData(path)
            action.triggered.connect(lambda checked, p=path: self.load_file_async(p))
            self.recent_files_menu.addAction(action)
            
    def _update_recent_list(self):
        self.recent_list.clear()
        for path in self.file_history:
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.UserRole, path)
            self.recent_list.addItem(item)
            
    def _open_recent_file(self, item):
        path = item.data(Qt.UserRole)
        self.load_file_async(path)
        
    def _rename_current_tab(self, name):
        index = self.tabs.currentIndex()
        if index >= 0:
            self.tabs.setTabText(index, name)
            
    def save_file(self):
        tab = self.current_tab()
        if not tab:
            return
            
        if tab.save_file():
            self._refresh_status()
            
    def save_file_as(self):
        tab = self.current_tab()
        if not tab:
            return False
            
        path, _ = QFileDialog.getSaveFileName(self, "حفظ الملف", 
                                              tab.file_path or "", 
                                              "ملفات XML (*.xml);;جميع الملفات (*)")
        if not path:
            return False
            
        try:
            with codecs.open(path, "w", encoding=self.current_encoding, errors="strict") as f:
                f.write(tab.editor.toPlainText())
                
            tab.file_path = path
            tab.original_content = tab.editor.toPlainText()
            tab.is_modified = False
            self._rename_current_tab(os.path.basename(path))
            self._add_to_recent_files(path)
            QMessageBox.information(self, "تم الحفظ", "تم حفظ الملف بنجاح")
            self._refresh_status()
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", str(e))
            return False
            
    def _refresh_status(self):
        editor = self.get_editor()
        if not editor:
            return
            
        cursor = editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        
        text = editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split('\n')) if text else 0
        
        self.st_pos.setText(f"السطر: {line}, العمود: {col}")
        self.st_size.setText(f"{char_count} حرف | {word_count} كلمة | {line_count} سطر")
        
        tab = self.current_tab()
        if tab and tab.is_modified:
            self.st_state.setText("تعديلات غير محفوظة")
            self.st_state.setStyleSheet("color: orange;")
        else:
            self.st_state.setText("محفوظ")
            self.st_state.setStyleSheet("color: green;")
            
        self.st_enc.setText(self.current_encoding.upper())
        
    def close_current_tab(self):
        index = self.tabs.currentIndex()
        if index >= 0:
            self.tabs.tabCloseRequested.emit(index)
            
    def _auto_backup(self):
        for i in range(self.tabs.count()):
            tab = getattr(self.tabs.widget(i), 'editor_tab', None)
            if tab and tab.is_modified and tab.file_path:
                try:
                    backup_path = tab.file_path + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    with open(backup_path, "w", encoding="utf-8") as f:
                        f.write(tab.editor.toPlainText())
                except:
                    pass
                    
    def _auto_save(self):
        if self.settings.value("auto_save", False):
            tab = self.current_tab()
            if tab and tab.is_modified and tab.file_path:
                self.save_file()
                
    def _copy_current_path(self):
        tab = self.current_tab()
        if tab and tab.file_path:
            clipboard = QApplication.clipboard()
            clipboard.setText(tab.file_path)
            
    def _toggle_comment(self):
        editor = self.get_editor()
        if not editor:
            return
            
        cursor = editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            lines = text.split('\u2029')
            commented_lines = []
            
            all_commented = all(line.strip().startswith('<!--') and line.strip().endswith('-->') for line in lines)
            
            for line in lines:
                if all_commented:
                    line = re.sub(r'^\s*<!--\s*', '', line)
                    line = re.sub(r'\s*-->\s*$', '', line)
                else:
                    line = f'<!-- {line} -->'
                commented_lines.append(line)
                
            new_text = '\n'.join(commented_lines)
            cursor.insertText(new_text)
            
    def _update_stats(self):
        editor = self.get_editor()
        if not editor:
            return
            
        text = editor.toPlainText()
        lines = text.split('\n') if text else ['']
        
        stats = f"""
إحصائيات الملف:
----------------
عدد الأحرف: {len(text)}
عدد الكلمات: {len(text.split())}
عدد الأسطر: {len(lines)}
عدد الوسوم: {len(re.findall(r'<[^>]+>', text))}
أكبر سطر: {max((len(l) for l in lines), default=0)} حرف
        """
        
        self.stats_text.setText(stats)
        
    def _reload_current_file(self):
        tab = self.current_tab()
        if tab and tab.file_path and os.path.exists(tab.file_path):
            if tab.is_modified:
                ret = QMessageBox.question(self, "إعادة تحميل", 
                                          "توجد تعديلات غير محفوظة. هل تريد إعادة التحميل وفقدان التغييرات؟",
                                          QMessageBox.Yes | QMessageBox.No)
                if ret != QMessageBox.Yes:
                    return
                    
            with open(tab.file_path, 'r', encoding=self.current_encoding) as f:
                tab.set_content(f.read())
                
    def _toggle_readonly(self):
        editor = self.get_editor()
        if editor:
            editor.setReadOnly(self.act_readonly.isChecked())
            
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.xml', '.zip', '.msi', '.appx')):
                self.load_file_async(path)
                break
        event.acceptProposedAction()
        
    def _rebuild_tree_from_editor(self):
        editor = self.get_editor()
        if not editor:
            return
            
        text = editor.toPlainText()
        if text.strip():
            self.tree_builder.build_tree(text)
        else:
            self.tree.clear()
            
    def _display_tree(self, dom):
        self.tree.clear()
        if dom is None:
            editor = self.get_editor()
            if editor:
                self._build_tree_by_regex(editor.toPlainText())
            return
            
        root = dom.documentElement
        root_item = QTreeWidgetItem([root.tagName])
        self.tree.addTopLevelItem(root_item)
        self._fill_tree(root_item, root)
        self.tree.expandToDepth(1)
        
    def _fill_tree(self, parent_item, node):
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                tag = child.tagName
                attrs = []
                if child.attributes:
                    for i in range(child.attributes.length):
                        attr = child.attributes.item(i)
                        attrs.append(f'{attr.name}="{attr.value}"')
                        
                label = tag if not attrs else f'{tag} {" ".join(attrs)}'
                item = QTreeWidgetItem([label])
                parent_item.addChild(item)
                self._fill_tree(item, child)
                
    def _build_tree_by_regex(self, text):
        tag_re = re.compile(r"<\s*/?\s*([A-Za-z_][\w\.\-:]*)[^>]*?>")
        stack = []
        root = QTreeWidgetItem(["المستند"])
        self.tree.addTopLevelItem(root)
        current_parent = root
        
        for match in tag_re.finditer(text):
            full = match.group(0)
            name = match.group(1).split(":")[-1]
            
            if full.startswith("</"):
                if stack:
                    stack.pop()
                    current_parent = stack[-1] if stack else root
            elif full.endswith("/>"):
                item = QTreeWidgetItem([name])
                current_parent.addChild(item)
            else:
                item = QTreeWidgetItem([name])
                current_parent.addChild(item)
                stack.append(item)
                current_parent = item
                
    def _show_tree_context_menu(self, position):
        menu = QMenu()
        menu.addAction("نسخ اسم الوسم", self._copy_tag_name)
        menu.addAction("حذف العنصر", self._delete_tree_item)
        menu.addAction("الذهاب للسطر", self._jump_to_selected_item)
        menu.addAction("طي الكل", self.tree.collapseAll)
        menu.addAction("توسيع الكل", self.tree.expandAll)
        menu.exec_(self.tree.mapToGlobal(position))
        
    def _copy_tag_name(self):
        item = self.tree.currentItem()
        if item:
            clipboard = QApplication.clipboard()
            clipboard.setText(item.text(0).split()[0])
            
    def _delete_tree_item(self):
        item = self.tree.currentItem()
        if item:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
        
    def _jump_to_tree_item(self, item, column):
        editor = self.get_editor()
        if not editor:
            return
            
        label = item.text(0)
        name = label.split()[0]
        pattern = QRegularExpression(r"<\s*" + re.escape(name) + r"(\s|>|/>)")
        cursor = editor.document().find(pattern, 0)
        if not cursor.isNull():
            editor.setTextCursor(cursor)
            
    def _jump_to_selected_item(self):
        self._jump_to_tree_item(self.tree.currentItem(), 0)
        
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self._refresh_status()
        
    def changeEvent(self, event):
        super().changeEvent(event)
        try:
            self._refreshStatus()
        except:
            pass
        
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("محرر XML المتقدم")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("XML-Editor")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
if __name__ == "__main__":
    main()

