import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QFileDialog, QMessageBox, QSpinBox, QTextEdit, 
                            QGridLayout, QGroupBox, QScrollArea, QFrame, QInputDialog)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC
from PIL import Image
import io

class MetadataEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.current_cover = None  # Добавляем хранение текущей обложки
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Редактор метаданных")
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
            }
            QLineEdit, QSpinBox, QTextEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
                min-width: 300px;
            }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
                border: 1px solid #4d4d4d;
                background-color: #333333;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #252525;
            }
            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                margin-top: 1.5em;
                padding: 15px;
            }
            QGroupBox::title {
                color: #e0e0e0;
                padding: 0 10px;
                subcontrol-origin: margin;
                subcontrol-position: top center;
                background-color: #1e1e1e;
            }
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4d4d4d;
                min-height: 20px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5d5d5d;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Создаем центральный виджет со скроллом
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Создаем scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)

        # Создаем контейнер для содержимого
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)
        scroll.setWidget(content_widget)

        # Верхняя панель с информацией о файле
        file_group = QGroupBox("Файл")
        file_layout = QVBoxLayout()
        
        # Кнопки управления файлом
        file_buttons = QHBoxLayout()
        file_button = QPushButton("Открыть файл")
        file_button.clicked.connect(self.open_file)
        rename_button = QPushButton("Переименовать")
        rename_button.clicked.connect(self.rename_file)
        file_buttons.addWidget(file_button)
        file_buttons.addWidget(rename_button)
        file_buttons.addStretch()
        
        # Информация о файле
        file_info = QGridLayout()
        self.file_label = QLabel("Файл не выбран")
        self.file_size_label = QLabel("Размер: -")
        self.file_format_label = QLabel("Формат: -")
        
        file_info.addWidget(QLabel("Путь:"), 0, 0)
        file_info.addWidget(self.file_label, 0, 1)
        file_info.addWidget(QLabel("Размер:"), 1, 0)
        file_info.addWidget(self.file_size_label, 1, 1)
        file_info.addWidget(QLabel("Формат:"), 2, 0)
        file_info.addWidget(self.file_format_label, 2, 1)
        
        file_layout.addLayout(file_buttons)
        file_layout.addLayout(file_info)
        file_group.setLayout(file_layout)
        content_layout.addWidget(file_group)

        # Создаем поля для метаданных
        self.metadata_fields = {}
        fields = {
            'title': 'Название трека',
            'artist': 'Исполнитель',
            'album': 'Альбом',
            'date': 'Дата выпуска',
            'genre': 'Жанр',
            'tracknumber': 'Номер трека',
            'copyright': 'Авторские права'
        }

        fields_layout = QGridLayout()
        fields_layout.setSpacing(10)
        row = 0
        
        for key, label in fields.items():
            label_widget = QLabel(label)
            label_widget.setMinimumWidth(120)
            
            if key == 'tracknumber':
                field_widget = QSpinBox()
                field_widget.setRange(1, 999)
                field_widget.setFixedWidth(100)
            else:
                field_widget = QLineEdit()
                field_widget.setMinimumWidth(300)
            
            self.metadata_fields[key] = field_widget
            fields_layout.addWidget(label_widget, row, 0)
            fields_layout.addWidget(field_widget, row, 1)
            row += 1

        # Группируем поля метаданных
        metadata_group = QGroupBox("Метаданные")
        metadata_group.setLayout(fields_layout)
        content_layout.addWidget(metadata_group)

        # Поле для комментариев
        comments_group = QGroupBox("Комментарии")
        comments_layout = QVBoxLayout()
        self.comments_field = QTextEdit()
        self.comments_field.setMaximumHeight(100)
        comments_layout.addWidget(self.comments_field)
        comments_group.setLayout(comments_layout)
        content_layout.addWidget(comments_group)

        # Область для обложки
        cover_group = QGroupBox("Обложка альбома")
        cover_layout = QVBoxLayout()
        
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #3d3d3d;
                border-radius: 4px;
            }
        """)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        cover_buttons_layout = QHBoxLayout()
        add_cover_button = QPushButton("Добавить обложку")
        add_cover_button.clicked.connect(self.add_cover)
        remove_cover_button = QPushButton("Удалить обложку")
        remove_cover_button.clicked.connect(self.remove_cover)
        
        cover_layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)
        cover_buttons_layout.addWidget(add_cover_button)
        cover_buttons_layout.addWidget(remove_cover_button)
        cover_layout.addLayout(cover_buttons_layout)
        
        cover_group.setLayout(cover_layout)
        content_layout.addWidget(cover_group)

        # Кнопка сохранения
        save_button = QPushButton("Сохранить изменения")
        save_button.clicked.connect(self.save_metadata)
        content_layout.addWidget(save_button)

        self.setMinimumSize(600, 800)

    def rename_file(self):
        if not self.current_file:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте файл")
            return
            
        current_name = os.path.basename(self.current_file)
        current_ext = os.path.splitext(current_name)[1]
        
        new_name, ok = QInputDialog.getText(
            self, 
            "Переименовать файл",
            "Новое имя файла:",
            QLineEdit.EchoMode.Normal,
            os.path.splitext(current_name)[0]  # Показываем имя без расширения
        )
        
        if ok and new_name:
            try:
                # Добавляем расширение к новому имени
                new_name = new_name + current_ext
                new_path = os.path.join(os.path.dirname(self.current_file), new_name)
                
                if os.path.exists(new_path):
                    QMessageBox.warning(self, "Ошибка", "Файл с таким именем уже существует")
                    return
                    
                os.rename(self.current_file, new_path)
                self.current_file = new_path
                self.update_file_info()
                QMessageBox.information(self, "Успех", "Файл успешно переименован")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при переименовании файла: {str(e)}")

    def update_file_info(self):
        """Обновление информации о файле"""
        if self.current_file:
            file_size = os.path.getsize(self.current_file)
            size_str = self.format_size(file_size)
            file_format = os.path.splitext(self.current_file)[1].upper()[1:]
            
            self.file_label.setText(os.path.basename(self.current_file))
            self.file_size_label.setText(size_str)
            self.file_format_label.setText(file_format)
        else:
            self.file_label.setText("Файл не выбран")
            self.file_size_label.setText("Размер: -")
            self.file_format_label.setText("Формат: -")

    def format_size(self, size):
        """Форматирование размера файла"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите музыкальный файл",
            "",
            "Музыкальные файлы (*.mp3 *.flac *.wav *.m4a)"
        )
        
        if file_path:
            self.current_file = file_path
            self.current_cover = None  # Сбрасываем текущую обложку
            self.update_file_info()
            self.load_metadata()

    def clear_fields(self):
        """Очистка всех полей перед загрузкой новых данных"""
        for field in self.metadata_fields.values():
            if isinstance(field, QSpinBox):
                field.setValue(1)
            else:
                field.clear()
        self.comments_field.clear()
        self.cover_label.clear()
        self.cover_label.setText("Нет обложки")

    def load_metadata(self):
        if not self.current_file:
            return

        audio = File(self.current_file)
        
        if audio is None:
            QMessageBox.warning(self, "Ошибка", "Невозможно прочитать метаданные файла")
            return

        # Очищаем все поля перед загрузкой новых данных
        self.clear_fields()
        
        # Загружаем метаданные в зависимости от формата
        if isinstance(audio, FLAC):
            self.load_flac_metadata(audio)
        elif self.current_file.lower().endswith('.mp3'):
            self.load_mp3_metadata()
        
        # Загружаем обложку
        self.load_cover_art(audio)

    def load_flac_metadata(self, audio):
        metadata_mapping = {
            'title': 'title',
            'artist': 'artist',
            'album': 'album',
            'date': 'date',
            'genre': 'genre',
            'tracknumber': 'tracknumber',
            'copyright': 'copyright'
        }

        for field, tag in metadata_mapping.items():
            value = audio.get(tag, [''])[0] if tag in audio else ''
            if field == 'tracknumber':
                try:
                    self.metadata_fields[field].setValue(int(value))
                except ValueError:
                    self.metadata_fields[field].setValue(1)
            else:
                self.metadata_fields[field].setText(value)

        self.comments_field.setText(audio.get('comment', [''])[0] if 'comment' in audio else '')

    def load_mp3_metadata(self):
        try:
            # Загружаем базовые теги через EasyID3
            try:
                id3 = EasyID3(self.current_file)
            except:
                audio = File(self.current_file)
                audio.add_tags()
                id3 = EasyID3(self.current_file)

            metadata_mapping = {
                'title': 'title',
                'artist': 'artist',
                'album': 'album',
                'date': 'date',
                'genre': 'genre',
                'tracknumber': 'tracknumber'
            }

            for field, tag in metadata_mapping.items():
                value = id3.get(tag, [''])[0] if tag in id3 else ''
                if field == 'tracknumber':
                    try:
                        track_num = int(value.split('/')[0])
                        self.metadata_fields[field].setValue(track_num)
                    except (ValueError, IndexError):
                        self.metadata_fields[field].setValue(1)
                else:
                    self.metadata_fields[field].setText(value)

            # Загружаем расширенные теги через ID3
            audio = ID3(self.current_file)

            # Загружаем комментарий
            comments = audio.getall('COMM')
            if comments:
                # Ищем комментарий на английском языке или берем первый доступный
                eng_comment = None
                any_comment = None
                
                for comm in comments:
                    if comm.lang == 'eng':
                        eng_comment = comm
                        break
                    any_comment = comm
                
                comment_text = (eng_comment or any_comment).text[0] if (eng_comment or any_comment) else ''
                self.comments_field.setText(comment_text)

            # Загружаем copyright
            copyright_tags = audio.getall('TCOP')
            if copyright_tags:
                self.metadata_fields['copyright'].setText(copyright_tags[0].text[0])

        except Exception as e:
            print(f"Ошибка при загрузке MP3 метаданных: {str(e)}")

    def load_cover_art(self, audio):
        """Загрузка обложки"""
        self.current_cover = None  # Сбрасываем текущую обложку
        cover_art = None
        
        if isinstance(audio, FLAC):
            if audio.pictures:
                cover_art = audio.pictures[0].data
        elif self.current_file.lower().endswith('.mp3'):
            try:
                id3 = ID3(self.current_file)
                for tag in id3.values():
                    if tag.FrameID == 'APIC':
                        cover_art = tag.data
                        break
            except:
                pass

        if cover_art:
            self.current_cover = cover_art  # Сохраняем текущую обложку
            pixmap = QPixmap()
            pixmap.loadFromData(cover_art)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            self.cover_label.setPixmap(scaled_pixmap)
        else:
            self.cover_label.clear()
            self.cover_label.setText("Нет обложки")

    def add_cover(self):
        if not self.current_file:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте файл")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение обложки",
            "",
            "Изображения (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            try:
                with Image.open(file_path) as img:
                    # Конвертируем в JPEG и оптимизируем размер
                    img = img.convert('RGB')
                    # Ограничиваем размер обложки
                    max_size = (800, 800)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Сохраняем в bytes
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=90, optimize=True)
                    self.current_cover = img_byte_arr.getvalue()

                    # Отображаем обложку
                    pixmap = QPixmap()
                    pixmap.loadFromData(self.current_cover)
                    scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
                    self.cover_label.setPixmap(scaled_pixmap)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке обложки: {str(e)}")

    def remove_cover(self):
        if not self.current_file:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте файл")
            return

        self.current_cover = None
        self.cover_label.clear()
        self.cover_label.setText("Нет обложки")

    def save_metadata(self):
        if not self.current_file:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте файл")
            return

        try:
            # Сначала сохраняем обложку
            self.save_cover_art()
            
            # Затем сохраняем остальные метаданные
            if self.current_file.lower().endswith('.mp3'):
                self.save_mp3_metadata()
            elif self.current_file.lower().endswith('.flac'):
                self.save_flac_metadata()
            
            QMessageBox.information(self, "Успех", "Метаданные успешно сохранены")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении метаданных: {str(e)}")

    def save_mp3_metadata(self):
        try:
            # Сначала сохраняем базовые теги через EasyID3
            try:
                audio_easy = EasyID3(self.current_file)
            except:
                audio = File(self.current_file)
                audio.add_tags()
                audio.save()
                audio_easy = EasyID3(self.current_file)

            # Сохраняем базовые теги
            basic_mapping = {
                'title': 'title',
                'artist': 'artist',
                'album': 'album',
                'date': 'date',
                'genre': 'genre',
                'tracknumber': 'tracknumber'
            }

            for field, tag in basic_mapping.items():
                if field == 'tracknumber':
                    value = str(self.metadata_fields[field].value())
                else:
                    value = self.metadata_fields[field].text()
                
                if value:
                    audio_easy[tag] = value

            audio_easy.save()

            # Теперь сохраняем расширенные теги через ID3
            audio = ID3(self.current_file)

            # Сохраняем комментарий
            comment_text = self.comments_field.toPlainText()
            if comment_text:
                from mutagen.id3 import COMM
                # Удаляем все старые комментарии
                audio.delall('COMM')
                # Добавляем новый комментарий
                audio.add(COMM(
                    encoding=3,  # UTF-8
                    lang='eng',  # Английский язык
                    desc='',     # Пустое описание
                    text=comment_text
                ))
            else:
                # Если комментарий пустой, удаляем все теги COMM
                audio.delall('COMM')

            # Сохраняем copyright
            if self.metadata_fields['copyright'].text():
                from mutagen.id3 import TCOP
                audio.add(TCOP(
                    encoding=3,
                    text=self.metadata_fields['copyright'].text()
                ))

            audio.save()

        except Exception as e:
            raise Exception(f"Ошибка при сохранении MP3 метаданных: {str(e)}")

    def save_flac_metadata(self):
        audio = FLAC(self.current_file)

        metadata_mapping = {
            'title': 'TITLE',
            'artist': 'ARTIST',
            'album': 'ALBUM',
            'date': 'DATE',
            'genre': 'GENRE',
            'tracknumber': 'TRACKNUMBER',
            'copyright': 'COPYRIGHT'
        }

        for field, tag in metadata_mapping.items():
            if field == 'tracknumber':
                value = str(self.metadata_fields[field].value())
            else:
                value = self.metadata_fields[field].text()
            
            if value:
                audio[tag] = value

        # Сохраняем комментарий
        comment_text = self.comments_field.toPlainText()
        if comment_text:
            audio['COMMENT'] = comment_text
        else:
            # Если комментарий пустой, удаляем тег
            if 'COMMENT' in audio:
                del audio['COMMENT']

        audio.save()

    def save_cover_art(self):
        """Сохранение обложки"""
        try:
            if self.current_file.lower().endswith('.mp3'):
                try:
                    audio = ID3(self.current_file)
                except:
                    audio = File(self.current_file)
                    audio.add_tags()
                    audio = ID3(self.current_file)

                # Удаляем все существующие обложки
                audio.delall('APIC')

                if self.current_cover is not None:
                    # Добавляем новую обложку
                    audio.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=self.current_cover
                    ))
                audio.save()

            elif self.current_file.lower().endswith('.flac'):
                audio = FLAC(self.current_file)
                audio.clear_pictures()

                if self.current_cover is not None:
                    from mutagen.flac import Picture
                    picture = Picture()
                    picture.type = 3
                    picture.mime = 'image/jpeg'
                    picture.desc = 'Cover'
                    picture.data = self.current_cover
                    audio.add_picture(picture)
                audio.save()

        except Exception as e:
            raise Exception(f"Ошибка при сохранении обложки: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MetadataEditor()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()