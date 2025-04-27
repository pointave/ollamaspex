import os
import base64
import markdown
from PyQt5.QtWidgets import (
    QMainWindow, 
    QMessageBox, 
    QApplication, 
    QMenu, 
    QAction,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QSizePolicy
)
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QPainter, QGuiApplication, QFont, QColor
from PyQt5.QtCore import Qt, QSize, QPoint
from .interface import Ui_MainWindow  # Import the generated UI class
from .local_generate import Worker_Local
import asyncio
import dotenv
import json
import requests
import pyperclip

USER_ROLE = "user"
AI_ROLE = "assistant"

class ImageLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = None
        self.zoom_factor = 1.0
        self.setMouseTracking(True)
        self.image_path = None
        self.drag_start = None
        self.scroll_offset = QPoint(0, 0)
        self.setAlignment(Qt.AlignCenter)
        # Set fixed size policy
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
    def setPixmap(self, pixmap):
        self.original_pixmap = pixmap
        self.scroll_offset = QPoint(0, 0)  # Reset offset when setting new image
        if self.original_pixmap:
            # Calculate initial zoom to fit the image in the view
            width_ratio = self.width() / self.original_pixmap.width()
            height_ratio = self.height() / self.original_pixmap.height()
            self.zoom_factor = min(width_ratio, height_ratio)
        self.update_pixmap()
        
    def set_image_path(self, path):
        self.image_path = path
        
    def update_pixmap(self):
        if self.original_pixmap and self.size().isValid():
            scaled_width = int(self.original_pixmap.width() * self.zoom_factor)
            scaled_height = int(self.original_pixmap.height() * self.zoom_factor)
            
            # Create scaled version of original image
            scaled_pixmap = self.original_pixmap.scaled(
                scaled_width,
                scaled_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Create a new pixmap of the widget's size
            final_pixmap = QPixmap(self.size())
            final_pixmap.fill(Qt.transparent)
            
            # Calculate position to center the image
            x = (self.width() - scaled_width) // 2 + self.scroll_offset.x()
            y = (self.height() - scaled_height) // 2 + self.scroll_offset.y()
            
            # Draw the scaled image
            painter = QPainter(final_pixmap)
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()
            
            super().setPixmap(final_pixmap)
    
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            old_zoom = self.zoom_factor
            
            # Calculate zoom
            if event.angleDelta().y() > 0:
                self.zoom_factor *= 1.1
            else:
                self.zoom_factor *= 0.9
            self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))
            
            # Adjust scroll offset to zoom toward cursor position
            if self.original_pixmap:
                mouse_pos = event.pos()
                rel_x = (mouse_pos.x() - self.width()/2 - self.scroll_offset.x()) / old_zoom
                rel_y = (mouse_pos.y() - self.height()/2 - self.scroll_offset.y()) / old_zoom
                self.scroll_offset = QPoint(
                    int(mouse_pos.x() - (rel_x * self.zoom_factor + self.width()/2)),
                    int(mouse_pos.y() - (rel_y * self.zoom_factor + self.height()/2))
                )
                
            self.update_pixmap()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        
    def mouseMoveEvent(self, event):
        if self.drag_start is not None:
            delta = event.pos() - self.drag_start
            self.scroll_offset += delta
            self.drag_start = event.pos()
            self.update_pixmap()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start = None
            self.setCursor(Qt.ArrowCursor)
            
    def contextMenuEvent(self, event):
        menu = QMenu(self)

        # Add actions
        copy_path = QAction("Copy Image Path", self)
        copy_path.triggered.connect(lambda: pyperclip.copy(self.image_path if self.image_path else ""))

        reset_zoom = QAction("Reset Zoom", self)
        reset_zoom.triggered.connect(self.reset_zoom)

        upload_image = QAction("Upload Image", self)
        upload_image.triggered.connect(self.upload_image)

        menu.addAction(copy_path)
        menu.addAction(reset_zoom)
        menu.addAction(upload_image)

        # Show menu at cursor position
        menu.exec_(event.globalPos())

    def upload_image(self):
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.set_image_path(file_path)
            # Find the parent ScreenshotAnalyzer and update its image_path
            parent = self.parent()
            while parent is not None and not hasattr(parent, 'display_image'):
                parent = parent.parent()
            if parent is not None:
                parent.image_path = file_path
                parent.display_image()
        
    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.update_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap and not self.drag_start:  # Don't auto-fit while dragging
            # Recalculate zoom factor to fit the new size
            width_ratio = self.width() / self.original_pixmap.width()
            height_ratio = self.height() / self.original_pixmap.height()
            self.zoom_factor = min(width_ratio, height_ratio)
            self.update_pixmap()

