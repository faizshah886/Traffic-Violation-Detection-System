"""
Database initialization and utilities for Traffic Violation System
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / 'database.db'

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    # Video configuration table (for stop-line)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            stopline TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    ''')
    
    # Challans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            violation_type TEXT NOT NULL,
            fine_amount INTEGER NOT NULL,
            plate_number TEXT,
            image_path TEXT,
            plate_image_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'unpaid',
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def insert_video(filename):
    """Insert new video record"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO videos (filename) VALUES (?)', (filename,))
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return video_id

def save_stopline_config(video_id, stopline_data):
    """Save stop-line configuration"""
    conn = get_connection()
    cursor = conn.cursor()
    stopline_json = json.dumps(stopline_data)
    
    # Check if config exists
    cursor.execute('SELECT id FROM video_config WHERE video_id = ?', (video_id,))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('UPDATE video_config SET stopline = ? WHERE video_id = ?', 
                      (stopline_json, video_id))
    else:
        cursor.execute('INSERT INTO video_config (video_id, stopline) VALUES (?, ?)',
                      (video_id, stopline_json))
    
    conn.commit()
    conn.close()

def get_stopline_config(video_id):
    """Get stop-line configuration"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT stopline FROM video_config WHERE video_id = ?', (video_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result['stopline']:
        return json.loads(result['stopline'])
    return None

def insert_challan(video_id, violation_type, fine_amount, plate_number=None, 
                  image_path=None, plate_image_path=None):
    """Insert new challan record"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO challans (video_id, violation_type, fine_amount, plate_number, 
                             image_path, plate_image_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (video_id, violation_type, fine_amount, plate_number, image_path, plate_image_path))
    challan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return challan_id

def get_all_challans():
    """Get all challans"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM challans ORDER BY timestamp DESC')
    challans = cursor.fetchall()
    conn.close()
    return [dict(row) for row in challans]

def get_challan_by_id(challan_id):
    """Get specific challan"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM challans WHERE id = ?', (challan_id,))
    challan = cursor.fetchone()
    conn.close()
    return dict(challan) if challan else None

def update_video_status(video_id, processed=True, status='completed'):
    """Update video processing status"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE videos SET processed = ?, status = ? WHERE id = ?',
                  (1 if processed else 0, status, video_id))
    conn.commit()
    conn.close()

def get_video_by_id(video_id):
    """Get video information"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
    video = cursor.fetchone()
    conn.close()
    return dict(video) if video else None

if __name__ == '__main__':
    init_database()
