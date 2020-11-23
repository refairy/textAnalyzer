# phrase 추출 문법
grammar = r"""
    CD: {<CD><\.><CD>}  # 소수점
    UNIT: {<UNIT><UNIT>}
    A-TIME: {<MON><.>?<CD>}
    A-TIME: {<CD><MON>}
    A-TIME: {<IN|A-TIMEIN><NP>?<DT>?<CD|A-TIME><NP>?}
    A-TIME: {<A-TIME><A-TIME>}
    A-NOT: {<A-NOT>}
    
    NP: {<JJ>?<N.*>+}
    NP: {<IN><N.*>}
    NPB: {<NNP>(<POS>?<NNP>?)*}
    NP: {<DT|PR.*>?<N.*|VBG><POS>?<DT|PR.*>?<JJ.*><DT|PR.*>?<N.*|VBG><POS>?'}
    NP: {<DT|PR.*>*<JJ.*>*<POS>?<DT|PR.*>?<N.*|VBG>+<POS>? <JJ.*>?}
    NP: {<DT><JJ>}
    NP: {<TO><V.*>}
    NP: {<PRP>}
    NP: {<CD><UNIT>}
    NP: {<TO><NP>}

    VP: {<JJ.*><V.*><RP>?}
    VP: {<V.*>+<RP>?}
    VP: {<MD><VP>}  # 조동사 ex: will do

    PP: {<JJ.*><P>}
    PP: {<P><N.*|VBG>}
    PP: {<P>*}
    INNP: {<IN><NP>}
    INNP: {<DDNP|NP|INNP><INNP>}
    DDNP: {<NP><NP>+}
    DDNP: {<NP>+<INNP>+}
    DDNP: {<INNP>+<NP>+}
    DDNP: {<INNP><INNP>+}
    JJJ: {<JJ>}
    WRB: {<WRB>}
"""


# 품사 우선순위. 한 리스트에 여러 품사가 있을 경우 priority의 앞쪽에 위치한 품사가 대표 품사가 된다.
priority = ['A-TIME', 'NPB', 'DDNP', 'INNP', 'NP', 'VP', 'PP', 'JJJ', 'WRB']

# 품사 그룹
pos_group = {
    'INNP': 'N', 'NP': 'N', 'DDNP': 'N', 'NPB': 'N',
    'VP': 'V',
    'PP': 'P',
    'JJJ': 'J',
    'A-TIME': 'A', 'A-NOT': 'A'  # 추가적인 정보
}
replace_pos = {
    'not': 'A-NOT',  # 'not'이라는 단어를 품사 'A-NOT'으로 replace
    'during': 'A-TIMEIN',
    '-ing': 'ING'  #
}

# 제거할 품사들
drops = ['FW', 'LS', 'PDT', 'RB', 'SENT', 'SYM', 'UH', 'DT', 'RBR', 'RBS']
hate_startswith = ['if', 'when', 'whether']  # 이 단어로 시작하는 절은 무조건 삭제

# 무조건 replace할 것들
absolute_replace = {"’s": "'s", "don't": 'not', "n't": ' not', "They're": 'They are', "they're": 'they are',
                    '!': '', '~': '', '^': '', 'did': '', 'does': ''}
absolute_mon = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'January',
                'February', 'March', 'April', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
absolute_unit = ['years', 'months', 'hours', 'minutes', 'seconds', 'millions', 'hundreds', 'degrees', 'billions',
                 'trillions', 'thousands']

# 관계대명사 목록
relatives = ['that', 'which', 'who', 'whom', 'whose']
