from construct import FuncPath

from bonfo.msp.fields.base import MSPFields


def zero_none_len(data):
    # TODO: please fix this, the rebuild shouldn't be passing the data class here.
    if isinstance(data, MSPFields):
        return len(data.get_struct().build(data))
    if data is None:
        return 0
    return len(data)


zero_none_len_ = FuncPath(zero_none_len)  # type: ignore
