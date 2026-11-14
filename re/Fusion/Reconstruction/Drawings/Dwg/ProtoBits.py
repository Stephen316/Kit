import struct


class Reader:
    def __init__(self, data, pos=0, limit=None):
        self.data = data
        self.pos = pos
        self.limit = len(data) * 8 if limit is None else limit

    def bits(self, count):
        end = self.pos + count
        if count < 0 or end > self.limit:
            raise ValueError('bit stream truncated at %d+%d > %d' % (self.pos, count, self.limit))
        if count == 0:
            return 0
        window = self.data[self.pos >> 3:(end + 7) >> 3]
        value = int.from_bytes(window, 'big') >> (-end & 7)
        self.pos = end
        return value & ((1 << count) - 1)

    def B(self):
        return self.bits(1)

    def BB(self):
        return self.bits(2)

    def B3(self):
        value = 0
        for _ in range(3):
            bit = self.bits(1)
            value = value << 1 | bit
            if not bit:
                break
        return value

    def RC(self):
        return self.bits(8)

    def raw(self, count):
        return bytes(self.bits(8) for _ in range(count))

    def RS(self):
        return struct.unpack('<H', self.raw(2))[0]

    def RL(self):
        return struct.unpack('<I', self.raw(4))[0]

    def RD(self):
        return struct.unpack('<d', self.raw(8))[0]

    def BS(self):
        code = self.bits(2)
        if code == 0:
            return self.RS()
        if code == 1:
            return self.RC()
        return 0 if code == 2 else 256

    def BL(self):
        code = self.bits(2)
        if code == 0:
            return self.RL()
        if code == 1:
            return self.RC()
        if code == 2:
            return 0
        raise ValueError('BL code 3')

    def BLL(self):
        count = self.B3()
        value = 0
        for index in range(count):
            value |= self.RC() << (8 * index)
        return value

    def BD(self):
        code = self.bits(2)
        if code == 0:
            return self.RD()
        if code == 1:
            return 1.0
        if code == 2:
            return 0.0
        raise ValueError('BD code 3')

    def DD(self, default):
        code = self.bits(2)
        if code == 0:
            return default
        packed = bytearray(struct.pack('<d', default))
        if code == 1:
            packed[0:4] = self.raw(4)
            return struct.unpack('<d', bytes(packed))[0]
        if code == 2:
            six = self.raw(6)
            packed[4:6] = six[0:2]
            packed[0:4] = six[2:6]
            return struct.unpack('<d', bytes(packed))[0]
        return self.RD()

    def BT(self):
        if self.B():
            return 0.0
        return self.BD()

    def BE(self):
        if self.B():
            return (0.0, 0.0, 1.0)
        return (self.BD(), self.BD(), self.BD())

    def MC(self):
        value = 0
        shift = 0
        while True:
            byte = self.RC()
            if byte & 0x80:
                value |= (byte & 0x7F) << shift
                shift += 7
                continue
            negative = byte & 0x40
            value |= (byte & 0x3F) << shift
            return -value if negative else value

    def UMC(self):
        value = 0
        shift = 0
        while True:
            byte = self.RC()
            value |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                return value

    def H(self):
        code = self.bits(4)
        counter = self.bits(4)
        value = 0
        for _ in range(counter):
            value = value << 8 | self.RC()
        return (code, counter, value)

    def TU(self):
        length = self.BS()
        raw = self.raw(2 * length)
        return raw.decode('utf-16-le', errors='surrogatepass')

    def TV(self):
        length = self.BS()
        return self.raw(length).decode('latin-1')

    def OT(self):
        code = self.bits(2)
        if code == 0:
            return self.RC()
        if code == 1:
            return self.RC() + 0x1F0
        return self.RS()


class Writer:
    def __init__(self):
        self.value = 0
        self.count = 0

    def bits(self, value, count):
        if count:
            self.value = (self.value << count) | (value & ((1 << count) - 1))
            self.count += count

    def extend(self, value, count):
        self.bits(value, count)

    def raw(self, data):
        for byte in data:
            self.bits(byte, 8)

    def tobytes(self):
        pad = -self.count & 7
        return (self.value << pad).to_bytes((self.count + pad) // 8, 'big')

    def B(self, v):
        self.bits(v, 1)

    def BB(self, v):
        self.bits(v, 2)

    def RC(self, v):
        self.bits(v, 8)

    def RS(self, v):
        self.raw(struct.pack('<H', v))

    def RL(self, v):
        self.raw(struct.pack('<I', v))

    def RD(self, v):
        self.raw(struct.pack('<d', v))

    def BS(self, v):
        if v == 0:
            self.bits(2, 2)
        elif v == 256:
            self.bits(3, 2)
        elif v < 256:
            self.bits(1, 2)
            self.RC(v)
        else:
            self.bits(0, 2)
            self.RS(v)

    def BL(self, v):
        if v == 0:
            self.bits(2, 2)
        elif v < 256:
            self.bits(1, 2)
            self.RC(v)
        else:
            self.bits(0, 2)
            self.RL(v)

    def BD(self, v):
        if v == 1.0 and struct.pack('<d', v) == struct.pack('<d', 1.0):
            self.bits(1, 2)
        elif struct.pack('<d', v) == struct.pack('<d', 0.0):
            self.bits(2, 2)
        else:
            self.bits(0, 2)
            self.RD(v)

    def H(self, ref):
        code, counter, value = ref
        self.bits(code, 4)
        self.bits(counter, 4)
        for index in reversed(range(counter)):
            self.RC(value >> (8 * index) & 0xFF)

    def TU(self, text):
        raw = text.encode('utf-16-le', errors='surrogatepass')
        self.BS(len(raw) // 2)
        self.raw(raw)

    def OT(self, v):
        if v < 0x1F0 and v <= 0xFF:
            self.bits(0, 2)
            self.RC(v)
        elif 0x1F0 <= v <= 0x2EF:
            self.bits(1, 2)
            self.RC(v - 0x1F0)
        else:
            self.bits(2, 2)
            self.RS(v)
