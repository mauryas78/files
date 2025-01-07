from azure.servicebus import ServiceBusClient, ServiceBusMessage
import os
from dotenv import load_dotenv

load_dotenv()

client_1 = ServiceBusClient.from_connection_string(conn_str=os.getenv("CONNECTION_STR"), logging_enable=False)
sender_1 = client_1.get_queue_sender(queue_name=os.getenv("QUEUE_1_NAME"))