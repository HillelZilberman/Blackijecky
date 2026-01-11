import unittest
from unittest.mock import MagicMock, patch
from network.server.server_tcp import recv_exact, create_tcp_listen_socket


class TestServerTCP(unittest.TestCase):
    def test_recv_exact_joins_chunks(self):
        sock = MagicMock()
        # Return partial chunks: total 5 bytes
        sock.recv.side_effect = [b"ab", b"cd", b"e"]

        data = recv_exact(sock, 5)
        self.assertEqual(data, b"abcde")
        self.assertEqual(sock.recv.call_count, 3)

    def test_recv_exact_raises_on_closed_socket(self):
        sock = MagicMock()
        sock.recv.return_value = b""  # peer closed immediately

        with self.assertRaises(ConnectionError):
            recv_exact(sock, 5)

    @patch("network.server.server_tcp.socket.socket")
    def test_create_tcp_listen_socket_binds_listens_and_timeout(self, mock_socket_ctor):
        fake_sock = MagicMock()
        mock_socket_ctor.return_value = fake_sock

        # bind(("",0)) then getsockname()[1] used as port
        fake_sock.getsockname.return_value = ("0.0.0.0", 12345)

        s, port = create_tcp_listen_socket()

        mock_socket_ctor.assert_called_once()
        fake_sock.setsockopt.assert_called()  # at least called for REUSEADDR

        fake_sock.bind.assert_called_once_with(("", 0))
        fake_sock.listen.assert_called_once()
        fake_sock.settimeout.assert_called_once_with(1.0)

        self.assertIs(s, fake_sock)
        self.assertEqual(port, 12345)


if __name__ == "__main__":
    unittest.main()
