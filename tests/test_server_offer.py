import unittest
from unittest.mock import patch, MagicMock

import socket

from common.protocol import unpack_offer
from network.server.server_offer import (
    get_local_ip,
    create_offer_socket,
)


class TestServerOffer(unittest.TestCase):
    def test_get_local_ip_returns_string(self):
        """
        get_local_ip should always return a string representing an IP address.
        """
        ip = get_local_ip()
        self.assertIsInstance(ip, str)
        self.assertGreater(len(ip), 0)

    def test_create_offer_socket_udp(self):
        """
        The offer socket must be a UDP socket with broadcast enabled.
        """
        s = create_offer_socket()
        try:
            self.assertEqual(s.family, socket.AF_INET)
            self.assertEqual(s.type, socket.SOCK_DGRAM)

            # Check SO_BROADCAST flag
            broadcast = s.getsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST)
            self.assertEqual(broadcast, 1)
        finally:
            s.close()

    @patch("network.server.server_offer.socket.socket")
    def test_offer_packet_is_sent(self, mock_socket_cls):
        """
        Verify that an offer packet is sent via UDP.
        """
        mock_socket = MagicMock()
        mock_socket_cls.return_value = mock_socket

        from network.server.server_offer import pack_offer

        tcp_port = 5000
        server_name = "TestServer"

        offer = pack_offer(tcp_port=tcp_port, server_name=server_name)

        # simulate sendto
        mock_socket.sendto(offer, ("<broadcast>", 13122))

        mock_socket.sendto.assert_called_once()

        sent_bytes, addr = mock_socket.sendto.call_args[0]
        self.assertEqual(addr[1], 13122)

        # Validate packet format
        offer = unpack_offer(sent_bytes)
        self.assertEqual(offer.tcp_port, tcp_port)
        self.assertEqual(offer.server_name, server_name)


if __name__ == "__main__":
    unittest.main()
