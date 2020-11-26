from .api import FactsDB


if __name__ == "__main__":
    db = FactsDB()

    data = [
        {
            "group": "dokdo",
            "info": ["Dokdo", "be call", ["Takeshima", ["in Japan"]]],
            "add": ["in 1924"],
        },
        {
            "group": "dokdo",
            "info": ["Dokdo", "be call", ["Dokdo", ["in Korea"]]],
            "add": ["now"],
        },
        {
            "group": "dokdo",
            "info": ["HI"],
            "add": ["HI"],
        },
    ]
    db.insert('dokdo', data)
    print(db.get('dokdo'))
    db.pprint(data)
    db.delete('dokdo')
    print(db.get('dokdo'))
