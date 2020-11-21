import nltk
from nltk.chunk import ne_chunk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet
import re
try:
    from .options import *
except:
    from options import *


class Analyzer:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.lemmatize = self.lemmatize_func

        self.cp = nltk.RegexpParser(grammar)  # grammar parser

    def analyze(self, sentence):
        # sentence를 분석한다.
        if self.is_bad_sentence(sentence):
            # 예외 문장일 경우
            return -1

        sentence = self.absolute_replace(sentence)  # 사전에 정의한 규칙대로 replace
        sentence, quotes = self.mask_quotes(sentence)  # 따옴표 내용 제거 (따옴표 내용은 QUITE{i} 형식으로 마스킹됨)
        tags = self.get_tags(sentence)  # 품사 태깅
        tags = self.absolute_replace_tag(tags)
        chunks = self.chunk(tags)  # 개체명 인식
        #tags = self.remove_pos(tags, drops)  # 특정 품사 제거
        a = self.cp.parse(tags)  # grammar 파싱
        a.draw()

        # 구 나누기
        phrases = self.get2(self.get(a))[0]  # 최종 phrase
        poses = self.get2(self.get_tag(a), tag=True)[0]  # 최종 phrase의 품사
        #print('ne_chunk:', chunks)
        print(phrases)
        print(poses)

        # 절 나누기 (conjs: 접속사 목록)
        clauses, poses, conjs = self.phrases_split(phrases, poses, 'S')
        clauses, poses, conjs = self.clauses_remove(clauses, poses, conjs)  # 특정 품사 포함한 절 제거
        print(conjs)

        print('  /  '.join([str(i) for i in clauses[0]]))

        print(poses)
        # ['NP', 'VP', ['NP', 'TIME']] 처럼 리스트에 여러 품사가 묶여 있는 경우 대표 품사 하나만 남김.
        repreposes = self.get_repreposes(poses)

        print('//////////////////////////////')
        print(clauses)
        print(poses)
        print(repreposes)
        print(conjs)
        print('//////////////////////////////')

        # 여러 절의 종속 관계 등을 고려하여 의미 관계 추출 (가장 중요한 과정)
        clauses, poses, repreposes, additions, addition_poses = self.normalize_clauses(clauses, poses, repreposes, conjs)
        # 중복 제거
        clauses, poses, repreposes, additions, addition_poses = self.unique(clauses, poses, repreposes, additions, addition_poses)

        # 출력
        for i in clauses:
            print(i)

        # 따옴표 제거했던 것 복원
        clauses = self.recover_quotes(clauses, quotes)

        print('=-===================')
        for i in range(len(clauses)):
            print(clauses[i])
            print(additions[i])
            print(addition_poses[i])

        a.draw()

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

    def substitute_equal(self, clauses, poses, repreposes, addictions, addiction_poses):
        # A be B, B be C -> A be C 같은 논리를 적용햐여 'be'라는 동사를 갖는 clauses들끼리 대입한다.
        pass

    def normalize_clauses(self, clauses, poses, repreposes, conjs):
        # 'S'를 기준으로 나눈 절들을 정리한다.
        def get_ai(l, i, d=1):
            # 바로 다음 원소 인덱스 반환. 바로 다음 원소가 None일 경우 다다음 원소를 선택하는 index 반환
            # d=1 : 다음 원소 방향으로 검색    d=-1 : 이전 원소 방향으로 검색
            ai = d
            while not l[i+ai]:
                ai += d
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
            elif pos_group[reprepos[0]] == 'N' and len(reprepos) == 1:
                if i < len(clauses) - 1:
                    # 뒷 문장과
                    ai = 1
                    while not r_clauses[i+ai]:
                        # 뒷 문장이 None일 수 있으므로
                        ai += 1
                else:
                    # 앞 문장과
                    ai = -1
                    while not r_clauses[i+ai]:
                        # 앞 문장이 None일 수 있으므로
                        ai -= 1
                    if pos_group[r_repreposes[i+ai][-1]] == 'V':
                        # 앞 문장 맨 마지막 단어가 동사구라면?
                        ai2 = 1
                        while not r_clauses[i + ai2]:
                            # 뒷 문장이 None일 수 있으므로
                            ai2 += 1
                        if pos_group[r_repreposes[i+ai][0]] == 'N':
                            # 그리고 뒷 문장 처음 단어가 명사구라면? -> 뒷 문장과 병렬 관계
                            ai = ai2
                if pos_group[r_repreposes[i+ai][0]] == 'N':
                    # 앞 뒤 문장이 명사구라면? ex) 'South korea, the republic of korea' -> 이웃 문장의 명사구와 be 관계 성립시키기
                    target_idx = [pos_group[j] for j in r_repreposes[i+ai]]
                    if ai < 0: # 앞 문장과 관계 성립시킬 경우 -> 맨 뒤 명사구(=선행사)와 관계 성립시키기
                        target_idx = -list(reversed(target_idx)).index('N') - 1
                    else:
                        target_idx = target_idx.index('N')
                    target = r_clauses[i+ai][target_idx]  # 앞 문장 주어
                    r_clauses[i] = [target, 'be', clause[0]]
                    r_poses[i] = [r_poses[i+ai][target_idx], 'VP', pos[0]]
                    r_repreposes[i] = [r_repreposes[i+ai][target_idx], 'VP', reprepos[0]]
                    try:
                        if pos_group[r_repreposes[i+ai][target_idx+1]] == 'V':
                            # 이웃 문장 구조 : [명사구] [동사구]라면 -> 현재 문장 명사구 | 이웃 문장 동사구
                            r_clauses.append([clause[0]] + r_clauses[i+ai][target_idx+1:])
                            r_poses.append([pos[0]] + r_poses[i+ai][target_idx+1:])
                            r_repreposes.append([reprepos[0]] + r_repreposes[i+ai][target_idx+1:])
                            # 아래처럼 append로 이웃 문장의 원소를 집어넣으면 나중에 해당 이웃 원소의 원소가 변경돼도 똑같이 변경됨 (주소가 같으므로)
                            r_additions.append(r_additions[i+ai])
                            r_addition_poses.append(r_addition_poses[i+ai])
                    except IndexError:
                        pass
                elif pos_group[r_repreposes[i+ai][0]] == 'V':
                    # 현재 문장이 명사구이고, 이웃 문장이 동사구라면? ex) 'South korea, is the powerful country' -> 이웃 문장의 동사구와 관계 성립시키기
                    r_clauses[i] = [clause[0]] + r_clauses[i+ai]
                    r_poses[i] = [pos[0]] + r_poses[i+ai]
                    r_repreposes[i] = [reprepos[0]] + r_repreposes[i+ai]
            elif pos_group[reprepos[0]] != 'N':
                # 맨 앞이 명사구가 아니라면? -> 주어 생략된 것이므로 앞 문장 주어 복붙
                if i > 0:
                    # 앞 문장 주어 복붙
                    ai = -1
                    while not r_clauses[i+ai]:
                        # 앞 문장이 None일 수 있으므로
                        ai -= 1
                else:
                    # 뒷 문장 주어 복붙
                    ai = 1
                    while not r_clauses[i+ai]:
                        # 뒷 문장이 None일 수 있으므로
                        ai += 1
                target_idx = [pos_group[j] for j in r_repreposes[i+ai]].index('N')
                target = r_clauses[i+ai][target_idx]  # 앞 문장 주어
                r_clauses[i].insert(0, target)
                r_poses[i].insert(0, r_poses[i+ai][target_idx])
                r_repreposes[i].insert(0, r_repreposes[i+ai][target_idx])

            # 추가적인 정보
            clause = r_clauses[i]
            pos = r_poses[i]
            reprepos = r_repreposes[i]
            if reprepos:
                remove_j = []
                for j, reprep in enumerate(reprepos):
                    if pos_group[reprep] == 'A':
                        print(i)
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

            print('====', i)
            print(r_clauses)
            print(r_poses)
            print(r_repreposes)
            print(r_additions)
            print(r_addition_poses)
        for i in remove_i:
            del r_clauses[i]
            del r_poses[i]
            del r_repreposes[i]
            del r_additions[i]
            del r_addition_poses[i]
        return r_clauses, r_poses, r_repreposes, r_additions, r_addition_poses


    def get_repreposes(self, poses):
        # 대표 품사를 반환한다.
        def find(a):
            # 리스트 l에서 원소 a의 index를 반환 (없을 경우 100 반환)
            try:
                return priority.index(a)
            except:
                return 100
        r = []
        for pos in poses:
            tmp = []
            for pos_i in pos:
                if isinstance(pos_i, list):
                    pos_i = self.totally_flatten(pos_i)
                    tmp.append(sorted(pos_i, key=find)[0])
                else:
                    tmp.append(pos_i)
            r.append(tmp)
        return r

    def phrases_split(self, phrases, poses, sep):
        # poses를 보면서 sep을 기준으로 split한다. split 대상은 phrases
        # ex) f(['my', 'name', 'is', 'jun'], ['N', 'S', 'V', 'N'], 'S') -> ([['my'], ['is', 'jun']], [['N'], ['V', 'N']])
        r_phrases = []
        r_poses = []
        r_conjs = []
        tmp_phrases = []
        tmp_poses = []
        for i in range(len(phrases)):
            if poses[i] == sep:
                if not tmp_phrases:
                    continue
                r_phrases.append(tmp_phrases)
                r_poses.append(tmp_poses)
                r_conjs.append(phrases[i])
                tmp_phrases = []
                tmp_poses = []
            else:
                tmp_phrases.append(phrases[i])
                tmp_poses.append(poses[i])
        if tmp_phrases:
            r_phrases.append(tmp_phrases)
            r_poses.append(tmp_poses)
        return r_phrases, r_poses, r_conjs

    def clauses_remove(self, clauses, poses, conjs):
        # phrases에서 특정 품사를 포함한 절 제거
        # ex) (seps=['WRB']) ['I', 'did', 'this', 'when', 'I', 'was', 'young'] -> ['I', 'did', 'this']
        r_clauses = []
        r_poses = []
        r_conjs = []
        for i in range(len(clauses)):
            tmp_clauses = []
            tmp_poses = []
            for j in range(len(clauses[i])):
                go = 0
                flattend_clauses = self.totally_flatten([clauses[i][j]])
                flattend_poses = self.totally_flatten([poses[i][j]])
                for k in range(len(self.totally_flatten([clauses[i][j]]))):
                    go += flattend_poses[k] in ['WRB'] or flattend_clauses[k].lower() in ['if', 'when', 'whether']
                #if poses[i][j] in ['WRB'] or clauses[i][j].lower() in ['if', 'when']:
                if go:
                    break
                else:
                    tmp_clauses.append(clauses[i][j])
                    tmp_poses.append(poses[i][j])
            if tmp_clauses:
                r_clauses.append(tmp_clauses)
                r_poses.append(tmp_poses)
                r_conjs.append(conjs[i])
        return r_clauses, r_poses, r_conjs

    def get_tags(self, sentence):
        # 품사 태깅
        return nltk.pos_tag(nltk.word_tokenize(sentence))

    def chunk(self, tags):
        # 개체명 인식
        return ne_chunk(tags)

    def mask_quotes(self, sentence):
        # 따옴표 문장 추출
        finds = re.findall(r' \"(.+?)\"', sentence)
        finds += re.findall(r' \'(.+?)\'', sentence)
        finds += re.findall(r' \“(.+?)\”', sentence)
        finds += re.findall(r' \„(.+?)\„', sentence)
        finds += re.findall(r' \‟(.+?)\‟', sentence)
        finds += re.findall(r' \`(.+?)\`', sentence)
        finds += re.findall(r' \❛(.+?)\❜', sentence)
        finds += re.findall(r' \❝(.+?)\❞', sentence)
        for i, find in enumerate(finds):
            alpha = ''
            if find[-1] == '.':
                # 따옴표 내용이 마침표로 끝나면 -> 문장의 마지막이라는 뜻이므로 마스킹 대상에도 적용
                alpha = '.'
            if find[-1] == ',':
                alpha = ','
            sentence = sentence.replace('"'+find+'"', 'QUOTE' + str(i) + alpha)
            sentence = sentence.replace("'"+find+"'", 'QUOTE' + str(i) + alpha)
            sentence = sentence.replace("“"+find+"”", 'QUOTE' + str(i) + alpha)
            sentence = sentence.replace("„"+find+"„", 'QUOTE' + str(i) + alpha)
            sentence = sentence.replace("‟"+find+"‟", 'QUOTE' + str(i) + alpha)
            sentence = sentence.replace("`"+find+"`", 'QUOTE' + str(i) + alpha)
            sentence = sentence.replace("❛"+find+"❜", 'QUOTE' + str(i) + alpha)
            sentence = sentence.replace("❝"+find+"❞", 'QUOTE' + str(i) + alpha)
        return sentence, finds

    def recover_quotes(self, sentence, quotes):
        # 따옴표 replace 했던 것을 복구
        r = []
        for i in sentence:
            if isinstance(i, list):
                r.append(self.recover_quotes(i, quotes))
            else:
                if re.match(r'QUOTE\d+', i):
                    # 따옴표 내용 복구
                    r.append(quotes[int(i.split('QUOTE')[-1])])
                else:
                    r.append(i)
        return r

    def is_bad_sentence(self, sentence):
        # 특정 조건을 부합하는 문장인가?
        # 1. 의문문인가?
        return '?' in sentence

    def absolute_replace(self, sentence):
        # absolute_replace dict대로 sentence를 replace
        for a, b in absolute_replace.items():
            sentence = sentence.replace(a, b)
        return sentence

    def absolute_replace_tag(self, tags):
        r = []
        for i in range(len(tags)):
            tag = tags[i]
            if not tag:
                continue
            if tag[0] in absolute_mon:
                tag = (tag[0], 'MON')
            if tag[0] in absolute_unit:
                tag = (tag[0], 'UNIT')
            r.append(tag)
        return r

    def remove_pos(self, tags, drops=[]):
        # drops 목록의 품사 모두 제거
        r = [i for i in tags if not i[1] in drops]
        return r

    def lemmatize_func(self, word):
        # lemmatize (원형으로 변환)
        if ' ' in word:
            return ' '.join([self.lemmatize(w) for w in word.split(' ')])
        r = self.lemmatizer.lemmatize(word, pos=wordnet.VERB)
        if word != r:
            return r
        r = self.lemmatizer.lemmatize(word, pos=wordnet.NOUN)
        if word != r:
            return r
        r = self.lemmatizer.lemmatize(word, pos=wordnet.ADJ)
        if word != r:
            return r
        r = self.lemmatizer.lemmatize(word, pos=wordnet.ADJ_SAT)
        if word != r:
            return r
        return self.lemmatizer.lemmatize(word, pos=wordnet.ADV)

    def get(self, t):
        # tree 구조에서 phrases 리스트로 변환
        r = []
        for i in t:
            if isinstance(i, nltk.tree.Tree):
                r.extend(self.get(i))
            elif not i[1] in drops or i[0] in replace_pos:
                r.append(i[0])
        return [r]

    def get_tag(self, t):
        # tree 구조에서 phrases의 품사 리스트로 변환
        r = []
        for i in t:
            if isinstance(i, nltk.tree.Tree):
                r.extend(self.get_tag(i))
            elif not i[1] in drops:
                r.append(t.label())
            elif i[0] in replace_pos:
                r.append(replace_pos[i[0]])
        return [r]

    def append(self, l, a, tag):
        # 리스트 l에 원소 a를 append한다. 이때 tag=True이면 whitespace 제거하고 append한다.
        if tag:
            l.append(a[1:].split(' ')[0])
        else:
            l.append(self.lemmatize(a[1:]))
        return l

    def totally_flatten(self, l):
        # reshape(-1)과 동일
        r = []
        for i in l:
            if isinstance(i, list):
                r.extend(self.totally_flatten(i))
            else:
                r.append(i)
        return r

    def flatten(self, l, tag=False):
        # [[a], b, [c, d]] -> [a, b, [c, d]]
        r = []
        for i in l:
            if len(i) == 1:
                if tag:
                    r.append(i[0].split(' ')[0])
                else:
                    r.append(i[0])
            else:
                r.append(i)
        return r

    def get2(self, l, tag=False):
        # tree 구조에서 phrases 리스트로 변환
        r = []
        tmp = ''
        for i in l:
            if isinstance(i, str):
                tmp += ' ' + i
            else:
                if tmp:
                    r = self.append(r, tmp, tag)
                    tmp = ''
                t = self.get2(i, tag=tag)
                r.append(self.flatten(t, tag=tag))
        if tmp:
            r = self.append(r, tmp, tag)
        return r




