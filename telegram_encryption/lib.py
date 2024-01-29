import os
import sqlite3         
from telethon.sync import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl import types
import tkinter as tk
from tkinter import ttk, scrolledtext
from ecies.utils import generate_eth_key, generate_key
from ecies import encrypt, decrypt

class MasterDatabase:
    def __init__(self): 
        self.con = sqlite3.connect("Accounts.db")
        self.cur = self.con.cursor()
        
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Accounts(
        ID INTEGER PRIMARY KEY,
        NAME TEXT
        )""")

    def check_name_exists(self, name):
        self.cur.execute(f"SELECT NAME FROM Accounts WHERE NAME='{name}'")
        check = self.cur.fetchone()[0]
        if check[0] == name:
            return True
        else:
            return False

    def fetch_all_accounts(self):
        self.cur.execute("""SELECT NAME FROM Accounts""")
        accounts = self.cur.fetchall()
        norm_accounts = []
        for account in accounts:
            norm_accounts.append(account[0])
        return norm_accounts
    def add_account(self, name):
        self.cur.execute(f"INSERT INTO Accounts(NAME) VALUES ('{name}');")
        self.con.commit()
    def del_account(self, name):
        self.cur.execute(f"DELETE FROM Accounts WHERE NAME='{name}'")
        self.con.commit()
        try:
            print(f"./telegram-{name}.db")
            os.remove(f"./telegram-{name}.db")
        except Exception as e:
            print(e)


class Account:
    def __init__(self, account_name):
        self.con = sqlite3.connect(f"telegram-{account_name}.db")
        self.cur = self.con.cursor() 
        
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Account(
            ID INTEGER PRIMARY KEY,
            API_ID TEXT,
            API_HASH TEXT,
            NAME TEXT,
            PUBLIC_KEY TEXT,
            PRIVATE_KEY TEXT
            )""")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Friends(
            ID INTEGER PRIMARY KEY,
            FRIEND_NAME TEXT,
            FRIEND_ID TEXT,
            FRIEND_PUBLIC_KEY TEXT
            )""")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Messages(
            ID INTEGER PRIMARY KEY,
            FRIEND_ID TEXT,
            MESSAGE_ID TEXT,
            MESSAGE TEXT
            )""")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Groups(
            ID INTEGER PRIMARY KEY,
            GROUP_NAME TEXT,
            GROUP_ID TEXT
            )""")
        self.con.commit()


    def write_account(self, api_id, api_hash, name, pubkey, prkey):
        self.cur.execute('SELECT MAX(id) FROM Account')
        last_id = self.cur.fetchone()[0]
        if last_id == 1:
            self.cur.execute(f"UPDATE Account SET API_ID='{api_id}', API_HASH='{api_hash}', NAME='{name}', PUBLIC_KEY='{pubkey}', PRIVATE_KEY='{prkey}' WHERE ID=1;")
        else:
            self.cur.execute("""INSERT INTO Account(API_ID, API_HASH, NAME, PUBLIC_KEY, PRIVATE_KEY) VALUES (?,?,?,?,?)""", (api_id, api_hash, name, pubkey, prkey))
        self.con.commit()
    
    def get_api_data(self):
        self.cur.execute(f"SELECT API_ID,API_HASH,NAME FROM Account WHERE ID=1;")
        api = self.cur.fetchone()
        api_id = api[0]
        api_hash = api[1]
        name = api[2]
        return api_id, api_hash, name

    def add_friend(self, friend_id, friend_name):
        self.cur.execute("""INSERT INTO Friends(FRIEND_ID, FRIEND_NAME, FRIEND_PUBLIC_KEY) VALUES (?,?,?);""", (friend_id, friend_name, "None"))
        self.con.commit()
    
    def add_pubkey_to_friend(self, public_key, user_id):
        self.cur.execute(f"UPDATE Friends SET FRIEND_PUBLIC_KEY='{public_key}' WHERE FRIEND_ID={user_id};")
        self.con.commit()
    
    def get_friend_pubkey(self, user_id):
        self.cur.execute(f"SELECT FRIEND_PUBLIC_KEY FROM Friends WHERE FRIEND_ID={user_id}")
        key = self.cur.fetchone()[0]
        return key

    def del_friend(self, user_id):
        self.cur.execute(f"DELETE FROM Friends WHERE USER_ID={user_id};")
        self.con.commit() 
    
    def del_friend_by_name(self, friend_name):
        self.cur.execute(f"DELETE FROM Friends WHERE FRIEND_NAME='{friend_name}'")
        self.con.commit()

    def get_public_key(self):
        self.cur.execute(f"SELECT PUBLIC_KEY FROM Account WHERE ID=1")
        return self.cur.fetchone()[0]

    def get_private_key(self):
        self.cur.execute(f"SELECT PRIVATE_KEY FROM Account WHERE ID=1")
        return self.cur.fetchone()[0]

    def get_all_friends_names(self):
        self.cur.execute(f"SELECT FRIEND_NAME FROM Friends")
        names_wrong = self.cur.fetchall()
        names = []
        for name in names_wrong:
            names.append(name[0])
        return names

    def add_message(self, message, messageid, friendid):
        self.cur.execute("""INSERT INTO Messages(FRIEND_ID, MESSAGE_ID, MESSAGE) VALUES (?,?,?)""", (friendid, messageid, message))
        self.con.commit()

    def check_existing_message(self, messageid, friendid):
        self.cur.execute(f"SELECT MESSAGE FROM Messages WHERE MESSAGE_ID={messageid} AND FRIEND_ID={friendid}")
        message = self.cur.fetchone()
        if message == None:
            return False
        else:
            return True

    def get_friend_user_id_by_name(self, friend_name):
        self.cur.execute(f"SELECT FRIEND_ID FROM Friends WHERE FRIEND_NAME = '{friend_name}'")
        return self.cur.fetchone()[0]
    
    def get_friend_name_by_id(self, friend_user_id):
        self.cur.execute(f"SELECT FRIEND_NAME FROM Friends WHERE FRIEND_ID = {friend_user_id}")
        return self.cur.fetchone()[0]
    
    def get_all_messages(self, friend_id):
        self.cur.execute(f"SELECT MESSAGE FROM Messages WHERE FRIEND_ID={friend_id}")
        messages = self.cur.fetchall()
        normanlized_messages = []
        for message in messages:
            normanlized_messages.append(message[0])
        return normanlized_messages

class Crypt:
    def __init__(self, db: Account):
        self.prkey = db.get_private_key()
        self.db = db
        self.friend_pubkey = None
    
    def encrypt_message(self, message):
        byte_message = message.encode('utf-8')
        return encrypt(self.friend_pubkey, byte_message).hex()

    def decrypt_message(self, message):
        return decrypt(self.prkey, bytes.fromhex(message)).decode()
    
    def generate_keys():
        eth_k = generate_eth_key()
        sk_hex = eth_k.to_hex()
        pk_hex = eth_k.public_key.to_hex()
        return sk_hex, pk_hex
    

class Telegram:
    def __init__(self, api_id, api_hash, name, crypt):
        self.crypt = crypt
        self.client = TelegramClient(name, api_id, api_hash)
        self.client.start() 

    def get_entity(self, friend_data):
        user_obj = self.client.get_entity(friend_data)
        return user_obj

    def get_dialogs(self):
        dialogs = self.client.get_dialogs()
        userdialogs = []
        for dialog in dialogs:
            if str(dialog.entity)[0:4] == 'User':
                userdialogs.append([dialog.name, dialog.entity.id])
        return userdialogs

    def send_message(self, entity, message):
        key = self.crypt.db.get_friend_pubkey(entity.id)
        if key != "None":
            self.crypt.friend_pubkey = key
            encrypted_message = self.crypt.encrypt_message(message) 
            #dialog = self.client.start_chat(self.get_entity(user_id))
            sentmessage = self.client.send_message(entity, f"Start of msg: {encrypted_message}")
            self.crypt.db.add_message(f"Me: {message}", sentmessage.id, entity.id)
            return message
        else:
            return "У вас нет публичного ключа вашего друга!"
    
    def send_public_key(self, entity):
        publickey = self.crypt.db.get_public_key()
        self.client.send_message(entity, f"Start of public key: {publickey}")
    
    def public_key_request(self, entity):
        self.client.send_message(entity, 'Give me your public key please')

    def get_me(self):
        return self.client.get_me() 

    def get_all_dialog_messages(self, entity, limit=30):
        messages = {}
        for message in self.client.iter_messages(entity):
            if limit<=0:
                break
            messages[message.id] = message.text
            limit -= 1
        return messages
    
    def messages_check_and_write(self, messages, friend_user_id):
        for key, value in messages.items():
            try:
                if value[0:14] == "Start of msg: ":
                    if self.crypt.db.check_existing_message(key, friend_user_id) == False:
                        try:
                            message = self.crypt.db.get_friend_name_by_id(friend_user_id) + ": " + self.crypt.decrypt_message(value[14:])
                            self.crypt.db.add_message(message, key, friend_user_id)
                            isnewmessage = True
                        except:
                            pass
                elif value[0:21] == "Start of public key: ":
                    if self.crypt.db.get_public_key() != value[21:]:
                        self.crypt.db.add_pubkey_to_friend(value[21:], user_id=friend_user_id)
                elif "Give me your public key please" in value:
                    key = self.crypt.db.get_public_key()
                    entity = self.get_entity(int(friend_user_id))
                    self.client.send_message(entity, key)
            except:
                pass

class FriendSelectionWindow:
    class CreateFriendWindow:
        def __init__(self, master, telegram):
            self.telegram = telegram
            self.master = master
            self.window = tk.Toplevel(self.master)
            self.window.title("Добавить друга")
            self.window.configure(bg="#333")
            self.create_widgets()
            self.friend_id = None
            self.friend_name = None
        
        def create_widgets(self):
            self.info_label = tk.Label(self.window, text="Для добавления друга он должен быть в списке ваших чатов")
            self.data_label = tk.Label(self.window, text="Выберите чат из списка:")
            self.info_label.pack(pady=10)
            self.data_label.pack(pady=10)
            self.data_listbox = tk.Listbox(self.window, selectmode=tk.SINGLE, bg="#444", fg="white")
            self.data_listbox.pack(pady=10)
            self.submit_button = tk.Button(self.window, text="Enter", command=self.submit_friend)
            self.submit_button.pack(pady=10)
            self.dialogs = self.telegram.get_dialogs()
            for dialog in self.dialogs:
                self.data_listbox.insert(tk.END, dialog[0])
                telegram_user_obj = self.telegram.get_entity(int(dialog[1]))
        
        def submit_friend(self):
            selected_index = self.data_listbox.curselection()
            if selected_index:
                self.selected_friend = self.data_listbox.get(selected_index)
                for dialog in self.dialogs:
                    if dialog[0] == self.selected_friend:
                        self.friend_name = dialog[0]
                        self.friend_id = dialog[1]
                        self.window.destroy()
        
        def get_friend(self):
            return self.friend_name, self.friend_id

    def __init__(self, root, accountdb, telegram):
        self.root = root
        self.root.title("Выберите друга")
        self.root.configure(bg="#333")
        self.accountdb = accountdb
        self.selected_friend = None
        self.telegram = telegram
        self.friends = self.accountdb.get_all_friends_names()
        self.create_widgets()

    def create_widgets(self):
        # Создание списка аккаунтов
        self.enter_friend_label = tk.Label(self.root, text="Выберите друга")
        self.enter_friend_label.pack(pady=10)
        self.friends_listbox = tk.Listbox(self.root, selectmode=tk.SINGLE, bg="#444", fg="white")
        for friend in self.friends:
            self.friends_listbox.insert(tk.END, friend)

        self.friends_listbox.pack(padx=10, pady=10)

        # Кнопка выбора аккаунта
        select_button = tk.Button(self.root, text="Выбрать", command=self.select_friend, bg="#666", fg="white")
        add_button = tk.Button(self.root, text="Добавить", command=self.add_friend, bg="#666", fg="white")
        del_button = tk.Button(self.root, text="Удалить", command=self.del_friend, bg="#666", fg="white")
        quit_button = tk.Button(self.root, text="Выйти", command=self.close, bg="#666", fg="white")
    
        select_button.pack(pady=10)
        add_button.pack(pady=10)
        del_button.pack(pady=10)
        quit_button.pack(pady=10)

    def del_friend(self):
        selected_index = self.friends_listbox.curselection()
        if selected_index:
            self.selected_friend = self.friends_listbox.get(selected_index)
            self.accountdb.del_friend_by_name(self.selected_friend)
            self.friends_listbox.delete(selected_index)

    def close(self):
        self.root.destroy()

    def add_friend(self):
        self.create_window = self.CreateFriendWindow(self.root, self.telegram)
        
        self.root.wait_window(self.create_window.window)
        friend_name, friend_id = self.create_window.get_friend()
        self.friends_listbox.insert(tk.END, friend_name)
        self.accountdb.add_friend(friend_id, friend_name)

    def select_friend(self):
        selected_index = self.friends_listbox.curselection()
        if selected_index:
            self.selected_friend = self.friends_listbox.get(selected_index)
            self.root.destroy()

class AccountSelectionWindow:
    def __init__(self, root, masterdb):
        self.masterdb = masterdb
        self.accounts = self.masterdb.fetch_all_accounts()
        self.root = root
        self.selected_account = None
        self.accountdb = None

        self.root.title("Выберите аккаунт")

        # Установка цветов фона
        self.root.configure(bg="#333")

        self.create_widgets()

    class CreateAccountWindow():
        def __init__(self, master):
            self.master = master
            self.window = tk.Toplevel(master)
            self.window.title("Создание аккаунта")
            self.accountdb = None
            self.account_name = None
            self.window.configure(bg="#333")

            self.create_widgets()

        def create_widgets(self):
            self.phone_label = tk.Label(self.window, text="Введите номер телефона:")
            self.phone_label.pack(pady=10)
            self.phone_entry = tk.Entry(self.window)
            self.phone_entry.pack(pady=10)

            self.api_id_label = tk.Label(self.window, text="Введите API ID:")
            self.api_id_label.pack(pady=10)
            self.api_id_entry = tk.Entry(self.window)
            self.api_id_entry.pack(pady=10)

            self.api_hash_label = tk.Label(self.window, text="Введите API HASH:")
            self.api_hash_label.pack(pady=10)
            self.api_hash_entry = tk.Entry(self.window)
            self.api_hash_entry.pack(pady=10)

            self.api_name_label = tk.Label(self.window, text="Введите название API:")
            self.api_name_label.pack(pady=10)
            self.api_name_entry = tk.Entry(self.window)
            self.api_name_entry.pack(pady=10)

            self.submit_button = tk.Button(self.window, text="Отправить код", command=self.send_code)
            self.submit_button.pack(pady=10)

            self.close_button = tk.Button(self.window, text="Выйти", command=self.close)
            self.close_button.pack(pady=10)
        def send_code(self):
            self.phone_number = self.phone_entry.get()
            self.api_id = self.api_id_entry.get()
            self.api_hash = self.api_hash_entry.get()
            self.api_name = self.api_name_entry.get()
            self.account_name = self.api_name
            self.client = TelegramClient(self.api_name, self.api_id, self.api_hash)
            self.client.connect()
            try:
                phone_code = self.client.send_code_request(self.phone_number)
                self.phone_code_hash = phone_code.phone_code_hash
                self.phone_label.destroy()
                self.phone_entry.destroy()
                self.api_id_label.destroy()
                self.api_id_entry.destroy()
                self.api_hash_label.destroy()
                self.api_hash_entry.destroy()
                self.api_name_label.destroy()
                self.api_name_entry.destroy()
                self.submit_button.destroy()
                self.code_label = tk.Label(self.window, text="Введите код подтверждения:")
                self.code_label.pack(pady=10)
                self.code_entry = tk.Entry(self.window)
                self.code_entry.pack(pady=10)
                self.submit_button = tk.Button(self.window, text="Enter", command=self.enter_code)
                self.submit_button.pack(pady=10)
                self.close_button = tk.Button(self.window, text="Выйти", command=self.close)
                self.close_button.pack(pady=10)
            except Exception as e:
                pass
            
        def enter_code(self):
            try:
                self.client.sign_in(self.phone_number, code=self.code_entry.get(), phone_code_hash=self.phone_code_hash)
                self.accountdb = Account(self.api_name)
                private_key, public_key = Crypt.generate_keys()
                self.accountdb.write_account(self.api_id, self.api_hash, self.api_name, public_key, private_key)
                masterdb = MasterDatabase()
                masterdb.add_account(self.api_name)
                self.window.destroy()
            except SessionPasswordNeededError:
                self.code = self.code_entry.get()
                self.code_label.destroy()
                self.code_entry.destroy()
                self.submit_button.destroy()
                self.close_button.destroy()
                self.password_entry_label = tk.Label(self.window, text="Введите облачный пароль:")
                self.password_entry = tk.Entry(self.window)
                self.submit_button = tk.Button(self.window, text="Enter", command=self.enter_password)
                self.close_button = tk.Button(self.window, text="Выйти", command=self.close)
                self.password_entry_label.pack(pady=10)
                self.password_entry.pack(pady=10)
                self.submit_button.pack(pady=10)
                self.close_button.pack(pady=10)
                
        
        def enter_password(self):
            self.password=self.password_entry.get()
            self.client.sign_in(password=self.password)
            self.accountdb = Account(self.api_name)
            private_key, public_key = Crypt.generate_keys()
            self.accountdb.write_account(self.api_id, self.api_hash, self.api_name, public_key, private_key)
            masterdb = MasterDatabase()
            masterdb.add_account(self.api_name)
            self.window.destroy()

        def close(self):
            self.window.destroy()

    def create_widgets(self):
        # Создание списка аккаунтов
        self.account_listbox = tk.Listbox(self.root, selectmode=tk.SINGLE, bg="#444", fg="white")
        for account in self.accounts:
            self.account_listbox.insert(tk.END, account)

        self.account_listbox.pack(padx=10, pady=10)

        # Кнопка выбора аккаунта
        select_button = tk.Button(self.root, text="Выбрать", command=self.select_account, bg="#666", fg="white")
        add_button = tk.Button(self.root, text="Добавить", command=self.add_account, bg="#666", fg="white")
        del_button = tk.Button(self.root, text="Удалить", command=self.del_account, bg="#666", fg="white")
        quit_button = tk.Button(self.root, text="Выйти", command=self.close, bg="#666", fg="white")
    
        select_button.pack(pady=10)
        add_button.pack(pady=10)
        del_button.pack(pady=10)
        quit_button.pack(pady=10)

    def del_account(self):
        selected_index = self.account_listbox.curselection()
        if selected_index:
            self.selected_account = self.account_listbox.get(selected_index)
            self.masterdb.del_account(self.selected_account)
            self.account_listbox.delete(selected_index)

    def close(self):
        self.root.destroy()

    def add_account(self):
        self.create_window = self.CreateAccountWindow(self.root)
        
        self.root.wait_window(self.create_window.window)
        self.account_listbox.insert(tk.END, self.create_window.account_name)



    def select_account(self):
        # Получение выбранного аккаунта
        selected_index = self.account_listbox.curselection()
        if selected_index:
            self.selected_account = self.account_listbox.get(selected_index)
            self.accountdb = Account(self.selected_account)
            self.root.destroy()

class ChatApp:
    def __init__(self, root, crypt, telegram, accountdb, friend_name, friend_user_id):
        self.root = root
        self.root.title("EncryptedGram")
        self.root.configure(bg='#333')  # Установка темного цвета фона
        self.telegram = telegram
        self.database = accountdb
        self.friend_name = friend_name
        self.friend_user_id = friend_user_id
        self.friend_entity = self.telegram.get_entity(int(self.friend_user_id))
        self.crypt = crypt
        self.timer = 0
        self.messages = []
        self.create_widgets()

    def create_widgets(self):
        # Создание поля для отображения сообщений
        self.message_display = scrolledtext.ScrolledText(self.root, state='disabled', wrap='word', height=15, width=40, bg='#333', fg='white', highlightthickness=0)
        self.message_display.grid(row=0, column=0, padx=10, pady=10, columnspan=2, sticky="nsew")

        # Создание поля ввода для сообщения
        self.message_entry = tk.Entry(self.root, width=30, bg='#444', fg='white', highlightthickness=0)
        self.message_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Кнопка для отправки сообщения
        send_button = tk.Button(self.root, text="Send", command=self.send_message, bg='blue', fg='white', highlightthickness=0)
        request_button = tk.Button(self.root, text="Key Request", command=self.request_key, bg='blue', fg='white', highlightthickness=0)
        send_key_button = tk.Button(self.root, text="Send Key", command=self.send_key, bg='blue', fg='white', highlightthickness=0)
        send_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        request_button.grid(row=1, column=2, padx=10, pady=10, sticky="ew")
        send_key_button.grid(row=1, column=3, padx=10, pady=10, sticky="ew")

        # Настройка параметров размещения
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Назначение события нажатия Enter для отправки сообщения
        self.message_entry.bind("<Return>", lambda event: self.send_message())

        # Установка цвета полосы прокрутки
        style = ttk.Style()
        style.theme_use('default')  # Используйте тему по умолчанию
        style.configure("Vertical.TScrollbar", troughcolor='#333', slidercolor='#666')
        
        self.root.after(5000, self.display_messages)

    def request_key(self):
        self.telegram.public_key_request(self.friend_entity)

    def send_key(self):
        self.telegram.send_public_key(self.friend_entity)

    def send_message(self):
        # Получение текста из поля ввода
        message_text = self.message_entry.get()

        if message_text:
            self.telegram.send_message(self.friend_entity, message_text)
            # Добавление нового сообщения в массив
            self.messages.append(f"Me: {message_text}")

            # Обновление отображения сообщений
            self.display_messages(issent=True)

            # Очистка поля ввода
            self.message_entry.delete(0, 'end')
   

    def display_messages(self, issent=False):
        # Очистка поля для отображения сообщений
        self.message_display.config(state='normal')
        self.message_display.delete(1.0, 'end')

        if issent == False:
            telegram_messages = self.telegram.get_all_dialog_messages(self.friend_entity, limit=10)
            self.telegram.messages_check_and_write(telegram_messages, self.friend_user_id)
            self.root.after(5000, self.display_messages)

        self.messages = self.database.get_all_messages(self.friend_user_id)

        # Отображение сообщений из массива messages
        for message in self.messages:
            self.message_display.insert('end', f"{message}\n")
        
        # Прокрутка текста вниз
        self.message_display.yview_moveto(1.0)

        # Блокировка поля для отображения, чтобы пользователь не мог редактировать текст
        self.message_display.config(state='disabled')
        
    
def select_account(masterdb):
    selection_window = tk.Tk()
    window = AccountSelectionWindow(selection_window, masterdb)
    selection_window.mainloop()
    account = window.accountdb
    return account

def select_friend(database, telegram):
    selection_window = tk.Tk()
    friend_window = FriendSelectionWindow(selection_window, database, telegram)
    selection_window.mainloop()
    return friend_window.selected_friend

def start_main(database, friend_name, crypt, telegram):
    root = tk.Tk()
    friend_user_id = database.get_friend_user_id_by_name(friend_name)
    app = ChatApp(root, crypt, telegram, database, friend_name, friend_user_id)
    root.mainloop()
