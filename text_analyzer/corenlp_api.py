"""
java 기반의 stanford corenlp api를 사용하는 코드
"""
import requests
import re
import json

req_uri = "http://localhost:9000"
req_uri = "https://refairy-ner-ffwfi5ynba-uc.a.run.app"
req_uri += '/?properties={"annotators":"ner"}'


def join_sentences(sentences: list) -> str:
    # 문장을 하나로 연결한다.
    # ex) f(['hello my name is jun.', 'hi!']) -> 'hello my name is jun. \t   hi! \t  '
    return ' '.join([sen + ' \t  ' if re.findall(r'(\. |\.|\! |\!|\? |\?)$', sen) else sen + '. \t  ' for sen in sentences])


def req(sentences: list) -> dict:
    # request & return response
    raw = join_sentences(sentences)
    print('REQUEST')
    res = requests.post(req_uri, data=raw.encode('utf8')).text
    return json.loads(res)


def parse(res: dict) -> tuple:
    # response 파싱
    sentences = res['sentences']
    tokens = []
    tags = []
    for sentence in sentences:
        tokens.append([i['word'] for i in sentence['tokens']])
        tags.extend(sentence['tokens'])

        for mention in sentence['entitymentions']:
            for i in range(mention['docTokenBegin'], mention['docTokenEnd']):
                tags[i]['entitymentions'] = mention

    return tokens, tags


def parse_api(sentences: list) -> dict:
    # req -> parse
    if isinstance(sentences, str):
        sentences = [sentences]
    res = req(sentences)
    return parse(res)


if __name__ == "__main__":
    res = parse_api(['hello 안녕 my name is jun.', 'japanese is korean territory', 'hello my name', 'hi', 'good.',
                     '1.42 hello', 'great.!', 'hello " wow', 'Correct me if wrong, but "whitespace" '
                                                             'is not synonymous with "space characters"',
                     'The current answer marked as correct does not remove',
                     'Comfort women were mainly women and girls that forced into sexual slavery '
                     'by the Imperial Japanese Army in occupied countries and territories before '
                     'and during World War II in 1930, or who participated in the earlier program '
                     'of voluntary prostitution. women that were forced to provide sex to Japanese '
                     'soldiers before and during World War II  in 1930.'])
    res = parse_api(['It is three thousands.', 'The Liancourt Rocks are a group of small islets in the Sea of Japan.'])

    print(res[1])
