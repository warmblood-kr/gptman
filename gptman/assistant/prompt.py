from gptman.exceptions import PreambleNotFound


def read_prompt_file(path):
    with open(path) as fin:
        body = fin.read()
        return parse_markdown_with_preamble(body)


def write_prompt_file(path, data: dict):
    temp_data = {**data}
    instructions = temp_data.pop('instructions')
    with open(path, 'w') as fout:
        fout.write('---\n')
        for k, v in temp_data.items():
            fout.write(f'{k}: {v}\n')
        if temp_data:
            fout.write('---\n')
        fout.write(instructions or '')
        fout.write('\n')


def parse_markdown_with_preamble(text):
    lines = text.split('\n')
    if not lines[0].startswith('---'):
        raise PreambleNotFound()

    data = {}

    for idx, line in enumerate(lines[1:], 1):
        if line.startswith('---'):
            data['instructions'] = '\n'.join(lines[idx+1:])
            return data

        entry = parse_preamble_data(line)
        if entry:
            k, v = entry
            data[k] = v

    raise PreambleNotFound()


def parse_preamble_data(line):
    if not line:
        return
    k, v = line.split(':', 1)
    return k, v.strip()
