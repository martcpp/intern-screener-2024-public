import unittest
from unittest.mock import patch, MagicMock
import main
from model import Message
from serializer import serialize, deserialize

class TestMain(unittest.TestCase):

    def test_random_id(self):
        id1 = main.random_id()
        id2 = main.random_id()
        self.assertEqual(len(id1), 10)
        self.assertEqual(len(id2), 10)
        self.assertNotEqual(id1, id2)

    @patch('main.socket.socket')
    def test_send_message(self, mock_socket):
        conn = mock_socket.return_value
        msg = Message(sender_id="A", receiver_id="B", msg_id="123", type="test")
        main.send_message(conn, msg)
        conn.sendall.assert_called_once_with(serialize(msg))

    @patch('main.extract_messages_from_buffer')
    def test_read_message(self, mock_extract):
        mock_conn = MagicMock()
        mock_conn.recv.return_value = b'{"sender_id": "A", "receiver_id": "B", "msg_id": "123", "type": "test"}'
        mock_extract.return_value = ([Message(sender_id="A", receiver_id="B", msg_id="123", type="test")], b'')
        buffer = bytearray()
        msg = main.read_message(mock_conn, buffer)
        self.assertEqual(msg.sender_id, "A")
        self.assertEqual(msg.receiver_id, "B")
        self.assertEqual(msg.msg_id, "123")
        self.assertEqual(msg.type, "test")

if __name__ == '__main__':
    unittest.main()