text = 'The history of the United States started with the arrival of Native Americans around 15,000 BC. Numerous indigenous cultures formed, and many disappeared in the 1500s.'
text = 'In 1987, Plastic isn\'t a word that originally meant “pliable and easily shaped”. It only recently became a name for a category of materials called polymers in the 1500s, and The word polymer means “of many parts,” and polymers are made of long chains of molecules. Polymers abound in nature. Cellulose, the material that makes up the cell walls of plants, is a very common natural polymer.'
text = "In 1885 at Pemberton's Eagle Drug and Chemical House, his drugstore in Columbus, Georgia, he registered Pemberton's French Wine Coca nerve tonic."
text = "It is also worth noting that a Spanish drink that called \"Kola Coca\" that was presented at a contest in Philadelphia in 1885, a year before the official birth of Coca-Cola."
text = "The rights for this Spanish drink were bought by Coca-Cola in 1953."
text = 'In 1886, when Atlanta and Fulton County passed prohibition legislation, Pemberton responded by developing Coca-Cola, a nonalcoholic version of Pemberton\'s French Wine Coca.'
text = 'Drugstore soda fountains were popular in the United States at the time due to the belief that carbonated water was good for the health, and Pemberton\'s new drink was marketed and sold as a patent medicine, Pemberton claiming it a cure for many diseases, including morphine addiction, indigestion, nerve disorders, headaches, and impotence.'
text = 'In 1892, Candler set out to incorporate a second company; "The Coca-Cola Company"'
text = 'The first outdoor wall advertisement that promoted the Coca-Cola drink was painted in 1894 in Cartersville, Georgia.'
#text = 'The longest running commercial Coca-Cola soda fountain anywhere was Atlanta\'s Fleeman\'s Pharmacy, which first opened its doors in 1914.'
text = 'His most famous victory occurred at the Battle of Myeongnyang, where despite being outnumbered 333 (133 warships, at least 200 logistical support ships) to 13, he managed to disable or destroy 31 Japanese warships without losing a single ship of his own.'
text = 'After the Japanese attacked Busan, Yi began his naval operations from his headquarters at Yeosu'
text = 'A Japanese invasion force landed at Busan and Dadaejin, port cities on the southern tip of Joseon.'
text = 'The National Liberation Day of Korea is a holiday celebrated annually on August. 15 in both South and North Korea.'
text = 'It commemorates Victory over Japan Day, when at the end of World War II, the U.S. and Soviet forces helped end three hundreds years of Japanese occupation and colonial rule of Korea that lasted from 1910-1945.'
text = "I will buy it if it's a jewel."

#text = 'Today is Jun 17'


anal = Analyzer()
anal.analyze(text)
