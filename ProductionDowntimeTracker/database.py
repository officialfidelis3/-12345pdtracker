import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('downtime.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downtime_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                shift TEXT,
                line TEXT,
                start_time TEXT,
                end_time TEXT,
                duration INTEGER,
                equipment TEXT,
                issue_type TEXT,
                issue_description TEXT,
                action_taken TEXT,
                responsible_person TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def insert_record(self, data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO downtime_records 
            (date, shift, line, start_time, end_time, duration, 
             equipment, issue_type, issue_description, action_taken, 
             responsible_person, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['date'], data['shift'], data['line'], 
            data['start_time'], data['end_time'], data['duration'],
            data['equipment'], data['issue_type'], data['issue_description'],
            data['action_taken'], data['responsible_person'], data['remarks']
        ))
        self.conn.commit()

    def get_all_records(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM downtime_records ORDER BY date DESC')
        columns = [description[0] for description in cursor.description]
        records = cursor.fetchall()
        return columns, records

    def delete_record(self, record_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM downtime_records WHERE id = ?', (record_id,))
        self.conn.commit()

    def get_equipment_stats(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT equipment, 
                   COUNT(*) as frequency,
                   SUM(duration) as total_duration
            FROM downtime_records 
            GROUP BY equipment
            ORDER BY total_duration DESC
        ''')
        return cursor.fetchall()

    def get_issue_type_stats(self):
        """Get statistics for downtime causes (issue types)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT issue_type, 
                   COUNT(*) as frequency,
                   SUM(duration) as total_duration
            FROM downtime_records 
            GROUP BY issue_type
            ORDER BY total_duration DESC
        ''')
        return cursor.fetchall()