from telegram_encryption.lib import Telegram, Crypt, MasterDatabase, Account, ChatApp, AccountSelectionWindow, FriendSelectionWindow
from timeit import default_timer
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext

def select_account(masterdb):
    selection_window = tk.Tk()
    window = AccountSelectionWindow(selection_window, masterdb)
    selection_window.mainloop()
    account = window.accountdb
    return account

def start_gui():
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()

def select_friend(database):#, telegram):
    selection_window = tk.Tk()
    friend_window = FriendSelectionWindow(selection_window, database)
    selection_window.mainloop()
    
    # friends = database.get_all_friends_names()
    # friends.append("Добавить друга")
    # friends.append("Удалить друга")
    # friend_name = fzf.prompt(friends)[0]
    # friend_user_id = None
    # if friend_name == "Добавить друга":
    #     dialogs = telegram.get_dialogs()
    #     usernames = []
    #     for dialog in dialogs:
    #         usernames.append(dialog[0])
    #     usernames.append("Добавить другим способом")
    #     selectedfriend = fzf.prompt(usernames)[0]
    #     if selectedfriend == "Добавить другим способом":
    #         print('Для добавления друга нужен его User id либо номер телефона либо его ник в формате @my_dear_friend')
    #         friend_user_id = input("Введите эти данные: ")
    #         telegram_user_obj = telegram.get_entity(friend_user_id)
    #         friendnamelocal = input("Как вы назовете своего друга? ")
    #         friend_user_id = telegram_user_obj.id
    #         database.add_friend(telegram_user_obj.id, friendnamelocal)
    #         return friend_user_id, friendnamelocal
    #     else:
    #         telegram_user_obj = telegram.get_entity(dialogs[usernames.index(selectedfriend)][1])
    #         friendnamelocal = input("Как вы назовете своего друга? ")
    #         friend_user_id = telegram_user_obj.id
    #         database.add_friend(telegram_user_obj.id, friendnamelocal)
    #         return friend_user_id
    # elif friend_name == "Удалить друга":
    #     friends = database.get_all_friends_names(account_id)
    #     friend_to_delete = fzf.prompt(friends)[0]
    #     database.del_friend_by_name(friend_to_delete)
    #     select_friend(fzf, database, telegram)
    # else:
    #     friend_user_id = database.get_friend_user_id_by_name(friend_name)
    #     return friend_user_id, friend_name

def start_interface(stdscr, database, telegram, friend_user_id, friend_name):
    messages = telegram.get_all_dialog_messages(friend_user_id)
   
    start = default_timer()
    timer = 5
    os.system("clear")
    try:
        allmsg = database.get_all_messages(friend_user_id)
        for message in allmsg:
            print(f"{friend_name}: {message}")
    finally:
        pass

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


def main():
    # fzf = FzfPrompt()
    masterdb = MasterDatabase()
    database = select_account(masterdb)
    select_friend(database)
    # crypt = Crypt(database)
    # api_id, api_hash, nameapi, my_id = database.get_api_data()

    # telegram = Telegram(api_id, api_hash, nameapi, crypt)
    # friend_user_id, friend_name = select_friend(fzf, database, telegram)
    # curses.wrapper(start_interface(database, telegram, friend_user_id, friend_name))
    
             

if __name__=='__main__':
    main()