from copy import deepcopy
from ..koreanfacts.api import FactsDB
from .options import OPT
from .sentence_comp import comp_with, comp_add_with, comp_ner_with
from .utils import flatten, flatten_overlapped_list, slice_list, printf, flatten

"""
<문장 비교 순서>
1. 주어 비교
2. 동사 비교
3. 목적어 비교 (목적어 = inform[2:])
"""


def compare_mean(main: str, sentences: list, _type: str = 'subj') -> list:
    # main_subj : 메인
    # sentences : 비교할 대상
    # main이랑 sentences랑 각각 비교하여 비슷한 주어만 해당 인덱스 반환
    # ex) f('She', ['Her', 'He', 'Mom'], 'subj') -> [0, 2]  # 'Her', 'Mom'만 비슷한 주어라는 뜻

    # 리스트 안에 리스트 있는 경우 -> flatten 후 ' '.join
    sentences = flatten_overlapped_list(sentences)
    main = flatten_overlapped_list([main])[0]

    # 유사도 계산
    comp_result = comp_with(main, sentences)
    printf(main, sentences, comp_result)

    # 기준에 맞춰 필터링
    min_sim = OPT['min_{}_sim'.format(_type)]

    return [i for i, (sim, subj) in enumerate(comp_result) if sim >= min_sim]


def compare_add(main: list, adds: list) -> bool:
    # main의 추가 정보와 adds의 추가 정보를 비교하여 각각에 대해
    # 오류가 있는지 반환
    # main, adds는 각각 add (list[dict])
    return bool(sum([comp_add_with(main, add) for add in adds]))  # main에 대해 adds 추가정보 하나씩 비교


def only_similar(_main: str, sentences: list, ner_main: str = None, ner_sentences: list = None) -> list:
    # main과 의미 비슷한 sentence를 반환한다. <문장 비교 순서>를 따른다.

    # main과 구성요소 개수 똑같은 애들만 남기기 ex) main이 S + V 형식이라면 sentences도 같은 형식만 남기기
    printf([len(i) for i in sentences])
    printf(sentences)
    sentences = [i for i in sentences if min(len(i), 3) == min(len(_main), 3)]
    ner_sentences = [ner_sentences[i] for i in range(len(sentences)) if min(len(sentences[i]), 3) == min(len(_main), 3)]
    printf(sentences)

    # 1. 주어
    indexes = compare_mean(_main[0], [i[0] for i in sentences], 'subj')
    sentences = slice_list(sentences, indexes)
    ner_sentences = slice_list(ner_sentences, indexes)

    if len(_main) == 1:
        # 주어만 있는 문장이면
        return sentences

    # 2. 동사
    indexes = compare_mean(_main[1], [i[1] for i in sentences], 'verb')
    sentences = slice_list(sentences, indexes)
    ner_sentences = slice_list(ner_sentences, indexes)

    if len(_main) == 2:
        # S + V 문장이면
        return sentences

    # 3. 목적어 (inform[2:])
    if ner_main:
        # 개체명은 문맥 고려 대상에서 제외하기 위해 일반화한 문장으로 대체
        _main[2] = ' '.join(flatten(ner_main))
        del _main[3:]
    if ner_sentences:
        # 개체명은 문맥 고려 대상에서 제외하기 위해 일반화한 문장으로 대체
        back_sentences = deepcopy(sentences)
        for i in range(len(sentences)):
            sentences[i][2] = ' '.join(flatten(ner_sentences[i]))
            del sentences[i][3:]
    indexes = compare_mean(_main[2:], [i[2:] for i in sentences], 'obj')
    sentences = slice_list(sentences, indexes)

    try:
        # 만약 일반화한 문장으로 대체했을 경우 원래 sentences로 바꿔서 반환하기
        sentences = slice_list(back_sentences, indexes)
        del back_sentences
    except NameError:
        pass

    # 결과 반환
    return sentences


