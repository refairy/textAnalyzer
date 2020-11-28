"""
여러 문장의 오류를 검사하는 함수
"""
from ..koreanfacts.api import FactsDB
from ..text_analyzer.analyzer import Analyzer
from ..text_analyzer.corenlp_api import join_sentences
from ..text_comparison.comparison import compare
from .options import OPT2
from .utils import flatten


def init():
    # 각종 함수나 변수를 선언한다.
    global anal, db
    anal = Analyzer()
    import os
    print('os.path.isdir:', os.path.isdir('./refairy_api/textAnalyzer/koreanfacts/db'))
    print('os.listdir:', os.listdir())
    db = FactsDB('./refairy_api/textAnalyzer/koreanfacts/db')  # db 연결
    print('db.get_groups:', db.get_groups())


class Check:
    def __init__(self):
        self.progress = 0  # 몇 개의 문장 분석 완료했는가?
        self.response = None  # check() 결과
        self.finished = False

    def check(self, sentences: list):
        # ex) sentences = ['hello my name is', 'blah blah blah.', ...]

        self.finished = False
        self.response = []  # 최종 결과 ex) [ {'origin': ..}, {'origin': ..}, ..]
        self.progress = 0

        # 대명사 제거
        sentences, sentences_d = self.coreference(sentences)

        # 오류 검출
        for chunk_i in range(0, len(sentences), OPT2['n_chunk']):  # NER 분석을 하나씩 하면 요청이 많아지므로 n_chunk개 씩 합쳐서 진행
            current_sentences = sentences[chunk_i:OPT2['n_chunk']+chunk_i]  # 분석할 문장들
            current_string = join_sentences(current_sentences)  # 분석할 문장들 합치기
            tokens, api_tags, quotes = anal.preprocessing(current_string, coref=False)  # 전처리 + NER
            api_tags = anal.like(tokens, api_tags)  # api_tags의 형태를 tokens와 동일하게 변경
            preprocessed_sentences = self.simple_preprocessings(current_sentences)  # 전처리 (NER은 안 함)
            for i, tk in enumerate(tokens):
                # tk : 토큰 ex) ['hello','my','name','is']
                self.progress += 1
                if tk[-1] == '.':  # 마지막에 .이 있다면 -> 제거 (마침표는 이전 과정에서 없다가 생겼을 가능성이 크므로)
                    tk = tk[:-1]
                if not tk:
                    # tk가 비어있다면?
                    continue

                origins = []  # 원래 문장 (응답의 origin과 동일)
                for j in range(len(preprocessed_sentences)):
                    if ''.join(tk).replace(' ', '') in preprocessed_sentences[j].replace(' ', ''):
                        # 전처리한 문장(tokens)과 대명사 제거된 문장(preprocessed_sentences)이 일치한다면?
                        # -> 원래 문장임
                        origins.extend(self.seek(sentences_d, current_sentences[j]))

                if not origins:
                    # 지금 분석하려는 문장이 원래 어떤 문장이었는지 모르면? -> 스킵
                    continue

                # 정보 확장, 대명사 제거 하지 않고 분석
                # try:
                results = anal('', augment=False,  # sentence 대신 토크나이징된 것 들어가므로 sentence는 무슨 값이든 상관X
                                   coref=False, preprocessing=([tk], api_tags[i], quotes))
                # except Exception as err:
                #     # 오류날 경우 -> 무시
                #     print("Error: {} (in check() -> anal())".format(err))
                #     continue

                if results == -1:
                    # bad sentence (일부러 분석 안 하도록 설정한 문장)일 경우 ex) 의문문
                    continue

                for result in results:
                    # result : data 하나 ex) {'info': ...}
                    for group in db.get_groups():
                        # 특정 group에 대해 오류 여부 검사

                        compare_result = compare(result, db.get(group))  # 오류 검사

                        if compare_result['type'] in ['NO_SIMILAR_DATA', 'CORRECT']:
                            # 오류 없다면? -> 스킵
                            continue
                        elif compare_result['type'] == 'ERROR':
                            # 오류 있다면? -> dict 형태로 보고서 만들어서 반환 결과에 저장
                            corrected = ' '.join(flatten(compare_result['basis'][0]))  # 올바른 문장
                            for origin in origins:
                                report = {
                                    "origin": origin,  # 원래 문장
                                    "is_wrong": True,  # 오류인가?
                                    "category": group,  # 그룹
                                    "corrected": corrected,  # 올바른 문장
                                    "confidence": 1.0  # confidence (측정 기능 안 만들어서 1.0로 고정)
                                }
                                self.response.append(report)  # response에 dict 추가
                                print('report:', report)

        self.finished = True  # 종료 알리기
        return self.response

    @staticmethod
    def simple_preprocessings(sentences: list):
        # 여러 문장을 전처리한다. (NER은 하지 않음)
        r = []
        for sentence in sentences:
            sentence = anal.absolute_replace(sentence)
            sentence, _ = anal.mask_quotes(sentence)
            r.append(sentence)
        return r

    @staticmethod
    def seek(sentences_d: dict, sen: str):
        # sentences_d에서 value가 sen을 포함된 key를 찾아 반환한다.
        return [key for key, value in sentences_d.items() if sen.replace(' ', '') in value.replace(' ', '')]

    @staticmethod
    def coreference(sentences: list) -> tuple:
        # 리스트를 한 문장으로 합치고 대명사를 제거한 결과를 반환하고,
        # 그와 함께 원래 문장과 대응하는 dictionary도 반환한다.

        # 한 문장으로 합치기
        sep = OPT2['sep']
        while True:  # 구분자가 이미 문장 안에 있다면? -> 문장 안에 없는 걸로 구분자 만들기
            if sum([sep in sen for sen in sentences]):
                sep += ' '
            else:
                break
        string = sep.join(sentences)

        # 대명사 제거
        string = anal.coref(string)
        uncoref_setences = string.split(sep)

        # sentences와 uncoref_sentences 대응하는 dict 만들기
        sentences_d = {sen: unc_sen for sen, unc_sen in zip(sentences, uncoref_setences)}

        return uncoref_setences, sentences_d


