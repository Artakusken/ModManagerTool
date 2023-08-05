import sqlite3
from ModWidget import *
from typing import Union


def connect_base(lang) -> Union[str, sqlite3.Connection]:
    con = sqlite3.connect("MMT_workbase.sqlite")
    try:
        con.cursor()
        return con
    except Exception as error:
        if lang == "RU":
            return f"Ошибка при подключении к базе данных: {error}"
        else:
            return f"Database connection error: {error}"


class Game:
    def __init__(self, button):
        self.id = None
        self.title = None
        self.mods = []
        self.button = button

    def import_mods(self, app):
        """ Gets all mods from a base by game_id (if id of a game == game_ifd of a mod) """
        con = connect_base("No_lang")
        if type(con) == sqlite3.Connection:
            cur = con.cursor()
            all_mod_args = cur.execute("""SELECT * FROM Mods WHERE Game_ID = ?""", (self.id,)).fetchall()
            for mod_args in sorted(all_mod_args):
                new_mod = ModInfoWidget(self, app)
                new_mod.clear_args()
                new_mod.game_id = mod_args[1]
                new_mod.title = mod_args[2]
                new_mod.tags = mod_args[3]
                new_mod.mod_version = mod_args[4]
                new_mod.supported_game_version = mod_args[5]
                new_mod.required_mods = mod_args[6]
                new_mod.filepath = mod_args[7]
                new_mod.incompatible_mods = mod_args[8]
                new_mod.commentary = mod_args[9]
                new_mod.image_path = mod_args[10]
                new_mod.initUI()
                new_mod.saved = True
                new_mod.savedLabel.setText(new_mod.widget_localization["saved"])
                self.mods.append(new_mod)
        else:
            print(con)

    def update_title(self, new_title: str):
        """ Renames game in a database. Executes sql query """
        con = connect_base("No_lang")
        if type(con) == sqlite3.Connection:
            cur = con.cursor()
            cur.execute('''UPDATE Games
                           SET Game_title = ? 
                           WHERE Game_title = ?''', (new_title, self.title))
            con.commit()
            con.close()
            self.title = new_title
        else:
            print(con)
