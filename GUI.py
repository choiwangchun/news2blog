import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QListWidget, QFileDialog, QMessageBox, QLabel, 
                             QHBoxLayout, QProgressBar)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDropEvent, QIcon, QColor
from PIL import Image

class ModernImageConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.image_list = []

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 드래그 앤 드롭 영역
        self.dropArea = QLabel("여기에 이미지를 드래그하세요")
        self.dropArea.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dropArea.setStyleSheet("""
            QLabel {
                border: 2px dashed #CCCCCC;
                border-radius: 10px;
                padding: 20px;
                background-color: #F8F8F8;
                color: #333333;
                font-size: 16px;
            }
        """)
        self.dropArea.setAcceptDrops(True)
        self.dropArea.dragEnterEvent = self.dragEnterEvent
        self.dropArea.dragMoveEvent = self.dragMoveEvent
        self.dropArea.dropEvent = self.dropEvent

        # 이미지 목록
        self.listWidget = QListWidget()
        self.listWidget.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #FFFFFF;
                border-radius: 10px;
                color: #333333;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #EEEEEE;
            }
            QListWidget::item:selected {
                background-color: #E6E6E6;
                color: #333333;
            }
        """)

        # 진행 상황 바
        self.progressBar = QProgressBar()
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #EEEEEE;
                height: 10px;
                text-align: center;
                color: #333333;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 5px;
            }
        """)
        self.progressBar.hide()

        # 버튼
        button_layout = QHBoxLayout()
        self.convertBtn = QPushButton('변환')
        self.convertBtn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056B3;
            }
            QPushButton:pressed {
                background-color: #003D80;
            }
        """)
        self.convertBtn.clicked.connect(self.convertImages)
        button_layout.addStretch()
        button_layout.addWidget(self.convertBtn)

        main_layout.addWidget(self.dropArea)
        main_layout.addWidget(self.listWidget)
        main_layout.addWidget(self.progressBar)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setWindowTitle('WebP 이미지 변환기')
        self.setGeometry(300, 300, 400, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F0F0;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #333333;
            }
        """)

    def dragEnterEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self.dropArea.setStyleSheet("""
                QLabel {
                    border: 2px dashed #007AFF;
                    border-radius: 10px;
                    padding: 20px;
                    background-color: #E6F2FF;
                    color: #007AFF;
                    font-size: 16px;
                }
            """)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')) and f not in self.image_list:
                self.image_list.append(f)
                self.listWidget.addItem(os.path.basename(f))
        self.dropArea.setStyleSheet("""
            QLabel {
                border: 2px dashed #CCCCCC;
                border-radius: 10px;
                padding: 20px;
                background-color: #F8F8F8;
                color: #333333;
                font-size: 16px;
            }
        """)

    def convertImages(self):
        if not self.image_list:
            QMessageBox.warning(self, "경고", "변환할 이미지가 없습니다.")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "저장할 디렉토리 선택")
        if not output_dir:
            return

        self.progressBar.show()
        self.progressBar.setMaximum(len(self.image_list))

        for i, image_path in enumerate(self.image_list):
            try:
                with Image.open(image_path) as img:
                    output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}.webp")
                    img.save(output_path, 'WEBP')
                print(f"변환 완료: {image_path} -> {output_path}")
            except Exception as e:
                print(f"변환 실패: {image_path}. 오류: {str(e)}")
            self.progressBar.setValue(i + 1)

        self.image_list.clear()
        self.listWidget.clear()
        self.progressBar.hide()
        QMessageBox.information(self, "완료", f"모든 이미지가 {output_dir}에 변환되어 저장되었습니다.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ModernImageConverter()
    ex.show()
    sys.exit(app.exec())