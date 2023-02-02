from bonfo.msp.message import Preamble

pre_size = Preamble.sizeof()


# Trim off preamble and CRC byte at end
def minus_preamble(msg):
    return msg[pre_size:-1]
