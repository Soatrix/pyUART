import threading
import time

class UARTPacket:
    STX = b"\x02"
    ETX = b"\x03"
    SEP = b"|"

    @staticmethod
    def build(command: str, data: str = "") -> bytes:
        """
        Build a packet with optional data and checksum.
        """
        payload = command.encode()
        if data:
            payload += UARTPacket.SEP + data.encode()

        packet = UARTPacket.STX + payload + UARTPacket.ETX
        checksum = UARTPacket.checksum(payload)
        return packet + bytes([checksum])

    @staticmethod
    def parse(raw: bytes):
        """
        Parse a packet. Returns (command, data) if valid, else None.
        """
        if len(raw) < 3:
            return None

        if raw[0:1] != UARTPacket.STX or raw[-2:-1] != UARTPacket.ETX:
            return None

        payload = raw[1:-2]
        checksum = raw[-1]

        if UARTPacket.checksum(payload) != checksum:
            return None

        if UARTPacket.SEP in payload:
            command, data = payload.split(UARTPacket.SEP, 1)
            return command.decode(), data.decode()
        else:
            return payload.decode(), ""

    @staticmethod
    def checksum(payload: bytes) -> int:
        """Simple XOR checksum"""
        c = 0
        for b in payload:
            c ^= b
        return c

class CommandManager:
    def __init__(self, uart, poll_interval=0.01):
        """
        uart: FlexUART instance
        poll_interval: seconds to sleep between reads
        """
        self.uart = uart
        self.poll_interval = poll_interval
        self.handlers = {}  # command -> callback
        self.running = False
        self.thread = None
        self.incoming_buffer = b""

    def register_handler(self, command, callback):
        """
        callback: function(command: str, data: str)
        """
        self.handlers[command] = callback

    def send_command(self, command: str, data: str = ""):
        packet = UARTPacket.build(command, data)
        self.uart.write(packet)

    def start(self):
        """Start the background thread to read incoming packets"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._poll_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _poll_loop(self):
        """Continuously read UART and parse packets"""
        while self.running:
            chunk = self.uart.read()
            if chunk:
                self.incoming_buffer += chunk.encode() if isinstance(chunk, str) else chunk

                # Attempt to extract packets
                while True:
                    start_idx = self.incoming_buffer.find(UARTPacket.STX)
                    end_idx = self.incoming_buffer.find(UARTPacket.ETX)
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        raw_packet = self.incoming_buffer[start_idx:end_idx+2]  # includes STX..ETX
                        self.incoming_buffer = self.incoming_buffer[end_idx+2:]

                        parsed = UARTPacket.parse(raw_packet)
                        if parsed:
                            cmd, data = parsed
                            handler = self.handlers.get(cmd)
                            if handler:
                                try:
                                    handler(cmd, data)
                                except Exception as e:
                                    print(f"Handler error for {cmd}: {e}")
                        else:
                            print(f"Invalid packet: {raw_packet}")
                    else:
                        break
            time.sleep(self.poll_interval)
