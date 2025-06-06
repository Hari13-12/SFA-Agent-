from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from app.schemas.chat_schema import chat_request_schema
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.async_db import get_db, get_psycopg_connection
from app.services.chat_service import Chat_service
import uuid

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db = Depends(get_psycopg_connection)):
    await websocket.accept()
    
    # Create a unique session ID for this connection
    session_id = str(uuid.uuid4())
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": "Connected to chat service",
            "session_id": session_id
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Validate the request format
            try:
                chat_request = chat_request_schema(**data)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid request format: {str(e)}"
                })
                continue

            # Extract request data
            message = chat_request.message
            access_token = chat_request.access_token
            userid = chat_request.userid
            
            # Validate required fields
            if not access_token:
                await websocket.send_json({
                    "type": "error",
                    "message": "Access token is required"
                })
                continue
                
            if not userid:
                await websocket.send_json({
                    "type": "error",
                    "message": "User ID is required"
                })
                continue
                
            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message is required"
                })
                continue
            
            # Create thread ID from user ID or use session ID
            thread_id = f"{userid}_{session_id}"
            
            # Initialize chat service with WebSocket for streaming
            chat_service = Chat_service(
                db=db,
                websocket=websocket,
                thread_id=thread_id
            )
            
            # Process the message
            await chat_service.chat(message, access_token, userid)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: session {session_id}")
    except Exception as e:
        error_msg = f"WebSocket error: {str(e)}"
        print(error_msg)
        try:
            await websocket.send_json({
                "type": "error",
                "message": error_msg
            })
        except:
            # Connection might be closed already
            pass
