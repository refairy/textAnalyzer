import nltk
from nltk.chunk import ne_chunk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet
import re
try:
    from .options import *
except:
    from options import *

class StringUtils:
    def printf(self, *string, end='\n'):
        if self.debug:
            print(*string, end=end)
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
        ai = 0
        for i in range(len(clauses)):
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
                    #self.printf(i, j, flattend_clauses[k])
                    go += flattend_poses[k] in ['WRB'] or flattend_clauses[k].lower() in ['if', 'when', 'whether'] or (k == 0 and flattend_clauses[k].lower() in ['after', 'before'])
                #self.printf(flattend_clauses[0], go)
                #if poses[i][j] in ['WRB'] or clauses[i][j].lower() in ['if', 'when']:
                if go:
                    self.printf(i, j)
                    tmp_conj = '.'
                    if not tmp_clauses and i:
                        self.printf(r_conjs)
                        r_conjs[i-1+ai] = '.'
                        ai -= 1
                    break
                else:
                    tmp_clauses.append(clauses[i][j])
                    tmp_poses.append(poses[i][j])
            if tmp_clauses:
                r_clauses.append(tmp_clauses)
                r_poses.append(tmp_poses)
                #self.printf('tmp_conj', tmp_conj)
                r_conjs.append(tmp_conj)
        return r_clauses, r_poses, r_conjs

    def get_tags(self, sentence):
        # 품사 태깅
        return nltk.pos_tag(nltk.word_tokenize(sentence))

    def chunk(self, tags):
        # 개체명 인식
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
        # 리스트 l에 원소 a를 append한다. 이때 tag=True면 whitespace 제거하고 append한다.
        if tag:
            l.append(a[1:].split(' ')[0])
        else:
            l.append(self.lemmatize(a[1:]))
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