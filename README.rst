textAnalyzer
============

'텍스트 오류 검출'

대한민국 온라인 수호 프로젝트, 리페어리의 텍스트 비교 패키지입니다.

시작하기
--------

poetry 또는 requirements.txt로 필요한 패키지를 다운받으세요.
그 다음 test.py를 실행해 보세요.

.. code-block:: bash

    pip install -r requirements.txt
    # poetry install  # 또는 poetry로 설치
    cd ..  # textAnalyzer도 패키지이기 때문에
    python -m textAnalyzer.test.py

.. contents::

koreanfacts
-----------

FactsDB
- 데이터를 저장, 삭제하는 등의 처리를 하기 위한 API입니다.

methods

- FactsDB.insert(group: str, data: Union[List[Dict], Dict]) -> None

[group]에 해당하는 json 파일을 읽어와 [data]를 저장합니다.

- FactsDB.get(group: str) -> List[Dict]

[group]에 해당하는 json 파일을 읽어와 List[Dict] 형태로 반환합니다.

- FactsDB.get_groups() -> List[str]

[self.data_dir]에서 그룹을 찾아 List[str] 형태로 반환합니다.

- FactsDB.delete(group: str) -> None

[group]에 해당하는 json 파일을 삭제합니다.


@staticmethod

- FactsDB.insert(data: Union[List[Dict], Dict]) -> None

[data]를 pretty-print합니다.


text_analyzer
-------------

Analyzer - 문장을 처리하기 위한 클래스입니다.

- Analyzer.analyze(sentence, augment=True, coref=True, preprocessing=None)

[sentences]의 문장을 분석해 clause, poses, repreproses, additions, addition_poses를 반환합니다.

text_comparison
---------------

- compare(main: dict, sentences: dict)

[sentences]의 문장을 DB의 사실 문장과 비교합니다.

반환 형태

- {'type': 'NO_SIMILAR_DATA'}: [sentences]의 문장이 [main]과 관련이 없습니다.

- {'type': 'CORRECT'}: [sentences]의 문장이 [main]의 내용과 오류 관계에 있지 않습니다.

- {'type': 'ERROR', 'basis': basis}: [sentences]의 문장이 [main]의 내용과 오류 관계에 있습니다.
