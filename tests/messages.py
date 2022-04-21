# V1.43 messages

# PID advanced
# does not include feedforward data or vbat sag comp or thrust linearization
# pid_advanced = b"$M>2^\x00\x00\x00\x00x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x007\x00\xfa\x00\xd8\x0e\x00\x00\x00\x00\x01\x01\x00\n\x14H\x00H\x00H\x00\x00\x15\x1a\x00(\x14\x00\xc8\x0fd\x04\x00\xb1"
pid_advanced = b'$M>2^\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x007\x00\xfa\x00\xd8\x0e\x00\x00\x00\x00\x01\x01\x00\n\x14H\x00H\x00H\x00\x00\x15\x1a\x00(\x14\x00\xc8\x0fd\x04\x00\xb1'

# PID coefficient
pid = b"$M>\x0fp\x16D\x1f\x1aD\x1f\x1dL\x0457K(\x00\x00G"

fc_version = b"$M>\x03\x03\x01\x0c\x15\x18"
fc_version_2 = b"$M>\x03\x01\x00\x01\x15\x16"
api_version = b"$M>\x03\x01\x00\x01\x15\x16"


status_response = b"$M>\x16e}\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x1a\x04\x01\x01\x00\x004"
status_ex_response = (
    b"$M>\x16\x96}\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x05\x00\x03\x00\x00\x1a\x04\x01\x01\x00\x00\xc4"
)

rc_tuning = b"$M>\x17od\x00FFFA2\x00F\x05\x00dd\x00\x00d\xce\x07\xce\x07\xce\x07\x00\xc7"
rx_tuning2 = (
    b"$M>\x02l\x07\xdc\x05\x1a\x04\x00u\x03C\x08\x02\x13\xe2\x04\x00\x00\x00\x00\x00\x00(\x02\x01\x00\x00\x01\x03\x00"
)