class ScreenshotAnalyzer(QMainWindow, Ui_MainWindow):
    def __init__(self, image_path = None):
        super().__init__()
        self.image_path = image_path
        self.memory = []
        self.load_config()
        
        # Set app-wide stylesheet for modern look
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 6px;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #2d5c8a;
                color: #ffffff;
                border-radius: 6px;
                padding: 6px 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3a75b0;
            }
            QPushButton:pressed {
                background-color: #1d4c7a;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: #e0e0e0;
                selection-background-color: #2d5c8a;
            }
        """)
        
        # Initialize UI using parent class's setupUi
        super().setupUi(self)
        
        # Remove tab widget and create simple layout
        self.setupSimpleLayout()
        
        # Initialize models
        models = self.get_ollama_models()
        
        # Set up models in combo box
        if models:
            self.ollama_model_combo.clear()
            self.ollama_model_combo.addItems(models)
            if self.LLM_MODEL_ID and self.LLM_MODEL_ID in models:
                self.ollama_model_combo.setCurrentText(self.LLM_MODEL_ID)
            else:
                self.ollama_model_combo.setCurrentText(models[0])
        
        self.ollama_system_message = 'You are an AI assistant analyzing images. Provide detailed and accurate descriptions of the image contents.'

    def setupSimpleLayout(self):
        # Create new central widget with layout
        centralWidget = QWidget()
        mainLayout = QVBoxLayout(centralWidget)
        # Set ALL margins to minimal values - no empty space at top
        mainLayout.setContentsMargins(10, 0, 10, 10)
        mainLayout.setSpacing(6)  # Reduce spacing between elements even more
        
        # Create model selection layout first (moved above image)
        modelLayout = QHBoxLayout()
        modelLayout.setContentsMargins(0, 0, 0, 0)
        modelLayout.setSpacing(8)
        
        modelLabel = QLabel("Model:")
        font = modelLabel.font()
        font.setPointSize(font.pointSize() + 1)
        modelLabel.setFont(font)
        
        self.ollama_model_combo = QComboBox()
        comboFont = self.ollama_model_combo.font()
        comboFont.setPointSize(comboFont.pointSize() + 1)
        self.ollama_model_combo.setFont(comboFont)
        self.ollama_model_combo.setFixedHeight(30)  # Reduced from 32
        
        self.refresh_models = QPushButton("Refresh")
        buttonFont = self.refresh_models.font()
        buttonFont.setPointSize(buttonFont.pointSize() + 1)
        self.refresh_models.setFont(buttonFont)
        self.refresh_models.setFixedHeight(40)  
        
        modelLayout.addWidget(modelLabel)
        modelLayout.addWidget(self.ollama_model_combo, 1)
        modelLayout.addWidget(self.refresh_models)
        mainLayout.addLayout(modelLayout)
        
        # Replace the image label with our custom ImageLabel (now below model selection)
        self.image_label = ImageLabel()
        self.image_label.setMinimumHeight(600)  # Further reduced height
        self.image_label.setMaximumHeight(600)  # Further reduced height
        self.image_label.setStyleSheet("border-radius: 8px; background-color: #232323;")
        mainLayout.addWidget(self.image_label)
        
        # Add conversation widget
        self.conversation = QtWidgets.QTextEdit()
        self.conversation.setReadOnly(True)
        self.conversation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        conversationFont = self.conversation.font()
        conversationFont.setPointSize(conversationFont.pointSize() + 2)
        self.conversation.setFont(conversationFont)
        self.conversation.setStyleSheet("border-radius: 8px; background-color: #232323; padding: 1px;")
        
        mainLayout.addWidget(self.conversation, 1)  # Give it stretch factor of 1
        
        # Add input and button layout
        inputLayout = QHBoxLayout()
        inputLayout.setSpacing(8)
        inputLayout.setContentsMargins(0, 0, 0, 0)  # No margins to prevent cutoff
        
        self.entry = QtWidgets.QLineEdit()
        entryFont = self.entry.font()
        entryFont.setPointSize(11)  # Standard, readable font size
        self.entry.setFont(entryFont)
        self.entry.setPlaceholderText("Ask about the image...")
        self.entry.setMinimumHeight(30)
        self.entry.setStyleSheet("""
            padding-top: 4px;
            padding-bottom: 4px;
            font-size: 11pt;
            border-radius: 8px;
        """)
        inputLayout.addWidget(self.entry, 1)  # Stretch factor 1: input fills all available space
        self.entry.setContentsMargins(0, 0, 0, 0)

        self.send_button = QPushButton("Send")
        sendFont = self.send_button.font()
        sendFont.setPointSize(sendFont.pointSize() + 1)
        self.send_button.setFont(sendFont)
        self.send_button.setMinimumHeight(32)
        inputLayout.addWidget(self.send_button, 0)

        self.loading_label = QLabel("")
        self.loading_label.setMinimumWidth(30)
        inputLayout.addWidget(self.loading_label, 0)

        self.reset_memory = QPushButton("Reset")
        resetFont = self.reset_memory.font()
        resetFont.setPointSize(resetFont.pointSize() + 1)
        self.reset_memory.setFont(resetFont)
        self.reset_memory.setMinimumHeight(32)
        self.reset_memory.setStyleSheet("background-color: #733e3e;")
        inputLayout.addWidget(self.reset_memory, 0)
        
        # Add adequate spacing before input layout to prevent cut-off
        mainLayout.addSpacing(5)
        mainLayout.addLayout(inputLayout)
        
        # Set central widget
        self.setCentralWidget(centralWidget)
        
        # Add drop shadow effect to main components
        self.add_shadow_effects()
        
        # Connect signals
        self.setup_ui()
        # Add quit shortcut
        self.setShortcut()

    def add_shadow_effects(self):
        # Add subtle shadow effect to components
        for widget in [self.image_label, self.conversation, self.entry, 
                      self.send_button, self.reset_memory, self.ollama_model_combo]:
            effect = QtWidgets.QGraphicsDropShadowEffect()
            effect.setBlurRadius(10)
            effect.setColor(QColor(0, 0, 0, 80))
            effect.setOffset(0, 2)
            widget.setGraphicsEffect(effect)

    def load_config(self):
        dotenv.load_dotenv(override=True)
        self.LLM_API_MODEL = os.getenv("LLM_API_KEY")
        self.LLM_MODEL_ID = os.getenv("LLM_MODEL_ID")
        self.OLLAMA = os.getenv("OLLAMA")        

    def setup_ui(self):
        self.display_image()
        self.conversation.setReadOnly(True)
       # self.conversation.append("<span style='color:#a0a0a0; font-size:14pt;'>Ask me anything about this screenshot!</span><br>")
        self.send_button.clicked.connect(self.send_text)
        self.reset_memory.clicked.connect(self.reset)
        self.refresh_models.clicked.connect(self.refresh_ollama_models)
        self.entry.returnPressed.connect(self.send_text)
        self.entry.setFocus()
        self.loading_label.setText("")

    def save_config(self):
        LLM_MODEL_ID = self.ollama_model_combo.currentText()
        
        with open(".env", "w") as env_file:
            env_file.write(f"LLM_API_KEY={self.LLM_API_MODEL or ''}\n")
            env_file.write(f"LLM_MODEL_ID={LLM_MODEL_ID}\n")
            env_file.write("OLLAMA=1\n")
        
        self.load_config()
        self.show_message("Configuration saved successfully!")
        
    def reset(self):
        self.memory = []
        self.conversation.clear()
        self.entry.setFocus()

    def display_image(self):
        if self.image_path:  # Check if image path exists
            pixmap = QPixmap(self.image_path)
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            
            # Calculate window dimensions
            self.w = int(screen_geometry.width() * 0.25)
            self.h = int(screen_geometry.height() * 0.25)
            
            # Set minimum sizes
            self.conversation.setMinimumSize(QSize(450, int(self.h*2)))
            self.image_label.setMinimumSize(self.w, self.h)
            
            # Scale and set the pixmap
            if not pixmap.isNull():  # Check if pixmap is valid
                self.image_label.set_image_path(self.image_path)
                self.image_label.setPixmap(pixmap)
            
            # Calculate window position and size
            right_padding = 300
            window_width = max(500, self.w)
            # Add extra padding at bottom to ensure text entry is visible
            window_height = self.h + 200
            
            # Position window more to the left
            x = screen_geometry.width() - window_width - right_padding
            y = 50
            
            self.resize(window_width, window_height)
            self.move(x, y)

    def send_text(self):        
        text = self.entry.text().strip()
        if not text:
            return
        self.entry.clear()
        self.update_conversation(text, USER_ROLE)
        # Update loading indicator with better styling
        self.loading_label.setText("⏳")
        self.loading_label.setStyleSheet("font-size: 18px; color: #6a9eda;")
        self.repaint()
        
        if len(self.memory) == 0:
            try:
                self.memory.append({'role': 'system', 'content': self.ollama_system_message})
                self.memory.append({'role': USER_ROLE, 'content': text, 'images': [self.image_path]})
            except Exception as e:
                self.show_error_message("No image found")
                self.loading_label.setText("")
                return
        else:
            self.memory.append({'role': USER_ROLE, 'content': text})
        
        print("Getting response")
        self.load_config()
        # Save current model selection to config
        current_model = self.ollama_model_combo.currentText()
        if current_model != self.LLM_MODEL_ID:
            self.LLM_MODEL_ID = current_model
            self.save_config()
            
        print("Using Ollama")
        generator = Worker_Local(self.memory, self.LLM_API_MODEL, self.ollama_model_combo.currentText())
        generator.finished.connect(self.finished)
        generator.error.connect(self.show_error_message)
        generator.partial.connect(self.stream_chunk)
        # Buffer for streaming assistant output
        self._streaming_ai_buffer = ""
        self._streaming_last_ai_html = None
        generator.start()
        print("Worker started")
        self.worker_reference = generator

    def stream_chunk(self, chunk):
        import markdown
        if not hasattr(self, '_streaming_ai_buffer'):
            self._streaming_ai_buffer = ""
        if not hasattr(self, '_assistant_label_shown'):
            self._assistant_label_shown = False
        self._streaming_ai_buffer += chunk
        paragraphs = self._streaming_ai_buffer.split('\n\n')
        for para in paragraphs[:-1]:
            # Inject CSS for list padding to prevent number cut-off
            css_padding = "<style>ol, ul { padding-left: 2em !important; }</style>"
            if not self._assistant_label_shown:
                html = (
                    css_padding +
                    "<div style='background-color: #333333; margin: 4px 0; padding: 8px; border-radius: 6px;'>"
                    "<b style='color: #6a9eda;'>ASSISTANT</b>: "
                    f"<span style='color: #e0e0e0;'>{markdown.markdown(para)}</span></div>"
                )
                self._assistant_label_shown = True
            else:
                html = (
                    css_padding +
                    "<div style='background-color: #333333; margin: 4px 0; padding: 8px; border-radius: 6px;'>"
                    f"<span style='color: #e0e0e0;'>{markdown.markdown(para)}</span></div>"
                )
            self.conversation.append(html)
            self._streaming_last_ai_block_number = self.conversation.document().blockCount() - 1
        self._streaming_ai_buffer = paragraphs[-1]
        self.conversation.ensureCursorVisible()

    def finished(self, response):
        import markdown
        # On finish, flush any remaining buffer
        self.loading_label.setText("")
        self.memory.append({'role': AI_ROLE, 'content': response})
        self.conversation.ensureCursorVisible()

    def show_message(self, message):
        message_box = QMessageBox()
        message_box.setWindowTitle("Message")
        message_box.setWindowModality(Qt.ApplicationModal)
        message_box.setText(message)
        message_box.exec_()
    
    def show_error_message(self, error):
        error_message = QMessageBox()
        red_color = "<font color='#ff6b6b'> {}</font>".format(error)
        error_message.setIcon(QMessageBox.Critical)
        error_message.setWindowTitle("Error")
        error_message.setWindowModality(Qt.ApplicationModal)
        error_message.setText("Error occurred. Please try again. Error: " + red_color)
        error_message.exec_()
        
    def update_conversation(self, text, role):
        markdown_text = markdown.markdown(text) if role == AI_ROLE else text
    
        # Inject CSS for list padding to prevent number cut-off
        css_padding = "<style>ol, ul { padding-left: 2em !important; }</style>"
        # Apply better styling to conversation messages
        if role == USER_ROLE:
            self.conversation.append(css_padding + f"<div style='background-color: #2d5c8a; margin: 4px 0; padding: 8px; border-radius: 6px;'>"
                               f"<b style='color: #ffffff;'>{role.upper()}</b>: "
                               f"<span style='color: #e0e0e0;'>{markdown_text}</span></div>")
        else:
            self.conversation.append(css_padding + f"<div style='background-color: #333333; margin: 4px 0; padding: 8px; border-radius: 6px;'>"
                               f"<b style='color: #6a9eda;'>{role.upper()}</b>: "
                               f"<span style='color: #e0e0e0;'>{markdown_text}</span></div>")
    
        self.conversation.ensureCursorVisible()

    def image_to_base64(self):
        with open(self.image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        # Add quit shortcut
        if event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier:
            self.close()

    def get_ollama_models(self):
        try:
            response = requests.get('http://localhost:11434/api/tags')
            if response.status_code == 200:
                data = response.json()
                if 'models' in data:
                    return [model['name'] for model in data['models']]
                return ['gemma3:latest']
            return ['gemma3:latest']
        except Exception as e:
            return ['gemma3:latest']

    def refresh_ollama_models(self):
        current_model = self.ollama_model_combo.currentText()
        self.ollama_model_combo.clear()
        models = self.get_ollama_models()
        if models:
            self.ollama_model_combo.addItems(models)
            if current_model in models:
                self.ollama_model_combo.setCurrentText(current_model)
            elif self.LLM_MODEL_ID and self.LLM_MODEL_ID in models:
                self.ollama_model_combo.setCurrentText(self.LLM_MODEL_ID)
            else:
                self.ollama_model_combo.setCurrentText(models[0])

    def setShortcut(self):
        # Set Ctrl+Q as a quit shortcut
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)  # Connect to the close method
        self.addAction(quit_action)


