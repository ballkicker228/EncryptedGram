import os
import sqlite3
from sqlite3 import Error
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP           
from telethon.sync import TelegramClient, events

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
        os.remove(f"telegram-{name}.db") 


class Account:
    def __init__(self, account_name):
        self.con = sqlite3.connect(f"telegram-{account_name}.db")
        self.cur = self.con.cursor() 
        
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Account(
            ID INTEGER PRIMARY KEY,
            API_ID TEXT,
            API_HASH TEXT,
            NAME TEXT,
            MY_ID TEXT,
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


    def write_account(self, api_id, api_hash, name, my_id, pubkey, prkey):
        self.cur.execute('SELECT MAX(id) FROM Account')
        last_id = self.cur.fetchone()[0]
        if last_id == 1:
            self.cur.execute(f"UPDATE Account SET API_ID='{api_id}', API_HASH='{api_hash}', NAME='{name}', MY_ID='{my_id}', PUBLIC_KEY='{pubkey}', PRIVATE_KEY='{prkey}' WHERE ID=1;")
        else:
            self.cur.execute("""INSERT INTO Account(API_ID, API_HASH, NAME, MY_ID, PUBLIC_KEY, PRIVATE_KEY) VALUES (?,?,?,?,?,?)""", (api_id, api_hash, name, my_id, pubkey, prkey))
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
