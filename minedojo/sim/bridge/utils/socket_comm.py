import struct


def send_message(sock, data):
    length = len(data)
    sock.sendall(struct.pack("!I", length))
    sock.sendall(data)


def recv_message(sock):
    lengthbuf = _recv_all(sock, 4)
    if not lengthbuf:
        return None
    (length,) = struct.unpack("!I", lengthbuf)
    return _recv_all(sock, length)


def _recv_all(sock, count):
    """
    receive all
    """
    buf = b""
    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf
