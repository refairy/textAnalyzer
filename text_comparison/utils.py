from .options import OPT


def printf(*args, **kwargs):
    # OPT['debug'] = True이면 출력한다.
    if OPT['debug']:
        print(*args, **kwargs)


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


def index_else_it(l: list, i):
    # l.index(i)를 반환한다. 만약 i not in l일 경우 i를 그대로 반환한다.
    # ex) f([1,2,3], 2) -> 1
    #     f([1,2,3], 'a') -> 'a'
    try:
        return l.index(i)
    except ValueError:
        return i


def get_prep(word: str) -> str:
    # word의 전치사를 반환한다.
    # ex) f('at the park') -> 'at'
    prep = word.split()[0]
    for i, group in enumerate(OPT['prep_groups']):
        if prep in group:
            return i
    return prep


def untoken(l: list) -> str:
    # list -> flatten() -> ' '.join()
    # ex) f(['I', 'have', ['a', 'dream']]) -> 'I have a dream'
    return ' '.join(flatten(l))
