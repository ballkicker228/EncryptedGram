from telegram_encryption.lib import Telegram, Crypt, MasterDatabase, Account, ChatApp, AccountSelectionWindow, FriendSelectionWindow, select_account, start_gui, select_friend

# def start_interface(stdscr, database, telegram, friend_user_id, friend_name):
#     messages = telegram.get_all_dialog_messages(friend_user_id)
   
#     start = default_timer()
#     timer = 5
#     os.system("clear")
#     try:
#         allmsg = database.get_all_messages(friend_user_id)
#         for message in allmsg:
#             print(f"{friend_name}: {message}")
#     finally:
#         pass

#     while True:
#         thistime = default_timer()
#         duration = thistime-start
#         start = thistime
#         timer += duration
#         isnewmessage = False
#         if timer >= 5:
#             messages = telegram.get_all_dialog_messages(friend_user_id, limit=10)
#             isnewmessage = crypt.messages_check_and_write(messages, friend_user_id)

#             timer = 0

#         if isnewmessage:
#             os.system("clear")
#             allmessages = database.get_all_messages(friend_user_id)
#             for message in allmessages:
#                 print(f"{friend_name}: {message}")
            

#         if key_i_pressed:
#             key = database.get_friend_pubkey(friend_user_id)
#             if key != "None":
#                 usermessage = input(":")
#                 telegram.send_message(friend_user_id, usermessage)
#             else:
#                 print("У вас нет публичного ключа друга!")
#             time.sleep(2)
#         elif key_l_pressed:
#             telegram.send_public_key(friend_user_id)
#             time.sleep(2)
#         elif key_k_pressed:
#             telegram.public_key_request(friend_user_id)
#             time.sleep(2)


def main():
    masterdb = MasterDatabase()
    database = select_account(masterdb)
    friend = select_friend(database)
    crypt = Crypt(database)
    # api_id, api_hash, nameapi, my_id = database.get_api_data()

    # telegram = Telegram(api_id, api_hash, nameapi, crypt)
    # friend_user_id, friend_name = select_friend(fzf, database, telegram)
    
             

if __name__=='__main__':
    main()