# -*- coding: utf-8 -*-
import json
import yaml
import pypandoc
import re

PANDOC_SPAN_TYPES = {
    "Strong": "span-strong",
    "Emph": "span-emphasized",
    "Strikeout": "span-strikeout"
}
CHARACTER_TYPES = {
    "Space": " ",
    "DoubleQuote": '"',
    "SingleQuote": "'",
    "SoftBreak": "\n"
}


def create_span(span_type: str, content: str) -> dict:
    if span_type == "span-listing":
        return {"type": "span-listing", "listing_text": content}
    return {"type": span_type, "text": content}


def consume_str(span_list: list) -> str:
    text = ""
    for elem in span_list:
        if elem['t'] in CHARACTER_TYPES.keys():
            text += CHARACTER_TYPES[elem['t']]
            continue
        if elem['t'] == "Str":
            text += elem['c']
            continue
        if 'c' in elem.keys() and type(elem['c']) is list:
            text += consume_str(elem['c'])
            continue
        raise SyntaxError("Unable to consume: " + str(elem))
    return text


def convert_list_text_only(elem_list: list) -> str:
    def extract_elem_text(accumulated_text: str, elem: dict):
        if elem['t'] == "Para":
            accumulated_text += convert_list_text_only(elem['c']) + "\n"
            return accumulated_text
        if elem['t'] == "Quoted":
            if type(elem['c'][0]) is dict:
                accumulated_text = extract_elem_text(accumulated_text, elem['c'][0])
                accumulated_text += convert_list_text_only(elem['c'][1])
                accumulated_text = extract_elem_text(accumulated_text, elem['c'][0])
            else:
                accumulated_text += elem['c'][0] + convert_list_text_only(elem['c'][1]) + elem['c'][0]
            return accumulated_text
        if elem['t'] == "SoftBreak":
            accumulated_text += " "
            return accumulated_text
        if elem['t'] in CHARACTER_TYPES.keys():
            accumulated_text += CHARACTER_TYPES[elem['t']]
            return accumulated_text
        if elem['t'] == "Str":
            accumulated_text += elem['c']
            return accumulated_text
        if elem['t'] == "Emph":
            accumulated_text += "*" + convert_list_text_only(elem['c']) + "*"
            return accumulated_text
        if elem['t'] == "Strong":
            accumulated_text += "**" + convert_list_text_only(elem['c']) + "**"
            return accumulated_text
        if elem['t'] == "Strikeout":
            accumulated_text += "~~" + convert_list_text_only(elem['c']) + "~~"
            return accumulated_text
        if elem['t'] == "Code":
            accumulated_text += elem['c'][1]
            return accumulated_text
        if elem['t'] == "Link":
            accumulated_text += consume_str(elem['c'][1])
            return accumulated_text
        if elem['t'] == "RawInline" and len(elem['c']) >= 3 and elem['c'][0] == "html":
            accumulated_text += convert_list_text_only(elem['c'][2])
            return accumulated_text
        if elem['t'] in PANDOC_SPAN_TYPES.keys():
            accumulated_text += convert_list_text_only(elem['c'])
            return accumulated_text

    text = ""
    for element in elem_list:
        text = extract_elem_text(text, element)
    return text


def convert_list_for_caption_spans(span_list: list, span_type: str = "caption-span-regular") -> list:
    def convert_elem(spans: list, span_elem: dict) -> None:
        if span_elem['t'] in ["Plain", "Para"]:
            spans.append(create_span(span_type, convert_list_text_only(span_elem['c'])))
            return
        if span_elem['t'] in CHARACTER_TYPES.keys():
            spans.append(create_span(span_type, CHARACTER_TYPES[span_elem['t']]))
            return
        if span_elem['t'] == "Str":
            spans.append(create_span(span_type, span_elem['c']))
            return
        if span_elem['t'] == "Emph":
            spans.append(create_span("caption-span-emphasized", convert_list_text_only(span_elem['c'])))
            return
        if span_elem['t'] == "Strong":
            spans.append(create_span("caption-span-strong", convert_list_text_only(span_elem['c'])))
            return
        if span_elem['t'] == "Link":
            spans.append({
                "type": "caption-span-link",
                "link_text": consume_str(span_elem['c'][1]),
                "url": span_elem['c'][2][0]
            })
            return

    def merge_list(long_span_list: list) -> None:
        pos = 0
        while len(long_span_list) > pos+1:
            if long_span_list[pos]['type'] == long_span_list[pos + 1]['type']:
                content_key = "text"
                pop_item = long_span_list.pop(pos + 1)
                long_span_list[pos][content_key] += pop_item[content_key]
            else:
                pos += 1

    converted_spans = []
    for span_element in span_list:
        convert_elem(converted_spans, span_element)
    merge_list(converted_spans)
    return converted_spans


