# phrase 추출 문법
grammar = r"""
    CD: {<CD><\.><CD>}  # 소수점
    UNIT: {<UNIT><UNIT>}
    
    A-NOT: {<A-NOT>}
    
    NP: {<CD>}
    NP: {<JJ>?<N.*>+}
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
    INNP: {<IN><N.*|RB>}
    INNP: {<IN><NP>}
    INNP: {<DDNP|NP|INNP><INNP>}
    DDNP: {<NP><NP>+}
    DDNP: {<NP>+<INNP>+}
    DDNP: {<INNP>+<NP>+}
    DDNP: {<INNP><INNP>+}
    JJJ: {<JJ.*>}
    WRB: {<WRB>}
    RB: {<RB>}
"""


# 품사 우선순위. 한 리스트에 여러 품사가 있을 경우 priority의 앞쪽에 위치한 품사가 대표 품사가 된다.
priority = ['A-TIME', 'NPB', 'INNP', 'DDNP', 'NP', 'VP', 'PP', 'JJJ', 'WRB', 'RB']
ner_priority = ['LOCATION', 'DATE', 'TIME', 'DURATION', 'MONEY', 'PERCENT',
                'MISC', 'ORGANIZATION', 'PERSON', 'NUMBER', 'ORDINAL', 'SET',
                'EMAIL', 'URL', 'CITY', 'STATE_OR_PROVINCE', 'COUNTRY', 'NATIONALITY',
                'RELIGION', 'TITLE', 'IDEOLOGY', 'CRIMINAL_CHARGE', 'CAUSE_OF_DEATH', 'HANDLE', 'O', None]

# 품사 그룹
pos_group = {
    'INNP': 'N', 'NP': 'N', 'DDNP': 'N', 'NPB': 'N',
    'VP': 'V',
    'PP': 'P',
    'JJJ': 'J', 'RB': 'J',
    'A-TIME': 'A', 'A-NOT': 'A'  # 추가적인 정보
}
replace_pos = {
    'not': 'A-NOT',  # 'not'이라는 단어를 품사 'A-NOT'으로 replace
}
ner_group = {
    'ORGANIZATION': 'COUNTRY',
    'COUNTRY': 'COUNTRY',
    'NATIONALITY': 'COUNTRY',
    'RELIGION': 'COUNTRY',
    'LOCATION': 'COUNTRY',
    'CITY': 'COUNTRY',
    'STATE_OR_PROVINCE': 'COUNTRY',
    'PERSON': 'COUNTRY',

    'DATE': 'TIME',
    'TIME': 'TIME',

    'PERCENT': 'NUMBER',
    'NUMBER': 'NUMBER',
    'ORDINAL': 'NUMBER',

    'EMAIL': 'TEXT',
    'URL': 'TEXT',
    'TITLE': 'TEXT',
    'IDEOLOGY': 'TEXT',

    'MISC': 'MISC',
    'MONEY': 'MONEY',
    'SET': 'SET',
    'CRIMINAL_CHARGE': 'CRIMINAL_CHARGE',
    'CAUSE_OF_DEATH': 'CAUSE_OF_DEATH',
    'HANDLE': 'HANDLE',
    'DURATION': 'DURATION',
    'O': 'O',
    None: None,
}

# 제거할 품사들
drops = ['FW', 'LS', 'PDT', 'RB', 'SENT', 'SYM', 'UH', 'DT', 'RBR', 'RBS']
hate_startswith = ['if', 'when', 'whether']  # 이 단어로 시작하는 절은 무조건 삭제

# 무조건 replace할 것들
absolute_replace = {"’s": "'s", "don't": 'not', "n't": ' not', "They're": 'They are', "they're": 'they are',
                    '!': '', '~': '', '^': '', 'did': '', 'does': '', '-': ' ', '\\"': '"', "\\'": "'"}
# absolute_mon = ['January', 'February', 'March', 'April', 'June', 'August', 'September', 'October', 'November', 'Jan',
#                 'July', 'December', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
absolute_mon = []  # stanford NER 사용하므로 더 이상 필요 없음
# absolute_unit = ['years', 'months', 'hours', 'minutes', 'seconds', 'millions', 'hundreds', 'degrees', 'billions',
#                  'trillions', 'thousands']
absolute_unit = []  # stanford NER 사용하므로 더 이상 필요 없음

# 관계대명사 목록
relatives = ['that', 'which', 'who', 'whom', 'whose']

# be 동사 목록
linking_verbs = ['be', 'is', 'were', 'was']

# 목적어절에서 개체명 추출할 때 고려하지 않을 전치사 목록
notIN = ['of']

not_addition = {  # 'not'의 추가 정보 형태
    'word': 'not',            # 단어 ex) 'in 1987'
    'lemma': 'not',           # 원형 ex) 'in 1987'
    'pos': 'NP',              # 품사 (형식적으로 존재함. NP로 고정)
    'ner': 'A-NOT',           # 개체명 ex) 'DATE'
    'normalizedNER': [None],  # 수정된 개체명 (형식적으로 존재함. None으로 고정)
    'timex': None             # 개체명이 시간일 경우 x 표현식으로 표현된 시간 (형식적으로 존재함. None으로 고정)
}
