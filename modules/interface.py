from PyQt5 import QtCore, QtGui, QtWidgets 

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow

        self.MainWindow.setObjectName("MainWindow")
        self.MainWindow.resize(640, 794)
        self.MainWindow.setStyleSheet(self.get_stylesheet())
        font = QtGui.QFont("Segoe UI", 10)

        # Set window flags to make it always on top
        self.MainWindow.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout.setSpacing(20)

        # Create main content directly without tabs
        self.setup_main_tab(font)
        self.verticalLayout.addWidget(self.tab1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # Set default position to top-right corner of the screen
        screen_geometry = QtWidgets.QDesktopWidget().screenGeometry()
        x = screen_geometry.width() - self.MainWindow.width()
        y = 0
        self.MainWindow.move(x, y)

        # Set window icon
        icon = QtGui.QIcon("icon_light.ico")
        self.MainWindow.setWindowIcon(icon)

    def setup_main_tab(self, font):
        self.tab1 = QtWidgets.QWidget()
        self.tab1.setObjectName("tab1")
        
        # Create main vertical layout for tab1
        self.main_layout = QtWidgets.QVBoxLayout(self.tab1)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create placeholder for image label
        self.image_label = QtWidgets.QLabel(self.tab1)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setMinimumHeight(300)
        self.main_layout.addWidget(self.image_label)
        
        # Add model selection layout
        model_layout = QtWidgets.QHBoxLayout()
        
        # Add model label
        model_label = QtWidgets.QLabel("Model:", self.tab1)
        model_label.setFont(font)
        model_label.setStyleSheet("color: #e0e0e0;")
        model_layout.addWidget(model_label)
        
        # Add model combo box
        self.ollama_model_combo = QtWidgets.QComboBox(self.tab1)
        self.ollama_model_combo.setFont(font)
        self.ollama_model_combo.setMinimumWidth(200)
        self.ollama_model_combo.setStyleSheet("""
            QComboBox {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px;
                color: #e0e0e0;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e0e0e0;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #333333;
                border: 1px solid #555555;
                selection-background-color: #0056b3;
                selection-color: #ffffff;
                color: #e0e0e0;
            }
        """)
        model_layout.addWidget(self.ollama_model_combo)
        
        # Add refresh button
        self.refresh_models = QtWidgets.QPushButton(self.tab1)
        self.refresh_models.setFont(font)
        self.refresh_models.setObjectName("refresh_models")
        self.refresh_models.setText("🔄")
        self.refresh_models.setFixedWidth(40)
        self.refresh_models.setStyleSheet("""
            QPushButton {
                background-color: #0056b3;
                border-radius: 6px;
                color: white;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
        """)
        model_layout.addWidget(self.refresh_models)
        
        # Add spacer to push everything to the left
        model_layout.addStretch()
        
        # Add model layout to main layout
        self.main_layout.addLayout(model_layout)
        
        # Add conversation text area
        self.conversation = QtWidgets.QTextEdit(self.tab1)
        self.conversation.setReadOnly(True)
        self.conversation.setMinimumHeight(200)
        self.main_layout.addWidget(self.conversation)
        
        # Create horizontal layout for entry and send button
        input_layout = QtWidgets.QHBoxLayout()
        
        # Add entry field
        self.entry = QtWidgets.QLineEdit(self.tab1)
        self.entry.setPlaceholderText("Type your message here...")
        self.entry.setFont(font)
        input_layout.addWidget(self.entry)
        
        # Add send button
        self.send_button = QtWidgets.QPushButton(self.tab1)
        self.send_button.setFont(font)
        self.send_button.setObjectName("send_button")
        self.send_button.setText("Send")
        input_layout.addWidget(self.send_button)
        
        # Add input layout to main layout
        self.main_layout.addLayout(input_layout)
        
        # Add reset memory button
        self.reset_memory = QtWidgets.QPushButton(self.tab1)
        self.reset_memory.setFont(font)
        self.reset_memory.setObjectName("reset_memory")
        self.reset_memory.setText("Reset Memory")
        self.main_layout.addWidget(self.reset_memory)
        
        # Add loading label
        self.loading_label = QtWidgets.QLabel(self.tab1)
        self.loading_label.setAlignment(QtCore.Qt.AlignCenter)
        self.loading_label.setFont(font)
        self.main_layout.addWidget(self.loading_label)
        
        # Set stretch factors
        self.main_layout.setStretch(0, 2)  # Image gets 2 parts
        self.main_layout.setStretch(1, 3)  # Conversation gets 3 parts



    def get_stylesheet(self):
        return """
            QMainWindow, QTabWidget, QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #333333;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 10px 15px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0056b3;
            }
            QLabel, QTextEdit, QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 10px;
                color: #e0e0e0;
            }
            QTextEdit {
                background-color: #2d2d2d;
            }
            QPushButton {
                background-color: #0056b3;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
            QCheckBox {
                spacing: 8px;
                color: #e0e0e0;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #404040;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #0056b3;
                border: 2px solid #0056b3;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #404040;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    def create_label(self):
        label = QtWidgets.QLabel(self.centralwidget)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("border-radius: 10px;")
        label.setObjectName("image_label")
        label.setFont(QtGui.QFont("Segoe UI", 10))
        return label

    def create_text_edit(self):
        text_edit = QtWidgets.QTextEdit(self.centralwidget)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("border-radius: 10px;")
        text_edit.setObjectName("conversation")
        text_edit.setFont(QtGui.QFont("Segoe UI", 10))
        return text_edit

    def create_line_edit(self, font):
        line_edit = QtWidgets.QLineEdit(self.centralwidget)
        line_edit.setPlaceholderText("Type your message here...")
        line_edit.setFocus()
        line_edit.setFont(font)
        line_edit.setObjectName("entry")
        return line_edit

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Ollama Vision"))
        self.send_button.setText(_translate("MainWindow", "Send"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
