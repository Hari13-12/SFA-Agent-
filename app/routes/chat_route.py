from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from app.schemas.chat_schema import chat_request_schema
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.async_db import get_db, get_psycopg_connection
import uuid
import os
import contextlib
from fastapi import Request
from dotenv import load_dotenv

# Load environment variables again to ensure they're available in this module
load_dotenv()

# Create router first to avoid circular imports
router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

# Phoenix imports - using the correct API structure
try:
    import phoenix
    from phoenix.otel import register
    
    # We need to get available features from phoenix.trace
    try:
        from phoenix.trace import using_project, suppress_tracing
    except ImportError:
        # Create placeholder functions if not available
        @contextlib.contextmanager
        def using_project(project_name):
            yield
            
        @contextlib.contextmanager
        def suppress_tracing():
            yield
    
    # Get configuration from environment variables
    PHOENIX_PROJECT = os.getenv("PHOENIX_PROJECT", "default")
    PHOENIX_API_KEY = os.getenv("PHOENIX_API_KEY", "")
    PHOENIX_ENDPOINT = os.getenv("PHOENIX_ENDPOINT", "https://app.phoenix.arize.com/v1/traces")
    
    if PHOENIX_API_KEY:
        # Set environment variables for Phoenix configuration
        os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = PHOENIX_ENDPOINT
        
        # Initialize the tracer (modern Phoenix API approach)
        try:
            tracer_provider = register(
                project_name=PHOENIX_PROJECT,
                endpoint=PHOENIX_ENDPOINT,      # Specify endpoint explicitly
                auto_instrument=True           # Automatically instrument supported libraries
            )
            tracer = tracer_provider.get_tracer("chat_service")
            PHOENIX_ENABLED = True
            # # print(f"Phoenix tracing initialized successfully with endpoint: {PHOENIX_ENDPOINT}")
        except Exception as e:
            print(f"Error initializing Phoenix tracing: {str(e)}")
            PHOENIX_ENABLED = False
    else:
        # print("No Phoenix API key found in environment variables")
        PHOENIX_ENABLED = False
except ImportError as e:
    print(f"Phoenix import error: {str(e)}")
    PHOENIX_ENABLED = False
    print("Phoenix library not available. Tracing disabled.")

