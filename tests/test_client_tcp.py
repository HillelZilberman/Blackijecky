import unittest
from unittest.mock import patch, MagicMock
from network.client.client_tcp import connect_and_send_request


class TestClientTCP(unittest.TestCase):
    @patch("network.client.client_tcp.pack_request")
    @patch("network.client.client_tcp.socket.socket")
    def test_connect_and_send_request_connects_and_sends(self, mock_socket_ctor, mock_pack_request):
        mock_pack_request.return_value = b"REQ_BYTES"

        fake_sock = MagicMock()
        mock_socket_ctor.return_value = fake_sock

        out_sock = connect_and_send_request("1.2.3.4", 5555, "Team", 3)

        # Correct socket type
        mock_socket_ctor.assert_called_once()
        # Connect called with (ip, port)
        fake_sock.connect.assert_called_once_with(("1.2.3.4", 5555))
        # sendall called with packed request
        fake_sock.sendall.assert_called_once_with(b"REQ_BYTES")
        # returns the socket so caller can use it for session
        self.assertIs(out_sock, fake_sock)

        # Ensure function does NOT close socket internally
        fake_sock.close.assert_not_called()


if __name__ == "__main__":
    unittest.main()
