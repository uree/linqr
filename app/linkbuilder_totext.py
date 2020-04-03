# -*- coding: utf-8 -*-
# python 3.6.9

from io import BytesIO
import os
import sys, getopt
import subprocess
import textract
import re
import pprint
from pprint import pformat
import logging

from quotes_regex import *


# LOGGING
logger = logging.getLogger('app.linknbuilder_totext')
vlogger = logging.getLogger('app_verbose.linknbuilder_totext')

pp = pprint.PrettyPrinter(indent=4)

intext_maps = {"mapping": []}


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def add_sg(subgroup, example, regex):
    output = {}
    output["subgroup"] = subgroup
    output["example"] = example
    output["regex"] = regex
    return output



def dsmbg(input_text):
    m = re.match("in:", input_text, re.I)
    m2 = re.search(r"[\d]+(\([\d–]+\)|:)", input_text)

    if m:
        return 'editor'
    elif m2:
        return 'journal'
    else:
        return 'publication'


def dsmbg_link(input_text, alternative):
    doi = re.search(r"doi", input_text)
    url = re.search(r"http:", input_text)
    if url:
        return 'url'
    elif doi:
        return 'doi'
    else:
        return alternative


def dsmbg_master(input_text):
    logger.info("--- dsmbg_master init: parsing reference --- ")
    editor = re.match("in:", input_text.lower(), re.I)

    journal = re.search(r"([\d]+\s+\([\d–]+\))|([\d]+(\([\d–]+\)|:))", input_text)
    # Capital and Class, 33 (2): 7–31
    # Journal for Critical Education Policy Studies 11 (3): 52–82
    # Capitalism, Nature, Socialism 25 (2): 25–37
    # Workplace 19: 1–3

    url = re.search(r"http", input_text.lower())
    doi = re.search(r"doi", input_text.lower())
    pages = re.search(r"^[\d]+–[\d]+", input_text)
    available = re.search(r"^Accessed", input_text)

    # this still needs work, many cases where there is no ed.
    if editor:
        splt = re.split(r"\(ed.*?\)", input_text, re.UNICODE)
        output = []
        editor = {'name': 'editor' , 'content': splt[0].replace('In:', '').strip()}
        try:
            book_title = {'name': 'book_title' , 'content': splt[1]}
            output.append(book_title)
        except Exception as e:
            logger.debug("Editorial error")
            vlogger.debug(input_text)

        output.append(editor)
        return  output
    elif journal:
        output = []
        return {'name': 'journal', 'content': input_text}
    elif url:
        output = input_text.replace('Available at: ', '')
        return {'name': 'url', 'content': output}
    elif doi:
        sub = re.sub('doi:', '', input_text, flags=re.IGNORECASE)
        output = sub.strip('.').strip()
        return {'name': 'doi' , 'content': output}
    elif pages:
        output = pages.group(0).strip('.')
        return {'name': 'page', 'content': output}
    elif available:
        return {'name': 'accessed', 'content': input_text}
    else:
        output = input_text.replace(', pp', '')
        return {'name': 'publisher', 'content': output}


def split_multiple_works(string):
    one = {}
    firstauthor = string.split(',')
    one['author'] = firstauthor[0]
    one['year'] = firstauthor[1]
    return one



def isolate_bibliography(refrnc_list):
    # extract largest chunk of entries which are in alphabetical order
    logger.info("--- isolate bibliography init ---")

    authors = [n['author'] for n in refrnc_list['entries']]

    all_pairs = []

    streak = 0
    start = 0
    end = 0

    for i in range(0, len(authors)):
        try:
            if authors[i].lower()<authors[i+1].lower() or authors[i].lower() == authors[i+1].lower():
                streak+=1
                if streak == 1:
                    start = i

            else:
                streak = 0
                end = i+1
                # alphabetic streak over, append
                all_pairs.append({'start': start, 'end': end, 'streak': end-start})

        except Exception as e:
            logger.debug(f"iteration {i} full length {len(authors)}")
            # if end of authors reached and the streak has not ended
            if i+1 == len(authors) and streak > 0:
                logger.info("End of bibliography")
                all_pairs.append({'start': start, 'end': i, 'streak': i-start})

    vlogger.debug("all pairs")
    vlogger.debug(pformat(all_pairs))

    try:
        domina = max(all_pairs, key=lambda x:x['streak'])
    except Exception as e:
        return None

    vlogger.debug("Longest streak")
    vlogger.debug(pformat(domina))

    # plus one! or it leaves out the last match
    entries_clean = refrnc_list['entries'][domina['start']:domina['end']+1]


    # return the position of the first reference in the reference list, so that i can split the text later
    begin_reflist = refrnc_list['entries'][domina['start']]['position_data']
    refrnc_list['entries'] = entries_clean
    refrnc_list['reflist_beginnig'] = begin_reflist
    return refrnc_list



