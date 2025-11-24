import queue
from machine import UART as HWUART, Pin

class VirtualUART:
    """Simulates a UART with RX/TX queues."""

    def __init__(self):
        self.rx = queue.Queue()
        self.tx = queue.Queue()

    def write(self, data: bytes):
        """Place outgoing data into TX queue."""
        self.tx.put(data)

    def read(self, nbytes=1024):
        """Read incoming data from RX queue."""
        try:
            return self.rx.get_nowait()
        except queue.Empty:
            return None


class PYUART:
    """Unified interface for real UART or virtual UART."""

    def __init__(self, rx=17, tx=16, virtual=False, baudrate=9600):
        self.virtual = virtual

        if not virtual:
            # REAL HARDWARE UART
            self.rx_pin = Pin(rx)
            self.tx_pin = Pin(tx)
            self.uart = HWUART(0, baudrate=baudrate,
                               tx=self.tx_pin, rx=self.rx_pin)
        else:
            # VIRTUAL BACKEND
            self.uart = VirtualUART()

    def write(self, data: bytes):
        """Write to UART (real or virtual)."""
        return self.uart.write(data)

    def read(self, nbytes=1024):
        """Read from UART (real or virtual)."""
        data = self.uart.read(nbytes)
        return data.decode() if isinstance(data, (bytes, bytearray)) else ""

    def connect_virtual_pair(self, other: "PYUART"):
        """
        Connect two virtual UARTs so that TX of one goes to RX of the other.
        Both must be virtual.
        """
        if not (self.virtual and other.virtual):
            raise ValueError("Both UARTs must be virtual to pair.")

        # Wiring: A.tx -> B.rx, and B.tx -> A.rx
        other.uart.rx = self.uart.tx
        self.uart.rx = other.uart.tx
