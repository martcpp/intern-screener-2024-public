import socket
import random
import string
import logging
from model import Message
from serializer import serialize, extract_messages_from_buffer
from savefile import makefile

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def random_id():
    """
    Generate a random ID consisting of 10 alphanumeric characters.
    """
    charset = string.ascii_letters + string.digits
    return ''.join(random.choice(charset) for _ in range(10))

def read_message(conn, buffer):
    """
    Read a message from the connection and manage the buffer.

    Parameters:
    - conn: socket connection object
    - buffer: bytearray to store incoming data

    Returns:
    - The first complete message from the buffer
    """
    logging.debug("Reading message from connection")
    tmp_buffer = conn.recv(1024)
    if not tmp_buffer:
        logging.error("Connection closed by the server")
        raise ConnectionError("Connection closed by the server")

    buffer.extend(tmp_buffer)
    message_queue, incomplete_buffer = extract_messages_from_buffer(buffer)

    buffer.clear()
    buffer.extend(incomplete_buffer)

    if message_queue:
        logging.debug("Message read successfully")
        return message_queue[0]
    return None

def send_message(conn, msg):
    """
    Serialize and send a message through the connection.

    Parameters:
    - conn: socket connection object
    - msg: Message object to be sent
    """
    logging.debug(f"Sending message: {msg}")
    data = serialize(msg)
    conn.sendall(data)

def make_message(msg_type, sender_id, receiver_id):
    """
    Create a message with a random ID.

    Parameters:
    - msg_type: type of the message
    - sender_id: ID of the sender
    - receiver_id: ID of the receiver

    Returns:
    - Message object
    """
    return Message(
        type=msg_type,
        sender_id=sender_id,
        receiver_id=receiver_id,
        msg_id=random_id()
    )

def handle(conn):
    """
    Handle the connection and process messages to build topology.

    Parameters:
    - conn: socket connection object
    """
    logging.info("Handling connection")
    buffer = bytearray()
    queue = []
    topology = {}
    visited = {}
    my_id = ""

    while True:
        try:
            msg = read_message(conn, buffer)
        except Exception as e:
            logging.error(f"Error reading message: {e}")
            continue

        if msg and msg.type == "init":
            logging.info("Init message received")
            my_id = msg.receiver_id
            logging.info(f"My ID: {my_id}")
            break

    queue.append(my_id)
    init_query = make_message("query", my_id, my_id)
    visited[my_id] = True
    send_message(conn, init_query)

    while queue:
        try:
            msg = read_message(conn, buffer)
        except Exception as e:
            logging.error(f"Error reading message: {e}")
            continue

        if msg:
            logging.info(f"Received num of neighbors: {len(msg.n)}")
            logging.info(f"Receiver: {msg.receiver_id}, Sender: {msg.sender_id}")

            node_id = queue.pop(0)
            topology[node_id] = msg.n

            for neighbor in msg.n:
                if not visited.get(neighbor):
                    queue.append(neighbor)
                    query_rpc = make_message("query", my_id, neighbor)

                    logging.info(f"Sender: {query_rpc.sender_id}, Receiver: {query_rpc.receiver_id}")

                    visited[neighbor] = True
                    send_message(conn, query_rpc)

    logging.info("Topology is created")

    final_msg = Message(
        type="topology",
        sender_id=my_id,
        receiver_id="",
        msg_id=random_id(),
        topology=topology
    )

    send_message(conn, final_msg)

def main():
    """
    Main function to establish connection and handle it.
    """
    host = 'localhost'
    port = 12080
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
        conn.connect((host, port))
        handle(conn)

if __name__ == "__main__":
    main()
    makefile()
