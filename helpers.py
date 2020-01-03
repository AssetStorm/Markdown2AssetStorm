# -*- coding: utf-8 -*-
import json
import yaml
import pypandoc
import re

PANDOC_SPAN_TYPES = {
    "Strong": "span-strong",
    "Emph": "span-emphasized"
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
        raise SyntaxError("unable to consume:" + str(elem))
    return text


def convert_list_text_only(elem_list: list) -> str:
    def extract_elem_text(accumulated_text: str, elem: dict):
        if elem['t'] == "Para":
            accumulated_text += convert_list_text_only(elem['c']) + "\n"
            return accumulated_text
        if elem['t'] == "Quoted":
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
        if elem['t'] == "Code":
            accumulated_text += elem['c'][1]
            return accumulated_text
        if elem['t'] == "Link":
            accumulated_text += consume_str(elem['c'][1])
            return accumulated_text
        if elem['t'] in PANDOC_SPAN_TYPES.keys():
            accumulated_text += convert_list_text_only(elem['c'])
            return accumulated_text

    text = ""
    for element in elem_list:
        text = extract_elem_text(text, element)
    return text


def convert_list(span_list, block_list, span_type="span-regular", indent=""):
    def convert_elem(spans: list, span_elem: dict) -> None:
        if span_elem['t'] == "Quoted":
            convert_elem(spans, span_elem['c'][0])
            spans += convert_list(span_elem['c'][1], block_list, span_type, indent + "  ")
            convert_elem(spans, span_elem['c'][0])
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
                "caption": convert_list_text_only(span_elem['c'][1]),
                "alt": span_elem['c'][2][1][4:]
            })
            return

    def merge_list(span_list: list) -> None:
        pos = 0
        while len(span_list) > pos+1:
            if span_list[pos]['type'] == span_list[pos+1]['type']:
                content_key = "text"
                if span_list[pos]['type'] == "span-listing":
                    content_key = "listing_text"
                pop_item = span_list.pop(pos+1)
                span_list[pos][content_key] += pop_item[content_key]
            else:
                pos += 1

    spans = []
    for span_element in span_list:
        convert_elem(spans, span_element)
    merge_list(spans)
    return spans


def json_from_markdown(markdown: str) -> list:
    def add_to_asset_list(asset_block: dict) -> None:
        if unfinished_key is not None:
            unfinished_block[unfinished_key].append(asset_block)
        else:
            block_assets_list.append(asset_block)

    block_assets_list = []
    pandoc_tree = json.loads(pypandoc.convert_text(markdown, to='json', format='md'))
    unfinished_block = {}
    unfinished_key = None
    for block in pandoc_tree['blocks']:
        if block['t'] == 'Para':
            paragraph_asset = {"type": 'block-paragraph',
                               "spans": convert_list(block['c'],
                                                     block_assets_list if unfinished_key is None else unfinished_block)}
            if len(paragraph_asset["spans"]) > 0:
                add_to_asset_list(paragraph_asset)
        elif block['t'] == 'Header':
            header_asset = {"type": "block-heading" if block['c'][0] == 1 else "block-subheading",
                            "heading": convert_list_text_only(block['c'][2])}
            add_to_asset_list(header_asset)
        elif block['t'] == 'BlockQuote':
            quote_asset = {"type": 'block-citation',
                           "statement": convert_list_text_only(block['c']),
                           "attribution": ""}
            add_to_asset_list(quote_asset)
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
                block_with_markdown = False
                for key in yaml_tree:
                    if yaml_tree[key] in ["MD_BLOCK", "MD-BLOCK", "MDBLOCK"]:
                        block_with_markdown = True
                        unfinished_key = key
                        unfinished_block[key] = []
                    else:
                        unfinished_block[key] = yaml_tree[key]
                if not block_with_markdown:
                    block_assets_list.append(unfinished_block)
                    unfinished_block = {}
                    unfinished_key = None
    return block_assets_list
