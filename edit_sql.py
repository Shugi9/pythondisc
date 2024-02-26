import sqlite3
conn = sqlite3.connect('Data/user.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE infos_salos (id_salon int, contenu str)")
conn.commit()
conn.close()
