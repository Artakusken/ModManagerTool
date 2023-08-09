import sqlite3
import json
from PyQt5.QtWidgets import QSizePolicy, QWidget, QLabel, QFrame, QPushButton, QPlainTextEdit, QLineEdit, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from os import listdir, path


class ModInfoWidget(QWidget):
    """ Widget that displays all info about the mod, used in MainWindow """
    def __init__(self, game, app):
        super().__init__()

        self.localization = json.load(open("localization.json", encoding="utf-8"))
        self.lang = open("config.txt", "r").readline().split(" = ")[-1]
        self.widget_localization = self.localization[self.lang]["ModInfoWidget"]

        self.title = self.widget_localization["init_title"]
        self.tags = [self.widget_localization["init_tags"]]
        self.filepath = self.widget_localization["init_filepath"]
        self.mod_version = self.widget_localization["init_mode_version"]
        self.supported_game_version = self.widget_localization["init_supported_game_version"]
        self.required_mods = [self.widget_localization["init_required_mods"]]
        self.incompatible_mods = [self.widget_localization["init_incompatible_mods"]]
        self.commentary = self.widget_localization["init_commentary"]
        self.saved = False
        self.game_id = 0
        self.main_window = app
        self.game_object = game
        self.image_path = ''

        self.initUI()

    def initUI(self) -> None:
        """ User interface initialization (QT objects) """
        self.setGeometry(0, 0, 950, 200)
        self.setMinimumSize(950, 200)

        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setLineWidth(2)
        self.frame.resize(950, 200)
        self.frame.setStyleSheet("background-color: rgb(100, 150, 220)")
        self.frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.titleLine = QLineEdit(self.title, self)
        self.titleLine.resize(272, 20)
        self.titleLine.move(4, 10)

        self.modVersionLabel = QLabel(self.widget_localization["modVersionLabel"], self)
        self.modVersionLabel.move(280, 10)
        self.modVersionLabel.resize(70, 20)

        self.modVersionLine = QLineEdit(self.mod_version, self)
        self.modVersionLine.resize(42, 20)
        self.modVersionLine.move(348, 10)

        self.gameVersionLabel = QLabel(self.widget_localization["gameVersionLabel"], self)
        self.gameVersionLabel.move(400, 10)
        self.gameVersionLabel.resize(160, 20)

        self.gameVersionLine = QLineEdit(self.supported_game_version, self)
        self.gameVersionLine.resize(62, 20)
        self.gameVersionLine.move(562, 10)

        self.imageLabel = QLabel(self)
        self.imageLabel.move(630, 5)
        self.imageLabel.resize(300, 180)
        self.imageLabel.setText(self.widget_localization["no_img"])

        self.tagsLabel = QLabel(self.widget_localization["tagsLabel"], self)
        self.tagsLabel.resize(32, 20)
        self.tagsLabel.move(4, 40)

        if isinstance(self.tags, list):  # It may be a list due to the peculiarities of data import
            self.tagsLine = QLineEdit(",".join(self.tags), self)
        else:
            self.tagsLine = QLineEdit(self.tags, self)  # a string, because the file processing has passed and transformed the list into a string
        self.tagsLine.resize(590, 20)
        self.tagsLine.move(34, 40)

        self.filepathLabel = QLabel(self.widget_localization["filepathLabel"], self)
        self.filepathLabel.move(4, 65)
        self.filepathLabel.resize(75, 20)

        self.filepathLine = QLineEdit(self.filepath, self)
        self.filepathLine.resize(526, 20)
        self.filepathLine.move(98, 65)

        self.requiredModsLabel = QLabel(self.widget_localization["requiredModsLabel"], self)
        self.requiredModsLabel.move(4, 90)
        self.requiredModsLabel.resize(90, 20)

        if isinstance(self.required_mods, list):
            self.requiredModsLine = QLineEdit(",".join(self.required_mods), self)
        else:
            self.requiredModsLine = QLineEdit(self.required_mods, self)
        self.requiredModsLine.resize(526, 20)
        self.requiredModsLine.move(98, 90)

        self.incompatibleModsLabel = QLabel(self.widget_localization["incompatibleModsLabel"], self)
        self.incompatibleModsLabel.move(4, 115)
        self.incompatibleModsLabel.resize(95, 20)

        if isinstance(self.incompatible_mods, list):
            self.incompatibleModsLine = QLineEdit(",".join(self.incompatible_mods), self)
        else:
            self.incompatibleModsLine = QLineEdit(self.incompatible_mods, self)
        self.incompatibleModsLine.resize(526, 20)
        self.incompatibleModsLine.move(98, 115)

        self.commentLabel = QLabel(self.widget_localization["commentLabel"], self)
        self.commentLabel.move(4, 140)
        self.commentLabel.resize(80, 20)

        self.commentText = QPlainTextEdit(self.commentary, self)
        self.commentText.resize(620, 40)
        self.commentText.move(4, 158)

        self.savedLabel = QLabel(self.widget_localization["notSaved"], self)
        self.savedLabel.resize(120, 20)
        self.savedLabel.move(838, 5)

        self.saveButton = QPushButton(self.widget_localization["saveButton"], self)
        self.saveButton.resize(106, 30)
        self.saveButton.move(837, 25)

        self.deleteButton = QPushButton(self.widget_localization["deleteButton"], self)
        self.deleteButton.resize(106, 30)
        self.deleteButton.move(837, 65)

        self.choosePic = QPushButton(self.widget_localization["choosePic"], self)
        self.choosePic.resize(106, 30)
        self.choosePic.move(837, 105)

        self.updateButton = QPushButton(self.widget_localization["updateButton"], self)
        self.updateButton.resize(106, 30)
        self.updateButton.move(837, 145)

        self.saveButton.clicked.connect(self.save_into_base)
        self.deleteButton.clicked.connect(self.delete)
        self.choosePic.clicked.connect(self.find_image)
        self.updateButton.clicked.connect(self.update_mod_data)

    def check_conn(self, conn: sqlite3.Connection) -> bool:
        """ Tests the connection to database """
        try:
            conn.cursor()
            return True
        except Exception as error:
            print(f"Database connection error: {error}")
            return False

    def set_image(self, image_path: str):
        """ Sets the widget image """
        image = QImage(image_path)
        if image.isNull():
            self.imageLabel.setText(self.widget_localization["pic_import_failure"])
        else:
            image = image.scaledToHeight(200, Qt.SmoothTransformation)
            pixmap = QPixmap.fromImage(image)
            self.image_path = image_path
            self.imageLabel.move(630, 0)
            self.imageLabel.resize(200, 200)
            self.imageLabel.setPixmap(pixmap)

    def find_image(self):
        """ Opens file dialog and tries to set image """
        if self.lang == "RU":  # language of the file dialogue
            impath = QFileDialog.getOpenFileName(self, 'Выберите картинку для мода', "", "Файл (*.jpg *.png)")[0]
        else:
            impath = QFileDialog.getOpenFileName(self, 'Select a picture for the mod', "", "Файл (*.jpg *.png)")[0]
        self.image_path = impath
        self.set_image(impath)

    def delete(self) -> None:
        """ Deletes modification from the database and widget from the app """
        con = sqlite3.connect(self.main_window.database_name)
        if not self.check_conn(con):
            self.informationText.setText("Ошибка при подключении к базе данных")
            return
        cur = con.cursor()

        #  SQL query to get the mod from the database
        mod_in_base = cur.execute('''SELECT Mod_ID FROM Mods 
                                     WHERE Title = ? AND Game_ID = ?''', (self.title, self.game_id))
        mod = mod_in_base.fetchone()
        if mod:  # case when the mod is in the database
            mod_id = mod[0]
            cur.execute(''' DELETE from Mods WHERE Mod_ID = ? AND Game_ID = ?''', (mod_id, self.game_id))
            con.commit()
            con.close()
            self.saved = False
            self.main_window.update_number_of_saved_mods()
            self.game_id = -1  # means the mod is deleted
            self.setParent(None)  # deletes the widget
        else:  # case when the mod exists only as widget in the app
            self.game_id = -1  # means the mod is deleted
            self.setParent(None)  # deletes the widget
        self.main_window.informationText.setText("'" + self.title + "' " + self.widget_localization['mod_deleted'])

        for i in range(len(self.game_object.mods)):  # remove a mod from the list
            if self.game_object.mods[i].title == self.title:
                self.game_object.mods.pop(i)
                break
        self.main_window.gameModsNumberLabel.setText(self.main_window.window_localization['gameModsNumberLabel'] + str(len(self.game_object.mods)))
        if len(self.game_object.mods) < 2:
            self.main_window.activate_mod_filter_buttons()

    def clear_args(self):
        """ Makes all widget fields empty """
        self.title = ''
        self.tags = []
        self.filepath = ''
        self.image_path = ''
        self.mod_version = ''
        self.supported_game_version = ''
        self.required_mods = []
        self.incompatible_mods = []
        self.commentary = ''

    def get_args(self) -> list:
        """ Returns a list with all widget info """
        return [self.title, self.tags, self.filepath, self.mod_version, self.supported_game_version, self.required_mods,
                self.incompatible_mods, self.commentary]

    def save_into_base(self, old_title: str = "") -> str:
        """ Saves/updates to database """
        con = sqlite3.connect(self.main_window.database_name)
        if not self.check_conn(con):
            self.informationText.setText("Ошибка при подключении к базе данных")
            return ""
        cur = con.cursor()
        if not old_title:  # SQL query when mod didn't change its own title during the update
            mod_in_base = cur.execute(''' SELECT Mod_ID FROM Mods
                                          WHERE Title = ? AND Game_ID = ? ''', (self.title, self.game_id))
        else:  # SQL query when mod changed its own title during the update
            mod_in_base = cur.execute(''' SELECT Mod_ID FROM Mods
                                          WHERE Title = ? AND Game_ID = ? ''', (old_title, self.game_id))
        mod = mod_in_base.fetchone()
        if mod and self.saved:  # update the mod in the database (mod is already saved in the database)
            for game_mod in self.game_object.mods:  # check if any of the other mods has same key (title, filepath) parameters
                if game_mod.title == self.titleLine.text() and game_mod.filepath == self.filepathLine.text() and game_mod != self and game_mod.saved:
                    self.main_window.informationText.setText("'" + self.titleLine.text() + "'" + self.main_window.errors_notes["same_mod_title"])
                    con.close()
                    return self.titleLine.text()
            mod_id = mod[0]
            self.title = self.titleLine.text()
            self.tags = self.tagsLine.text()
            self.filepath = self.filepathLine.text()
            self.image_path = self.image_path
            self.mod_version = self.modVersionLine.text()
            self.supported_game_version = self.gameVersionLine.text()
            self.required_mods = self.requiredModsLine.text()
            self.incompatible_mods = self.incompatibleModsLine.text()
            self.commentary = self.commentText.toPlainText()
            #  ↓ update SQL query
            cur.execute('''UPDATE Mods
                           SET Title = ?,
                               Tags = ?,
                               Mversion = ?,
                               Gversion = ?,
                               Requirements = ?,
                               Filepath = ?,
                               Incompatible = ?,
                               Commentary = ?,
                               IMG_Path = ?
                           WHERE Mod_ID = ? ''', (self.title, self.tags, self.mod_version, self.supported_game_version,
                                                  self.required_mods, self.filepath, self.incompatible_mods, self.commentary,
                                                  self.image_path, mod_id))
        else:  # add the mod to the database
            for game_mod in self.game_object.mods:  # check if any of the other mods has same key (title, filepath) parameters
                if game_mod.title == self.titleLine.text() and game_mod.filepath == self.filepathLine.text() and game_mod != self and game_mod.saved:
                    self.main_window.informationText.setText("'" + self.titleLine.text() + "'" + self.main_window.errors_notes["same_mod_title"])
                    con.close()
                    return self.titleLine.text()
            self.title = self.titleLine.text()
            self.tags = self.tagsLine.text()
            self.filepath = self.filepathLine.text()
            self.image_path = self.image_path
            self.mod_version = self.modVersionLine.text()
            self.supported_game_version = self.gameVersionLine.text()
            self.required_mods = self.requiredModsLine.text()
            self.incompatible_mods = self.incompatibleModsLine.text()
            self.commentary = self.commentText.toPlainText()
            #  ↓ insert SQL query
            cur.execute('''INSERT INTO Mods(Game_ID,Title,Tags,Mversion,Gversion,Requirements,Filepath,Incompatible,Commentary,IMG_Path) 
                           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (self.game_id, self.title, self.tags, self.mod_version, self.supported_game_version, self.required_mods,
                         self.filepath, self.incompatible_mods, self.commentary, self.image_path))
            self.saved = True
            self.savedLabel.setText(self.widget_localization['saved'])
            self.main_window.informationText.setText("'" + self.title + "' " + self.widget_localization['saved'])
            self.main_window.update_number_of_saved_mods()
        con.commit()
        con.close()
        return ""

    def update_mod_data(self, all_mods_update: bool = False) -> str:
        """ Updates all widget fields. Almost the same function as add_mod_with_info from the MainWindow Class
            Returns title of the mod if mod data has changed (later the main window will show which mods have been updated),
            otherwise returns '' """
        descriptor_file_path = ""
        mod_title_changed = ""

        if self.filepath:
            try:  # try to find mod descriptor from the folder where mod is located
                for i in listdir(self.filepath):
                    if i.endswith(".mod"):
                        descriptor_file_path = self.filepath + "/" + i
                        break
            except Exception as error:  # otherwise user selects the file by himself
                print(error)
                if not all_mods_update:  # if update is only for this mod
                    if self.lang == "RU":
                        descriptor_file_path = QFileDialog.getOpenFileName(self, 'Выберите файл с дескрпитором мода', ".", "Файл (*.mod *.txt)")[0]
                    else:
                        descriptor_file_path = QFileDialog.getOpenFileName(self, 'Select the file with the mod descriptor', ".", "File (*.mod *.txt)")[0]
                else:
                    return self.title

        if descriptor_file_path != '':
            with open(descriptor_file_path, encoding="UTF8") as descriptor_file:
                braces = False
                braces_content = ''
                image_file = 1
                self.tags = []
                self.required_mods = []
                for i in descriptor_file.readlines():
                    if '=' in i or '\t' in i or '}' in i:
                        if not braces:
                            key = i[:i.index('=')].strip()
                            if '#' in i:
                                value = i[i.index('=') + 1:i.index('#')].strip('"\n ')
                            else:
                                value = i[i.index('=') + 1::].strip('"\n ')
                        else:
                            braces_content = i.strip('\t\n"')

                        if key == 'name' or key == 'title':
                            if self.title != value:
                                mod_title_changed = self.title
                            self.title = value
                            self.titleLine.setText(self.title)
                        elif (key == 'tags' or key == 'dependencies') and not braces:
                            braces = True
                        elif '}' in i and braces is True:
                            braces = False
                        elif braces is True and key == 'tags':
                            self.tags.append(braces_content)
                            self.tagsLine.setText(",".join(self.tags))
                        elif braces is True and key == 'dependencies':
                            self.required_mods.append(braces_content)
                            self.requiredModsLine.setText(",".join(self.required_mods))
                        elif key == 'version':
                            self.mod_version = value
                            self.modVersionLine.setText(self.mod_version)
                        elif key == 'supported_version':
                            self.supported_game_version = value
                            self.gameVersionLine.setText(self.supported_game_version)
                        elif key == 'path' or key == 'archive':
                            if path.exists(value):
                                self.filepath = value
                            else:
                                self.filepath = descriptor_file_path[:descriptor_file_path.rfind("/")]
                        elif key == 'picture' or key == 'poster':
                            image_file = value

                if self.filepath == '':
                    self.filepath = descriptor_file_path[:descriptor_file_path.rfind("/")]
                if image_file != 1 and self.filepath != '':
                    image_path = self.filepath + '/' + image_file
                    self.set_image(image_path)
                else:
                    for file in listdir(self.filepath):
                        if file.endswith((".png", ".jpg")):
                            image_path = descriptor_file_path[:descriptor_file_path.rfind("/") + 1] + file
                            self.set_image(image_path)
                            break

                if mod_title_changed:  # if mod has new title
                    self.save_into_base(mod_title_changed)
                else:
                    self.save_into_base()
        return ""
