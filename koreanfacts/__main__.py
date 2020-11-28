from .api import FactsDB


if __name__ == "__main__":
    db = FactsDB()

    data = [
        {
            "group": "dokdo",
            "info": ["Dokdo", "be call", ["Takeshima", ["in Japan"]]],
            "add": ["in 1924"],
            "ner": ["territory", "of", "COUNTRY"],
        },
        {
            "group": "dokdo",
            "info": ["Dokdo", "be call", ["Dokdo", ["in Korea"]]],
            "add": ["now"],
            "ner": ["territory", "of", "COUNTRY"],
        },
        {
            "group": "dokdo",
            "info": ["HI"],
            "add": ["HI"],
            "ner": ["HI"],
        },
    ]
    data2 = {
            "group": "dokdo",
            "info": ["Hello", "world!"],
            "add": ["hw"],
            "ner": ["hw"],
    }
    db.insert('dokdo', data2)
    db.insert('dokdo', data)

    print(db.get_groups())

    print(db.get('dokdo'))
    db.insert('dokdo', data)
    print(db.get('dokdo'))
    db.insert('dokdo', data2)
    print(db.get('dokdo'))
