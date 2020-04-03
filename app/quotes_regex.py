# -*- coding: utf-8 -*-
# python 3.6.9

import re
import logging

logger = logging.getLogger('app.linkbuilder_totext.quotes_regex')

def count_marks(text):
    logger.info("--- count marks init ---")

    quotes = [{'name': 'single', 'regex': '‘(.*?)’'}, {'name': 'double', 'regex': '“(.*?)”'}]

    results = []
    for q in quotes:
        matches = re.findall(q['regex'], text, re.MULTILINE | re.UNICODE)
        q['count'] = len(matches)
        results.append(q)

    try:
        domina = max(results, key=lambda x:x['count'])
    except Exception as e:
        return None

    return domina


def which_style_refs(text):
    logger.info("--- which style refs init ---")

    # differentiated based on a different number of matches (author year: pages) vs (author year, pages) and (author, year) vs (author year)
    quotes_m = [{'name': 'apa', 'regex': [{'exp': '\((?P<all>(?P<author>[A-Za-z\s\.]*)[,\s]+(?P<year>[1|2]\d{3}))\)'}, {'exp': '(?P<quote>.*?)\((?P<all>(?P<author>[\w+,\s\.]+)(?P<year>[1|2]\d{3}):(?P<page>\s[\d].*?[\d]*))\)'}]}, {'name': 'chicago', 'regex': [{'exp': '\((?P<all>(?P<author>[A-Za-z\s\.]*)[\s]+(?P<year>[1|2]\d{3}))\)'}, {'exp': '(?P<quote>.*?)\((?P<all>(?P<author>[\w+,\s\.]+)(?P<year>[1|2]\d{3}),(?P<page>\s[\d].*?[\d]*))\)'}] }]

    results = []

    for qm in quotes_m:
        count = 0
        for r in qm['regex']:
            matches = re.findall(r['exp'], text, re.MULTILINE | re.UNICODE)
            count += len(matches)
        qm['count'] = count
        results.append(qm)

    try:
        domina = max(results, key=lambda x:x['count'])
    except Exception as e:
        return None

    return domina


def which_style_bib(text):
    logger.info("--- which style bib init ---")

    # do the bibliography items contain patentheses ~ (year)
    apa_cat = r"(?sm)^([^()\n\r]+)\(([12]\d{3})\)"
    chicago_cat = r"(?sm)^([^()\n\r]+)([12]\d{3})"
    apa_prod = r"(?sm)^([^()\n\r]+)\(([12]\d{3})\)(.*?)(?=^[^()\n\r]+\([12]\d{3}\)|\s\n|\Z)"
    chicago_prod = r"(?sm)^([^()\n\r]+)\..([12]\d{3}[a-z]?)\.(.*?)(?=^[^()\n\r]+\..[12]\d{3}[a-z]?\.|\s\n|\Z)"

    refs = [{'name': 'chicago', 'categorization_regex': chicago_cat, 'production_regex': chicago_prod}, {'name': 'apa', 'categorization_regex': apa_cat, 'production_regex': apa_prod}]

    results = []
    for r in refs:
        matches = re.findall(r['categorization_regex'], text, re.MULTILINE | re.UNICODE)
        r['count'] = len(matches)
        results.append(r)

    try:
        domina = max(results, key=lambda x:x['count'])
    except Exception as e:
        return None

    return domina
