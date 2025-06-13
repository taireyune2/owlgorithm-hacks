IDLE_TIMEOUT_SECONDS = 30
PING_INTERVAL = 10

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    idle_time = 0

    try:
        while True:
            try:
                # Wait up to PING_INTERVAL for client message
                message = await asyncio.wait_for(websocket.receive_text(), timeout=PING_INTERVAL)
                idle_time = 0  # Reset idle time if message received
                await websocket.send_text(f"✅ Received: {message}")
            except asyncio.TimeoutError:
                idle_time += PING_INTERVAL
                if idle_time >= IDLE_TIMEOUT_SECONDS:
                    await websocket.send_text("❌ Disconnected due to inactivity.")
                    await websocket.close(code=1001)
                    self.cleanup()
                    break
                else:
                    await websocket.send_text(f"⏳ Still waiting for input... ({idle_time}s idle)")
    except WebSocketDisconnect:
        print(f"Client #{user_id} disconnected.")