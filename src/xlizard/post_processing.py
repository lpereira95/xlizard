
# TODO: review


def get_function_content(global_content, function, keep_children=True):
    if keep_children:
        return global_content[function.start:function.end + 1]

    no_children_indices = [[function.start]]
    for child_span in function.children_spans:
        start, end = child_span

        no_children_indices[-1].append(start)
        no_children_indices.append([end + 1])
    no_children_indices[-1].append(function.end + 1)

    return ''.join([global_content[start:end] for start, end in no_children_indices])


def get_function_clean_content(global_content, function, keep_lines=True):
    """Gets content without comments.

    If `keep_lines`, then comments are simply replaced by empty spaces.
    For now it removes children.
    """
    # TODO: add ability to keep children

    clean_content_indices = [[function.start]]
    nlines = []

    comments_spans = function.comments_spans
    children_spans = function.children_spans
    comment_start = comments_spans[0][0] if len(comments_spans) else function.end + 1
    child_start = children_spans[0][0] if len(children_spans) else function.end + 1

    pointer_comment, pointer_child = 0, 0
    for _ in range(len(comments_spans) + len(children_spans)):
        if comment_start < child_start:
            span = comments_spans[pointer_comment]
            pointer_comment += 1
            is_comment = True
            try:
                comment_start = comments_spans[pointer_comment][0]
            except IndexError:
                comment_start = function.end + 1
        else:
            span = children_spans[pointer_child]
            pointer_child += 1
            is_comment = False
            try:
                child_start = children_spans[pointer_child][0]
            except IndexError:
                child_start = function.end + 1

        start, end = span

        if is_comment:
            n_newlines = global_content[start:end + 1].count('\n') if keep_lines else 0
        else:
            n_newlines = 0
        nlines.append(n_newlines)

        clean_content_indices[-1].append(start)
        clean_content_indices.append([end + 1])

    nlines.append(0)
    clean_content_indices[-1].append(function.end + 1)

    return ''.join([global_content[start:end] + '\n' * n_lines
                    for (start, end), n_lines in zip(clean_content_indices, nlines)])
