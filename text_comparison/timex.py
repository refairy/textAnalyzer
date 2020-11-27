"""
Stanford NER에서 시간을 timex라는 방식으로 표현하는데,
이들끼리 비교하기 위한 타입을 선언한다.
"""
import re


class TimeX:
    def __init__(self, raw: str) -> None:
        """
        timex 형식 : XXXX-XX-XX xx:xx:xx (yyyy-mm-dd hh:mm:ss)
                      <date>    <time>
                    ex) XXXX-08-12 xx:12:xx
        timex 형태 : (<date>, <time>)
                    ex) ('XXXX-08-12', 'xx:12:xx')
        """
        self.timex = self.parse_raw(raw)

    def parse_raw(self, raw: str) -> tuple:
        # raw 텍스트를 timex 형태로 바꾼다.
        # ex) f('XXXX-08') -> 'XXXX-08-XX xx:xx:xx'
        date, time = None, None
        for sec in raw.split(' '):
            if self.is_date(sec):
                date = self.fill(sec, date=True)
                time = 'xx:xx:xx'
            else:
                date = 'XXXX-XX-XX'
                time = self.fill(sec, date=False)

        return date, time

    def fill(self, raw: str, date: bool=True) -> str:
        # <date>의 부족한 부분을 채운다.
        # ex) f('XXXX-08', date=True) -> 'XXXX-08-XX'
        if date:
            # <date> : XXXX-XX-XX
            sep = '-'
            shape = ['XXXX', 'XX', 'XX']
        else:
            # <time> : xx:xx:xx
            sep = ':'
            shape = ['xx', 'xx', 'xx']
            raw = raw.replace('PT', '').replace('T', '')
            # 'PT20M' 이런 경우라면
            for i in range(len('HMS')):
                hms = 'HMS'[i]
                if hms in raw:
                    raw = raw.replace(hms, '')
                    attach = sep.join(shape[:i]) + sep
                    if not attach == sep:
                        raw = attach + raw
                    break

        attach = sep + sep.join(shape[raw.count(sep)+1:])
        if not attach == sep:
            raw += attach
        return raw

    def is_date(self, raw: str) -> bool:
        # raw가 <date>인지 판단한다.
        # ex) f('XXXX-08') -> True
        if raw[0] == 'T' or raw[:2] == 'PT':
            # ex) PT10M ('T' 혹은 'PT'가 앞에 오는 것은 <time> 특징임)
            return False
        if ':' in raw:
            # ex) T15:12 (':' 들어 있으면 <time>)
            return False

        if '-' in raw:
            # ex) XXXX-08 (하이픈 들어있을 때)
            return True
        if re.match(r'^\d{4}$', raw):
            # ex) 1567 (4자리 정수)
            return True
        if 'X' in raw:
            # ex) 15XX ('X' 대문자 엑스가 포함돼 있을 때)
            return True
        return False

    def is_time(self, raw: str) -> bool:
        # raw가 <time>인지 판단한다.
        # ex) f('PT10M') -> True
        return not self.is_date(raw)

    def rm_start0(self, s):
        # s에서 0으로 시작하는 부분 제거
        # ex) f('09') -> 9
        while s.startswith('0'):
            s = s[1:]
        return s

    def strcmp(self, s1, s2, x='X'):
        # 왼쪽에서 한 글자씩 비교한다. 'X'는 깍두기
        # ex) f('1234', '123X') -> True
        #     f('123X', '1324') -> False
        s1 = self.rm_start0(s1)  # '09' -> '9'
        s2 = self.rm_start0(s2)  # '09' -> '9'

        if set(s1) == {x} or set(s2) == {x}:
            # 둘 중 하나라도 'XX'처럼 x만 존재할 경우 깍두기이므로
            # 무조건 True임
            return True

        # 길이가 다르면? -> 무조건 다른 것
        if len(s1) != len(s2):
            return False

        # 한 글자씩 비교
        for i in range(len(s1)):
            if s1[i] != s2[i] and s1[i] != x and s2[i] != x:
                return False
        return True

    def __eq__(self, other):
        # TimeX끼리 비교
        # <date> 비교
        for i, other_d in enumerate(other.timex[0].split('-')):
            d = self.timex[0].split('-')[i]  # self.timex
            print(other_d, d)
            if not self.strcmp(other_d, d):  # 비교
                # 만약 다르다면? -> False
                return False
        # <time> 비교
        for i, other_t in enumerate(other.timex[1].split(':')):
            t = self.timex[1].split(':')[i]  # self.timex
            print(other_t, t)
            if not self.strcmp(other_t, t, x='x'):  # 비교
                # 만약 다르다면? -> False
                return False
        # 같을 경우 -> True
        return True

    def __str__(self):
        return ' '.join(self.timex)


if __name__ == "__main__":
    print(TimeX('15XX').timex)
    print(TimeX('XXXX-10').timex)
    print(TimeX('XXXX-10-23').timex)
    print(TimeX('XXXX-08-15').timex)
    print(TimeX('T15:12').timex)
    print(TimeX('T01:00').timex)
    print(TimeX('PT1000M').timex)
    print(TimeX('PT2H').timex)
    print(TimeX('PT20S').timex)

    print(TimeX('1000-9') == TimeX('XXXX-09-23'))
    print(TimeX('1978-08-12') == TimeX('XXXX-08-12'))
