import nltk
from nltk.stem.wordnet import WordNetLemmatizer
from koreanfacts.api import FactsDB
try:
    from .options import *
    from .string_utils import StringUtils
    from .coreference import Coref
    from .corenlp_api import parse_api
    from .test_cases import text
except:
    from options import *
    from string_utils import StringUtils
    from coreference import Coref
    from corenlp_api import parse_api
    from test_cases import text


class Analyzer(StringUtils):
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.lemmatize = self.lemmatize_func

        self.cp = nltk.RegexpParser(grammar)  # grammar parser
        self.coref = Coref()  # 대명사 제거

        self.debug = True

    def analyze(self, sentence):
        # sentence를 분석한다.
        if self.is_bad_sentence(sentence):
            # 예외 문장일 경우
            return -1

        sentence = self.coref(sentence)  # 대명사 제거 (neuralcoref를 이용하여 대명사를 바꾼다)
        sentence = self.absolute_replace(sentence)  # 사전에 정의한 규칙대로 replace
        sentence, quotes = self.mask_quotes(sentence)  # 따옴표 내용 제거 (따옴표 내용은 QUITE{i} 형식으로 마스킹됨)
        # tags = self.get_tags(sentence)  # 품사 태깅
        tokens, api_tags = parse_api(sentence)
        tokens = self.totally_flatten(tokens)
        tags = self.get_tags(tokens=tokens)  # 품사 태깅
        tags = self.absolute_replace_tag(tags)
        chunks = self.chunk(tags)  # 개체명 인식
        tags = self.zip_like(tags, api_tags)
        tags = self.remove_pos(tags, drops)  # 특정 품사 제거
        a = self.cp.parse([i[0] for i in tags])  # grammar 파싱
        if self.debug:
            a.draw()

        self.printf('a:', a)

        # 구 나누기
        get_result = self.get(a)
        phrases = self.get2(get_result)[0]  # 최종 phrase
        poses = self.get2(self.get_tag(a), tag=True)[0]  # 최종 phrase의 품사
        self.printf('ne_chunk:', chunks)
        self.printf('phrases:', phrases)
        self.printf('poses:', poses)
        # list_like ex) ([1,2,3,4], [1,3,2,3,6,7,4]) -> [1,2,3,4]
        api_tags = self.list_like(self.totally_flatten(phrases), api_tags, key=lambda x: x['word'])

        poses = self.zip_like(poses, api_tags)  # poses 형태 : [['NP', ({},)], ['VP', ({},)]]

        # 절 나누기 (conjs: 접속사 목록)
        clauses, poses, conjs = self.phrases_split(phrases, poses, 'S')
        self.printf(clauses)
        self.printf(conjs)
        self.printf(len(clauses), len(conjs))

        # 특정 품사 포함한 절 제거
        clauses, poses, conjs = self.clauses_remove(clauses, poses, conjs)

        self.printf(conjs)
        self.printf('  /  '.join([str(i) for i in clauses[0]]))
        self.printf(poses)

        # ['NP', 'VP', ['NP', 'A-TIME']] 처럼 리스트에 여러 품사가 묶여 있는 경우 대표 품사 하나만 남김.
        repreposes = self.get_repreposes(poses)

        self.printf('//////////////////////////////')
        self.printf(clauses)
        self.printf(poses)
        self.printf(repreposes)
        self.printf(conjs)
        self.printf('//////////////////////////////')

        # 여러 절의 종속 관계 등을 고려하여 의미 관계 추출 (가장 중요한 과정)
        clauses, poses, repreposes, additions, addition_poses = \
            self.normalize_clauses(clauses, poses, repreposes, conjs)

        self.printf('clauses:', clauses)
        self.printf('poses:', poses)
        self.printf('repreposes:', repreposes)

        # 중복 제거
        clauses, poses, repreposes, additions, addition_poses = \
            self.unique(clauses, poses, repreposes, additions, addition_poses)

        # 출력
        for i in clauses:
            self.printf(i)

        # A = B이고 B = C이면 A = C라는 논리 적용하여 정보 확장
        self.substitute_equal(clauses, poses, repreposes, additions, addition_poses)

        # 중복 제거
        clauses, poses, repreposes, additions, addition_poses = \
            self.unique(clauses, poses, repreposes, additions, addition_poses)

        # 따옴표 제거했던 것 복원
        clauses = self.recover_quotes(clauses, quotes)

        self.printf('=-===================')
        for i in range(len(clauses)):
            self.printf(clauses[i])
            self.printf(additions[i])
            self.printf(addition_poses[i])

        # 개체명 들어간 정보만 남기기
        clauses, poses, repreposes, additions, addition_poses = \
            self.only_ne(clauses, poses, repreposes, additions, addition_poses, chunks)

        self.printf('=+===================')
        for i in range(len(clauses)):
            self.printf(clauses[i])
            self.printf(additions[i])
            self.printf(addition_poses[i])

        if self.debug:
            a.draw()

        return clauses, poses, repreposes, additions, addition_poses

    @staticmethod
    def unique(*lists):
        # lists의 중복을 제거한다 (순서는 유지한 채, lists[0]를 기준으로 중복 제거)
        r = []
        trues = []
        for i in range(len(lists[0])):
            trues.append(not lists[0][i] in lists[0][:i])
        for i in range(len(lists)):
            tmp = []
            for j in range(len(lists[i])):
                if trues[j]:
                    tmp.append(lists[i][j])
            r.append(tmp)
        return r

    def only_ne(self, clauses, poses, repreposes, additions, addition_poses, chunks):
        # 개체명이 들어간 clauses만 반환
        r = {
            'clauses': [], 'poses': [], 'repreposes': [], 'additions': [], 'addition_poses': []
        }
        for i in range(len(clauses)):
            passed = False  # True면 해당 clause에 개체명이 포함돼 있다는 뜻
            for j in range(len(clauses[i])):
                passed += sum([k in chunks for k in ' '.join(self.totally_flatten(clauses[i][j])).split()])
            if passed:
                r['clauses'].append(clauses[i])
                r['poses'].append(poses[i])
                r['repreposes'].append(repreposes[i])
                r['additions'].append(additions[i])
                r['addition_poses'].append(addition_poses[i])
        return r['clauses'], r['poses'], r['repreposes'], r['additions'], r['addition_poses']

    @staticmethod
    def substitute_equal(clauses, poses, repreposes, additions, addition_poses):
        # A be B, B be C -> A be C 같은 논리를 적용햐여 'be'라는 동사를 갖는 clauses들끼리 대입한다.
        r = {
            'clauses': [], 'poses': [], 'repreposes': [], 'additions': [], 'addition_poses': []
        }
        for i in range(len(clauses)):
            if len(clauses[i]) < 3:
                continue
            if clauses[i][1] in linking_verbs:
                # A be B 형식인가?
                a, b = clauses[i][0], clauses[i][2]
                for j in range(len(clauses)):
                    if i == j:
                        continue
                    for k in range(len(clauses[j])):
                        if clauses[j][k] == a:
                            target = clauses[j].copy()
                            target[k] = b
                            r['clauses'].append(target.copy())
                            target = poses[j].copy()
                            target[k] = poses[i][2]
                            r['poses'].append(target.copy())
                            target = repreposes[j].copy()
                            target[k] = repreposes[i][2]
                            r['repreposes'].append(target.copy())
                            target = additions[j].copy()
                            r['additions'].append(target.copy())
                            target = addition_poses[j].copy()
                            r['addition_poses'].append(target.copy())
                        elif clauses[j][k] == b:
                            target = clauses[j].copy()
                            target[k] = a
                            r['clauses'].append(target.copy())
                            target = poses[j].copy()
                            target[k] = poses[i][0]
                            r['poses'].append(target.copy())
                            target = repreposes[j].copy()
                            target[k] = repreposes[i][0]
                            r['repreposes'].append(target.copy())
                            target = additions[j].copy()
                            r['additions'].append(target.copy())
                            target = addition_poses[j].copy()
                            r['addition_poses'].append(target.copy())
        # 결과 적용하여 반환
        clauses += r['clauses']
        poses += r['poses']
        repreposes += r['repreposes']
        additions += r['additions']
        addition_poses += r['addition_poses']
        return clauses, poses, repreposes, additions, addition_poses

    def normalize_clauses(self, clauses, poses, repreposes, conjs):
        # 'S'를 기준으로 나눈 절들을 정리한다. (주요 알고리즘)
        def get_ai(l, i, d=1):
            # 바로 다음 원소 인덱스 반환. 바로 다음 원소가 None일 경우 다다음 원소를 선택하는 index 반환
            # d=1 : 다음 원소 방향으로 검색    d=-1 : 이전 원소 방향으로 검색
            # ex) f([0,1,None,2,3], 1) -> 3 (index 2는 None이므로 3 반환)
            ai = d
            try:
                while not l[i+ai]:
                    ai += d
            except IndexError:
                return None
            return ai

        r_clauses = clauses.copy()  # 절
        r_poses = poses.copy()  # 품사
        r_repreposes = repreposes.copy()  # 대표 품사
        r_additions = [[] for _ in range(len(clauses))]  # 추가적인 정보
        r_addition_poses = [[] for _ in range(len(clauses))]  # 추가적인 정보의 품사
        remove_i = []
        for i in range(len(clauses)):
            clause = r_clauses[i]
            pos = r_poses[i]
            reprepos = repreposes[i]

            ai = get_ai(r_clauses, i, -1)
            if i > 0 and not conjs[i+ai] == '.':
                # 앞 문장 탐색 (<-)
                if pos_group[reprepos[0]] in ['V', 'N'] and len(reprepos) == 1:
                    # <... , [현재동사구]> -> 앞 문장의 동사구.replace( 현재동사구)
                    # <... and [현재동사구]> -> 앞 문장의 동사구.replace( 현재동사구)
                    # ex) I ate cake and bread -> I ate bread.
                    # ex) I ate cake, cookies, bread -> I ate bread.
                    target_idx = [pos_group[j] for j in r_repreposes[i + ai]]

                    if not target_idx.count('V') == 0 and target_idx.count('N') >= 2:
                        # 앞 문장에 명사구 두 개, 동사구 하나는 꼭 있어야 함
                        target_idx = -list(reversed(target_idx))\
                            .index(pos_group[reprepos[0]]) - 1  # 앞 문장의 마지막 동/명사구 index
                        target = r_clauses[i + ai].copy()  # 앞 문장 복사
                        target[target_idx] = clause[0]
                        r_clauses[i] = target.copy()
                        target = r_poses[i + ai].copy()  # 앞 문장 복사
                        target[target_idx] = pos[0]
                        r_poses[i] = target.copy()
                        target = r_repreposes[i + ai].copy()  # 앞 문장 복사
                        target[target_idx] = reprepos[0]
                        r_repreposes[i] = target.copy()
                        r_additions[i] += r_additions[i + ai].copy()  # 앞 문장 복사
                        r_addition_poses[i] += r_addition_poses[i + ai].copy()  # 앞 문장 복사
                elif pos_group[reprepos[0]] == 'V' and len(reprepos) >= 2:
                    # <... , [현재동사구] ...> -> 앞 문장의 주어 가져오기
                    # <... and [현재동사구] ...> -> 앞 문장의 주어 가져오기
                    # ex) I ate cake and cooked bread. -> I cooked bread.
                    modified = False
                    if conjs[i+ai-1] in relatives:
                        # 앞 문장이 관계대명사절이었다면 -> 앞앞 문장으로
                        ai += -1
                        modified = True
                    target_idx = [pos_group[j] for j in r_repreposes[i + ai]]

                    if target_idx.count('N') >= 1:  # 앞 문장에 명사구, 동사구 하나는 꼭 있어야 함
                        target_idx = target_idx.index('N')  # 앞 문장의 첫번째 명사구 index
                        target = r_clauses[i + ai][target_idx]  # 앞 문장 주어 (첫째 명사구)

                        r_clauses[i] = [target] + clause
                        r_poses[i] = [r_poses[i + ai][target_idx]] + pos
                        r_repreposes[i] = [r_repreposes[i + ai][target_idx]] + reprepos
                        r_additions[i] += r_additions[i + ai].copy()  # 앞 문장 복사
                        r_addition_poses[i] += r_addition_poses[i + ai].copy()  # 앞 문장 복사
                    if modified:
                        # 관계대명사절이어서 한 문장 건너뛰었으면 다시 ai 되돌리기
                        ai += 1
                if conjs[i+ai] in relatives:  # 앞 문장을 탐색하는 것이므로 conjs도 앞엣것을 기준으로 계산해야 함.
                    if pos_group[reprepos[0]] == 'V':
                        # <... [명사구] that [현재동사구] ...> -> 앞 문장의 명사구를 주어로
                        # ex) I like cake that is made of chocolate
                        target_idx = [pos_group[j] for j in r_repreposes[i + ai]]

                        if not target_idx.count('N') == 0:  # 앞 문장에 명사구가 없으면? -> 패스
                            target_idx = -list(reversed(target_idx)).index('N') - 1  # 앞 문장의 마지막 명사구 index
                            target = r_clauses[i + ai][target_idx]  # 앞 문장 명사구
                            r_clauses[i] = [target] + clause
                            r_poses[i] = [r_poses[i + ai][target_idx]] + pos
                            r_repreposes[i] = [r_repreposes[i + ai][target_idx]] + reprepos
                    if len(reprepos) >= 2 and pos_group[reprepos[0]] == 'N' and pos_group[reprepos[1]] == 'V':
                        if not (len(reprepos) >= 3 and pos_group[reprepos[2]] == 'N'):  # <that 명사구 동사구 명사구> 형태라면? -> 패스
                            # <... [명사구] that [현재명사구] [현재동사구] ...> -> 앞 문장의 명사구를 주어로
                            # ex) I like cake that is made of chocolate
                            target_idx = [pos_group[j] for j in r_repreposes[i + ai]]
                            current_idx = [pos_group[j] for j in r_repreposes[i]]

                            if not target_idx.count('N') == 0:  # 앞 문장에 명사구가 없으면? -> 패스
                                target_idx = -list(reversed(target_idx)).index('N') - 1  # 앞 문장의 마지막 명사구 index
                                target = r_clauses[i + ai][target_idx]  # 앞 문장 명사구
                                current_idx = current_idx.index('V')  # 현재 문장의 첫번째 동사구 index
                                r_clauses[i] = clause[:current_idx+1] + [target] + clause[current_idx+1:]
                                r_poses[i] = pos[:current_idx+1] + [r_poses[i + ai][target_idx]] + pos[current_idx+1:]
                                r_repreposes[i] = \
                                    reprepos[:current_idx+1] + [r_repreposes[i + ai][target_idx]] + \
                                    reprepos[current_idx+1:]

            ai = get_ai(r_clauses, i, 1)
            if i < len(clauses) - 1 and not conjs[i] == '.':
                # 뒷 문장 탐색 (->)
                if conjs[i] == ',':
                    if pos_group[reprepos[0]] == 'N' and len(reprepos) == 1:
                        # <[현재명사구], [명사구] ...> ->  현재명사구 | be | 명사구
                        target_idx = [pos_group[j] for j in r_repreposes[i + ai]]

                        if reprepos[0] == 'INNP' and not target_idx.count('N') == 0 and not target_idx.count('V') == 0:
                            # 주어, 동사 다 있고, 현재 명사구가 전치사 명사구라면? -> 다음 문장 뒤로 옮기기
                            # ex) In 1987, I have ... -> I have ... in 1987
                            r_clauses[i+ai].extend(r_clauses[i])
                            r_poses[i+ai].extend(r_poses[i])
                            r_repreposes[i+ai].extend(r_repreposes[i])
                            r_clauses[i] = r_poses[i] = r_repreposes[i] = None
                            remove_i.append(i - len(remove_i))
                        elif not target_idx.count('N') == 0:  # 앞 문장에 명사구가 없으면? -> 패스
                            target_idx = -list(reversed(target_idx)).index('N') - 1  # 앞 문장의 마지막 명사구 index
                            print(clause)
                            target = r_clauses[i + ai][target_idx]  # 앞 문장 명사구
                            r_clauses[i] = [target, 'be', clause[0]]
                            r_poses[i] = [r_poses[i + ai][target_idx], 'VP', pos[0]]
                            r_repreposes[i] = [r_repreposes[i + ai][target_idx], 'VP', reprepos[0]]
                if conjs[i] == 'and':
                    if pos_group[reprepos[0]] in ['V', 'N'] and len(reprepos) == 1:
                        # <[현재명사구] and [명사구] ...> -> 앞 문장의 명사구.replace( 현재명사구)
                        # ex) He and I will go to the shop.
                        target_idx = [pos_group[j] for j in r_repreposes[i + ai]]

                        if not target_idx.count('V') == 0 and target_idx.count('N') >= 2:
                            # 앞 문장에 명사구 두 개, 동사구 하나는 꼭 있어야 함
                            target_idx = target_idx.index(pos_group[reprepos[0]])  # 앞 문장의 첫번째 동/명사구 index
                            target = r_clauses[i + ai].copy()  # 앞 문장 복사
                            target[target_idx] = clause[0]
                            r_clauses[i] = target.copy()
                            target = r_poses[i + ai].copy()  # 앞 문장 복사
                            target[target_idx] = pos[0]
                            r_poses[i] = target.copy()
                            target = r_repreposes[i + ai].copy()  # 앞 문장 복사
                            target[target_idx] = reprepos[0]
                            r_repreposes[i] = target.copy()
                            r_additions[i] += r_additions[i + ai].copy()  # 앞 문장 복사
                            r_addition_poses[i] += r_addition_poses[i + ai].copy()  # 앞 문장 복사

            # 추가적인 정보 처리
            # 추가적인 정보 기준 : 전치사 + 개체명 ex) in 1987 (전치사 in, 개체명 1987)
            clause = r_clauses[i]
            pos = r_poses[i]
            reprepos = r_repreposes[i]
            if reprepos:
                remove_j = []
                for j, reprep in enumerate(reprepos):
                    if j >= 2:
                        # 목적어구일 때 (주어, 동사구에는 해당X)
                        if len(clauses) == j or len(pos) == j:
                            # 리스트 모두 돌았다면 (중간에 del할 수 있으므로 이렇게 따로 지정해줘야 함)
                            break

                        bio = self.get_bio(pos[j])  # 개체명 인식을 기반으로 bio 만들고 추가적인 정보 추출
                        # bio = (추가적인 정보를 제외하고 남은 것들, bio[0]의 pos, 추가적인 정보)
                        if bio[0]:
                            r_clauses[i][j] = bio[0]
                        else:
                            # 추가적인 정보를 제외하고 남은 게 하나도 없으면 -> 그냥 삭제
                            del r_clauses[i][j]
                        if bio[0]:
                            r_poses[i][j] = bio[1]
                        else:
                            # 추가적인 정보를 제외하고 남은 게 하나도 없으면 -> 그냥 삭제
                            del r_poses[i][j]
                        r_additions[i].extend(bio[2])
                        clause = r_clauses[i]
                        pos = r_poses[i]

                    if pos_group[reprep] == 'A':
                        r_additions[i].append({
                            'word': ' '.join(clause[j]),   # 단어 ex) 'in 1987'
                            'lemma': ' '.join(clause[j]),  # 원형 ex) 'in 1987'
                            'pos': 'NP',                   # 품사 (형식적으로 존재함. NP로 고정)
                            'ner': reprep,                 # 개체명 ex) 'DATE'
                            'normalizedNER': [None],       # 수정된 개체명 (형식적으로 존재함. None으로 고정)
                            'timex': None                  # 개체명이 시간일 경우 x 표현식으로 표현된 시간 (형식적으로 존재함. None으로 고정)
                        })
                        r_clauses[i][j] = None
                        r_poses[i][j] = None
                        r_repreposes[i][j] = None
                        remove_j.append(j - len(remove_j))

                # 값이 None인 단어는 제거
                for j in remove_j:
                    del r_clauses[i][j]
                    del r_poses[i][j]
                    del r_repreposes[i][j]

            self.printf('====', i)
            self.printf(r_clauses)
            self.printf(r_poses)
            self.printf(r_repreposes)
            self.printf(r_additions)
            self.printf(r_addition_poses)

        # 값이 None인 절은 제거
        for i in remove_i:
            del r_clauses[i]
            del r_poses[i]
            del r_repreposes[i]
            del r_additions[i]
            del r_addition_poses[i]

        return r_clauses, r_poses, r_repreposes, r_additions, r_addition_poses


if __name__ == "__main__":
    db = FactsDB(port=27017)  # db 연결 (MongoDB)
    anal = Analyzer()  # 텍스트 분석기
    result = anal.analyze(text)  # 분석

    for i in range(len(result[0])):
        # 결과 DB에 저장 및 출력
        d = {}
        tmp = [result[j][i] for j in range(len(result))]
        db.insert({'group': 'dokdo', 'info': tmp[0], 'add': tmp[3]})  # 저장
        [print(i) for i in tmp]  # 출력

    # 위 작업 한 번 더 반복
    text = 'Dokdo which is erroneously called Takeshima in Japan until now, ' \
           'isn\'t Korean territory. The Liancourt Rocks are a group of small islets in the Sea of Japan. ' \
           'While South Korea controls the islets, its sovereignty over them is contested by Japan.'
    result = anal.analyze(text)  # 분석

    for i in range(len(result[0])):
        # 결과 DB에 저장 및 출력
        d = {}
        tmp = [result[j][i] for j in range(len(result))]
        db.insert({'group': 'dokdo', 'info': tmp[0], 'add': tmp[3]})  # 저장
        [print(i) for i in tmp]  # 출력

    db.pprint(db.find())  # DB 출력
    db.delete()  # DB 초기화
