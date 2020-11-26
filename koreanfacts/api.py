import os
import io
import json
from typing import Dict, List, Union


class FactsDB:
    def __init__(self, data_dir: str = './db/'):
        """
        Class of the database. Files are managed by groups and also manually editable.
        """
        self.data_dir = data_dir
        if not os.path.isdir(self.data_dir):
            os.mkdir(self.data_dir)

    def get(self, group: str) -> List[Dict]:
        """
        Returns data found from a group.
        """
        filename: str = os.path.join(self.data_dir, f'{group}.json')
        if os.path.exists(filename):
            with io.open(filename, 'r') as f:
                cursor = json.load(f)
            return cursor
        else:
            return []

    def insert(self, group: str, data: Union[List[Dict], Dict]) -> None:
        """
        Inserts data into the file of the group.
        """
        if type(data) == dict:
            data = [data]

        filename: str = os.path.join(self.data_dir, f'{group}.json')

        # create empty file
        if not os.path.isfile(filename):
            with io.open(filename, 'w', encoding='utf-8') as f:
                f.write('[]')

        # update file
        with io.open(filename, 'r+', encoding='utf-8') as f:
            cursor: List[Dict] = json.load(f)
            for d in data:
                if d not in cursor:
                    cursor.append(d)
        with io.open(filename, 'w', encoding='utf-8') as f:
            json.dump(cursor, f, indent=4)

    @staticmethod
    def pprint(data: Union[List[Dict], Dict]) -> None:
        """
        Pretty-prints the data.
        """
        if type(data) == list:
            for d in data:
                formatted = \
                        f'info:         \t{d["info"]}\n' \
                        f'add:          \t{d["add"]}\n'
                print(formatted)

        elif type(data) == dict:
            formatted = ""
            formatted += \
                    f'info:         \t{data["info"]}\n' \
                    f'add:          \t{data["add"]}\n'
            print(formatted)

    def delete(self, group: str) -> None:
        """
        Deletes the group data file.
        """
        filename: str = os.path.join(self.data_dir, f'{group}.json')
        os.remove(filename)