def convert_list(span_list: list, block_list: list, span_type: str = "span-regular", indent: str = "") -> list:
    def convert_elem(spans: list, span_elem: dict) -> None:
        if span_elem['t'] == "Quoted":
            if type(span_elem['c'][0]) is dict:
                spans += convert_list([span_elem['c'][0]] +
                                      span_elem['c'][1] +
                                      [span_elem['c'][0]],
                                      block_list, span_type,
                                      indent + "  ")
            else:
                spans += convert_list([{'t': 'Str', 'c': span_elem['c'][0]}] +
                                      span_elem['c'][1] +
                                      [{'t': 'Str', 'c': span_elem['c'][0]}],
                                      block_list, span_type,
                                      indent + "  ")
            return
        if span_elem['t'] in ["Plain", "Para"]:
            spans.append({"type": "span-container",
                          "spans": convert_list(span_elem['c'], block_list, span_type, indent + "  ")})
            return
        if span_elem['t'] in CHARACTER_TYPES.keys():
            spans.append(create_span(span_type, CHARACTER_TYPES[span_elem['t']]))
            return
        if span_elem['t'] == "Str":
            spans.append(create_span(span_type, span_elem['c']))
            return
        if span_elem['t'] == "Code":
            spans.append(create_span("span-listing", span_elem['c'][1]))
            return
        if span_elem['t'] == "RawInline" and span_elem['c'][0] == "html" and span_elem['c'][1] == "</fs-path>" \
                and len(span_elem['c']) >= 3:
            spans.append({"type": "span-path", "path": convert_list_text_only(span_elem['c'][2])})
            return
        if span_elem['t'] == "RawInline" and span_elem['c'][0] == "html" and span_elem['c'][1] == "</program-name>" \
                and len(span_elem['c']) >= 3:
            spans.append({"type": "span-program", "program_name": convert_list_text_only(span_elem['c'][2])})
            return
        if span_elem['t'] == "RawInline" and span_elem['c'][0] == "html" and \
                span_elem['c'][1].startswith("<ctlink") and span_elem['c'][1].endswith("/>"):
            spans.append({"type": "span-ct-link"})
            return
        if span_elem['t'] == "RawInline" and span_elem['c'][0] == "html" and span_elem['c'][1] == "</abbr>" \
                and len(span_elem['c']) >= 3:
            abbr_long = ""
            for child_pos, child in enumerate(span_elem['c'][2]):
                if child['t'] == "RawInline" and child['c'][0] == "html" and child['c'][1] == "</abbr-long>" \
                        and len(child['c']) >= 3:
                    abbr_long = convert_list_text_only([span_elem['c'][2].pop(child_pos)])
                    break
            spans.append({"type": "span-abbreviation",
                          "abbreviation": convert_list_text_only(span_elem['c'][2]),
                          "long_name": abbr_long})
            return
        if span_elem['t'] == "Link":
            spans.append({
                "type": "span-link",
                "link_text": consume_str(span_elem['c'][1]),
                "url": span_elem['c'][2][0]
            })
            return
        if span_elem['t'] in PANDOC_SPAN_TYPES.keys() and span_type in PANDOC_SPAN_TYPES.values():
            spans += convert_list(span_elem['c'], block_list, "span-strong-emphasized", indent + "  ")
            return
        if span_elem['t'] in PANDOC_SPAN_TYPES.keys():
            spans += convert_list(span_elem['c'], block_list, PANDOC_SPAN_TYPES[span_elem['t']], indent + "  ")
            return
        if span_elem['t'] == "Image":
            block_list.append({
                "type": "block-image",
                "image_uri": span_elem['c'][2][0],
                "caption": convert_list_for_caption_spans(span_elem['c'][1]),
                "alt": span_elem['c'][2][1]
            })
            return
        raise SyntaxError(indent + "Unknown type: " + str(span_elem))

    def merge_list(long_span_list: list) -> None:
        pos = 0
        while len(long_span_list) > pos+1:
            if long_span_list[pos]['type'] == long_span_list[pos + 1]['type']:
                content_key = "text"
                if long_span_list[pos]['type'] == "span-listing":
                    content_key = "listing_text"
                elif long_span_list[pos]['type'] == "span-container":
                    content_key = "spans"
                pop_item = long_span_list.pop(pos + 1)
                long_span_list[pos][content_key] += pop_item[content_key]
            else:
                pos += 1

    converted_spans = []
    for span_element in span_list:
        convert_elem(converted_spans, span_element)
    merge_list(converted_spans)
    return converted_spans


