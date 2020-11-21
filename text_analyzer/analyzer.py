import nltk
from nltk.chunk import ne_chunk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet
import re
try:
    from .options import *
    from .string_utils import StringUtils
    from .coreference import Coref
except:
    from options import *
    from string_utils import StringUtils
    from coreference import Coref


class Analyzer(StringUtils):
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.lemmatize = self.lemmatize_func

        self.cp = nltk.RegexpParser(grammar)  # grammar parser
        self.coref = Coref()  # 대명사 제거

        self.debug = False

    def analyze(self, sentence):
        # sentence를 분석한다.
        if self.is_bad_sentence(sentence):
            # 예외 문장일 경우
            return -1

        sentence = self.coref(sentence)  # 대명사 제거 (neuralcoref를 이용하여 대명사를 바꾼다)
        sentence = self.absolute_replace(sentence)  # 사전에 정의한 규칙대로 replace
        sentence, quotes = self.mask_quotes(sentence)  # 따옴표 내용 제거 (따옴표 내용은 QUITE{i} 형식으로 마스킹됨)
        tags = self.get_tags(sentence)  # 품사 태깅
        tags = self.absolute_replace_tag(tags)
        chunks = self.chunk(tags)  # 개체명 인식
        tags = self.remove_pos(tags, drops)  # 특정 품사 제거
        a = self.cp.parse(tags)  # grammar 파싱
        if self.debug: a.draw()

        # 구 나누기
        phrases = self.get2(self.get(a))[0]  # 최종 phrase
        poses = self.get2(self.get_tag(a), tag=True)[0]  # 최종 phrase의 품사
        self.printf('ne_chunk:', chunks)
        self.printf(phrases)
        self.printf(poses)

        # 절 나누기 (conjs: 접속사 목록)
        clauses, poses, conjs = self.phrases_split(phrases, poses, 'S')
        self.printf(clauses)
        self.printf(conjs)
        self.printf(len(clauses), len(conjs))
        clauses, poses, conjs = self.clauses_remove(clauses, poses, conjs)  # 특정 품사 포함한 절 제거
        self.printf(conjs)

        self.printf('  /  '.join([str(i) for i in clauses[0]]))

        self.printf(poses)
        # ['NP', 'VP', ['NP', 'TIME']] 처럼 리스트에 여러 품사가 묶여 있는 경우 대표 품사 하나만 남김.
        repreposes = self.get_repreposes(poses)

        self.printf('//////////////////////////////')
        self.printf(clauses)
        self.printf(poses)
        self.printf(repreposes)
        self.printf(conjs)
        self.printf('//////////////////////////////')

        # 여러 절의 종속 관계 등을 고려하여 의미 관계 추출 (가장 중요한 과정)
        clauses, poses, repreposes, additions, addition_poses = self.normalize_clauses(clauses, poses, repreposes, conjs)
        # 중복 제거
        clauses, poses, repreposes, additions, addition_poses = self.unique(clauses, poses, repreposes, additions, addition_poses)

        # 출력
        for i in clauses:
            self.printf(i)

        # A = B이고 B = C이면 A = C라는 논리 적용하여 정보 확장
        self.substitute_equal(clauses, poses, repreposes, additions, addition_poses)
        # 중복 제거
        clauses, poses, repreposes, additions, addition_poses = self.unique(clauses, poses, repreposes, additions, addition_poses)

        # 따옴표 제거했던 것 복원
        clauses = self.recover_quotes(clauses, quotes)

        self.printf('=-===================')
        for i in range(len(clauses)):
            self.printf(clauses[i])
            self.printf(additions[i])
            self.printf(addition_poses[i])

        # 개체명 들어간 정보만 남기기
        clauses, poses, repreposes, additions, addition_poses = self.only_ne(clauses, poses, repreposes, additions, addition_poses, chunks)

        self.printf('=-===================')
        for i in range(len(clauses)):
            self.printf(clauses[i])
            self.printf(additions[i])
            self.printf(addition_poses[i])

        if self.debug: a.draw()

        return clauses, poses, repreposes, additions, addition_poses

    def unique(self, *lists):
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

    def substitute_equal(self, clauses, poses, repreposes, additions, addition_poses):
        # A be B, B be C -> A be C 같은 논리를 적용햐여 'be'라는 동사를 갖는 clauses들끼리 대입한다.
        r = {
            'clauses': [], 'poses': [], 'repreposes': [], 'additions': [], 'addition_poses': []
        }
        for i in range(len(clauses)):
            if len(clauses[i]) < 3:
                continue
            if clauses[i][1] == 'be':
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
        clauses += r['clauses']
        poses += r['poses']
        repreposes += r['repreposes']
        additions += r['additions']
        addition_poses += r['addition_poses']
        return clauses, poses, repreposes, additions, addition_poses



    def normalize_clauses(self, clauses, poses, repreposes, conjs):
        # 'S'를 기준으로 나눈 절들을 정리한다.
        def get_ai(l, i, d=1):
            # 바로 다음 원소 인덱스 반환. 바로 다음 원소가 None일 경우 다다음 원소를 선택하는 index 반환
            # d=1 : 다음 원소 방향으로 검색    d=-1 : 이전 원소 방향으로 검색
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
        r_additions = [[] for i in range(len(clauses))]  # 추가적인 정보
        r_addition_poses = [[] for i in range(len(clauses))]  # 추가적인 정보의 품사
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

                    if not target_idx.count('V') == 0 and target_idx.count('N') >= 2:  # 앞 문장에 명사구 두 개, 동사구 하나는 꼭 있어야 함
                        target_idx = -list(reversed(target_idx)).index(pos_group[reprepos[0]]) - 1  # 앞 문장의 마지막 동/명사구 index
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
                    if conjs[i+ai] in ['that', 'which']:
                        ai += -1
                        modified = True
                    target_idx = [pos_group[j] for j in r_repreposes[i + ai]]

                    if not target_idx.count('V') == 0 and target_idx.count('N') >= 1:  # 앞 문장에 명사구, 동사구 하나는 꼭 있어야 함
                        target_idx = target_idx.index('N')  # 앞 문장의 첫번째 명사구 index
                        target = r_clauses[i + ai][target_idx]  # 앞 문장 주어 (첫째 명사구)

                        r_clauses[i] = [target] + clause
                        r_poses[i] = [r_poses[i + ai][target_idx]] + pos
                        r_repreposes[i] = [r_repreposes[i + ai][target_idx]] + reprepos
                        r_additions[i] += r_additions[i + ai].copy()  # 앞 문장 복사
                        r_addition_poses[i] += r_addition_poses[i + ai].copy()  # 앞 문장 복사
                    if modified:
                        ai += 1
                if conjs[i+ai] in ['that', 'which']:  # 앞 문장을 탐색하는 것이므로 conjs도 앞엣것을 기준으로 계산해야 함.
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
                        if not (len(reprepos) >= 3 and pos_group[reprepos[2]] == 'N'): # <that 명사구 동사구 명사구> 형태라면? -> 패스
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
                                r_repreposes[i] = reprepos[:current_idx+1] + [r_repreposes[i + ai][target_idx]] + reprepos[current_idx+1:]

            ai = get_ai(r_clauses, i, 1)
            if i < len(clauses) - 1 and not conjs[i] == '.':
                # 뒷 문장 탐색 (->)
                if conjs[i] == ',':
                    if pos_group[reprepos[0]] == 'N' and len(reprepos) == 1:
                        # <[현재명사구], [명사구] ...> ->  현재명사구 | be | 명사구
                        target_idx = [pos_group[j] for j in r_repreposes[i + ai]]
                        if not target_idx.count('N') == 0:  # 앞 문장에 명사구가 없으면? -> 패스
                            target_idx = -list(reversed(target_idx)).index('N') - 1  # 앞 문장의 마지막 명사구 index
                            target = r_clauses[i + ai][target_idx]  # 앞 문장 명사구
                            r_clauses[i] = [target, 'be', clause[0]]
                            r_poses[i] = [r_poses[i + ai][target_idx], 'VP', pos[0]]
                            r_repreposes[i] = [r_repreposes[i + ai][target_idx], 'VP', reprepos[0]]
                if conjs[i] == 'and':
                    if pos_group[reprepos[0]] in ['V', 'N'] and len(reprepos) == 1:
                        # <[현재명사구] and [명사구] ...> -> 앞 문장의 명사구.replace( 현재명사구)
                        # ex) He and I will go to the shop.
                        target_idx = [pos_group[j] for j in r_repreposes[i + ai]]

                        if not target_idx.count('V') == 0 and target_idx.count('N') >= 2:  # 앞 문장에 명사구 두 개, 동사구 하나는 꼭 있어야 함
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

            if pos_group[reprepos[0]] == 'A' and len(reprepos) == 1:
                # 추가적인 정보만 존재한다면? ex) 'In 1987' -> 뒷 문장 추가적인 정보에 추가

                if i < len(clauses) - 1:
                    # 뒷 문장
                    ai = get_ai(r_clauses, i, 1)
                else:
                    # 앞 문장
                    ai = get_ai(r_clauses, i, -1)
                r_additions[i+ai].append(clause[0])
                r_addition_poses[i+ai].append(pos[0])
                r_clauses[i] = None
                r_poses[i] = None
                r_repreposes[i] = None
                r_additions[i] = []
                r_addition_poses[i] = []
                remove_i.append(i - len(remove_i))

            # 추가적인 정보
            clause = r_clauses[i]
            pos = r_poses[i]
            reprepos = r_repreposes[i]
            if reprepos:
                remove_j = []
                for j, reprep in enumerate(reprepos):
                    if pos_group[reprep] == 'A':
                        self.printf(i)
                        r_additions[i].append(clause[j])
                        r_addition_poses[i].append(pos[j])
                        r_clauses[i][j] = None
                        r_poses[i][j] = None
                        r_repreposes[i][j] = None
                        remove_j.append(j - len(remove_j))
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
        for i in remove_i:
            del r_clauses[i]
            del r_poses[i]
            del r_repreposes[i]
            del r_additions[i]
            del r_addition_poses[i]
        return r_clauses, r_poses, r_repreposes, r_additions, r_addition_poses







