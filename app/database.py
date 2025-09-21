import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class ViolationDatabase:
    def __init__(self, db_path: str = "violations.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create violations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                camera_id INTEGER NOT NULL,
                violation_type TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                details TEXT NOT NULL,
                duration REAL DEFAULT 0,
                screenshot_path TEXT,
                status TEXT DEFAULT 'ongoing',
                analysis TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create camera status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camera_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                last_seen TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_violations INTEGER DEFAULT 0,
                safety_gear_violations INTEGER DEFAULT 0,
                proximity_violations INTEGER DEFAULT 0,
                resolved_violations INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_violation(self, violation_data: Dict) -> int:
        """Add a new violation to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO violations 
            (timestamp, camera_id, violation_type, worker_id, details, duration, screenshot_path, status, analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            violation_data.get('timestamp', datetime.now().isoformat()),
            violation_data.get('camera_id', 0),
            violation_data.get('type', 'unknown'),
            violation_data.get('worker_id', ''),
            violation_data.get('details', ''),
            violation_data.get('duration', 0),
            violation_data.get('screenshot', ''),
            violation_data.get('status', 'ongoing'),
            violation_data.get('analysis', '')
        ))
        
        violation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return violation_id
    
    def get_violations(self, limit: int = 100, offset: int = 0, 
                      camera_id: Optional[int] = None, 
                      violation_type: Optional[str] = None,
                      status: Optional[str] = None) -> List[Dict]:
        """Get violations with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM violations WHERE 1=1"
        params = []
        
        if camera_id is not None:
            query += " AND camera_id = ?"
            params.append(camera_id)
        
        if violation_type is not None:
            query += " AND violation_type = ?"
            params.append(violation_type)
        
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        violations = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return violations
    
    def update_violation_status(self, violation_id: int, status: str) -> bool:
        """Update the status of a violation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE violations 
            SET status = ? 
            WHERE id = ?
        ''', (status, violation_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0
    
    def get_violation_stats(self, date_from: Optional[str] = None, 
                           date_to: Optional[str] = None) -> Dict:
        """Get violation statistics for a date range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) as total FROM violations WHERE 1=1"
        params = []
        
        if date_from:
            query += " AND timestamp >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND timestamp <= ?"
            params.append(date_to)
        
        cursor.execute(query, params)
        total_violations = cursor.fetchone()[0]
        
        # Get violations by type
        cursor.execute(query + " AND violation_type = 'safety_gear'", params)
        safety_violations = cursor.fetchone()[0]
        
        cursor.execute(query + " AND violation_type = 'proximity'", params)
        proximity_violations = cursor.fetchone()[0]
        
        cursor.execute(query + " AND status = 'resolved'", params)
        resolved_violations = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_violations': total_violations,
            'safety_gear_violations': safety_violations,
            'proximity_violations': proximity_violations,
            'resolved_violations': resolved_violations
        }
    
    def update_camera_status(self, camera_id: int, status: str):
        """Update camera status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO camera_status (camera_id, status, last_seen)
            VALUES (?, ?, ?)
        ''', (camera_id, status, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_camera_status(self) -> List[Dict]:
        """Get current camera status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT camera_id, status, last_seen 
            FROM camera_status 
            ORDER BY camera_id
        ''')
        
        columns = [description[0] for description in cursor.description]
        statuses = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return statuses
