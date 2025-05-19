from app.agent.state_graph import builder
from app.agent.core.llm_manager import LLMManger
from app.agent.core.state_models import State
from app.agent.nodes.get_access_token import get_salesforce_access_token
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import psycopg
from app.core.config import Settings
from typing import Dict, Any, Optional
import json
import uuid
import asyncio
import contextlib
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Phoenix imports - added at the top level to avoid import issues
try:
    import phoenix
    from phoenix.otel import register
    # Import OpenInference conventions if available
    try:
        from openinference.semconv.trace import SpanAttributes
        OPENINFERENCE_AVAILABLE = True
    except ImportError:
        # Create a placeholder for SpanAttributes if not available
        class SpanAttributesPlaceholder:
            LLM_INPUT_MESSAGES = "llm.input_messages"
            LLM_OUTPUT_MESSAGES = "llm.output_messages"
            
        SpanAttributes = SpanAttributesPlaceholder()
        OPENINFERENCE_AVAILABLE = False
    
    # Get Phoenix configuration
    PHOENIX_PROJECT = os.getenv("PHOENIX_PROJECT", "default")
    PHOENIX_API_KEY = os.getenv("PHOENIX_API_KEY", "")
    PHOENIX_ENDPOINT = os.getenv("PHOENIX_ENDPOINT", "https://app.phoenix.arize.com/v1/traces")
    
    if PHOENIX_API_KEY:
        # Configure Phoenix
        os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = PHOENIX_ENDPOINT
        PHOENIX_AVAILABLE = True
    else:
        PHOENIX_AVAILABLE = False
        # # print("No Phoenix API key found. Tracing will be disabled.")
except ImportError as e:
    # Phoenix not available
    print(f"Phoenix import error: {str(e)}")
    PHOENIX_AVAILABLE = False
    
    # Create placeholder for SpanAttributes
    class SpanAttributesPlaceholder:
        LLM_INPUT_MESSAGES = "llm.input_messages"
        LLM_OUTPUT_MESSAGES = "llm.output_messages"
        
    SpanAttributes = SpanAttributesPlaceholder()

# Initialize Phoenix settings
settings = Settings()