def compare(main: dict, sentences: dict):
    # main과 sentences를 비교한다.
    # type은 db에 저장돼 있는 dict 그대로이다.

    # 비슷한 의미의 데이터 추리기 (=비교할 데이터)
    printf("main:", main)
    nexts = only_similar(deepcopy(main['info']), [d['info'] for d in deepcopy(sentences)],
                         deepcopy(main['ner']), [d['ner'] for d in deepcopy(sentences)])
    if not nexts:
        return {'type': 'NO_SIMILAR_DATA'}  # 비교할 데이터가 없어서 비교 못 한다고 반환
    sentences = [d for d in sentences if d['info'] in nexts]

    printf("main:", main)
    printf(sentences)
    # 추가적인 정보 비교
    errors = []  # [True, False] -> [오류, 정상]
    for d in sentences:
        errors.append(compare_add(main['add'].copy(), d['add'].copy()))  # True or False

    printf("main:", main)
    printf('add compared errors:', errors)

    # 목적어구 내의 개체명 비교
    for i, d in enumerate(sentences):
        if not errors[i]:
            # error가 0이라면 (1이면 어차피 오류여서 이 검사를 진행할 필요 없으므로)
            errors[i] += comp_ner_with(main.copy(), d.copy())

    basis = []
    for i in range(len(errors)):
        if errors[i]:
            sen = sentences[i]['info']
            if 'A-NOT' in [d['ner'] for d in sentences[i]['add']]:
                # not이 있다면? -> 동사구 마지막에 'not' 추가
                try:
                    sen[1] += ' not'
                except IndexError:
                    # 동사구가 없을 수도 있음
                    pass
            basis.append(sen)

    # 결과 반환
    if not basis:
        return {'type': 'CORRECT'}  # 오류가 없는 경우
    return {'type': 'ERROR', 'basis': basis}  # errors[i]=True인 sentence만 반환


if __name__ == "__main__":
    db = FactsDB('../koreanfacts/db')  # db 연결 (KoreanFactsDB)

    db.pprint(db.get('dokdo'))

    print(compare({
        'info': ['Dokdo', 'is', ['island', 'of', 'Korea']],
        'add': [],
        'ner': ['island', 'of', 'COUNTRY']
    }, db.get('dokdo')))

    print(compare({
        'info': ['Dokdo', 'is miscalled', ['Takeshima']],
        'add': [{'word': 'in Japan', 'lemma': 'in Japan', 'pos': ['IN', 'NNP'], 'ner': 'COUNTRY', 'normalizedNER': [None, None], 'timex': None}],
        'ner': ['Takeshima']
    }, db.get('dokdo')))

    print(compare({
        'info': ['Takeshima', 'is', [['inherent part', ['of', 'territory']], ['of', 'Japan']]],
        'add': [{'word': 'in Japan', 'lemma': 'of Japan', 'pos': ['IN', 'NNP'], 'ner': 'COUNTRY', 'normalizedNER': [None, None], 'timex': None}],
        'ner': ['Takeshima', 'is', ['inherent', 'part', 'of', 'territory', 'of', 'COUNTRY']]
    }, db.get('dokdo')))

    print(compare({
        'info': ['Dokdo', 'is', ['territory', 'of', 'Japan']],
        'add': [],
        'ner': ['territory', 'of', 'COUNTRY']
    }, db.get('dokdo')))

    print(compare_mean('She', ['Her', 'He', 'she', 'woman'], 'subj'))
    print(compare_mean('be forced', ['force', 'forced', 'forcing', 'compelled', 'compel', 'be compel'], 'verb'))
    print(compare_mean('to sex', ['into sexual slavery', 'to provide sex',
                                  'forcing', 'compelled', 'compel', 'be compel'], 'obj'))
    print(only_similar(['Comfort woman', 'forced', ['to', 'be', 'sex', 'slave']],
                       [['Comfort women', 'were', ['women']],
                       ['Comfort women', 'were', ['girls']],
                       ['Japan Times', 'promised', ['to', 'conduct', 'thorough', 'review', 'of', 'description'],
                        ['In', 'response']],
                       ['Japan Times', 'announce', ['Japan', 'Times', 'conclusions']],
                       ['Japan Times', 'described', ['comfort women', 'as',
                                                     'women who were forced to provide sex '
                                                     'to Japanese soldiers before and during World War II in 1930.']],
                       ['Comfort women', 'compelled', ['to', 'be', 'sex']],
                       ['Comfort women', 'forced', ['territories']]]
                       ))
    print(compare_add([{'word': 'in 1987', 'ner': 'NUMBER', 'normalizedNER': ['1.9'], 'timex':  None}],
                      [{'word': 'at 1986', 'ner': 'NUMBER', 'normalizedNER': ['1.9'], 'timex': None},
                       {'word': 'at January', 'ner': 'NUMBER', 'normalizedNER': ['>=200.0'], 'timex': None},
                       {'word': 'in Japan', 'ner': 'COUNTRY', 'normalizedNER': [None], 'timex': None}]))
