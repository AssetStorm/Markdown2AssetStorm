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


def create_span(span_type, content):
    if span_type == "span-listing":
        return {"type": "span-listing", "listing_text": content}
    return {"type": span_type, "text": content}


def consume_str(span_list):
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
        print("unable to consume:", elem)
    return text


def convert_list_text_only(elem_list):
    def extract_elem_text(accumulated_text, elem):
        print("extract_elem_text", elem)
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


def convert_list(span_list, span_type="span-regular", indent=""):
    def convert_elem(spans, span_elem):
        if span_elem['t'] == "Quoted":
            convert_elem(spans, span_elem['c'][0])
            spans += convert_list(span_elem['c'][1], span_type, indent + "  ")
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
        if span_elem['t'] in PANDOC_SPAN_TYPES.keys():
            spans += convert_list(span_elem['c'], PANDOC_SPAN_TYPES[span_elem['t']], indent + "  ")
            return

    def merge_list(span_list):
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


def json_from_markdown(markdown):
    block_assets_list = []
    pandoc_tree = json.loads(pypandoc.convert_text(markdown, to='json', format='md'))
    #print(json.dumps(pandoc_tree, indent=2))
    unfinished_block = {}
    unfinished_key = None
    for block in pandoc_tree['blocks']:
        if block['t'] == 'Para':
            paragraph_asset = {"type": 'block-paragraph',
                               "spans": convert_list(block['c'])}
            if unfinished_key is not None:
                unfinished_block[unfinished_key].append(paragraph_asset)
            else:
                block_assets_list.append(paragraph_asset)
        elif block['t'] == 'BlockQuote':
            quote_asset = {"type": 'block-citation',
                           "statement": convert_list_text_only(block['c']),
                           "attribution": ""}
            if unfinished_key is not None:
                unfinished_block[unfinished_key].append(quote_asset)
            else:
                block_assets_list.append(quote_asset)
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