def extract_ref_list(input_text):
    logger.info("--- extract_ref_list init ---")

    author_len_limit = 69


    refrnc_list = {'entries': []}

    # which style
    style = which_style_bib(input_text)
    logger.debug(f"Reference style extract_ref_list {style['name']}")

    # [chicago](https://www.chicagomanualofstyle.org/tools_citationguide/citation-guide-2.html) guidelines

    # [APA](https://apastyle.apa.org/style-grammar-guidelines/references) guidelines

    # can be condensed
    if style['name'] == 'apa':
        prom_match = re.finditer(style['production_regex'], input_text, re.UNICODE)
        match_len = 0

        for m in prom_match:
            match_len+=1

            vlogger.debug(m.groups())

            author = m.groups()[0]
            year = m.groups()[1]
            therest = m.groups()[2]
            # remove linebreaks
            therest = therest.replace('\n', '')

            restless_init = re.split(r"\.\s(?!\(ed.)|\s\.|[!?]", therest, re.UNICODE)

            # remove sneaky page numbers
            if len(restless_init[-1].strip())<3:
                restless = restless_init[:-1]
            else:
                restless = restless_init

            item = {}

            #disqualify false positives ... they are usually very long compared to bibentries  (arbitrary = author_len_limit)
            if len(author)<author_len_limit:
                item['author'] = author
                #print("Looking for authority")
                #print(author)
                item['year'] = re.sub("[a-z]?", '', year)
                #print("This is where it begins {}".format(m.start()))
                item['position_data'] = m.start()

                if len(restless) >= 2:
                    item['title'] = restless[0].strip()

                    touch = dsmbg_master(restless[1])

                    for r in range(1, len(restless)):
                        touch = dsmbg_master(restless[r])
                        if isinstance(touch, list):
                            for t in touch:
                                item[t['name']] = t['content']
                        elif touch['content'] == None:
                            item[touch['name']] = restless[r].strip('.')
                        else:
                            item[touch['name']] = touch['content']

                refrnc_list['entries'].append(item)

        logger.info(f"Efficiency: {len(refrnc_list['entries'])}/{match_len}")
        output = isolate_bibliography(refrnc_list)

    elif style['name'] == 'chicago':
        logger.info('--- chicago is. my kind of style. chicago is. ---')
        prom_match = re.finditer(style['production_regex'], input_text, re.UNICODE)
        match_len = 0

        for m in prom_match:
            match_len+=1

            vlogger.debug(m.groups())

            author = m.groups()[0]

            year = m.groups()[1]
            leftovers = m.groups()[2]
            # remove linebreaks
            therest = leftovers.replace('\n', ' ')

            # this splits the rest of the bib entry @punctuation
            restless_init = re.split(r"\.\s(?!\(ed.)|\s\.|[!?]\s", therest, re.UNICODE)


            if len(restless_init[-1].strip())<3:
                restless = restless_init[:-1]
            else:
                restless = restless_init


            item = {}

            #disqualify matches which are too long (arbitrary border 50 characters)

            if len(author)<author_len_limit:
                item['author'] = author

                # remove any letters appended to publication date
                item['year'] = re.sub("[a-z]?", '', year)
                item['position_data'] = m.start()

                if len(restless) >= 2:

                    item['title'] = restless[0].strip()

                    touch = dsmbg_master(restless[1])

                    for r in range(1, len(restless)):
                        touch = dsmbg_master(restless[r])
                        if isinstance(touch, list):
                            for t in touch:
                                item[t['name']] = t['content']
                        elif touch['content'] == None:
                            item[touch['name']] = restless[r].strip('.')
                        else:
                            item[touch['name']] = touch['content']

                refrnc_list['entries'].append(item)

        logger.info(f"Efficiency: {len(refrnc_list['entries'])}/{match_len}")

        output = isolate_bibliography(refrnc_list)

    else:
        return False


    output['citation_style_bib'] = style['name']
    vlogger.debug(pformat(output))
    return output



