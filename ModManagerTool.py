import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
from GameClass import *


class CrashWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crash")
        self.setGeometry(800, 400, 400, 80)
        self.crash = QLabel("App is not usable. Reason:", self)
        self.crash_info = QLabel("", self)
        self.crash.move(20, 10)
        self.crash.resize(400, 30)
        self.crash_info.move(20, 40)
        self.crash_info.resize(400, 30)


class MainWindow(QMainWindow):
    """ Application's main window """
    def __init__(self):
        super().__init__()

        try:
            self.lang = open("config.txt", "r").readline().split(" = ")[-1]
        except Exception as error:
            print("Config.txt file error: ", error)
            self.lang = "EN"
            config_file = open("config.txt", "w")
            print("lang = EN", end="", file=config_file)
            config_file.close()

        try:
            self.localization = json.load(open("localization.json", encoding="utf-8"))
        except FileNotFoundError:
            uic.loadUi('MMT_EN.ui', self)
            crash = CrashWindow()
            crash.crash_info.setText("No localization file (localization.json). Download it from github to the root folder")
            self.show()
            crash.show()
            sys.exit(app.exec())

        self.window_localization = self.localization[self.lang]["MainWindow"]
        self.errors_notes = self.localization[self.lang]["Errors/Notes"]
        if self.lang == "RU":
            uic.loadUi('MMT_RU.ui', self)
            self.RULang.setChecked(True)
            self.game_label = "Игра:"
        else:
            uic.loadUi('MMT_EN.ui', self)
            self.ENLang.setChecked(True)
            self.game_label = "Game:"

        self.games_counter = 0  # used as text when new game button is created
        self.games_titles_list = []  # list of all game titles
        self.games = []  # list of 'Game' classes
        self.chosen_game = None  # currently opened game
        self.chosen_game_button = None  # it's ↑ button in QT gamesVLayout
        self.import_games()  # get all games and mods from the database

        if len(self.games) > 0:
            self.game_name_is_set = True  # variable that controls app's functionality (it's shortened until user will name recently created game)
        else:
            self.game_name_is_set = False

        self.RULang.clicked.connect(self.switch_language)
        self.ENLang.clicked.connect(self.switch_language)
        self.createGameButton.clicked.connect(self.create_game_button)
        self.nameGameButton.clicked.connect(self.add_game_button)
        self.deleteGameButton.clicked.connect(self.delete_game)
        self.renameGameButton.clicked.connect(self.rename_game_button)
        self.addBlankModButton.clicked.connect(self.add_blank_mod_widget)
        self.addModWInfoButton.clicked.connect(self.add_mod_with_info)
        self.allFolderModsButton.clicked.connect(self.folder_mods)
        self.ABCButton.clicked.connect(lambda: self.open_mods(self, mod_filter="alphabetical"))
        self.supVersionButton.clicked.connect(lambda: self.open_mods(self, mod_filter="supported_version"))
        self.gameVersionButton.clicked.connect(self.ver_highlight)
        self.tagsButton.clicked.connect(self.tag_highlight)
        self.requiredButton.clicked.connect(self.relation_highlight)
        self.saveAllMods.clicked.connect(self.save_all)
        self.updateAllMods.clicked.connect(self.update_all)

    def activate_mod_filter_buttons(self):
        """ Activates/disables all mod_filter group buttons """
        for button in self.buttonGroup.buttons():
            if len(self.chosen_game.mods) > 1:
                button.setEnabled(True)
            else:
                button.setEnabled(False)

    def clear_layout(self):
        """ Makes the mods' layout empty. Deletes all widgets one by one """
        while self.modsVLayout.count() > 0:
            self.modsVLayout.itemAt(0).widget().setParent(None)

    def update_number_of_saved_mods(self):
        """ Updates the number of saved mods in savedModsNumberLabel """
        counter = 0
        if self.chosen_game:
            for mod in self.chosen_game.mods:
                if mod.saved:
                    counter += 1
        self.savedModsNumberLabel.setText(self.window_localization['savedModsNumberLabel'] + str(counter))

    def switch_language(self):
        """ Writes chosen language in the config file """
        if self.lang == self.sender().text():  # if current language == button of this language, no info displayed
            self.informationText.setText("")
        elif self.sender() == self.ENLang:
            self.informationText.setText("You have switched language to english. Reboot the app")
        elif self.sender() == self.RULang:
            self.informationText.setText("Вы сменили язык на русский. Перезагрузите приложение")

        print(f"lang = {self.sender().text()}", end="", file=open("config.txt", "w"))  # config file rewritten with chosen language

    def import_games(self) -> None:
        """ Retrieves info from the database and creates game classes along with buttons """
        con = connect_base(self.lang)
        if type(con) == sqlite3.Connection:
            cur = con.cursor()
            games = cur.execute("""SELECT * FROM Games""").fetchall()
        else:
            self.informationText.setText(con)
            return

        for game in games:
            new_game_button = QPushButton(game[1], self)  # game button ↓
            self.gamesVLayout.insertWidget(0, new_game_button)  # in a layout
            new_game_button.clicked.connect(self.open_mods)  # if clicked execute this function
            self.games_counter += 1
            # self.game_name_is_set = False
            imported_game = Game(new_game_button)  # game class
            imported_game.title = game[1]
            imported_game.id = game[0]
            imported_game.import_mods(self)
            self.games.append(imported_game)
            self.games_titles_list.append(imported_game.title)

    def rename_game_button(self):
        """ Renames game in the database and in the application """
        new_game_title = self.gameLineEdit.text()  # new title from gameLineEdit
        if self.chosen_game:  # game that will be renamed
            if new_game_title not in self.games_titles_list:  # check repetition
                self.chosen_game.update_title(new_game_title)
                self.chosen_game.button.setText(new_game_title)
                self.games_titles_list = [game.title for game in self.games]
                self.gameModsLabel.setText(f"{self.game_label} {self.chosen_game.title}")
            else:
                self.informationText.setText(f"'{new_game_title}' {self.errors_notes['same_game_title']}")
        else:
            self.informationText.setText(self.errors_notes['choose_game_to_rename_it'])

    def create_game_button(self):
        """ Creates a new game (not from the base) along with new button """
        new_game_button = QPushButton(str(self.games_counter), self)  # new button, without attached game
        self.gamesVLayout.insertWidget(0, new_game_button)
        new_game_button.clicked.connect(self.open_mods)
        self.games.append(Game(new_game_button))
        self.chosen_game = self.games[-1]
        self.createGameButton.setEnabled(False)  # no new game can be added
        self.game_name_is_set = False  # disable app, wait for add_game_button func

    def add_game_button(self) -> None:
        """ Sets the title of the game and its button, then adds the game to the database """
        game_title = self.gameLineEdit.text()  # title from gameLineEdit

        if not self.chosen_game:  # game and it's button that will be named
            self.informationText.setText(self.errors_notes['init_game_title'])
            return

        if self.chosen_game.button and not self.game_name_is_set:
            con = connect_base(self.lang)
            if type(con) == sqlite3.Connection:
                cur = con.cursor()
                if game_title not in self.games_titles_list:
                    self.chosen_game.button.setText(game_title)
                    self.createGameButton.setEnabled(True)  # new game can be added
                    self.game_name_is_set = True  # app is now functional
                    cur.execute('''INSERT INTO Games(Game_title) VALUES(?)''', (game_title,))  # add to database
                    self.informationText.clear()
                    self.games[-1].title = game_title
                    self.open_mods(new_game=self.chosen_game)
                    self.games_counter += 1
                    con.commit()
                    con.close()
                else:
                    self.informationText.setText(f"'{game_title}' {self.errors_notes['same_game_title']}")
            else:
                self.informationText.setText(self.errors_notes['base_connection_failure'])

    def delete_game(self) -> None:
        """ Deletes the game from the database and all related widgets and button from the app """
        con = connect_base(self.lang)
        if type(con) != sqlite3.Connection:
            self.informationText.setText(self.errors_notes['base_connection_failure_when_deleting_game'])
            return

        if not self.game_name_is_set:
            self.informationText.setText(self.errors_notes['finish_game_init'])
            return
        
        for mod in self.chosen_game.mods:  # delete all game mods from the database and widgets from the layout
            mod.delete()

        cur = con.cursor()
        cur.execute("""DELETE from Games WHERE Game_Title = ?""", (self.chosen_game.title,))  # query to delete game
        con.commit()
        con.close()
        if self.chosen_game.button:
            self.chosen_game.button.setParent(None)
        for i in range(len(self.games)):  # pop class from self.games list
            if self.games[i].title == self.chosen_game.title:
                self.games.pop(i)
                break
        self.chosen_game = None
        self.gameModsLabel.setText(f"{self.game_label} ")
        self.games_counter -= 1

    def open_mods(self, new_game: bool = None, mod_filter: str = "") -> None:
        """ Creates a ModInfoWidget for each mod of the game """
        if type(new_game) == Game:  # game button that associates with mods
            clicked_button = new_game.button
        elif mod_filter != "":
            clicked_button = self.chosen_game.button
        else:
            clicked_button = self.sender()

        if not self.game_name_is_set:
            self.informationText.setText(self.errors_notes['finish_game_init'])
            return

        self.clear_layout()
        for game in self.games:
            if game.button == clicked_button:
                self.chosen_game = game
                self.gameModsLabel.setText(f"{self.game_label} {self.chosen_game.title}")

                if mod_filter == "alphabetical":  # check for filters
                    mods = sorted(self.chosen_game.mods, key=lambda x: x.title)
                elif mod_filter == "supported_version":
                    mods = sorted(self.chosen_game.mods, key=lambda x: x.supported_game_version, reverse=True)
                else:
                    mods = self.chosen_game.mods

                for mod in mods:
                    try:
                        mod.set_image(mod.image_path)
                    except Exception as fail:
                        print(mod.title, fail)
                        self.informationText.setText(self.errors_notes['image_import_failure'])  # text instead picture
                    self.modsVLayout.addWidget(mod)  # new widget with mod info

                self.activate_mod_filter_buttons()
                self.gameModsNumberLabel.setText(self.window_localization['gameModsNumberLabel'] + str(len(self.chosen_game.mods)))
                self.update_number_of_saved_mods()
                break

    def add_blank_mod_widget(self):
        """ Adds new blank mod widget in the app (it's not saved in database yet) """
        if self.chosen_game:
            new_widget = ModInfoWidget(self.chosen_game, self)
            new_widget.game_id += self.chosen_game.id
            self.modsVLayout.addWidget(new_widget)
            self.chosen_game.mods += [new_widget]
            self.informationText.setText(self.window_localization["blank_widget_added"] + self.chosen_game.title)
            self.activate_mod_filter_buttons()
            self.gameModsNumberLabel.setText(self.window_localization['gameModsNumberLabel'] + str(len(self.chosen_game.mods)))
        else:
            self.informationText.setText(self.errors_notes["choose_game_to_add_mod"])

    def add_mod_with_info(self, descriptor_file_path: bool = None):
        """ Adds new mod widget with the data from descriptor file in the app (it's not saved in database yet) """
        if self.chosen_game:
            if not descriptor_file_path:  # creates file dialogue
                descriptor_file_path = QFileDialog.getOpenFileName(self, self.window_localization["file_dialog_desc"], ".",
                                                                   self.window_localization["file_dialog_type"])[0]
            if descriptor_file_path:
                with open(descriptor_file_path, encoding="UTF8") as descriptor_file:  # file parsing (for now only paradox games descriptor type)
                    new_widget = ModInfoWidget(self.chosen_game, self)
                    new_widget.clear_args()
                    braces = False  # bool to check braces were opened before
                    braces_content = ''
                    image_file = 1  # image file name
                    for i in descriptor_file.readlines():  # read all lines in the file
                        if '=' in i or '\t' in i or '}' in i:
                            if not braces:  # get key and value, they are divided by '='
                                key = i[:i.index('=')].strip()
                                if '#' in i:
                                    value = i[i.index('=') + 1:i.index('#')].strip('"\n ')
                                else:
                                    value = i[i.index('=') + 1::].strip('"\n ')
                            else:
                                braces_content = i.strip('\t\n"')

                            if key == 'name' or key == 'title':  # check key and set value for this key in the widget
                                new_widget.title = value
                            elif (key == 'tags' or key == 'dependencies') and not braces:
                                braces = True
                            elif '}' in i and braces is True:  # braces end
                                braces = False
                            elif braces is True and key == 'tags':  # keys for braces
                                new_widget.tags.append(braces_content)
                            elif braces is True and key == 'dependencies':
                                new_widget.required_mods.append(braces_content)
                            elif key == 'version':
                                new_widget.mod_version = value
                            elif key == 'supported_version':
                                new_widget.supported_game_version = value
                            elif key == 'path' or key == 'archive':
                                if path.exists(value):  # check if filepath exists
                                    new_widget.filepath = value
                                else:
                                    new_widget.filepath = descriptor_file_path[:descriptor_file_path.rfind("/")]
                            elif key == 'picture' or key == 'poster':
                                image_file = value

                    if not new_widget.title:  # check condition (has title and doesn't exist in base) for mod creation
                        return
                    for mod in self.chosen_game.mods:  # check if mod with same title and path already in the database
                        if mod.filepath == new_widget.filepath and mod.title == new_widget.title and mod.game_id != -1:
                            self.informationText.setText(self.errors_notes["mod_is_already_added"])
                            return

                    if new_widget.filepath == '':
                        new_widget.filepath = descriptor_file_path[:descriptor_file_path.rfind("/")]  # descriptor file folder
                    new_widget.initUI()
                    if image_file != 1 and new_widget.filepath != '':  # path for image file
                        image_path = new_widget.filepath + '/' + image_file
                        new_widget.set_image(image_path)
                    else:
                        for file in listdir(new_widget.filepath):  # look for some image files in the mod folder
                            if file.endswith((".png", ".jpg")):
                                image_path = new_widget.filepath + '/' + file
                                new_widget.set_image(image_path)
                                break

                    new_widget.game_id = self.chosen_game.id
                    self.modsVLayout.addWidget(new_widget)
                    self.chosen_game.mods += [new_widget]
                    self.informationText.setText(self.chosen_game.title + self.errors_notes["new_mod_is_added"] + new_widget.title)
                    self.gameModsNumberLabel.setText(self.window_localization['gameModsNumberLabel'] + str(len(self.chosen_game.mods)))
                    self.activate_mod_filter_buttons()
            else:
                self.informationText.setText(self.errors_notes["no_mod_selected"])
        else:
            self.informationText.setText(self.errors_notes["choose_game_to_add_mod"])

    def folder_mods(self):
        """ Parses the folder """
        if self.chosen_game:  # folder dialogue
            folder_path = QFileDialog.getExistingDirectory(None, self.window_localization["folder_dialog_desc"])
            try:
                folder = listdir(folder_path)
            except Exception as error:
                self.informationText.setText(self.errors_notes["no_mod_selected"])
                print(error)
                return
            for data in folder:
                if data.count(".") == 0:  # folder contains only folders
                    for mod_data in listdir(folder_path + "/" + data):  # parse new folder
                        if mod_data.endswith((".mod", ".txt")):
                            try:
                                self.add_mod_with_info(folder_path + "/" + data + "/" + mod_data)
                                print("++++++++++++++", folder_path,  data, mod_data, self.chosen_game.mods[-1].title)
                            except Exception as fail:
                                print("--------------", mod_data, fail)
                            if mod_data.endswith(".mod"):  # that's definitely enough
                                break
                else:  # some files
                    if data.endswith((".mod", ".txt")):
                        try:
                            self.add_mod_with_info(folder_path + "/" + data)
                            print("++++++++++++++", folder_path, data, self.chosen_game.mods[-1].title)
                        except Exception as fail:
                            print("--------------", data, fail)
            self.informationText.setText(self.errors_notes["mods_from_folder"] + folder_path)

    def tag_highlight(self):
        """ Changes widget frame color, green highlight means mod has searched tag """
        for mod in self.chosen_game.mods:  # read all mods tags
            mod_tags, searched_tags = mod.tags.split(','), self.tagsEdit.text().split(',')
            flag = True
            for j in searched_tags:
                if j.strip() in mod_tags:
                    mod.frame.setStyleSheet("background-color: rgb(40, 175, 40)")  # change widget frame color to green
                    flag = False
                    break
            if flag:
                mod.frame.setStyleSheet("background-color: rgb(100, 150, 220)")

    def ver_highlight(self):
        """ Changes widget frame color, green highlight means mod supports searched game version """
        for mod in self.chosen_game.mods:
            mod_version, game_version = mod.supported_game_version, self.gameVersionEdit.text()
            if mod_version == game_version:
                mod.frame.setStyleSheet("background-color: rgb(40, 175, 40)")  # change widget frame color to green
            else:
                mod.frame.setStyleSheet("background-color: rgb(100, 150, 220)")

    def relation_highlight(self):
        """ Changes widget frame color,
         green highlight means that searched mod depends on another one or needed for another one (mutual highlight),
         red highlight means that this mod is incompatible for another one or incompatible for searched one (mutual highlight) """
        mod_title = self.gameNameEdit.text().strip()
        searched_mod = None

        for mod in self.chosen_game.mods:  # find this title in our mods
            if mod.title == mod_title:
                searched_mod = mod
                break

        if searched_mod:  # get info about required_mods and forbidden_mods
            required_mods = [i.strip() for i in searched_mod.required_mods.split(",")]
            forbidden_mods = [i.strip() for i in searched_mod.incompatible_mods.split(",")]
            for mod in self.chosen_game.mods:
                if mod_title in mod.incompatible_mods or mod.title in forbidden_mods:
                    mod.frame.setStyleSheet("background-color: rgb(175, 40, 40)")  # change widget frame color to red
                elif mod_title in mod.required_mods or mod.title in required_mods:
                    mod.frame.setStyleSheet("background-color: rgb(40, 175, 40)")  # change widget frame color to green
                else:
                    mod.frame.setStyleSheet("background-color: rgb(100, 150, 220)")
        else:
            self.informationText.setText(self.errors_notes["choose_game_to_add_mod"])

    def save_all(self):
        """ Saves all mods of the chosen game """
        if self.chosen_game:
            not_saved_mods = []  # stores titles of all unsaved mods
            for mod in self.chosen_game.mods:
                if mod.game_id != -1:  # check if mod deleted (legacy, 'cause program pop all deleted games from the list)
                    not_saved_mod = mod.save_into_base()
                    if not_saved_mod:
                        not_saved_mods.append(not_saved_mod)
            if len(not_saved_mods) > 0:
                self.informationText.setText(self.errors_notes["not_saved_mods"] + ";\n".join(not_saved_mods))
            else:
                self.informationText.setText(self.errors_notes["all_saved_mods"])

    def update_all(self):
        """ Updates all mods of the chosen game """
        if self.chosen_game:  # stores titles of all unsaved mods
            not_updated_mods = []
            for mod in self.chosen_game.mods:
                if mod.game_id != -1:  # check if mod deleted (legacy, 'cause program pop all deleted games from the list)
                    not_updated_mod = mod.update_mod_data(True)  # True means we're updating all mods, not some specific one
                    if not_updated_mod:
                        not_updated_mods.append(not_updated_mod)
            if len(not_updated_mods) > 0:
                self.informationText.setText(self.errors_notes["not_updated_mods"] + ";\n".join(not_updated_mods))
            else:
                self.informationText.setText(self.errors_notes["all_updated_mods"])
            self.open_mods(self.chosen_game)  # refresh widgets


if __name__ == "__main__":
    app = QApplication(sys.argv)
    k = MainWindow()
    k.show()
    sys.exit(app.exec())
