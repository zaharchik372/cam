import cv2
import os
import PyQt5
from pathlib import Path
import pytesseract
from PyQt5.QtWidgets import QApplication,QMessageBox, QMainWindow, QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, QTableView, QAbstractItemView, QFileDialog
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtXml import QDomDocument
import csv

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(
    Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.label = QLabel(self)
        self.line_edit = QLineEdit(self)
        self.line_edit.setReadOnly(True)
        self.button = QPushButton('Сохранить в базу данных', self)
        self.table_view = QTableView(self)
        self.search_edit = QLineEdit(self)
        self.search_button = QPushButton('Поиск', self)
        self.export_xml_button = QPushButton('Экспорт в XML', self)
        self.export_csv_button = QPushButton('Экспорт в CSV', self)

        self.setStyleSheet("""
               QWidget {
                   background-color: #F5F5F5;
               }
               QLabel {
                   background-color: #FFFFFF;
                   border: 1px solid #CCCCCC;
                   padding: 10px;
                   font-size: 18px;
               }
               QLineEdit {
                   background-color: #FFFFFF;
                   border: 1px solid #CCCCCC;
                   padding: 10px;
                   font-size: 16px;
               }
               QPushButton {
                   background-color: #4CAF50;
                   border: none;
                   color: white;
                   padding: 10px;
                   text-align: center;
                   font-size: 16px;
                   cursor: pointer;
               }
               QPushButton:hover {
                   background-color: #45a049;
               }
               QTableView {
                   background-color: #FFFFFF;
                   border: 1px solid #CCCCCC;
               }
               QHeaderView::section {
                   background-color: #4CAF50;
                   color: white;
                   padding: 8px;
                   font-size: 16px;
               }
               QTableView QScrollBar {
                   background-color: #F5F5F5;
                   width: 15px;
               }
               QTableView QScrollBar::handle {
                   background-color: #CCCCCC;
                   border-radius: 7px;
               }
               QTableView QScrollBar::handle:hover {
                   background-color: #BBBBBB;
               }
               QTableView QScrollBar::handle:pressed {
                   background-color: #999999;
               }
               QTableView QScrollBar::add-page, QTableView QScrollBar::sub-page {
                   background-color: #F5F5F5;
               }
               QLineEdit:focus, QPushButton:focus, QTableView:focus {
                   border: 2px solid #4CAF50;
               }
           """)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.button)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.search_button)
        layout.addWidget(self.table_view)
        layout.addWidget(self.export_xml_button)
        layout.addWidget(self.export_csv_button)

        main_widget = QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        # Подключение сигналов к слотам
        self.button.clicked.connect(self.save_to_database)
        self.search_edit.textChanged.connect(self.search_database)
        self.export_xml_button.clicked.connect(self.export_to_xml)
        self.export_csv_button.clicked.connect(self.export_to_csv)

        self.model = QSqlTableModel()
        self.model.setTable('numbers')
        self.model.select()
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)

        self.timer = QTimer()
        self.timer.timeout.connect(self.save_to_database)
        self.timer.start(5000)

    def save_to_database(self):
        result = self.line_edit.text()
        if result:
            db = QSqlDatabase.addDatabase('QSQLITE')
            db.setDatabaseName('database.db')
            if db.open():
                query = QSqlQuery()
                query.prepare('INSERT INTO numbers (value, date, time) VALUES (?, ?, ?)')
                query.addBindValue(result)
                date_time = QDateTime.currentDateTime()
                query.addBindValue(date_time.date())
                query.addBindValue(date_time.time())
                query.exec_()
                db.close()

    def display_image(self, image):
        height, width, _ = image.shape
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_img))

    def search_database(self, keyword):
        # Подключение к базе данных
        db = QSqlDatabase.database()
        if db.isValid():
            # Проверка наличия соединения с базой данных
            if not db.isOpen():
                if not db.open():
                    print("Не удалось открыть базу данных")
                    return

            # Формирование фильтра
            filter_str = f"date LIKE '%{keyword}%'"
            self.model.setFilter(filter_str)
            self.model.select()

    def capture_and_recognize(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray, config='--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789')
            self.line_edit.setText(text)
            self.display_image(frame)
            QApplication.processEvents()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def export_to_xml(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Экспорт в XML", "", "XML Files (*.xml)")
        if file_path:
            doc = QDomDocument("numbers")
            root = doc.createElement("Numbers")
            doc.appendChild(root)

            for row in range(self.model.rowCount()):
                record = self.model.record(row)
                value = record.value("value")
                date = record.value("date")
                time = record.value("time")

                number_elem = doc.createElement("Number")
                value_elem = doc.createElement("Value")
                value_elem.appendChild(doc.createTextNode(str(value)))
                date_elem = doc.createElement("Date")
                date_elem.appendChild(doc.createTextNode(str(date)))
                time_elem = doc.createElement("Time")
                time_elem.appendChild(doc.createTextNode(str(time)))

                number_elem.appendChild(value_elem)
                number_elem.appendChild(date_elem)
                number_elem.appendChild(time_elem)

                root.appendChild(number_elem)

            with open(file_path, "w") as file:
                file.write(doc.toString())

    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Экспорт в CSV", "", "CSV Files (*.csv)")
        if file_path:
            with open(file_path, "w", newline="") as file:
                writer = csv.writer(file)
                headers = ["Value", "Date", "Time"]
                writer.writerow(headers)

                for row in range(self.model.rowCount()):
                    record = self.model.record(row)
                    value = record.value("value")
                    date = record.value("date")
                    time = record.value("time")
                    writer.writerow([value, date, time])

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', 'Are you sure you want to quit?',
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    # Подключение к базе данных (если она не существует, будет создана новая)
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName('database.db')  # Имя файла базы данных
    if db.open():
        query = QSqlQuery()
        query.exec_("CREATE TABLE IF NOT EXISTS numbers (value TEXT, date TEXT, time TEXT)")
        db.close()

    # Создание экземпляра приложения PyQt
    app = QApplication([])
    window = MainWindow()
    window.setWindowTitle('Распознавание номеров')
    window.setFixedSize(800, 900)
    window.show()

    # Запуск захвата и распознавания
    window.capture_and_recognize()
    window.search_database('')

    # Запуск обновления lineEdit каждую секунду
    window.update_line_edit()

    # Запуск главного цикла приложения PyQt
    app.exec_()
