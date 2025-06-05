import asyncio
import websockets
import sqlite3
import json
from datetime import datetime

connected_clients = set()

def save_message(username, message):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    timestamp = datetime.now().isoformat()
    cursor.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
                   (username, message, timestamp))
    conn.commit()
    conn.close()
    return timestamp

async def handler(websocket):
    connected_clients.add(websocket)

    try:
        # ส่งประวัติแชทย้อนหลัง
        conn = sqlite3.connect("chat.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, message, timestamp FROM messages ORDER BY id ASC")
        history = cursor.fetchall()
        conn.close()

        for row in history:
            username, message, timestamp = row
            history_data = json.dumps({
                "username": username,
                "message": message,
                "timestamp": timestamp
            })
            await websocket.send(history_data)

        # รับข้อความใหม่
        async for raw_data in websocket:
            data = json.loads(raw_data)
            username = data.get("username", "Unknown")
            message = data.get("message", "")
            timestamp = save_message(username, message)

            broadcast_data = json.dumps({
                "username": username,
                "message": message,
                "timestamp": timestamp
            })

            for client in connected_clients:
                await client.send(broadcast_data)

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        connected_clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 10000):  # ใช้ 0.0.0.0 สำหรับ Render
        print("✅ Chat Server running at port 10000")
        await asyncio.Future()

asyncio.run(main())
