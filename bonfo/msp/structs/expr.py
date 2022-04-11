from construct import FuncPath


def zero_none_len(data):
    if data is None:
        return 0
    return len(data)


zero_none_len_ = FuncPath(zero_none_len)  # type: ignore
