
def flatten(l: list) -> list:
    # l.reshape(-1)과 동일
    if not isinstance(l, list):
        return [l]
    r = []
    for i in l:
        if isinstance(i, list):
            r.extend(flatten(i))
        else:
            r.append(i)
    return r


def flatten_overlapped_list(l: list) -> list:
    # f(['Japan Times', 'promise', [['In', 'response']]]) -> ['Japan Times', 'promise', 'In response']
    r = []
    for i in l:
        if isinstance(i, list):
            r.append(' '.join(flatten(i)))
        else:
            r.append(i)
    return r


def slice_list(l: list, indexes: list) -> list:
    # ex) f([1,2,3,4], [0,2]) -> [1, 3]  # index 0, 2만 반환
    return [l[i] for i in indexes]
