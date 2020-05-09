from data.data import Student


def match_students(all_students, still_to_match, moodle_students, condition_mode='normal'):
    if condition_mode == 'normal':
        condition = matches
    else:
        condition = complex_part_matching

    i, j = 0, 0
    while True:
        if len(moodle_students) <= j:
            j = 0
            i += 1

        if len(still_to_match) <= i:
            break

        index, to_match = still_to_match[i]
        possible_match = moodle_students[j]

        if condition(to_match, possible_match):
            to_match.set_moodle_identity(*possible_match)
            print(f"{str(to_match):35} <-> {possible_match[1]} ({possible_match[0]})")
            all_students[index] = to_match
            del still_to_match[i]
            del moodle_students[j]
            j = 0
            continue

        j += 1

    if condition_mode == 'normal' and len(still_to_match) > 0:
        match_students(all_students, still_to_match, moodle_students, condition_mode='complex')


def matches(to_match: Student, possible_match: tuple):
    return same_email(to_match, possible_match) \
           or exact_same_name(to_match, possible_match) \
           or same_first_and_last(to_match, possible_match)


def same_email(to_match: Student, possible_match: tuple) -> bool:
    return to_match.muesli_mail == possible_match[2]


def exact_same_name(to_match: Student, possible_match: tuple) -> bool:
    return to_match.muesli_name == possible_match[1]


def same_first_and_last(to_match: Student, possible_match: tuple) -> bool:
    to_match_parts = to_match.muesli_name.lower().split()
    possible_match_parts = possible_match[1].lower().split()

    return to_match_parts[0] == possible_match_parts[0] and to_match_parts[-1] == possible_match_parts[-1]


def complex_part_matching(to_match: Student, possible_match: tuple) -> bool:
    def normalize(parts):
        parts = [_.strip() for _ in parts if len(_.strip()) > 0]
        parts = [_.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss') for _ in parts]
        parts = [_.replace('.', '') for _ in parts]

        return parts

    to_match_parts = normalize(to_match.muesli_name.lower().split())
    possible_match_parts = normalize(possible_match[1].lower().split())

    i, j = 0, 0
    same_ordered_parts = 0
    while i < len(to_match_parts) and j < len(possible_match_parts):
        if to_match_parts[i] == possible_match_parts[j]:
            i += 1
            j += 1
            same_ordered_parts += 1
        else:
            if len(to_match_parts) > len(possible_match_parts):
                i += 1
            else:
                j += 1

    return same_ordered_parts >= min(len(to_match_parts), len(possible_match_parts))


def print_result_table(still_to_match, moodle_students):
    table_header_left = "In MÜSLI but not in Moodle"
    table_header_right = "In Moodle but not in MÜSLI"
    still_to_match = [student.muesli_name.strip() for i, student in still_to_match]
    moodle_students = [student[1].strip() for student in moodle_students]

    max_len_left = max(len(table_header_left), max(map(len, still_to_match)))
    max_len_right = max(len(table_header_right), max(map(len, moodle_students)))

    print(f" {table_header_left.ljust(max_len_left, ' ')} │ {table_header_right}")
    print('─' * (max_len_left + 2) + '┼' + '─' * (max_len_right + 2))
    for i in range(max(len(still_to_match), len(moodle_students))):
        left_name = f'{still_to_match[i] if i < len(still_to_match) else ""}'.ljust(max_len_left, ' ')
        right_name = f'{moodle_students[i] if i < len(moodle_students) else ""}'.ljust(max_len_right, ' ')
        print(f' {left_name} │ {right_name}')
