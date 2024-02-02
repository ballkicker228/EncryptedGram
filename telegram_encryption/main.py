from telegram_encryption.lib import Telegram, Crypt, MasterDatabase, Account, select_account, select_friend, start_main

def main():
    masterdb = MasterDatabase()
    database = select_account(masterdb)
    if database != None:
        while True:
            crypt = Crypt(database)
            api_id, api_hash, name = database.get_api_data()
            telegram = Telegram(api_id, api_hash, name, crypt)
            friend = select_friend(database, telegram)
            if friend != None:
                chat = start_main(database, friend, crypt, telegram)
                if chat == "change_friend":
                    pass
                else:
                    break
                    

if __name__=='__main__':
    main()