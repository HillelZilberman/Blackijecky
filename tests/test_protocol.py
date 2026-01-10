import unittest

from common.protocol import (
    pack_offer, unpack_offer,
    pack_request, unpack_request,
    pack_payload_decision, unpack_payload_decision,
    pack_payload_server, unpack_payload_server,
    ProtocolError,
    DECISION_HIT, DECISION_STAND,
    RESULT_NOT_OVER,
)

class TestProtocol(unittest.TestCase):
    def test_offer_roundtrip(self):
        b = pack_offer(2048, "MyServer")
        offer = unpack_offer(b)
        self.assertEqual(offer.tcp_port, 2048)
        self.assertEqual(offer.server_name, "MyServer")

    def test_request_roundtrip(self):
        b = pack_request(7, "TeamX")
        req = unpack_request(b)
        self.assertEqual(req.rounds, 7)
        self.assertEqual(req.team_name, "TeamX")

    def test_payload_decision_roundtrip(self):
        b = pack_payload_decision(DECISION_HIT)
        d = unpack_payload_decision(b)
        self.assertEqual(d, DECISION_HIT)

        b2 = pack_payload_decision(DECISION_STAND)
        d2 = unpack_payload_decision(b2)
        self.assertEqual(d2, DECISION_STAND)

    def test_payload_server_roundtrip(self):
        b = pack_payload_server(RESULT_NOT_OVER, rank=13, suit=3)
        p = unpack_payload_server(b)
        self.assertEqual(p.result, RESULT_NOT_OVER)
        self.assertEqual(p.rank, 13)
        self.assertEqual(p.suit, 3)

    def test_invalid_decision_rejected(self):
        with self.assertRaises(ProtocolError):
            pack_payload_decision("hit")  # wrong value / length

    def test_invalid_rank_rejected(self):
        with self.assertRaises(ProtocolError):
            pack_payload_server(0, rank=0, suit=0)  # rank must be 1..13

        with self.assertRaises(ProtocolError):
            pack_payload_server(0, rank=14, suit=0)

    def test_invalid_suit_rejected(self):
        with self.assertRaises(ProtocolError):
            pack_payload_server(0, rank=1, suit=4)  # suit must be 0..3


if __name__ == "__main__":
    unittest.main()
