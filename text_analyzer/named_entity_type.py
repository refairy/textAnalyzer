"""
custom type "NamedEntity"
"""


class NamedEntity:
    def __init__(self, data: dict) -> None:
        self.data = data

    def items(self):
        return self.data.items()

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def __getitem__(self, item):
        return self.data[item]

    def __str__(self):
        return f"NamedEntity(text={self.data['text']}, ner={self.data['ner']})"
