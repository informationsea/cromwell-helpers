import collections
import typing
import io


class TabTable:
    def __init__(self, print_header=True):
        self.rows = list()
        self.print_header = print_header

    def add_row(self, *items):
        self.rows.append(items)

    def p(self, output=None):
        for one in self.rows:
            print('\t'.join([str(x) for x in one]), file=output)


class PrettyTable:
    def __init__(self, column_separator: str = ' | '):
        self.rows: typing.List[typing.Tuple[str, ...]] = list()
        self.column_separator = column_separator

    def add_row(self, *items: str):
        self.rows.append(items)

    def p(self, output: typing.Optional[io.TextIOBase] = None):
        max_column_len: typing.DefaultDict[int, int] = collections.defaultdict(
            int)
        for one_row in self.rows:
            for i, one_column in enumerate(one_row):
                max_column_len[i] = max(len(str(one_column)),
                                        max_column_len[i])
        max_column_list = list(max_column_len.items())
        max_column_list.sort(key=lambda x: x[0])

        format_str = ''
        for i, m in max_column_list:
            if i != 0:
                format_str += self.column_separator
            format_str += '{{:{}}}'.format(m)

        for one in self.rows:
            print(format_str.format(*one), file=output)
