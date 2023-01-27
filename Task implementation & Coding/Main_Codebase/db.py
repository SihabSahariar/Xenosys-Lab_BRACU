# Developed By Xenosys Lab
'''
Module : db
Responsibilities : A Class for CRUD operation on the Database
Data Field : device_name,additional_info,cam_group,login_type,ip,port,username,password,protocol
'''
import sqlite3
class DataBase:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS data (ID INTEGER PRIMARY KEY, device_name TEXT, additional_info TEXT, cam_group TEXT,
                login_type TEXT, ip TEXT, port TEXT, username TEXT, password TEXT, protocol TEXT)""")
        self.conn.commit()
        self.msg = 'S'+'I'+'H'+'A'+'B'+' '+'W'+'A'+'S'+' '+'H'+'E'+'R'+'E'+'!'

    def fetch(self):
        self.cur.execute("SELECT * FROM data")
        rows = self.cur.fetchall()
        return rows

    def fetchone_f(self, ID):
        self.cur.execute("SELECT * FROM data WHERE ID = ?", (ID,))
        row = self.cur.fetchone()
        return row

    def insert(self, device_name, additional_info, cam_group, login_type, ip, port, username, password, protocol):
        self.cur.execute("INSERT INTO data VALUES(NULL, ? , ?, ?, ?, ?, ?, ?, ?, ?)",
                         (device_name, additional_info, cam_group, login_type, ip, port, username, password, protocol))
        self.conn.commit()

    def remove(self, ID):
        self.cur.execute("DELETE FROM data WHERE ID=?", (ID,))
        self.conn.commit()

    def update(self, ID, device_name, additional_info, cam_group, login_type, ip, port, username, password, protocol):
        self.cur.execute("UPDATE data SET device_name = ?, additional_info = ?, cam_group = ?, login_type = ?, ip = ?, port = ?, username = ?, password = ?, protocol = ? WHERE ID = ?",(device_name, additional_info, cam_group, login_type, ip, port, username, password, protocol, ID))
        self.conn.commit()

    def __del__(self):
        self.conn.close()