text = 'The history of the United States started with the arrival of Native Americans around 15,000 BC. Numerous indigenous cultures formed, and many disappeared in the 1500s.'
text = 'In 1987, Plastic isn\'t a word that originally meant “pliable and easily shaped”. It only recently became a name for a category of materials called polymers in the 1500s, and The word polymer means “of many parts,” and polymers are made of long chains of molecules. Polymers abound in nature. Cellulose, the material that makes up the cell walls of plants, is a very common natural polymer.'
text = "In 1885 at Pemberton's Eagle Drug and Chemical House, his drugstore in Columbus, Georgia, he registered Pemberton's French Wine Coca nerve tonic."
text = "It is also worth noting that a Spanish drink that called \"Kola Coca\" that was presented at a contest in Philadelphia in 1885, a year before the official birth of Coca-Cola."
text = "The rights for this Spanish drink were bought by Coca-Cola in 1953."
text = 'In 1886, when Atlanta and Fulton County passed prohibition legislation, Pemberton responded by developing Coca-Cola, a nonalcoholic version of Pemberton\'s French Wine Coca.'
text = 'Drugstore soda fountains were popular in the United States at the time due to the belief that carbonated water was good for the health, and Pemberton\'s new drink was marketed and sold as a patent medicine, Pemberton claiming it a cure for many diseases, including morphine addiction, indigestion, nerve disorders, headaches, and impotence.'
#text = 'In 1892, Candler set out to incorporate a second company; "The Coca-Cola Company"'
#text = 'The first outdoor wall advertisement that promoted the Coca-Cola drink was painted in 1894 in Cartersville, Georgia.'
#text = 'The longest running commercial Coca-Cola soda fountain anywhere was Atlanta\'s Fleeman\'s Pharmacy, which first opened its doors in 1914.'
#text = 'His most famous victory occurred at the Battle of Myeongnyang, where despite being outnumbered 333 (133 warships, at least 200 logistical support ships) to 13, he managed to disable or destroy 31 Japanese warships without losing a single ship of his own.'
#text = 'After the Japanese attacked Busan, Yi began his naval operations from his headquarters at Yeosu'
#text = 'A Japanese invasion force landed at Busan and Dadaejin, port cities on the southern tip of Joseon.'
#text = 'The National Liberation Day of Korea is a holiday that celebrated annually on August 15 in both South and North Korea.'
#text = 'It commemorates Victory over Japan Day, when at the end of World War II, the U.S. and Soviet forces helped end three hundreds years of Japanese occupation and colonial rule of Korea that lasted from 1910-1945.'
#text = "I will eat coffee, bread and cake which he loves."
text = 'Comfort women were mainly women and girls that forced into sexual slavery by the Imperial Japanese Army in occupied countries and territories before and during World War II in 1930, or who participated in the earlier program of voluntary prostitution. women that were forced to provide sex to Japanese soldiers before and during World War II  in 1930. '
text += 'In response, The Japan Times promised to conduct a thorough review of the description and announce its conclusions. '
text += 'Previously, The Japan Times described “comfort women” simply as “women who were forced to provide sex to Japanese soldiers before and during World War II in 1930.” '
#text = "women that were forced to provide sex to Japanese soldiers before and during World War II."

#text = 'Today is Jun 17'

#text = 'Benjamin Franklin once said that if you love life, then do not squander time because that is what life is made of. That is something on which I intend to concentrate. Koizumi defended his visits, insisting that they were to pray for peace and adding that he is only respecting the war dead in general, not the war criminals in particular. The blank spaces are words which could not be deciphered. Benjamin Franklin once said that if you love life, then do not squander time because that is what life is made of.'

#text = 'Dokdo which is erroneously called Takeshima in Japan until now, is Korean territory.'

anal = Analyzer()
result = anal.analyze(text)
for i in range(len(result[0])):
    for j in range(len(result)):
        print(result[j][i])

