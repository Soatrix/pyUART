from ..command import *
from ..pyuart import *

# Virtual UART setup
pi_uart = PYUART(virtual=True)
pico_uart = PYUART(virtual=True)
pi_uart.connect_virtual_pair(pico_uart)

# Pico-side mock manager
def pico_led_handler(cmd, data):
    print(f"Pico received: {cmd} with data {data}")

pico_mgr = CommandManager(pico_uart)
pico_mgr.register_handler("LED_ON", pico_led_handler)
pico_mgr.start()

# Pi-side command sender
pi_mgr = CommandManager(pi_uart)
pi_mgr.send_command("LED_ON", "1")

# Allow some time for async processing
time.sleep(0.1)

pico_mgr.stop()
