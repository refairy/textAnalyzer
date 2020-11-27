"""
Stanford NER에서 숫자로 NUMBER라는 태그로 관리하는데,
이들끼리 비교하기 위한 타입을 선언한다.
ex) >=200 : 200 이상
"""
import re


class Number:
    def __init__(self, raw: str) -> None:
        """
        num : 숫자
        sign : 부등호 기호
        """
        self.sign: str = '=' if '=' in raw else ''  # ex) '>=200'에서 '>='
        self.sign = ('>' if '>' in raw else '') + self.sign
        self.sign = ('<' if '<' in raw else '') + self.sign
        self.num: float = float(raw.replace(self.sign, ''))   # ex) '>=200'에서 200

    def __eq__(self, other) -> bool:
        if self.sign == other.sign == '':
            # 둘 다 부등호 없을 때 ex) 200, 100 -> 단순 비교하여 반환
            return self.num == other.num

        if self.sign:
            # self.sign != ''일 때
            if self.sign.replace('=', '') == other.sign.replace('=', ''):
                # '=' 제외하고 비교하는 이유 : >=100, >100 이렇게 들어와도 둘은 똑같은 내용임. (정수일 경우 >=100, >=101이라고 볼 수 있으므로)
                # 부등호 똑같을 때 ex) >=100, >=300 -> 무조건 동일
                return True
            else:
                if other.sign:
                    # ex) self: >=100, <300 -> 부호 방향 다를 때
                    if self.sign.replace('=', '') == '<':
                        # 부등호 (<) -> 양수
                        self_num = self.num
                    else:
                        # 부등호 (>) -> 음수
                        self_num = -self.num
                    if other.sign.replace('=', '') == '<':
                        # 부등호 (<) -> 양수
                        other_num = other.num
                    else:
                        # 부등호 (>) -> 음수
                        other_num = -other.num
                    if self_num + other_num > 0:
                        # 더했을 때 양수라면 -> True ex) <300, >100 => 300 + -100 = 200
                        return True
                    if self_num + other_num == 0 and '=' in self.sign and '=' in other.sign:
                        # 모두 '='을 부호에 포함돼 있고 두 값이 같을 때 -> True
                        # ex) <=300, >=300 => 300 + -300 = 0
                        return True
                    return False
                else:
                    # ex) self: >=100, 300 -> self만 부호 있을 때
                    return self.safe_eval(other.num, self.sign, self.num)
        else:
            if other.sign:
                # ex) self: 100, other: >=200
                return self.safe_eval(self.num, other.sign, other.num)

    @staticmethod
    def safe_eval(d1, sign, d2):
        # 조건 연산만 수행하는 eval 함수
        if sign == '>':
            return d1 > d2
        if sign == '>=':
            return d1 >= d2
        if sign == '<':
            return d1 < d2
        if sign == '<=':
            return d1 <= d2

    def __str__(self) -> str:
        return f'Number({self.sign}, {self.num})'


if __name__ == "__main__":
    a = ['1', '127', '>=200', '>100', '<150', '<=200']
    for i in a:
        for j in a:
            print(Number(i), Number(j), Number(i) == Number(j))
    print(Number('1'))
    print(Number('127'))
    print(Number('>=200'))
    print(Number('>200'))
    print(Number('<200'))
    print(Number('<=200'))
