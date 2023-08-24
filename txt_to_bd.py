import sqlite3

def add_mnemonics_from_txt_to_db(txt_file_path, db_path):
    """
    :param txt_file_path:
    :param db_path:
    """
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        mnemonic TEXT NOT NULL,
        link TEXT
    )
    ''')
    conn.commit()

    with open(txt_file_path, 'r') as file:
        mnemonics = file.readlines()


    for mnemonic in mnemonics:
        cursor.execute("INSERT INTO accounts (mnemonic) VALUES (?)", (mnemonic,))
    conn.commit()

    conn.close()

add_mnemonics_from_txt_to_db('mnemonics.txt', 'accounts.db')

