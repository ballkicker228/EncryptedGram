import os
import sqlite3
from sqlite3 import Error
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP           
from telethon.sync import TelegramClient, events
import tkinter as tk
from tkinter import ttk, scrolledtext

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
        self.cur.execute(f"SELECT API_ID,API_HASH,NAME,MY_ID FROM Account WHERE ID=1;")
        api = self.cur.fetchone()
        api_id = api[0]
        api_hash = api[1]
        name = api[2]
        my_id = api[3]
        return api_id, api_hash, name, my_id

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
    
    def get_all_messages(self, friend_id):
        self.cur.execute(f"SELECT MESSAGE FROM Messages WHERE FRIEND_ID={friend_id}")
        messages = self.cur.fetchall()
        normanlized_messages = []
        for message in messages:
            normanlized_messages.append(message[0])
        return normanlized_messages

class Crypt:
    def __init__(self, db: Account):
        self.prkey = RSA.import_key(db.get_private_key())
        self.cipher = None
        self.db = db
        #self.pubkey = RSA.import_key(db.get_public_key(account_id))
        self.private_cipher = PKCS1_OAEP.new(self.prkey)
        self.friend_pubkey = None
    
    #def add_friend_pubkey(self, friend_user_id, pubkey):
    #self.db.add_pubkey_to_friend
    
    def encrypt_message(self, message):
        #if self.friend_pubkey == None:
        #    print("Sorry, but you can't encrypt message without your friend's publickey!")
        #    quit()
        #else:
        self.cipher = PKCS1_OAEP.new(self.friend_pubkey)
        byte_message = message.encode('utf-8')
        return self.cipher.encrypt(byte_message).hex()

    def decrypt_message(self, message):
        return self.private_cipher.decrypt(bytes.fromhex(message)).decode()
    
    def generate_keys():
        key = RSA.generate(4096)
        privatekey = key.export_key()
        publickey = key.publickey().export_key()
        return privatekey, publickey
    
    def messages_check_and_write(self, messages, friend_user_id):
        isnewmessage = False
        for key, value in messages.items():
            if value[0:14] == "Start of msg: ":
                if self.db.check_existing_message(key, friend_user_id) == False:
                    message = self.decrypt_message(value[14:])
                    self.db.add_message(message, key, friend_user_id)
                    isnewmessage = True
            elif value[0:21] == "Start of public key: ":
                self.db.add_pubkey_to_friend(value[21:], user_id=friend_user_id)
        return isnewmessage

class Telegram:
    def __init__(self, api_id, api_hash, name, crypt):
        self.crypt = crypt
        self.client = TelegramClient(name, api_id, api_hash)
        self.client.start() 

    def get_entity(self, friend_user_id):
        user_obj = self.client.get_entity(int(friend_user_id))
        return user_obj

    def get_dialogs(self):
        dialogs = self.client.get_dialogs()
        userdialogs = []
        for dialog in dialogs:
            if str(dialog.entity)[0:4] == 'User':
                userdialogs.append([dialog.name, dialog.entity.id])
        return userdialogs

    def send_message(self, user_id, message):
        key = self.crypt.db.get_friend_pubkey(user_id)
        self.crypt.friend_pubkey = RSA.import_key(key)
        encrypted_message = self.crypt.encrypt_message(message) 
        #dialog = self.client.start_chat(self.get_entity(user_id))
        self.client.send_message(int(user_id), f"Start of msg: {encrypted_message}")
    
    def send_public_key(self, user_id):
        publickey = self.crypt.db.get_public_key()
        self.client.send_message(int(user_id), f"Start of public key: {publickey.decode()}")
    
    def public_key_request(self, user_id):
        self.client.send_message(int(user_id), 'Give me your public key please')

    def get_me(self):
        return self.client.get_me() 

    def get_all_dialog_messages(self, id, limit=30):
        messages = {}
        for message in self.client.iter_messages(int(id)):
            if limit<=0:
                break
            messages[message.id] = message.text
            limit -= 1
        return messages

class FriendSelectionWindow:
    def __init__(self, root, accountdb):
        self.root = root
        self.accountdb = accountdb
        self.selected_friend = None
        self.friends = self.accountdb.get_all_friends_names()
        for friend in self.friends:
            print(friend)

        def create_widgets(self):
            pass

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
                #messagebox.showinfo("Успех", "Код аутентификации отправлен. Пожалуйста, введите код.")
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
                #messagebox.showerror("Ошибка", f"Не удалось отправить код аутентификации: {e}")
        def enter_code(self):
            self.client.sign_in(self.phone_number, code=self.code_entry.get(), phone_code_hash=self.phone_code_hash)
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
    def __init__(self, root, telegram, accountdb):
        self.root = root
        self.root.title("EncryptedGram")
        self.root.configure(bg='#333')  # Установка темного цвета фона
        self.telegram = telegram
        self.masterdb = masterdb

        self.messages = []

        self.create_widgets()

    def account_select(self):
        pass

    def create_widgets(self):
        # Создание поля для отображения сообщений
        self.message_display = scrolledtext.ScrolledText(self.root, state='disabled', wrap='word', height=15, width=40, bg='#333', fg='white', highlightthickness=0)
        self.message_display.grid(row=0, column=0, padx=10, pady=10, columnspan=2, sticky="nsew")

        # Создание поля ввода для сообщения
        self.message_entry = tk.Entry(self.root, width=30, bg='#444', fg='white', highlightthickness=0)
        self.message_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Кнопка для отправки сообщения
        send_button = tk.Button(self.root, text="Send", command=self.send_message, bg='blue', fg='white', highlightthickness=0)
        send_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

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

    def send_message(self):
        # Получение текста из поля ввода
        message_text = self.message_entry.get()

        if message_text:
            # Добавление нового сообщения в массив
            self.messages.append(message_text)

            # Обновление отображения сообщений
            self.display_messages()

            # Очистка поля ввода
            self.message_entry.delete(0, 'end')

    def display_messages(self):
        # Очистка поля для отображения сообщений
        self.message_display.config(state='normal')
        self.message_display.delete(1.0, 'end')

        # Отображение сообщений из массива messages
        for message in self.messages:
            self.message_display.insert('end', f"{message}\n")

        # Прокрутка текста вниз
        self.message_display.yview_moveto(1.0)

        # Блокировка поля для отображения, чтобы пользователь не мог редактировать текст
        self.message_display.config(state='disabled')
