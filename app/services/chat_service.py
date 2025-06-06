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

from opentelemetry import trace

# Get the tracer instance from Phoenix registration
tracer = trace.get_tracer(__name__)


settings = Settings()

class Chat_service:
    def __init__(self, db, websocket=None, thread_id="default"):
        """
        Initialize the Chat service
        
        Args:
            db: Database connection
            websocket: WebSocket connection for streaming responses
            thread_id: Unique identifier for the conversation thread
        """
        self.db = db
        self.llm_manager = LLMManger()
        self.state = State
        self.memory = None
        self.graph = None
        self.websocket = websocket
        self.thread_id = thread_id
        self.config = {"configurable": {"thread_id": thread_id}}

    async def initialize(self):
        """Initialize the memory and graph asynchronously"""
        if self.memory is None:
            try:
                conn_string = f"postgresql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
                conn = await psycopg.AsyncConnection.connect(conn_string, autocommit=True)
                self.memory = AsyncPostgresSaver(conn)
                await self.memory.setup()
                self.graph = builder.compile(self.memory, interrupt_after=["ask_user_node"])
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
        try:
            state = await self.graph.aget_state(self.config)
            return state.next if hasattr(state, 'next') else []
        except Exception as e:
            print(f"Error getting graph state: {str(e)}")
            return []

    async def process_and_send_message(self, content: str, node_name: Optional[str] = None):
        """Process and send a message through the WebSocket"""
        if not content or not self.websocket:
            return
            
        try:
            # Create a structured message
            message = {
                "type": "message",
                "content": content,
                "node": node_name,
            }
            
            # Remove None values
            message = {k: v for k, v in message.items() if v is not None}
            
            # Debug ##print
            # print(f"Sending to WebSocket: {message}")
            
            # Send the message
            await self.websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    async def send_map(self, map_data: str):
        """Process and send a message through the WebSocket"""
        if not self.websocket:
            return
            
        try:
            # Create a structured message
            map_file = {
                "map_data": map_data
            }
            
            # # Remove None values
            # message = {k: v for k, v in message.items() if v is not None}
            
            # # Debug ##print
            # print(f"Sending to WebSocket: {map_file}")
            
            # Send the message
            await self.websocket.send_json(map_file)
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
        with tracer.start_as_current_span("chat_service.chat"):
            try:
                # Initialize the graph and memory
                await self.initialize()
                
                # Check if we're in the middle of a conversation that needs human input
                next_state = await self.get_graph_state()
                print(f"Next state: {next_state}")
                
                access_token = get_salesforce_access_token()
                if next_state:
                    # We're waiting for human decision
                    # await self.process_and_send_message(
                    #     "Continuing from previous conversation. Processing your input...",
                    #     "human_decision_router"
                    # )
                    
                    # Update the state with the human's message
                    # input_message = "approve"  # This is what your code was using
                    # await self.graph.aupdate_state(
                    #     self.config,
                    #     {"messages": [HumanMessage(content=input_message)], "access_token": access_token}
                    # )
                    
                    await self.graph.aupdate_state(
                        self.config,
                        {"messages": [HumanMessage(content=message)], "access_token": access_token}
                    )

                    # Continue processing from where we left off
                    async for event in self.graph.astream(
                        None, config=self.config, stream_mode="updates"
                    ):
                        ##print(f"Stream event (continuation): {event}")
                        with tracer.start_as_current_span("langgraph_stream_event"):
                            await self._process_stream_event(event)
                else:
                    # Start a new conversation
                    self.state = {
                        "messages": [HumanMessage(content=message)],
                        "access_token": access_token,
                        "resolved_user_id":"",
                        "user_search_results":"",
                        "user_id": self.config["configurable"]["thread_id"]
                    }
                    
                    # Stream the response
                    async for event in self.graph.astream(
                        self.state, config=self.config, stream_mode="updates"
                    ):
                        ##print(f"Stream event (new): {event}")
                        await self._process_stream_event(event)
                
                # Send a completion message
                # await self.process_and_send_message("Processing complete", "complete")
                
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
        try:
            # ##print the full event for debugging
            ##print(f"Processing event: {event}")
            
            # Handle interruption events
            # if "__interrupt__" in event:
            #     await self.process_and_send_message(
            #         "Waiting for confirming the user_id to continue...",
            #         "interrupt"
            #     )
            #     return
            
            # Handle different event formats
            
            # Format 1: Direct message content in the event
            if isinstance(event, dict) and "messages" in event:
                messages = event["messages"]
                ##print("\n\nInside Format 1\n\n", messages)
                # if messages and len(messages) > 0:
                if messages:
                    latest_message = messages[-1]
                    if isinstance(latest_message, AIMessage) and latest_message.content:
                        await self.process_and_send_message(
                            latest_message.content,
                            event.get("current_node")
                        )
            
            # Format 2: Node-specific content
            elif isinstance(event, dict) and len(event) == 1:
                # This might be a node-specific update
                for node_name, content in event.items():
                    if content and isinstance(content, list) and len(content) > 0:
                        # Try to extract message from the content
                        ##print("\n\nInside Format 2\n\nIf\n\n")
                        for item in content:
                            if node_name == "human_decision_router" or node_name == "assistant_node" or node_name == "ask_user_node":
                                if hasattr(item, 'content'):
                                    await self.process_and_send_message(
                                        item.content,
                                        node_name
                                    )
                    elif isinstance(content, dict) and "messages" in content:
                        # Extract messages from nested structure
                        messages = content["messages"]
                        map_cr = content.get("map_cr")
                        # ##print("\n\nInside Format 2\n\n",messages)
                        ##print("\n\nInside Format 2\n\nElse\n\n")
                        # if messages and len(messages) > 0:
                        if messages and (node_name == "human_decision_router" or node_name == "assistant_node" or node_name == "ask_user_node"):
                            latest_message = messages
                            # print("\n\nLatest Message\n", latest_message)
                            # if node_name == "human_decision_router" or node_name == "assistant_node" or node_name == "ask_user_node":
                            if map_cr is not None and hasattr(latest_message, 'content'):
                                    # print("Map CR:\n\n ", map_cr)
                                    await self.process_and_send_message(
                                        latest_message.content,
                                        node_name
                                    )
                                    await self.send_map(
                                        map_cr,
                                    )
                                    
                            else:
                                    await self.process_and_send_message(
                                        latest_message.content,
                                        node_name
                                    )
                    elif isinstance(content, str):
                        # Direct string content
                        if node_name == "human_decision_router" or node_name == "assistant_node" or node_name == "ask_user_node":
                            await self.process_and_send_message(
                                content,
                                node_name
                            )
            
            # Format 3: Simple string content
            elif isinstance(event, str) and event:
                await self.process_and_send_message(event, None)
                
        except Exception as e:
            print(f"Error processing event: {str(e)}")
            if self.websocket:
                await self.websocket.send_json({
                    "type": "error", 
                    "message": f"Error processing event: {str(e)}"
                })