if __name__ == "__main__":
    sentences = ['Skip to main content FAQ Site Map Links ', 'Countries & Regions',
                 'Top\xa0>\xa0Foreign Policy\xa0>\xa0Others\xa0>\xa0Japanese Territory\xa0>\xa0Takeshima',
                 'April 23, 2020', '  ', 'Japan’s Consistent Position on the Territorial Sovereignty over Takeshima',
                 'Takeshima is indisputably an inherent part of the territory of Japan, in light of '
                 'historical facts and based on international law.',
                 'The Republic of Korea has been occupying Takeshima with no basis in international law. '
                 'Any measures the Republic of Korea takes regarding Takeshima based on such an illegal '
                 'occupation have no legal justification.',
                 'Japan will continue to seek the settlement of the dispute over territorial sovereignty over '
                 'Takeshima on the basis of international law in a calm and peaceful manner.',
                 "Note: The Republic of Korea has never demonstrated any clear basis for its claims that it had taken "
                 "effective control over Takeshima prior to Japan's effective control over Takeshima and reaffirmation "
                 "of its territorial sovereignty in 1905.",
                 'Video:Takeshima - Seeking a Solution based on Law and Dialogue',
                 'Pamphlet: Takeshima\u3000(10 pages) (PDF)', '10 points to understand the Takeshima Dispute (PDF)',
                 'Recognition of Takeshima', 'Sovereignty over Takeshima', 'Prohibition of Passage to Utsuryo Island',
                 'Incorporation of Takeshima into Shimane Prefecture', 'Takeshima Immediately After World War II',
                 'Treatment of Takeshima in the San Francisco Peace Treaty',
                 'Takeshima as a Bombing Range for the U.S. Forces',
                 'Establishment of “Syngman Rhee Line” and Illegal Occupation of Takeshima by the Republic of Korea',
                 'Proposal of Referral to the International Court of Justice', 'Q&A About the Takeshima Dispute',
                 'Japan-Republic of Korea Relations', ' (Open a New Window)', 'Back to Japanese Territory',
                 'Embassies & Consulates', 'About this Site', 'Interviews & Articles',
                 "Japan's Security / Peace & Stability of the International Community", 'Global Issues & ODA',
                 'Countries & Regions', 'Latin America and the Caribbean', 'Residing in Japan',
                 'Information about Japan (Links)', 'The Hague Convention',
                 'Legal Matters Accessibility Privacy Policy About this Site',
                 'Copyright © Ministry of Foreign Affairs of Japan',
                 'Ministry of Foreign Affairs of Japan 2-2-1 Kasumigaseki, Chiyoda-ku, Tokyo 100-8919, '
                 'Japan MAPPhone: +81-(0)3-3580-3311\xa0\xa0Japan Corporate Number(JCN): 9000012040001']

    with open('test.txt', 'r', encoding='utf8') as f:
        sentences = eval(f.read())

    print(sentences)

    init()

    ch = Check()

    print(ch.check(sentences))
