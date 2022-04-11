from bonfo.msp.codes import MSP

struct_map = dict()


def msp_code(code: MSP, struct):
    # TODO: direction
    struct._msp_code = code
    struct_map[code] = struct
    return struct