# Import Chat_service after Phoenix setup to avoid circular imports
from app.services.chat_service import Chat_service

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db = Depends(get_psycopg_connection)):
    # Create a unique trace ID for this connection
    trace_id = str(uuid.uuid4())
    
    # Create a context manager for tracing
    if PHOENIX_ENABLED:
        # Use the tracer's context manager
        session_trace_context = tracer.start_as_current_span(
            "websocket_session",
            attributes={"trace_id": trace_id, "session_type": "websocket"}
        )
    else:
        # Use an empty context manager if Phoenix is disabled
        session_trace_context = contextlib.nullcontext()
    
    # Start a trace for the entire WebSocket session
    with session_trace_context as session_span:
        await websocket.accept()
        
        # Create a unique session ID for this connection
        session_id = str(uuid.uuid4())
        
        # Add session metadata to the span if Phoenix is enabled
        if session_span is not None:
            session_span.set_attribute("session_id", session_id)
            session_span.set_attribute("connection_type", "websocket")
        
        try:
            # Send welcome message
            await websocket.send_json({
                "type": "system",
                "message": "Connected to chat service",
                "session_id": session_id,
                "trace_id": trace_id  # Send trace ID to client for frontend correlation
            })
            
            while True:
                # Create a span for each message cycle
                if PHOENIX_ENABLED:
                    msg_trace_context = tracer.start_as_current_span(
                        "message_cycle",
                        attributes={"trace_id": trace_id}
                    )
                else:
                    # Use an empty context manager if Phoenix is disabled
                    msg_trace_context = contextlib.nullcontext()
                
                with msg_trace_context as msg_span:
                    # Receive message from client
                    data = await websocket.receive_json()
                    
                    # Add received data to span (excluding sensitive info)
                    if msg_span is not None and "message" in data:
                        msg_span.set_attribute("message_length", len(data["message"]))
                        msg_span.set_attribute("has_userid", "userid" in data and bool(data.get("userid")))
                        msg_span.set_attribute("has_token", "access_token" in data and bool(data.get("access_token")))
                    
                    # Validate the request format
                    try:
                        chat_request = chat_request_schema(**data)
                        if msg_span is not None:
                            msg_span.add_event("request_validated", {})
                    except Exception as e:
                        error_msg = f"Invalid request format: {str(e)}"
                        if msg_span is not None:
                            msg_span.add_event("validation_error", {"error": error_msg})
                        await websocket.send_json({
                            "type": "error",
                            "message": error_msg
                        })
                        continue

                    # Extract request data
                    message = chat_request.message
                    access_token = chat_request.access_token
                    userid = chat_request.userid
                    
                    # Validate required fields
                    if not access_token:
                        if msg_span is not None:
                            msg_span.add_event("missing_access_token", {})
                        await websocket.send_json({
                            "type": "error",
                            "message": "Access token is required"
                        })
                        continue
                        
                    if not userid:
                        if msg_span is not None:
                            msg_span.add_event("missing_userid", {})
                        await websocket.send_json({
                            "type": "error",
                            "message": "User ID is required"
                        })
                        continue
                        
                    if not message:
                        if msg_span is not None:
                            msg_span.add_event("missing_message", {})
                        await websocket.send_json({
                            "type": "error",
                            "message": "Message is required"
                        })
                        continue
                    
                    # Create thread ID from user ID or use session ID
                    thread_id = f"{userid}_{session_id}"
                    if msg_span is not None:
                        msg_span.set_attribute("thread_id", thread_id)
                        msg_span.set_attribute("user_id", userid)
                    
                    # Initialize chat service with WebSocket for streaming and trace ID
                    chat_service = Chat_service(
                        db=db,
                        websocket=websocket,
                        thread_id=thread_id,
                        trace_id=trace_id  # Pass the trace ID to maintain correlation
                    )
                    
                    if msg_span is not None:
                        msg_span.add_event("processing_start", {})
                    
                    # Process the message
                    result = await chat_service.chat(message, access_token, userid)
                    
                    if msg_span is not None:
                        msg_span.add_event("processing_complete", 
                                          {"result": "success" if result.get("status") == "success" else "error"})

        except WebSocketDisconnect:
            if session_span is not None:
                session_span.add_event("websocket_disconnected", {})
            print(f"WebSocket disconnected: session {session_id}")
        except Exception as e:
            error_msg = f"WebSocket error: {str(e)}"
            if session_span is not None:
                session_span.add_event("websocket_error", {"error": error_msg})
            print(error_msg)
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": error_msg
                })
            except:
                # Connection might be closed already
                if session_span is not None:
                    session_span.add_event("failed_to_send_error", {})
                pass

# Debug endpoint to check configuration
@router.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration (disable in production)"""
    if os.getenv("DEBUG", "false").lower() == "true":
        return {
            "phoenix_enabled": PHOENIX_ENABLED,
            "phoenix_project": PHOENIX_PROJECT,
            "phoenix_endpoint": PHOENIX_ENDPOINT,
            "api_key_length": len(PHOENIX_API_KEY) if PHOENIX_API_KEY else 0,
        }
    return {"error": "Debug mode disabled"}

# Additional endpoint to expose trace information for debugging or frontend correlation
@router.get("/trace/{trace_id}")
async def get_trace_info(trace_id: str):
    """Get trace information by ID - useful for debugging or frontend correlation"""
    return {
        "trace_id": trace_id,
        "phoenix_url": f"https://app.phoenix.arize.com/phoenix/traces/{trace_id}"
    }