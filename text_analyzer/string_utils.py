import nltk
from nltk.chunk import ne_chunk
from nltk.corpus import wordnet
import re
try:
    from .options import *
except:
    from options import *


class StringUtils:
    def printf(self, *args, **kwargs):
        # debug=True일 때만 print를 작동시킨다.
        if self.debug:
            print(*args, **kwargs)

    def get_repreposes(self, poses):
        # 대표 품사를 반환한다.
        def find(a):
            # 리스트 priority에서 원소 a의 index를 반환 (없을 경우 100 반환)
            try:
                return priority.index(a)
            except:
                return 100

        r = []
        for pos in poses:
            tmp = []
            for pos_i in pos:
                if isinstance(pos_i, list):
                    # 여러 품사 있을 경우 -> priority 기준으로 대표 품사 결정
                    pos_i = self.totally_flatten(pos_i)
                    pos_i = [i[0] for i in pos_i]
                    tmp.append(sorted(pos_i, key=find)[0])
                else:
                    # 하나의 품사만 있을 경우 -> 그 품사가 대표 품사
                    tmp.append(pos_i[0])
            r.append(tmp)
        return r

    def phrases_split(self, phrases, poses, sep):
        # poses를 보면서 sep을 기준으로 split한다. split 대상은 phrases
        # ex) f(['my', 'name', 'is', 'jun'], ['N', 'S', 'V', 'N'], 'S')
        #     -> ([['my'], ['is', 'jun']], [['N'], ['V', 'N']])
        r_phrases = []
        r_poses = []
        r_conjs = []
        tmp_phrases = []
        tmp_poses = []
        for i in range(len(phrases)):
            # poses 형태 : [['NP', ({},)], ['VP', ({},)]]
            if poses[i][0] == sep:
                if not tmp_phrases:
                    continue
                r_phrases.append(tmp_phrases)
                r_poses.append(tmp_poses)
                r_conjs.append(phrases[i].split(' ')[-1])  # conj가 ', and'일 경우 제일 마지막 걸로 저장 'and'
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
        # ex) (seps=['WRB']) ['I', 'did', 'this', 'when', 'I', 'was', 'young']
        #      -> ['I', 'did', 'this']
        r_clauses = []
        r_poses = []
        r_conjs = []
        ai = 0
        for i in range(len(clauses)):
            # poses 형태 : [['NP', ({},)], ['VP', ({},)]]
            tmp_clauses = []
            tmp_poses = []
            try:
                tmp_conj = conjs[i]
            except IndexError:
                tmp_conj = '.'
            self.printf('len:', len(r_clauses), len(r_conjs))
            for j in range(len(clauses[i])):
                go = 0
                flattend_clauses = self.totally_flatten([clauses[i][j]])
                flattend_poses = self.totally_flatten([poses[i][j]])
                for k in range(len(self.totally_flatten([clauses[i][j]]))):
                    go += flattend_poses[k][0] in ['WRB'] or \
                          flattend_clauses[k].lower() in hate_startswith or \
                          (k == 0 and flattend_clauses[k].lower() in ['after', 'before'])
                if go:
                    self.printf(i, j)
                    tmp_conj = '.'
                    if not tmp_clauses and i:
                        self.printf(r_conjs)
                        r_conjs[i-1+ai] = '.'
                        ai -= 1
                    break
                else:  # go == False면? -> 이 이후 절은 제거해야 하는 절임 (when, after 등의 금지 단어로 인해)
                    # 현재까지의 절만 결과에 저장
                    tmp_clauses.append(clauses[i][j])
                    tmp_poses.append(poses[i][j])
            if tmp_clauses:
                # 결과 리스트에 추가
                r_clauses.append(tmp_clauses)
                r_poses.append(tmp_poses)
                r_conjs.append(tmp_conj)
        # 결과 반환
        return r_clauses, r_poses, r_conjs

    @staticmethod
    def get_tags(sentence=None, tokens=None):
        # 품사 태깅
        if tokens:  # 만약 tokens가 주어졌다면? -> tokenize 스킵하고 pos tagging 진행
            return nltk.pos_tag(tokens)
        # tokenize -> pos tagging
        return nltk.pos_tag(nltk.word_tokenize(sentence))

    def chunk(self, tags):
        # 개체명 인식 (nltk에서 기본 지원하는 ne_chunk 사용)
        r = []
        for chunk in ne_chunk(tags):
            if hasattr(chunk, 'label'):
                r.append(' '.join(c[0] for c in chunk))
        r = ' '.join(r).split(' ')
        return r

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
        finds += re.findall(r' \“(.+?)\”', sentence)
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
        # ex) f(['I', 'said', 'QUOTE0'], ['"there is my parents"']) -> ['I', 'said', '"there is my parents"']
        r = []
        for i in sentence:
            if isinstance(i, list):
                r.append(self.recover_quotes(i, quotes))
            else:
                matched = re.match(r'QUOTE(\d+)', i)
                if matched:
                    # 따옴표 내용 복구
                    r.append(i.replace(matched.group(0), quotes[int(matched.group(1))]))
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
        # absolute_replace에 따라 replace 진행
        r = []
        for i in range(len(tags)):
            tag = tags[i]
            if not tag:
                continue
            if tag[0] in absolute_mon:
                tag = (tag[0], 'MON')
            if tag[0] in absolute_unit:
                tag = (tag[0], 'UNIT')
            if tag[0] in replace_pos.keys():
                tag = (tag[0], replace_pos[tag[0]])
            r.append(tag)
        return r

    def remove_pos(self, tags, drops=[]):
        # drops 목록의 품사 모두 제거
        # 단, tags는 zip_like(tags, api_tags) 돼 있어야 함
        r = [i for i in tags if not i[0][1] in drops or not i[1].get('ner') in [None, 'O', "SET"]]
        return r

    def lemmatize_func(self, word):
        # lemmatize (원형으로 변환)
        if ' ' in word:
            return ' '.join([self.lemmatize(w) for w in word.split(' ')])
        for pos in [wordnet.VERB, wordnet.NOUN, wordnet.ADJ, wordnet.ADJ_SAT, wordnet.ADV]:
            r = self.lemmatizer.lemmatize(word, pos=pos)
            if word != r:
                return r
        return r

    def get(self, t):
        # tree 구조에서 phrases 리스트로 변환
        r = []
        for i in t:
            if isinstance(i, nltk.tree.Tree):
                tmp = self.get(i)
                if not self.totally_flatten(tmp):
                    continue
                r.extend(tmp)
            else:
                r.append(i[0])
        return [r]

    def get_tag(self, t):
        # tree 구조에서 phrases의 품사 리스트로 변환
        r = []
        for i in t:
            if isinstance(i, nltk.tree.Tree):
                r.extend(self.get_tag(i))
            elif i[0] in replace_pos:
                r.append(replace_pos[i[0]])
            else:
                r.append(t.label())
        return [r]

    def append(self, l, a, tag):
        # 리스트 l에 원소 a를 append한다. 이때 tag=True면 whitespace 제거하고 append한다.
        if tag:
            l.append(a[1:].split(' ')[0])
        else:
            l.append(a[1:])
        return l

    def totally_flatten(self, l):
        # reshape(-1)과 동일
        if not isinstance(l, list):
            return [l]
        r = []
        for i in l:
            if isinstance(i, list):
                r.extend(self.totally_flatten(i))
            else:
                r.append(i)
        return r

    def flatten(self, l, tag=False):
        # [a] 이렇게 홀로 감싸져 있는 원소만 밖으로 빼낸다.
        # [[a], b, [c, d]] -> [a, b, [c, d]]
        def get_depth(l, i=0, maxlen=0):
            if isinstance(l, list):
                return get_depth(l[0], i+1, max([maxlen, len(l)]))
            return l, i, maxlen
        r = []
        for i in l:
            depth = get_depth(i)
            if depth[2] == 1:
                if tag:
                    r.append(depth[0].split(' ')[0])
                else:
                    r.append(depth[0])
            else:
                r.append(i)
        return r

    def like(self, l1, l2, idx=0):
        # l1.shape를 l2.shape와 같게 만드는 건데 여러 리스트 중첩돼 있어도 동작한다.
        # ex) f([[1,2],3], ['a','b','c']) -> [['a','b'],'c']
        # 단, l2는 flat list여야 한다. dim=1이어야 함.
        r = []
        for i in range(len(l1)):
            if isinstance(l1[i], list):
                r.append(self.like(l1[i], l2, idx=idx))
                idx += len(self.totally_flatten(l1[i])) - 1
            else:
                r.append(l2[idx])
            idx += 1
        return r

    def zip_like(self, l1, l2, idx=0):
        # zip(l1, l2)인데 여러 리스트 중첩돼 있어도 동작한다.
        # ex) f([[1,2],3], ['a','b','c']) -> [[(1,'a'),(2,'b')],(3,'c')]
        # 단, l2는 flat list여야 한다. dim=1이어야 함.
        r = []
        for i in range(len(l1)):
            if isinstance(l1[i], list):
                r.append(self.zip_like(l1[i], l2, idx=idx))
                idx += len(self.totally_flatten(l1[i])) - 1
            else:
                r.append((l1[i], l2[idx]))
            idx += 1
        return r

    def list_like(self, l1, l2, key=lambda x: x):
        # l2의 내용을 l1의 내용과 같게 만들어서 출력한다.
        # ex) f([1,2,3,4], [1,3,2,3,6,7,4]) -> [1,2,3,4]
        r = []
        idx = 0
        for i in l1:
            tmp = []
            for j in i.split(' '):
                # 'before and' -> 'before' + 'and'
                while key(l2[idx]) != j:
                    idx += 1
                    if idx == len(l2):
                        # 끝까지 탐색했다면?
                        raise NotImplementedError("not proper list")
                tmp.append(l2[idx])
            r.append(tuple(tmp))
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

    def get_bio(self, pos):
        # bio 표기법으로 변환 (normalize_clauses()에서 사용)
        flat_pos = self.totally_flatten(pos)
        api_tags = [list(p[1]) for p in flat_pos]
        api_tags = self.totally_flatten(api_tags)
        poses = self.totally_flatten([[p[0]] * len(p[1]) for p in flat_pos])
        bio = []
        for i, p in enumerate(api_tags):
            if p.get('ner') != 'O' and p.get('ner'):
                # Named Entity가 포함돼 있는가?
                if not bio or bio[-1] == 'o':
                    bio.append('b')
                else:
                    bio.append('i')
                continue
            bio.append('o')

        current_b = None
        current_i = None
        r_remain = []
        r_addition = []
        r_remain_pos = []
        r_remain_ner = []  # ex) ['territory','of','Korea'] -> ['territory','of','COUNTRY']
        for i in range(len(bio)-1, -1, -1):
            if bio[i] == 'i':
                current_b = i
                if i == len(bio)-1 or bio[i+1] == 'o':
                    current_i = i
            if bio[i] == 'b':
                current_b = i
                if current_i is None:
                    # 'b'만 달랑 있는 경우 -> current_i도 같이 설정
                    current_i = i
            if current_b is not None and current_b - i >= 3:
                # 현재 포인터가 b와 너무 멀리 떨어져 있으면
                current_b = None
                r_remain = [i['word'] for i in api_tags[i:current_i+1]] + r_remain
                r_remain_pos = [(poses[i], (api_tags[i],)) for i in range(len(poses[i:current_i+1]))] + r_remain_pos
                r_remain_ner = [ner_group[i['ner']] if not i.get('ner') in [None, 'O'] else i['word']
                                for i in api_tags[i:current_i + 1]] + r_remain_ner
            if current_b is not None:
                if api_tags[i]['pos'] == 'IN' and bio[i] == 'o':
                    if api_tags[i]['word'] not in notIN:  # 현재 전치사가 고려하지 않을 전치사 목록에 있지 않아야 함
                        try:
                            timex = [t.get('timex') for t in api_tags[i:current_i + 1] if 'timex' in t][0]['value']
                        except IndexError:
                            # timex가 없다면?
                            timex = None
                        tmp = {
                            # 단어 ex) 'in 1987'
                            'word': ' '.join([t['word'] for t in api_tags[i:current_i + 1]]),
                            # 원형 ex) 'in 1987'
                            'lemma': ' '.join([t['lemma'] for t in api_tags[i:current_i + 1]]),
                            # 품사 ex) ['NR']
                            'pos': [t['pos'] for t in api_tags[i:current_i + 1]],
                            # 개체명 ex) 'DATE'
                            'ner': self.get_ner([t['ner'] for t in api_tags[i:current_i + 1]]),
                            # 수정된 개체명 ex) in 1500x -> ['in 15XX']
                            'normalizedNER': [t.get('normalizedNER') for t in api_tags[i:current_i + 1]],
                            # 개체명이 시간일 경우 x 표현식으로 표현된 시간 ex) 1500x -> ['15XX'] (1500년대라는 뜻)
                            'timex': timex
                        }
                        r_addition.insert(0, tmp)
                    else:
                        # 고려하지 않을 목록에 있는 전치사라면? -> 현재 개체명 스킵
                        r_remain = [i['word'] for i in api_tags[i:current_i + 1]] + r_remain
                        r_remain_pos = [(poses[i], (api_tags[i],)) for i in
                                        range(len(poses[i:current_i + 1]))] + r_remain_pos
                        r_remain_ner = [ner_group[i['ner']] if not i.get('ner') in [None, 'O'] else i['word']
                                        for i in api_tags[i:current_i + 1]] + r_remain_ner
                    current_b = current_i = None
            else:
                r_remain.insert(0, api_tags[i]['word'])
                r_remain_pos.insert(0, (poses[i], (api_tags[i],)))
                if bio[i] != 'o':
                    r_remain_ner.insert(0, api_tags[i]['ner'])
                else:
                    r_remain_ner.insert(0, api_tags[i]['word'])
        if current_b is not None:
            # 다 돌았는데 추가 안 된 부분이 있다면?
            r_remain = [i['word'] for i in api_tags[i:current_i + 1]] + r_remain
            r_remain_pos = [(poses[i], (api_tags[i],)) for i in range(len(poses[i:current_i + 1]))] + r_remain_pos
            r_remain_ner = [ner_group[i['ner']] if not i.get('ner') in [None, 'O'] else i['word']
                            for i in api_tags[i:current_i + 1]] + r_remain_ner

        r_remain_pos = self.like(r_remain, r_remain_pos)
        r_remain_ner = self.like(r_remain, r_remain_ner)

        self.printf('get bios, poses:', poses)
        self.printf('get bios, r_addition:', r_addition)
        self.printf('get bios, r_remain:', r_remain)
        self.printf('get bios, r_remain_pos:', r_remain_pos)
        self.printf('get bios, r_remain_ner:', r_remain_ner)
        return r_remain, r_remain_pos, r_addition, r_remain_ner

    @staticmethod
    def get_ner(ners):
        # ners[string] 중 대표 ner 하나를 골라서 반환한다.
        # 대표 ner을 고르는 기준은 ner_priority의 앞에 위치한 순이다.
        return sorted(ners, key=lambda x: ner_priority.index(x))[0]

    @staticmethod
    def get_antonyms(word, pos='v'):
        # word에 대한 반의어를 리스트 형식으로 반환한다.
        # ex) f('like') -> ['dislike']
        r = []
        for syn in wordnet.synsets(word, pos):  # synset 검색
            for lm in syn.lemmas():  # 원형으로 변환
                if lm.antonyms():  # 반의어 있으면? -> 리스트에 추가
                    r.append(lm.antonyms()[0].name().replace('_', ' '))
        return r
