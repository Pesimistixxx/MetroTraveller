def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def find_closest_matches(data, query, threshold=10, max_results=6):
    query_lower = query.lower()
    results = []
    if query in data:
        return query
    for item in data:
        parts = item.split(' ', 1)
        if len(parts) < 2:
            continue

        number, name = parts
        name_lower = name.lower()
        name_without_line = '_'.join(name_lower.split('_')[:-1])

        distance = levenshtein_distance(query_lower, name_without_line)
        is_substring = query_lower in name_lower

        if distance <= threshold or is_substring:
            position_bonus = 0
            if is_substring:
                start_index = name_lower.find(query_lower)
                position_bonus = 100 - start_index * 10

            adjusted_distance = distance - position_bonus
            results.append((adjusted_distance, int(number), name))
    if not results:
        return []
    min_distance = min(result[0] for result in results)
    best_results = [result for result in results if result[0] == min_distance]
    return [name for _, _, name in best_results]


data = []

with open('stations_data.txt', 'r') as f:
    for line in f.readlines():
        data.append(line.strip())

