import unittest
from unittest.mock import patch, MagicMock

import socket

from common.protocol import pack_offer, UDP_PORT_OFFER_LISTEN


class TestClientListener(unittest.TestCase):
    def test_create_listen_socket_binds_correct_port(self):
        """
        Ensure the UDP socket binds to the hardcoded offer port (13122) and is UDP.
        """
        from client.client_listener import create_listen_socket

        s = create_listen_socket()
        try:
            self.assertEqual(s.family, socket.AF_INET)
            self.assertEqual(s.type, socket.SOCK_DGRAM)

            # Check bound port is 13122
            host, port = s.getsockname()
            self.assertEqual(port, UDP_PORT_OFFER_LISTEN)
        finally:
            s.close()

    @patch("client.client_listener.unpack_offer")
    @patch("client.client_listener.socket.socket")
    def test_main_processes_one_offer_and_prints(self, mock_socket_cls, mock_unpack_offer):
        """
        Simulate receiving exactly one UDP packet and verify:
        - unpack_offer is called with the received bytes
        - a 'Received offer from ...' line is printed
        Then stop the loop by raising KeyboardInterrupt.
        """
        # Prepare fake socket instance
        fake_sock = MagicMock()
        mock_socket_cls.return_value = fake_sock

        # Prepare a valid offer bytes (the bytes content isn't crucial because we mock unpack_offer,
        # but it's nice to keep it realistic)
        offer_bytes = pack_offer(5000, "TestServer")
        fake_sock.recvfrom.side_effect = [
            (offer_bytes, ("192.168.1.10", 55555)),
            KeyboardInterrupt(),  # stop the infinite loop
        ]

        # Fake unpack_offer return object with required attributes
        fake_offer = MagicMock()
        fake_offer.server_name = "TestServer"
        fake_offer.tcp_port = 5000
        mock_unpack_offer.return_value = fake_offer

        with patch("builtins.print") as mock_print:
            from client.client_listener import main
            main()

        # Ensure unpack_offer called with the received bytes
        mock_unpack_offer.assert_called_with(offer_bytes)

        # Ensure we printed the "Received offer..." message at least once
        printed_texts = [" ".join(str(x) for x in call.args) for call in mock_print.call_args_list]
        self.assertTrue(
            any("Received offer from 192.168.1.10" in t for t in printed_texts),
            "Expected a print containing 'Received offer from 192.168.1.10'"
        )

        # Ensure socket was closed
        fake_sock.close.assert_called()

    @patch("client.client_listener.unpack_offer")
    @patch("client.client_listener.socket.socket")
    def test_main_ignores_corrupted_packets(self, mock_socket_cls, mock_unpack_offer):
        """
        If unpack_offer raises an exception (corrupted packet), main should ignore it and continue.
        We then stop using KeyboardInterrupt.
        """
        fake_sock = MagicMock()
        mock_socket_cls.return_value = fake_sock

        fake_sock.recvfrom.side_effect = [
            (b"corrupted", ("10.0.0.5", 11111)),
            KeyboardInterrupt(),
        ]

        mock_unpack_offer.side_effect = ValueError("bad packet")

        with patch("builtins.print") as mock_print:
            from client.client_listener import main
            main()

        # unpack_offer was attempted
        mock_unpack_offer.assert_called_with(b"corrupted")

        # Should not print "Received offer ..." for corrupted packet
        printed_texts = [" ".join(str(x) for x in call.args) for call in mock_print.call_args_list]
        self.assertFalse(any("Received offer from" in t for t in printed_texts))

        fake_sock.close.assert_called()


if __name__ == "__main__":
    unittest.main()
