from lib import Telegram, Crypt, MasterDatabase, Account #, generate_keys
from pyfzf.pyfzf import FzfPrompt
from timeit import default_timer
import os
from pynput import keyboard
import threading
import time

key_i_pressed = False
key_l_pressed = False
key_k_pressed = False

def on_press(key):
    global key_i_pressed
    global key_l_pressed
    global key_k_pressed

    try:
        if key.char == 'i':
            key_i_pressed = True
        elif key.char == 'l':
            key_l_pressed = True
        elif key.char == 'k':
            key_k_pressed = True
    except AttributeError:
        pass

def on_release(key):
    global key_i_pressed
    global key_l_pressed
    global key_k_pressed

    try:
        if key.char == 'i':
            key_i_pressed = False
        elif key.char == 'l':
            key_l_pressed = False
        elif key.char == 'k':
            key_k_pressed = False
    except AttributeError:
        pass

def select_account(fzf, masterdb):
    accounts = masterdb.fetch_all_accounts()
    accounts.append("Добавить аккаунт")
    accounts.append("Удалить аккаунт")
    account = fzf.prompt(accounts)[0]
    if account == "Добавить аккаунт":
        name = input("Введите имя аккаунта: ")
        masterdb.add_account(name)
        print('Первым делом вам нужно получить ключ и хеш API. Сделать это можно на сайте my.telegram.org')
        api_id = input("Введите API ID: ")
        api_hash = input("Введите API HASH: ")
        nameapi = input("Введите имя API: ")
        my_id = input("Введите свой user id(Его можно получить у ботов): ")
        prkey, pubkey = Crypt.generate_keys()
        database = Account(name)
        database.write_account(api_id, api_hash, nameapi, my_id, pubkey, prkey)
        return database
    elif account == "Удалить аккаунт":
        confirm = input("Вы уверены что хотите удалить аккаунт(yes/no)? ")
        if confirm in ["yes", "Yes", "YES", "Да", "ДА", "y", "Y", "Д", "д"]:
            name = input("Введите имя аккаунта: ")
            masterdb.del_account(name)
        
        select_account(fzf, masterdb)
    else:
        return Account(account)

def select_friend(fzf, database, telegram):
    friends = database.get_all_friends_names()
    friends.append("Добавить друга")
    friends.append("Удалить друга")
    friend_name = fzf.prompt(friends)[0]
    friend_user_id = None
    if friend_name == "Добавить друга":
        dialogs = telegram.get_dialogs()
        usernames = []
        for dialog in dialogs:
            usernames.append(dialog[0])
        usernames.append("Добавить другим способом")
        selectedfriend = fzf.prompt(usernames)[0]
        if selectedfriend == "Добавить другим способом":
            print('Для добавления друга нужен его User id либо номер телефона либо его ник в формате @my_dear_friend')
            friend_user_id = input("Введите эти данные: ")
            telegram_user_obj = telegram.get_entity(friend_user_id)
            friendnamelocal = input("Как вы назовете своего друга? ")
            friend_user_id = telegram_user_obj.id
            database.add_friend(telegram_user_obj.id, friendnamelocal)
            return friend_user_id, friendnamelocal
        else:
            telegram_user_obj = telegram.get_entity(dialogs[usernames.index(selectedfriend)][1])
            friendnamelocal = input("Как вы назовете своего друга? ")
            friend_user_id = telegram_user_obj.id
            database.add_friend(telegram_user_obj.id, friendnamelocal)
            return friend_user_id
    elif friend_name == "Удалить друга":
        friends = database.get_all_friends_names(account_id)
        friend_to_delete = fzf.prompt(friends)[0]
        database.del_friend_by_name(friend_to_delete)
        select_friend(fzf, database, telegram)
    else:
        friend_user_id = database.get_friend_user_id_by_name(friend_name)
        return friend_user_id, friend_name

def start_interface(database, telegram, friend_user_id, friend_name):
    messages = telegram.get_all_dialog_messages(friend_user_id)
   
    start = default_timer()
    timer = 5
    os.system("clear")
    try:
        allmsg = database.get_all_messages(friend_user_id)
        for message in allmsg:
            print(f"{friend_name}: {message}")
    finally:
        print("\tНажмите I для написания сообщения; L для отправки публичного ключа; K для запроса ключа;")

    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    keyboard_listener_thread = threading.Thread(target=keyboard_listener.run)
    keyboard_listener_thread.start()

    while True:
        thistime = default_timer()
        duration = thistime-start
        start = thistime
        timer += duration
        isnewmessage = False
        if timer >= 5:
            messages = telegram.get_all_dialog_messages(friend_user_id, limit=10)
            isnewmessage = crypt.messages_check_and_write(messages, friend_user_id)

            timer = 0

        if isnewmessage:
            os.system("clear")
            allmessages = database.get_all_messages(friend_user_id)
            for message in allmessages:
                print(f"{friend_name}: {message}")
            print("\tНажмите I для написания сообщения; L для отправки публичного ключа; K для запроса ключа;")

        if key_i_pressed:
            key = database.get_friend_pubkey(friend_user_id)
            if key != "None":
                usermessage = input(":")
                telegram.send_message(friend_user_id, usermessage)
            else:
                print("У вас нет публичного ключа друга!")
            time.sleep(2)
        elif key_l_pressed:
            telegram.send_public_key(friend_user_id)
            time.sleep(2)
        elif key_k_pressed:
            telegram.public_key_request(friend_user_id)
            time.sleep(2)

        threading.Event().wait(0.04)

def main():
    fzf = FzfPrompt()
    masterdb = MasterDatabase()
    database = select_account(fzf, masterdb)
    crypt = Crypt(database)
    api_id, api_hash, nameapi, my_id = database.get_api_data()

    telegram = Telegram(api_id, api_hash, nameapi, crypt)
    friend_user_id, friend_name = select_friend(fzf, database, telegram)
    start_interface(database, telegram, friend_user_id, friend_name)
    
             

if __name__=='__main__':
    main()