try:
    from .options import OPT
    from .sentence_comp import comp_with
    from .utils import flatten, flatten_overlapped_list, slice_list
except:
    from options import OPT
    from sentence_comp import comp_with
    from utils import flatten, flatten_overlapped_list, slice_list

"""
<문장 비교 순서>
1. 주어 비교
2. 동사 비교
3. 목적어 비교 (목적어 = inform[2:])
"""


def compare(main: str, sentences: list, _type: str = 'subj') -> list:
    # main_subj : 메인
    # sentences : 비교할 대상
    # main이랑 sentences랑 각각 비교하여 비슷한 주어만 해당 인덱스 반환
    # ex) f('She', ['Her', 'He', 'Mom'], 'subj') -> [0, 2]  # 'Her', 'Mom'만 비슷한 주어라는 뜻

    # 리스트 안에 리스트 있는 경우 -> flatten 후 ' '.join
    sentences = flatten_overlapped_list(sentences)
    main = flatten_overlapped_list([main])[0]

    # 유사도 계산
    comp_result = comp_with(main, sentences)

    # 기준에 맞춰 필터링
    min_sim = OPT['min_{}_sim'.format(_type)]
    return [i for i, (sim, subj) in enumerate(comp_result) if sim >= min_sim]


def only_similar(main: str, sentences: list) -> list:
    # main과 의미 비슷한 sentence를 반환한다. <문장 비교 순서>를 따른다.

    # main과 구성요소 개수 똑같은 애들만 남기기 ex) main이 S + V 형식이라면 sentences도 같은 형식만 남기기
    sentences = [sentences[i] for i in sentences if min(len(i), 3) == min(len(main), 3)]
    print(sentences)

    # 1. 주어
    indexes = compare(main[0], [i[0] for i in sentences], 'subj')
    sentences = slice_list(sentences, indexes)

    if len(main) == 1:
        # 주어만 있는 문장이면
        return sentences

    # 2. 동사
    indexes = compare(main[1], [i[0] for i in sentences], 'verb')
    sentences = slice_list(sentences, indexes)

    if len(main) == 2:
        # S + V 문장이면
        return sentences

    # 2. 목적어 (inform[2:])
    indexes = compare(main[2:], [i[2:] for i in sentences], 'verb')
    sentences = slice_list(sentences, indexes)

    # 결과 반환
    return sentences


if __name__ == "__main__":
    print(compare('She', ['Her', 'He', 'she', 'woman'], 'subj'))
    print(compare('be forced', ['force', 'forced', 'forcing', 'compelled', 'compel', 'be compel'], 'verb'))
    print(compare('to sex', ['into sexual slavery', 'to provide sex',
                             'forcing', 'compelled', 'compel', 'be compel'], 'obj'))
