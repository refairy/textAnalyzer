from koreanfacts.api import FactsDB
from text_analyzer.analyzer import Analyzer
from text_comparison.comparison import compare


if __name__ == "__main__":
    db = FactsDB('./koreanfacts/db')  # db 연결 (KoreanFactsDB)
    anal = Analyzer()

    while True:
        inp = input('Enter sentence:')

        results = anal(inp, augment=False)  # 분석

        print('analyzing result:', results)
        for result in results:
            print(compare(result, db.get('dokdo')))  # 'dokdo' 주제로 오류 검사
