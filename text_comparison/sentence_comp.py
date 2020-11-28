import tensorflow_hub as hub
from numpy import dot
from numpy.linalg import norm

from .options import OPT
from .utils import get_prep, untoken, flatten, printf
from .timex import TimeX
from .number import Number

print('load hub..')
embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder-large/5")
print('finish')


def cos_sim(A, B):
    # 코사인 유사도
    return dot(A, B)/(norm(A)*norm(B))


def comp_with(main, sentences):
    # main과 sentences의 문장을 비교한다.
    if not isinstance(main, str):
        raise TypeError("`main` must be a str type.")
    if not isinstance(sentences, list):
        sentences = [sentences]

    embeddings = embed([main] + sentences)
    main_emb = embeddings[0]
    sene_emb = embeddings[1:]

    result = [(cos_sim(embedding, main_emb), sen) for embedding, sen in zip(sene_emb, sentences)]
    return result


def comp_ner_with(data1, data2):
    # 개체명이 들어 있는 두 문장을 비교한다. (오류 여부 반환. 오류:True, 정상:False)
    # data1, data2 = DB에 저장되는 data

    data1['info'] = flatten(data1['info'][2:])
    data2['info'] = flatten(data2['info'][2:])
    data1['ner'] = flatten(data1['ner'])
    data2['ner'] = flatten(data2['ner'])
    while 'not' in data1['ner']:
        data1['ner'].remove('not')
    while 'not' in data2['ner']:
        data2['ner'].remove('not')

    if data1['info'] == data1['add'] or data2['info'] == data2['add']:
        # 둘 중 하나라도 개체명이 들어있지 않으면? -> 오류 아님
        return False

    isnot = ('A-NOT' in [d['ner'] for d in data1['add']]) ^ ('A-NOT' in [d['ner'] for d in data2['add']])

    # 내용이 완전히 같아야 하는 개체명은 여기서 계산
    number_cnt = 0
    for i in range(len(data2['ner'])):
        if data2['ner'][i] == 'NUMBER':
            data2['ner'][i] = data2['info'][i]
            number_cnt += 1
            tmp_cnt = 0
            for j in range(len(data1['ner'])):
                if data1['ner'][j] == 'NUMBER':
                    tmp_cnt += 1
                    data1['ner'][j] = data1['info'][j]
                    if tmp_cnt == number_cnt and data2['info'][i] != data1['info'][j]:
                        # 숫자가 다르다면?
                        return isnot - True  # True (not이 있다면 False)

    # 원본 문장끼리 비교 ex) 'territory of Japan' vs 'Koean territory'
    sim0 = comp_with(untoken(data1['info']), [untoken(data2['info'])])[0][0]  # 유사도

    # 개체명을 일반화한 문장끼리 비교 ex) 'territory of COUNTRY' vs 'COUNTRY territory'
    sim2 = comp_with(untoken(data1['ner']), [untoken(data2['ner'])])[0][0]  # 유사도

    printf('comp_ner A and B', data1['info'], data1['ner'], data2['info'], data2['ner'])
    printf('comp_ner_with sim diff:', abs(sim0 - sim2))

    if OPT['min_ner_sim_diff'] >= abs(sim0 - sim2):
        # 같은 문장
        return isnot - False  # False (not이 있다면 True)
    else:
        # 다른 문장 (개체명이 다름)
        return isnot - True  # True (not이 있다면 False)


def comp_add_with(add1: list, add2: dict):
    # 두 추가정보를 비교한다. add1이 사실이라고 가정하고 add2가 오류를 범했는지 여부를 반환한다.
    # True : 오류, False : 오류 아님

    isnot = ('A-NOT' in [d['ner'] for d in add1]) ^ ('A-NOT' == add2['ner'])  # 둘 중 하나에만 'not'이 들어있는가?

    def return_isnot(b: bool) -> bool:
        # isnot=True -> return not b
        # isnot=False -> return b
        if isnot:
            return not b
        else:
            return b

    i = add2
    prep = get_prep(i['word'])  # 전치사 (그룹이 있을 경우 그룹 index가 변수값임)
    if i.get('timex') is not None:
        prep = 'T'  # 시간을 나타낼 경우 전치사를 'T'로 지정
    if i.get('ner') == 'NUMBER':
        prep = 'N'
    for j in add1:
        jprep = get_prep(j['word'])  # 전치사
        if j.get('timex') is not None:
            jprep = 'T'  # 시간 나타낼 경우
        if j.get('ner') == 'NUMBER':
            jprep = 'N'
        if prep == jprep:
            # i와 j의 전치사가 일치한다면? -> 비교
            if jprep == 'T':
                # 시간을 나타낸다면? -> 단순 비교
                print('시간 단순 비교')
                printf(i.get('timex'), j.get('timex'))
                printf(TimeX(i.get('timex')), TimeX(j.get('timex')), TimeX(i.get('timex')) == TimeX(j.get('timex')))
                if TimeX(i.get('timex')) == TimeX(j.get('timex')):  # XXXX-08-12 == 1978-08-12 이런 것까지 고려
                    # 시간이 일치한다면? -> 오류 아님
                    pass
                else:
                    # 시간이 다르다면? -> 오류
                    if return_isnot(True):
                        return True
            elif jprep == 'N':
                # 숫자를 나타낸다면? -> 단순 비교
                printf('숫자 단순 비교')
                inormed = [t for t in i.get('normalizedNER') if t is not None][0]  # i의 normalizedNER ex) '>=200'
                jnormed = [t for t in j.get('normalizedNER') if t is not None][0]  # j의 normalizedNER ex) '100'
                printf(Number(inormed), Number(jnormed))
                if return_isnot(not Number(inormed) == Number(jnormed)):  # 비교
                    return True
            else:
                # 아니라면? -> 의미 비교
                printf('의미 비교')
                sim = comp_with(jprep, [prep])[0][0]  # 코사인 유사도
                if sim >= OPT['min_add_sim']:
                    # 의미 유사하다면? -> 오류 아님
                    pass
                else:
                    # 의미 다르다면? -> 오류
                    if return_isnot(True):  # 오류
                        return True
    #return return_isnot(False)
    return False  # 비교할 추가정보가 없을 때 혹은 모두 비교했으나 오류가 아닐 때


if __name__ == "__main__":
    sentences = [
        "dokdo is japanese territory",
        "dokdo is island of korea"
    ]

    print(comp_with('dokdo is korean territory', sentences))

    print(comp_with('territoriy of Country', ['Country territory']))
    print(comp_with('territoriy of Korea', ['Korean territory']))
    print(comp_with('territoriy of Japan', ['Korean territory']))

    print()
    print(comp_with('president of Country', ['Country president']))
    print(comp_with('president of Korea', ['Korean president']))
    print(comp_with('president of Japan', ['Korean president']))
