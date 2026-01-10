# common/protocol.py
"""
Application-layer protocol implementation for the Blackjack hackathon.

This module contains ONLY protocol concerns:
- constants (magic cookie, message types, lengths)
- pack/unpack functions for Offer / Request / Payload
- strict validation (cookie/type/length)
- recv_exact helper for TCP streams

It does NOT open sockets, does NOT implement game logic.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Optional


# =========================
# Constants (per spec)
# =========================

MAGIC_COOKIE = 0xABCDDCBA

TYPE_OFFER = 0x2
TYPE_REQUEST = 0x3
TYPE_PAYLOAD = 0x4

UDP_PORT_OFFER_LISTEN = 13122

NAME_LEN = 32
DECISION_LEN = 5

# Message lengths (bytes)
OFFER_LEN = 4 + 1 + 2 + NAME_LEN          # 39
REQUEST_LEN = 4 + 1 + 1 + NAME_LEN        # 38
PAYLOAD_CLIENT_LEN = 4 + 1 + DECISION_LEN # 10
PAYLOAD_SERVER_LEN = 4 + 1 + 1 + 3        # 9 (result + rank(2) + suit(1))

# Results (server -> client)
RESULT_NOT_OVER = 0x0
RESULT_TIE = 0x1
RESULT_LOSS = 0x2
RESULT_WIN = 0x3

# Decisions (client -> server)
DECISION_HIT = "Hittt"   # exactly 5 bytes
DECISION_STAND = "Stand" # exactly 5 bytes

# Suit encoding order (HDCS) - for your own consistency checks/logging
SUIT_H = 0
SUIT_D = 1
SUIT_C = 2
SUIT_S = 3


# =========================
# Exceptions
# =========================

class ProtocolError(ValueError):
    """Raised when a message does not match the protocol (cookie/type/length/etc.)."""


# =========================
# Data classes (optional, convenient)
# =========================

@dataclass(frozen=True)
class Offer:
    tcp_port: int
    server_name: str

@dataclass(frozen=True)
class Request:
    rounds: int
    team_name: str

@dataclass(frozen=True)
class ServerPayload:
    result: int
    rank: int  # 1..13 (encoded in 2 bytes)
    suit: int  # 0..3  (encoded in 1 byte)


# =========================
# Helpers: name/decision encoding
# =========================

def _encode_fixed_str(s: str, length: int) -> bytes:
    """
    Encode string to fixed-length bytes:
    - UTF-8 encoding
    - truncate to 'length'
    - pad with 0x00 up to 'length'
    """
    raw = s.encode("utf-8", errors="replace")
    raw = raw[:length]
    return raw + b"\x00" * (length - len(raw))

def _decode_fixed_str(b: bytes) -> str:
    """Decode fixed-length string by stripping trailing NULs and decoding as UTF-8."""
    b = b.split(b"\x00", 1)[0]
    return b.decode("utf-8", errors="replace")

def _validate_cookie_and_type(cookie: int, msg_type: int, expected_type: int) -> None:
    if cookie != MAGIC_COOKIE:
        raise ProtocolError(f"Bad magic cookie: 0x{cookie:08x}")
    if msg_type != expected_type:
        raise ProtocolError(f"Bad message type: 0x{msg_type:02x} (expected 0x{expected_type:02x})")

def _validate_port(port: int) -> None:
    if not (0 <= port <= 65535):
        raise ProtocolError(f"Invalid TCP port: {port}")

def _validate_rounds(rounds: int) -> None:
    if not (0 <= rounds <= 255):
        raise ProtocolError(f"Invalid rounds (must fit 1 byte): {rounds}")

def _validate_rank_suit(rank: int, suit: int) -> None:
    if not (1 <= rank <= 13):
        raise ProtocolError(f"Rank must be in range 1..13, got {rank}")
    if not (0 <= suit <= 3):
        raise ProtocolError(f"Suit must be in range 0..3, got {suit}")


# =========================
# Offer (UDP): pack/unpack
# Format: cookie(4) type(1) tcp_port(2) server_name(32)
# =========================

def pack_offer(tcp_port: int, server_name: str) -> bytes:
    _validate_port(tcp_port)
    name_bytes = _encode_fixed_str(server_name, NAME_LEN)
    return struct.pack("!IBH32s", MAGIC_COOKIE, TYPE_OFFER, tcp_port, name_bytes)

def unpack_offer(data: bytes) -> Offer:
    if len(data) != OFFER_LEN:
        raise ProtocolError(f"Bad offer length: {len(data)} (expected {OFFER_LEN})")
    cookie, msg_type, tcp_port, name_bytes = struct.unpack("!IBH32s", data)
    _validate_cookie_and_type(cookie, msg_type, TYPE_OFFER)
    _validate_port(tcp_port)
    return Offer(tcp_port=tcp_port, server_name=_decode_fixed_str(name_bytes))


# =========================
# Request (TCP): pack/unpack
# Format: cookie(4) type(1) rounds(1) team_name(32)
# =========================

def pack_request(rounds: int, team_name: str) -> bytes:
    _validate_rounds(rounds)
    name_bytes = _encode_fixed_str(team_name, NAME_LEN)
    return struct.pack("!IBB32s", MAGIC_COOKIE, TYPE_REQUEST, rounds, name_bytes)

def unpack_request(data: bytes) -> Request:
    if len(data) != REQUEST_LEN:
        raise ProtocolError(f"Bad request length: {len(data)} (expected {REQUEST_LEN})")
    cookie, msg_type, rounds, name_bytes = struct.unpack("!IBB32s", data)
    _validate_cookie_and_type(cookie, msg_type, TYPE_REQUEST)
    _validate_rounds(rounds)
    return Request(rounds=rounds, team_name=_decode_fixed_str(name_bytes))


# =========================
# Payload (TCP): pack/unpack
# Header: cookie(4) type(1)
# Client->Server payload body: decision(5 bytes): b"Hittt" or b"Stand"
# Server->Client payload body: result(1) + rank(2) + suit(1)  => total 4 bytes body, 9 total
# =========================

def pack_payload_decision(decision: str) -> bytes:
    if decision not in (DECISION_HIT, DECISION_STAND):
        raise ProtocolError(f"Decision must be '{DECISION_HIT}' or '{DECISION_STAND}', got: {decision!r}")
    decision_bytes = decision.encode("ascii", errors="strict")
    if len(decision_bytes) != DECISION_LEN:
        raise ProtocolError("Decision must be exactly 5 ASCII bytes")
    return struct.pack("!IB5s", MAGIC_COOKIE, TYPE_PAYLOAD, decision_bytes)

def unpack_payload_decision(data: bytes) -> str:
    if len(data) != PAYLOAD_CLIENT_LEN:
        raise ProtocolError(f"Bad client payload length: {len(data)} (expected {PAYLOAD_CLIENT_LEN})")
    cookie, msg_type, decision_bytes = struct.unpack("!IB5s", data)
    _validate_cookie_and_type(cookie, msg_type, TYPE_PAYLOAD)
    try:
        decision = decision_bytes.decode("ascii", errors="strict")
    except UnicodeDecodeError as e:
        raise ProtocolError("Decision payload is not valid ASCII") from e
    if decision not in (DECISION_HIT, DECISION_STAND):
        raise ProtocolError(f"Unknown decision value: {decision!r}")
    return decision

def pack_payload_server(result: int, rank: int, suit: int) -> bytes:
    if not (0 <= result <= 255):
        raise ProtocolError(f"Result must fit 1 byte: {result}")
    # Strict check as per spec (1..13 and 0..3); allow 0 if you want "no card" semantics.
    _validate_rank_suit(rank, suit)
    # card_value is 3 bytes: rank (2 bytes) + suit (1 byte)
    card_bytes = struct.pack("!HB", rank, suit)
    return struct.pack("!IBB3s", MAGIC_COOKIE, TYPE_PAYLOAD, result, card_bytes)

def unpack_payload_server(data: bytes) -> ServerPayload:
    if len(data) != PAYLOAD_SERVER_LEN:
        raise ProtocolError(f"Bad server payload length: {len(data)} (expected {PAYLOAD_SERVER_LEN})")
    cookie, msg_type, result, card_bytes = struct.unpack("!IBB3s", data)
    _validate_cookie_and_type(cookie, msg_type, TYPE_PAYLOAD)
    rank, suit = struct.unpack("!HB", card_bytes)
    _validate_rank_suit(rank, suit)
    return ServerPayload(result=result, rank=rank, suit=suit)


# =========================
# TCP helper: recv_exact
# =========================

def recv_exact(sock, n: int) -> bytes:
    """
    Receive exactly n bytes from a TCP socket.
    - Returns bytes of length n
    - Raises ConnectionError if the connection is closed before n bytes arrive
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError(f"Socket closed while expecting {remaining} more bytes")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)