def json_from_markdown(markdown: str) -> list:
    def add_to_asset_list(asset_block: dict) -> None:
        if unfinished_key is not None:
            unfinished_block[unfinished_key].append(asset_block)
        else:
            block_assets_list.append(asset_block)

    def extract_list_items(list_block_items: list) -> list:
        items = []
        for para in list_block_items:
            paras_list = []
            if len(para) > 0:
                paras_list.append(convert_list(para[:1],
                                               block_assets_list
                                               if unfinished_key is None else
                                               unfinished_block[unfinished_key]
                                               )[0])
            if len(para) > 1:
                paras_list.append({"type": "span-line-break-container",
                                   "spans": convert_list(para[1:],
                                                         block_assets_list
                                                         if unfinished_key is None else
                                                         unfinished_block[unfinished_key])})
            items.append({"type": "span-container", "spans": paras_list})
        return items

    def is_typed_sublist(o: dict) -> bool:
        if 'c' not in o.keys():
            return False
        if type(o['c']) is not list:
            return False
        child_list = o['c']
        if o['t'] == 'OrderedList':
            child_list = o['c'][1][0]
        elif o['t'] == 'BulletList':
            child_list = o['c'][0]
        all_typed = True
        for child_item in child_list:
            if type(child_item) is not dict or 't' not in child_item.keys():
                all_typed = False
        return all_typed

    def collect_html_content(o_list: list, html_content: dict, current_tag_stack: list) -> dict:
        def merge_content(old_content: dict, new_content: dict):
            for content_key in new_content.keys():
                if content_key in old_content.keys():
                    old_content[content_key] += new_content[content_key]
                else:
                    old_content[content_key] = new_content[content_key]

        i = 0
        while i < len(o_list):
            o = o_list[i]
            if is_typed_sublist(o):
                if o['t'] == 'OrderedList':
                    for item_spans in o['c'][1]:
                        merge_content(html_content,
                                      collect_html_content(item_spans, html_content, current_tag_stack))
                elif o['t'] == 'BulletList':
                    for item_spans in o['c']:
                        merge_content(html_content,
                                      collect_html_content(item_spans, html_content, current_tag_stack))
                else:
                    merge_content(html_content,
                                  collect_html_content(o['c'], html_content, current_tag_stack))
            if o['t'] in ['RawInline'] and o['c'][0] == 'html':
                html_regex_matches = re.finditer(r"^<(?P<end_tag>/)?(?P<tag_name>[\w\-_]+)(?P<empty_tag>[ ]?/)?>$",
                                      o['c'][1])
                for match in html_regex_matches:
                    if match.group('empty_tag') is not None:
                        o['c'].append([])
                        i += 1
                        break
                    if match.group('end_tag') is None:
                        if match.group('tag_name') not in html_content.keys():
                            html_content[match.group('tag_name')] = [[]]
                        else:
                            html_content[match.group('tag_name')].append([])
                        current_tag_stack.append(match.group('tag_name'))
                        o_list.pop(i)
                        break
                    else:  # closing tag
                        for current_tag_stack_counter in range(len(current_tag_stack)-1, -1, -1):
                            if current_tag_stack[current_tag_stack_counter] == match.group('tag_name'):
                                current_tag_stack.pop(current_tag_stack_counter)
                        o['c'].append(html_content[match.group('tag_name')].pop(-1))
                        if len(html_content[match.group('tag_name')]) == 0:
                            html_content.pop(match.group('tag_name'), None)
                        if len(current_tag_stack) > 0:
                            html_content[current_tag_stack[-1]][-1].append(o)
                            o_list.pop(i)
                        else:
                            i += 1
                        break
                continue
            else:
                if len(current_tag_stack) > 0:
                    html_content[current_tag_stack[-1]][-1].append(o)
                    o_list.pop(i)
                else:
                    i += 1
        return html_content

    def replace_specials(tree: dict):
        for tree_key in tree.keys():
            if type(tree[tree_key]) is dict:
                tree[tree_key] = replace_specials(tree[tree_key])
            elif type(tree[tree_key]) in [float, int]:
                tree[tree_key] = str(tree[tree_key])
            elif tree[tree_key] in ['<ctlink />', '<ctlink/>']:
                tree[tree_key] = {'type': 'span-ct-link'}
        return tree

    def replace_specials_list(element_list: list):
        for i, element_list_item in enumerate(element_list):
            if type(element_list_item) is list:
                element_list[i] = replace_specials_list(element_list_item)
            elif type(element_list_item) is dict:
                element_list[i] = replace_specials(element_list_item)
        return element_list


    block_assets_list = []
    pandoc_tree = json.loads(pypandoc.convert_text(markdown, to='json', format='markdown_github-smart',
                                                   extra_args=['--preserve-tabs']))
    # print(json.dumps(pandoc_tree, indent=2))
    collect_html_content(pandoc_tree['blocks'], {}, current_tag_stack=[])

    unfinished_block = {}
    unfinished_key = None
    for block in pandoc_tree['blocks']:
        if block['t'] == 'Para':
            paragraph_asset = {"type": 'block-paragraph',
                               "spans": convert_list(block['c'],
                                                     block_assets_list if unfinished_key is None else
                                                     unfinished_block[unfinished_key])}
            if len(paragraph_asset["spans"]) > 0:
                add_to_asset_list(paragraph_asset)
        elif block['t'] == 'Header':
            header_asset = {"type": "block-" + "sub"*(block['c'][0]-1) + "heading",
                            "heading": convert_list_text_only(block['c'][2])}
            add_to_asset_list(header_asset)
        elif block['t'] == 'BlockQuote':
            quote_asset = {"type": 'block-citation',
                           "statement": convert_list_text_only(block['c']),
                           "attribution": ""}
            add_to_asset_list(quote_asset)
        elif block['t'] == 'OrderedList':
            list_asset = {"type": "block-ordered-list", "items": extract_list_items(block['c'][1])}
            add_to_asset_list(list_asset)
        elif block['t'] == 'BulletList':
            list_asset = {"type": "block-unordered-list", "items": extract_list_items(block['c'])}
            add_to_asset_list(list_asset)
        elif block['t'] == 'CodeBlock':
            code_asset = {"type": 'block-listing',
                          "language": block['c'][0][1][0],
                          "code": block['c'][1]}
            add_to_asset_list(code_asset)
        elif block['t'] == "RawBlock":
            yaml_regex = r"^<!---(?P<yaml>[\s\S]*?)-->$"
            matches = re.match(yaml_regex, block['c'][1])
            if matches:
                yaml_tree = yaml.safe_load(matches.groupdict()['yaml'])
                if yaml_tree is None:
                    yaml_tree = {}
                block_with_markdown = False  # type: bool
                for key in yaml_tree:
                    if yaml_tree[key] in ["MD_BLOCK", "MD_BLOCK\n",
                                          "MD-BLOCK", "MD-BLOCK\n",
                                          "MDBLOCK", "MDBLOCK\n"]:
                        block_with_markdown = True
                        unfinished_key = key
                        unfinished_block[key] = []
                    else:
                        if type(yaml_tree[key]) is list:
                            unfinished_block[key] = replace_specials_list(yaml_tree[key])
                        elif type(yaml_tree[key]) is dict:
                            unfinished_block[key] = replace_specials(yaml_tree[key])
                        else:
                            unfinished_block[key] = str(yaml_tree[key])
                if block_with_markdown is False:
                    block_assets_list.append(unfinished_block)
                    unfinished_block = {}
                    unfinished_key = None
    return block_assets_list
