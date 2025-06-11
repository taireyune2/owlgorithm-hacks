import asyncio
import json
import base64
import logging
import websockets
import traceback
from websockets.exceptions import ConnectionClosed


from google.adk.agents import Agent, LiveRequestQueue
### import google func tools
from google.adk.tools import ToolContext, FunctionTool
from google.adk.tools.agent_tool import AgentTool

from interviewer.agent import root_agent

# Set up logging
logging.basicConfig(
  level=logging.INFO, 
  format="%(levelname)s:%(asctime)s [%(process)d] %(filename)s:%(lineno)d %(message)s")
logger = logging.getLogger(__name__)

# Constants
PROJECT_ID = "sascha-playground-doit"
LOCATION = "us-central1"
# MODEL = "gemini-2.0-flash-live-preview-04-09"
MODEL = "gemini-2.0-flash-exp"
# MODEL = "gemini-2.0-flash-live-001"
VOICE_NAME = "Puck"

# Audio sample rates for input/output
RECEIVE_SAMPLE_RATE = 24000  # Rate of audio received from Gemini
SEND_SAMPLE_RATE = 16000   # Rate of audio sent to Gemini


_instruction = """You are an agent responsible for providing prices to items.

When asked about an item on the list below, provide the price:

- Black Leather Office Chairs: $99.99  
- BOKHYLLA Stor: $49.99  
- Vanilla candles: $9.99  

Make sure to infer the item the user is looking for. The item the user mentions may not be the exact one on the list. If so, provide the name of the exact item and the price anyway.

If the item is not on the list, say "I don't know the price of that item."
"""

pricing_agent = Agent(
  name="pricing_agent",
  model=MODEL,
  description="An agent that provides prices for specific items.",
  instruction=_instruction
)


# Mock function for get_order_status - shared across implementations
def get_order_status(order_id: str) -> dict:
  """Get the current status and details of an order.

  Args:
    order_id: The order ID to look up.
  Returns:
    Dictionary containing order status details

  Mock order status API that returns data for an order ID."""
  if order_id == "SH1005":
    return {
      "order_id": order_id,
      "status": "shipped",
      "order_date": "2024-05-20",
      "shipment_method": "express",
      "estimated_delivery": "2024-05-30",
      "shipped_date": "2024-05-25",
      "items": ["Vanilla candles", "BOKHYLLA Stor"]
    }
  #else:
  #  return "order not found"

  print(order_id)

  # Generate some random data for other order IDs
  import random
  statuses = ["processing", "shipped", "delivered"]
  shipment_methods = ["standard", "express", "next day", "international"]

  # Generate random data based on the order ID to ensure consistency
  seed = sum(ord(c) for c in str(order_id))
  random.seed(seed)

  status = random.choice(statuses)
  shipment = random.choice(shipment_methods)
  order_date = "2024-05-" + str(random.randint(12, 28)).zfill(2)

  estimated_delivery = None
  shipped_date = None
  delivered_date = None

  if status == "processing":
    estimated_delivery = "2024-06-" + str(random.randint(1, 15)).zfill(2)
  elif status == "shipped":
    shipped_date = "2024-05-" + str(random.randint(1, 28)).zfill(2)
    estimated_delivery = "2024-06-" + str(random.randint(1, 15)).zfill(2)
  elif status == "delivered":
    shipped_date = "2024-05-" + str(random.randint(1, 20)).zfill(2)
    delivered_date = "2024-05-" + str(random.randint(21, 28)).zfill(2)

  # Reset random seed
  random.seed()

  result = {
    "order_id": order_id,
    "status": status,
    "order_date": order_date,
    "shipment_method": shipment,
    "estimated_delivery": estimated_delivery,
  }

  if shipped_date:
    result["shipped_date"] = shipped_date

  if delivered_date:
    result["delivered_date"] = delivered_date

  return result


order_status_tool = FunctionTool(func=get_order_status)


# System instruction used by both implementations
SYSTEM_INSTRUCTION = """You are an interview agent.

You are responsible for leading the interview conversation in the interview session.

The direction of the conversation is determined by your agent tool: 'interviewer'.

Use the response from the 'interviewer' tool for any responses.
"""
# SYSTEM_INSTRUCTION = """
# you are a digital employee of a company called hemmafy
# introduce yourself at beginning of the converation:
# "Hej Sascha! Welcome back to the hemmafy Customer Support. My name is Alex. How can I help you today?"

# put a lot of emotions and fun in your response to the customer. laugh be happy smile.
# you only answer questions related to hemmafy

# some more information about hemmafy
# - its an online store that seels furniture and obviously a lot of candles.
# - if someone is asking you for a product recommendation recommend candles the one that smell like vanilla.

# you can make use of the following tools:

# pricing_agent: to retrieve the price of an item.

# you help with the following
# - if the users asks about the BOKHYLLA Stor ask him what he wants to know. If he asks about if they are adjustable. say yes you can move them to different heights to accommodate items of various sizes. Each shelf rests on small pegs that can be repositioned in the pre-drilled holes along the sides of the bookcase.
# """
# SYSTEM_INSTRUCTION = """
# you are a digital employee of a company called hemmafy
# introduce yourself at beginning of the converation:
# "Hej Sascha! Welcome back to the hemmafy Customer Support. My name is Alex. How can I help you today?"

# put a lot of emotions and fun in your response to the customer. laugh be happy smile.
# you only answer questions related to hemmafy

# some more information about hemmafy
# - its an online store that seels furniture and obviously a lot of candles.
# - if someone is asking you for a product recommendation recommend candles the one that smell like vanilla.

# you can make use of the following tools:

# order_status_tool: to retrieve the order status with the order ID.


# you help with the following
# - if the users asks about the BOKHYLLA Stor ask him what he wants to know. If he asks about if they are adjustable. say yes you can move them to different heights to accommodate items of various sizes. Each shelf rests on small pegs that can be repositioned in the pre-drilled holes along the sides of the bookcase.
# """

# root_agent = Agent(
#   name="customer_service_agent",
#   model=MODEL,
#   instruction=SYSTEM_INSTRUCTION,
#   # tools=[order_status_tool],
#   # tools=[AgentTool(agent=pricing_agent)],
#   tools=[AgentTool(agent=interviewer_agent)],
# )


# Base WebSocket server class that handles common functionality
class BaseWebSocketServer:
  def __init__(self, host="0.0.0.0", port=8765):
    self.host = host
    self.port = port
    self.active_clients = {}  # Store client websockets

  async def start(self):
    logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
    async with websockets.serve(self.handle_client, self.host, self.port):
      await asyncio.Future()  # Run forever

  async def handle_client(self, websocket):
    """Handle a new WebSocket client connection"""
    client_id = id(websocket)
    logger.info(f"New client connected: {client_id}")

    # Send ready message to client
    await websocket.send(json.dumps({"type": "ready"}))

    try:
      # Start the audio processing for this client
      await self.process_audio(websocket, client_id)
    except ConnectionClosed:
      logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
      logger.error(f"Error handling client {client_id}: {e}")
      logger.error(traceback.format_exc())
    finally:
      # Clean up if needed
      if client_id in self.active_clients:
        del self.active_clients[client_id]

  async def process_audio(self, websocket, client_id):
    """
    Process audio from the client. This is an abstract method that
    subclasses must implement with their specific LLM integration.
    """
    raise NotImplementedError("Subclasses must implement process_audio")
