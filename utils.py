from enum import Enum
from pydantic import BaseModel
import uuid
from faker import Faker
faker = Faker()

class OrderSide(str, Enum):
    BUY = "Buy"
    SELL = "Sell"

class OrderType(str, Enum):
    LIMIT = "Limit"
    MARKET = "Market"

class MessageType(str, Enum):
    ORDER = "order"
    ORCHESTRATOR_COMMAND = "orchestrator_command"
    ORCHESTRATOR_RESPONSE = "orchestrator_response"

class Message(BaseModel):
    message_type: MessageType
    data: dict


def mini_uuid():
    # return str(uuid.uuid4())[:6]
    return faker.name()
