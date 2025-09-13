from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from api.router import router as api_router
from core.config import settings
import asyncio

app = FastAPI(
    title=settings.app_name,
    openapi_url=f"{settings.api_v1_str}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_str)

@app.get("/")
async def root():
    return {"message": "Linux Mirror Testing API"}

# Keep the original WebSocket endpoint for backward compatibility (if needed)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send a test message to verify connection
            await websocket.send_text("Connected to WebSocket")
            # Wait for a short time before sending next message
            await websocket.receive_text()
    except Exception as e:
        print(f"WebSocket error: {e}")

# Test-specific WebSocket endpoint (this was causing the issue)
@app.websocket("/test/ws")
async def test_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Send initial message
        await websocket.send_text("Connected to test WebSocket")
        while True:
            # In a real implementation, this would receive messages from test runner
            # and broadcast updates to connected clients
            try:
                data = await websocket.receive_text()
                # Echo the received message back to client
                await websocket.send_text(f"Echo: {data}")
            except Exception as e2:
                # If we can't receive, just continue listening
                print(f"Error receiving from WebSocket: {e2}")
                await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error in test endpoint: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
