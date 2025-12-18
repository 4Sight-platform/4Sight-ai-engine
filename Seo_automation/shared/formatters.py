def format_table(data: list, headers: list) -> str:
    rows = [headers] + [[str(row.get(h, '')) for h in headers] for row in data]
    col_widths = [max(len(str(row[i])) for row in rows) for i in range(len(headers))]
    return '\n'.join([' | '.join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers))) for row in rows])