def extract_refs(input_text):
    # this code primarily finds apa and also catches some chicago
    logger.info("--- extract_refs init: extracting citations ---")

    # count quotation marks, determine outer ones
    q_marks = count_marks(input_text)

    # set the right quotation marks based on count_marks output
    if q_marks != None:
        logger.info("quotation marks detected")
        fnd_quot = q_marks['regex']
    else:
        logger.info("quotation marks not detected, reverting to default")
        fnd_quot = r"“(.*?)”"


    style = which_style_refs(input_text)
    logger.info(f"Reference style refs inner: {style}")
    if style == None:
        style = 'apa'


    #MATCH ALL (AUTHOR YEAR: PAGES) / (AUTHOR YEAR, PAGES)
    author_year_pages = r"(?P<quote>.*?)\((?P<all>(?P<author>[\w+,\s\.\-\,]+)(?P<year>[1|2]\d{3}):(?P<page>\s[\d].*?[\d]*))\)"
    author_year_pages_chi = r"(?P<quote>.*?)\((?P<all>(?P<author>[\w+,\s\.\-\,]+)(?P<year>[1|2]\d{3}),(?P<page>\s[\d].*?[\d]*))\)"

    #MATCH ALL (AUTHOR YEAR) / (AUTHOR YEAR)
    author_year = r"\((?P<all>(?P<author>[A-Za-z\s\.\-\,]*)[,\s]+(?P<year>[1|2]\d{3}))\)"
    author_year_chi = r"\((?P<all>(?P<author>[A-Za-z\s\.\-\,]*)[\s]+(?P<year>[1|2]\d{3}))\)"

    #MATCH ALL AUTHOR (YEAR: PAGES) / AUTHOR (YEAR, PAGES)
    author_p_yearpages_p = r"(?P<quote>.*?)(?P<all>(?P<author>[\w]+)\s\((?P<year>[1|2]\d{3,}):\s(?P<page>[\d].*?[\d]*))\)"
    author_p_yearpages_p_chi = r"(?P<quote>.*?)(?P<all>(?P<author>[\w]+)\s\((?P<year>[1|2]\d{3,}),\s(?P<page>[\d].*?[\d]*))\)"

    #MATCH ALL AUTHOR (YEAR)
    author_p_year_p = r"(?P<all>(?P<author>[A-Z][a-z\s\.\-]*)\s\((?P<year>[1|2]\d{3}))\)"


    #MATCH ALL (author, year; author, year; author, year)
    multiple = r"\((?P<all>(?P<firstwork>[A-Za-z\s\.]*[,\s]+[1|2][\d]{3});(?P<otherworks>[^\)]*))\)"
    multiple_chi = r"\((?P<all>(?P<firstwork>[A-Za-z\s\.]*[\s]+[1|2][\d]{3});(?P<otherworks>[^\)]*))\)"


    # UNRELIABLE: this has not yet been implemented. does not work.
    # MATCH ALL (pp. 133–134) & (p.59) ibid?
    p_pages_p = r"(?P<quote>.*?)("+author_year_pages+r"|"+author_p_year_p+r")(?:.*?)(\(?P<page>p+\..*?\))|(\(?P<ibid>ibid.*?\))"
    p_pages_p_chi = r"(?P<quote>.*?)("+author_year_pages_chi+r"|"+author_p_year_p+r")(?:.*?)(\(?P<page>p+\..*?\))|(\(?P<ibid>ibid.*?\))"

    master_dict = {'apa': {'categories': [{'id': 0, 'name': 'author_year_pages', 'regex': author_year_pages, 'matches': []}, {'id': 1 , 'name': 'author_year', 'regex': author_year, 'matches': []}, {'id': 2, 'name': 'author_p_yearpages_p', 'regex': author_p_yearpages_p, 'matches': []}, {'id': 3, 'name': 'author_p_year_p', 'regex': author_p_year_p, 'matches': []}, {'id': 4, 'name': 'multiple', 'regex': multiple, 'matches': []}, {'id': 5, 'name': 'p_pages_p', 'regex': 'p_pages_p', 'matches': []}]}, 'chicago': {'categories': [{'id': 0, 'name': 'author_year_pages', 'regex': author_year_pages_chi, 'matches': []}, {'id': 1 , 'name': 'author_year', 'regex': author_year_chi, 'matches': []}, {'id': 2, 'name': 'author_p_yearpages_p', 'regex': author_p_yearpages_p_chi, 'matches': []}, {'id': 3, 'name': 'author_p_year_p', 'regex': author_p_year_p, 'matches': []}, {'id': 4, 'name': 'multiple', 'regex': multiple_chi, 'matches': []}, {'id': 5, 'name': 'p_pages_p', 'regex': 'p_pages_p_chi', 'matches': []}]}}

    #matches_dict = {'categories': []}
    matches_dict = {'matches': []}


    for cat in master_dict[style['name']]['categories']:

        matches = re.finditer(cat['regex'], input_text, re.MULTILINE | re.UNICODE)
        matches = tuple(matches)
        logger.info(f"Category: {cat['name']} Number of matches: {len(matches)}")

        for m in matches:
            one_match = {'groups': None, 'start': None, 'end': None, 'id': cat['id'], 'name': cat['name']}


            # this one often matches text from reference lists which start with initials, so i need to clean that up
            if cat['id'] == 3 and len(m.groups()[0]) == 1:
                pass
            else:
                # check if groups findall strings within quotation marks and retrurn last match[-1]
                gps = m.groupdict()
                new_gps = m.groupdict()

                try:
                    all_quotes = gps['quote']
                    last_quote = re.findall(fnd_quot, gps['quote'])[-1]
                    logger.debug(f"last quote: {last_quote}")
                    new_gps['quote'] = last_quote
                    one_match['start'] = m.start(2)
                except Exception as e:
                    one_match['start'] = m.start()

                # clean up multiple cos regex can't; could this be more elegant?
                if cat['id'] == 4:
                    match_list = {'works': [], 'all': ''}
                    try:
                        one = split_multiple_works(gps['firstwork'])
                        match_list['works'].append(one)
                    except Exception as e:
                        logger.debug("Error splitting multiple works @ step 1")
                        pass

                    try:
                        low = gps['otherworks'].split(';')
                    except Exception as e:
                        logger.debug("Error splitting multiple works by ;")
                        pass

                    if low:
                        for i in low:
                            try:
                                one = split_multiple_works(i)
                                match_list['works'].append(one)
                            except Exception as e:
                                logger.debug("Error splitting multiple works @ final step")
                                pass

                    match_list['all'] = gps['all']
                    new_gps = match_list


                vlogger.debug("new groups")
                vlogger.debug(pformat(new_gps))

                try:
                    wks = new_gps['works']
                    logger.debug("The groups are inappropriately nested")
                    vlogger.debug(pformat(wks))
                except:
                    logger.debug("The groups look fine")
                    vlogger.debug(pformat(new_gps))
                    tmp = {}
                    match_list = {'works': [], 'all': ''}
                    for k,v in new_gps.items():
                        if k != 'all':
                            if k == 'author':
                                v_str = v.strip()
                                if v_str.endswith(','):
                                    vlogger.debug("we have a comma")
                                    ap = v_str[:-1]
                                    vlogger.debug(f"AP: {ap}")
                                else:
                                    ap = v_str
                            else:
                                ap = v
                            tmp[k] = ap
                    match_list['works'].append(tmp)
                    match_list['all'] = new_gps['all']
                    new_gps = match_list


                one_match['groups'] = new_gps
                one_match['end'] = m.end()
                vlogger.debug(one_match)


                matches_dict['matches'].append(one_match)


    matches_sorted = sorted(matches_dict['matches'], key = lambda k:k['start'])
    matches_out = {'matches': []}
    matches_out['matches'] = matches_sorted
    matches_out['number_of_matches'] = len(matches_sorted)
    matches_out['citation_style_refs'] = style['name']
    logger.debug(f"Total number of matches: {len(matches_sorted)}")
    return matches_out




def textract_convert(input_file):
    output = textract.process(input_file)
    return output


def delegate(input_file):
    if input_file.endswith('.pdf'):
        output = textract_convert(input_file)
    elif input_file.endswith('.doc'):
        output = textract_convert(input_file)
    elif input_file.endswith('.docx'):
        output = textract_convert(input_file)
    elif input_file.endswith('.odt'):
        output = textract_convert(input_file)
    elif input_file.endswith('.txt'):
        output = input_file
    elif input_file.endswith('.md'):
        output = input_file
    else:
        return "invalid format"


    # fixes linebreaks in paragraphs
    output = re.sub(r'([^\.])\n([^A-Z])', r'\1 \2', output.decode('utf-8'))
    return output
