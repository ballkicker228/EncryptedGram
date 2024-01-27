from telegram_encryption.lib import Telegram, Crypt, MasterDatabase, Account, select_account, select_friend, start_main

def main():
    masterdb = MasterDatabase()
    database = select_account(masterdb)
    crypt = Crypt(database)
    api_id, api_hash, name = database.get_api_data()
    telegram = Telegram(api_id, api_hash, name, crypt)
    friend = select_friend(database, telegram)
    chat = start_main(database, friend, crypt, telegram)
    

    
    # friend_user_id, friend_name = select_friend(fzf, database, telegram)
    
             

if __name__=='__main__':
    main()