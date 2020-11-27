textAnalyzer
============

대한민국 온라인 수호 프로젝트, 리페어리의 텍스트 비교 패키지입니다.

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

- FactsDB.delete(group: str) -> None

[group]에 해당하는 json 파일을 삭제합니다.


@staticmethod

- FactsDB.insert(data: Union[List[Dict], Dict]) -> None

[data]를 pretty-print합니다.