class Chat_service:
    def __init__(self, db, websocket=None, thread_id="default", trace_id=None):
        """
        Initialize the Chat service
        
        Args:
            db: Database connection
            websocket: WebSocket connection for streaming responses
            thread_id: Unique identifier for the conversation thread
            trace_id: Phoenix trace ID for observability
        """
        self.db = db
        self.llm_manager = LLMManger()
        self.state = State
        self.memory = None
        self.graph = None
        self.websocket = websocket
        self.thread_id = thread_id
        self.config = {"configurable": {"thread_id": thread_id}}
        self.trace_id = trace_id or str(uuid.uuid4())
        
        # Initialize Phoenix LangChain instrumentation if available
        if PHOENIX_AVAILABLE:
            try:
                # Get the tracer for this class
                self.tracer_provider = register(
                    project_name=PHOENIX_PROJECT,
                    endpoint=PHOENIX_ENDPOINT,
                    auto_instrument=False  # We're handling instrumentation manually
                )
                self.tracer = self.tracer_provider.get_tracer("chat_service")
                
                # Initialize LangChain instrumentation
                try:
                    from phoenix.trace.langchain import LangChainInstrumentor
                    LangChainInstrumentor().instrument()
                    # # print("Phoenix LangChain instrumentation initialized")
                except Exception as e:
                    print(f"Error initializing LangChain instrumentation: {str(e)}")
            except Exception as e:
                print(f"Error initializing Phoenix tracing: {str(e)}")
                self.tracer = None
        else:
            self.tracer = None

    @asynccontextmanager
    async def phoenix_trace(self, span_name, **attrs):
        """Context manager for Phoenix tracing"""
        try:
            if PHOENIX_AVAILABLE and hasattr(self, 'tracer') and self.tracer:
                # Create a span using the tracer
                with self.tracer.start_as_current_span(
                    span_name, 
                    attributes={"trace_id": self.trace_id, **attrs}
                ) as span:
                    try:
                        yield span
                    except Exception as e:
                        if span is not None:
                            span.add_event("error", {"error.message": str(e)})
                        raise
            else:
                # If Phoenix is not available, use a null context
                yield None
        except Exception as e:
            # If Phoenix tracing fails, yield None and log the error
            print(f"Phoenix tracing error: {str(e)}")
            try:
                yield None
            except Exception as inner_e:
                raise inner_e

    async def initialize(self):
        """Initialize the memory and graph asynchronously"""
        async with self.phoenix_trace("initialize_graph") as span:
            if self.memory is None:
                try:
                    conn_string = f"postgresql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
                    conn = await psycopg.AsyncConnection.connect(conn_string, autocommit=True)
                    self.memory = AsyncPostgresSaver(conn)
                    await self.memory.setup()
                    
                    if span is not None:
                        span.add_event("graph_compilation_start", {})
                    
                    self.graph = builder.compile(self.memory, interrupt_after=["ask_user_node"])
                    
                    if span is not None:
                        span.add_event("graph_compilation_complete", {})
                    
                    return True
                except Exception as e:
                    if self.websocket:
                        await self.websocket.send_json({
                            "type": "error", 
                            "message": f"Initialization error: {str(e)}"
                        })
                    raise e
            return True

    async def get_graph_state(self):
        """Get the current state of the graph"""
        async with self.phoenix_trace("get_graph_state") as span:
            try:
                state = await self.graph.aget_state(self.config)
                next_state = state.next if hasattr(state, 'next') else []
                if span is not None:
                    span.set_attribute("next_state", str(next_state))
                return next_state
            except Exception as e:
                print(f"Error getting graph state: {str(e)}")
                return []

    async def process_and_send_message(self, content: str, node_name: Optional[str] = None):
        """Process and send a message through the WebSocket"""
        if not content or not self.websocket:
            return
            
        async with self.phoenix_trace("process_and_send_message", 
                                  node_name=node_name,
                                  content_length=len(content)) as span:
            try:
                # Create a structured message
                message = {
                    "type": "message",
                    "content": content,
                    "node": node_name
                }
                
                # Remove None values
                message = {k: v for k, v in message.items() if v is not None}
                
                # Debug # # print
                # # print(f"Sending to WebSocket: {message}")
                
                # Send the message
                await self.websocket.send_json(message)
                if span is not None:
                    span.add_event("message_sent", {})
            except Exception as e:
                print(f"Error sending message: {str(e)}")


    async def send_map(self, map_data: str):
        """Process and send a message through the WebSocket"""
        if not self.websocket:
            return
        
        async with self.phoenix_trace("send_map", 
                                map_data = "map") as span:
            try:
                # Create a structured message
                map_file = {
                    "map_data": map_data
                }
                
                # # Debug ##print
                print(f"Sending to WebSocket: {map_file}")
                
                # Send the message
                await self.websocket.send_json(map_file)
                if span is not None:
                    span.add_event("message_sent", {})
            except Exception as e:
                print(f"Error sending message: {str(e)}")


    async def send_map_message(self, map_message: str):
        """Process and send a message through the WebSocket"""
        if not self.websocket:
            return
        
        async with self.phoenix_trace("send_map_message",
                                      map_message = "map_message") as span:
            try:
                # Create a structured message
                map_file = {
                    "map_message": map_message
                }
                
                # # Debug ##print
                print(f"Sending to WebSocket: {map_file}")
                
                # Send the message
                await self.websocket.send_json(map_file)
                if span is not None:
                    span.add_event("message_sent", {})
            except Exception as e:
                print(f"Error sending message: {str(e)}")


    async def chat(self, message: str, access_token: str, userid: str):
        """
        Process a chat message and stream the response through WebSocket
        
        Args:
            message: User's message
            access_token: Authentication token
            userid: User identifier
        """
        async with self.phoenix_trace("chat_session", 
                                  user_id=userid,
                                  message_length=len(message)) as span:
            try:
                # Record input message for tracing
                if span is not None:
                    span.set_attribute(f"{SpanAttributes.LLM_INPUT_MESSAGES}.0.message.role", "user")
                    span.set_attribute(f"{SpanAttributes.LLM_INPUT_MESSAGES}.0.message.content", message)
                
                # Initialize the graph and memory
                await self.initialize()
                
                # Check if we're in the middle of a conversation that needs human input
                next_state = await self.get_graph_state()
                # # print(f"Next state: {next_state}")
                if span is not None:
                    span.set_attribute("next_state", str(next_state))
                
                access_token = get_salesforce_access_token()
                
                if next_state:
                    # We're waiting for human decision
                    if span is not None:
                        span.add_event("continuing_conversation", {})
                    
                    # Update the state with the human's message
                    if span is not None:
                        span.add_event("updating_graph_state", {})
                    
                    await self.graph.aupdate_state(
                        self.config,
                        {"messages": [HumanMessage(content=message)], "access_token": access_token}
                    )

                    # Continue processing from where we left off
                    if span is not None:
                        span.add_event("streaming_from_graph_continuation", {})
                    
                    async for event in self.graph.astream(
                        None, config=self.config, stream_mode="updates"
                    ):
                        # # print(f"Stream event (continuation): {event}")
                        await self._process_stream_event(event)
                        
                else:
                    # Start a new conversation
                    if span is not None:
                        span.add_event("starting_new_conversation", {})
                    
                    self.state = {
                        "messages": [HumanMessage(content=message)],
                        "access_token": access_token,
                        "resolved_user_id":"",
                        "user_search_results":""
                    }
                    
                    # Stream the response
                    if span is not None:
                        span.add_event("streaming_from_graph_new", {})
                    
                    async for event in self.graph.astream(
                        self.state, config=self.config, stream_mode="updates"
                    ):
                        # # print(f"Stream event (new): {event}")
                        await self._process_stream_event(event)
                
                # Record completion
                if span is not None:
                    span.add_event("processing_complete", {})
                
                # Return the final state for non-WebSocket contexts
                return {"status": "success", "message": "Processing complete"}
                
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                print(error_msg)
                if self.websocket:
                    await self.websocket.send_json({"type": "error", "message": error_msg})
                return {"error": error_msg}

    async def _process_stream_event(self, event: Dict[str, Any]):
        """
        Process a streaming event from LangGraph
        
        Args:
            event: Event data from LangGraph
        """
        async with self.phoenix_trace("process_stream_event", 
                                  event_type=type(event).__name__) as span:
            try:
                # # # print the full event for debugging
                # # print(f"Processing event: {event}")
                if span is not None:
                    span.set_attribute("event", str(event)[:1000])  # Truncate for very large events
                
                # Handle different event formats
                
                # Format 1: Direct message content in the event
                if isinstance(event, dict) and "messages" in event:
                    messages = event["messages"]
                    # # print("\n\nInside Format 1\n\n", messages)
                    if span is not None:
                        span.add_event("format_1_messages", {})
                    
                    if messages:
                        latest_message = messages[-1]
                        if isinstance(latest_message, AIMessage) and latest_message.content:
                            # Record AI response for tracing
                            if span is not None:
                                span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.role", "assistant")
                                span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.content", latest_message.content)
                                span.set_attribute("node", event.get("current_node", "unknown"))
                            
                            await self.process_and_send_message(
                                latest_message.content,
                                event.get("current_node")
                            )
                
                # Format 2: Node-specific content
                elif isinstance(event, dict) and len(event) == 1:
                    # This might be a node-specific update
                    if span is not None:
                        span.add_event("format_2_node_specific", {})
                    
                    for node_name, content in event.items():
                        if content and isinstance(content, list) and len(content) > 0:
                            # Try to extract message from the content
                            for item in content:
                                if node_name in ["human_decision_router", "assistant_node", "ask_user_node"]:
                                    if hasattr(item, 'content'):
                                        # Record node response for tracing
                                        if span is not None:
                                            span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.role", "assistant")
                                            span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.content", item.content)
                                            span.set_attribute("node", node_name)
                                        
                                        await self.process_and_send_message(
                                            item.content,
                                            node_name
                                        )
                        elif isinstance(content, dict) and "messages" in content:
                            # Extract messages from nested structure
                            messages = content["messages"]
                            # # print("\n\nInside Format 2\n\n", messages)
                            
                            # if messages:
                            if messages and (node_name == "human_decision_router" or node_name == "assistant_node" or node_name == "ask_user_node"):
                                latest_message = messages
                                map_cr = content.get("map_cr")
                                # # print("\n\nLatest Message\n", latest_message)
                                if node_name in ["human_decision_router", "assistant_node", "ask_user_node"]:
                                    if map_cr is not None and hasattr(latest_message, 'content'):
                                        map_message = "Loading Map"
                                        # Record node response for tracing
                                        if span is not None:
                                            span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.role", "assistant")
                                            span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.content", latest_message.content)
                                            span.set_attribute("node", node_name)
                                            span.set_attribute("map", map_cr)
                                            # span.set_attribute("map_message", map_message)
                                        
                                        await self.process_and_send_message(
                                            latest_message.content,
                                            node_name
                                        )
                                        # await self.send_map_message(map_message)
                                        await self.send_map(
                                        map_cr,
                                        )
                                    else:
                                        if span is not None:
                                            span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.role", "assistant")
                                            span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.content", latest_message.content)
                                            span.set_attribute("node", node_name)
                                            await self.process_and_send_message(
                                            latest_message.content,
                                            node_name
                                    )
                        elif isinstance(content, str):
                            # Direct string content
                            if node_name in ["human_decision_router", "assistant_node", "ask_user_node"]:
                                # Record string response for tracing
                                if span is not None:
                                    span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.role", "assistant")
                                    span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.content", content)
                                    span.set_attribute("node", node_name)
                                
                                await self.process_and_send_message(
                                    content,
                                    node_name
                                )
                
                # Format 3: Simple string content
                elif isinstance(event, str) and event:
                    if span is not None:
                        span.add_event("format_3_string", {})
                    
                    # Record string response for tracing
                    if span is not None:
                        span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.role", "assistant")
                        span.set_attribute(f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.message.content", event)
                    
                    await self.process_and_send_message(event, None)
                    
            except Exception as e:
                error_msg = f"Error processing event: {str(e)}"
                if span is not None:
                    span.add_event("error", {"error.message": error_msg})
                print(error_msg)
                if self.websocket:
                    await self.websocket.send_json({
                        "type": "error", 
                        "message": f"Error processing event: {str(e)}"
                    })