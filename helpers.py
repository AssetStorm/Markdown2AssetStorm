# -*- coding: utf-8 -*-
import json
import pypandoc


def consume_str(content_list):
    consumed_text = ""
    for i, span in enumerate(content_list):
        if span['t'] == "Space":
            consumed_text += " "
        elif span['t'] == "Str":
            consumed_text += span['c']
        else:
            return consumed_text, content_list[i:]
    return consumed_text, []


def json_from_markdown(markdown):
    block_assets_list = []
    pandoc_tree = json.loads(pypandoc.convert_text(markdown, to='json', format='md'))
    #print(json.dumps(pandoc_tree, indent=2))
    for block in pandoc_tree['blocks']:
        if block['t'] == 'Para':
            spans = []
            block_spans = block['c'].copy()
            while len(block_spans) > 0:
                span_type = 'span-regular'
                if block_spans[0]['t'] == "Strong":
                    span_type = 'span-strong'
                elif block_spans[0]['t'] == "Emph":
                    span_type = 'span-emphasized'
                elif block_spans[0]['t'] == "Code":
                    span_type = 'span-listing'
                old_block_spans_len = len(block_spans)
                text, block_spans = consume_str(block_spans)
                if not len(block_spans) < old_block_spans_len:
                    print("Consumation error!")
                    print(block_spans)
                    break
                span_asset = {"type": span_type, "text": text}
                spans.append(span_asset)
            paragraph_asset = {"type": 'block-paragraph',
                               "spans": spans}
            block_assets_list.append(paragraph_asset)
    return block_assets_list
