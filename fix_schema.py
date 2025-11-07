#!/usr/bin/env python3
import sqlite3
import sys

try:
    conn = sqlite3.connect('/app/instance/pepperai.db')
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute('PRAGMA table_info(notification_attachment)')
    columns = cursor.fetchall()
    
    print('Current schema:')
    notification_id_col = None
    for col in columns:
        print(f'  {col[1]}: NOT NULL={bool(col[3])}')
        if col[1] == 'notification_id':
            notification_id_col = col
    
    if notification_id_col and notification_id_col[3] == 1:
        print('\nUpdating schema...')
        try:
            # Create new table with nullable notification_id
            cursor.execute('''
                CREATE TABLE notification_attachment_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_id INTEGER,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_size INTEGER,
                    mime_type VARCHAR(100),
                    file_type VARCHAR(20),
                    uploaded_at DATETIME
                )
            ''')
            
            # Copy existing data
            cursor.execute('''
                INSERT INTO notification_attachment_new 
                SELECT * FROM notification_attachment
            ''')
            
            # Drop old and rename
            cursor.execute('DROP TABLE notification_attachment')
            cursor.execute('ALTER TABLE notification_attachment_new RENAME TO notification_attachment')
            
            conn.commit()
            print('✅ SUCCESS: Schema updated! notification_id is now nullable')
        except Exception as e:
            print(f'❌ ERROR: {str(e)}')
            import traceback
            traceback.print_exc()
            conn.rollback()
    else:
        print('\n✅ Schema already allows NULL - no changes needed')
    
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f'❌ FATAL ERROR: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

