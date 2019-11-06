# -*- coding: utf-8 -*-
import json
import pypandoc

PANDOC_SPAN_TYPES = {
    "Strong": "span-strong",
    "Emph": "span-emphasized"
}
CHARACTER_TYPES = {
    "Space": " ",
    "DoubleQuote": '"',
    "SingleQuote": "'"
}


def create_span(span_type, content):
    if span_type == "span-listing":
        return {"type": "span-listing", "listing_text": content}
    return {"type": span_type, "text": content}


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
    print(json.dumps(pandoc_tree, indent=2))
    for block in pandoc_tree['blocks']:
        if block['t'] == 'Para':
            paragraph_asset = {"type": 'block-paragraph',
                               "spans": convert_list(block['c'])}
            block_assets_list.append(paragraph_asset)
    return block_assets_list
