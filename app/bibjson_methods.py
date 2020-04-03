# -*- coding: utf-8 -*-
# python 3.6.9

import json
import re
import os.path
from collections import Counter
import logging
import pprint
from pprint import pformat

# LOGGING
logger = logging.getLogger('app.bibjson_methods')
vlogger = logging.getLogger('app_verbose.bibjson_methods')

pp = pprint.PrettyPrinter(indent=4)

bibjson_aliases = {'abstract': ['abstract', 'AB'], 'address': ['address'], 'annote': ['annote', 'descr', 'desc', 'N2'], 'booktitle': ['booktitle'], 'chapter': ['chapter'], 'crossref': ['crossref'], 'edition': ['edition'], 'howpublished': ['howpublished'], 'institution': ['institution'], 'key': ['key'], 'month': ['month'], 'note': ['note'], 'number': ['number'], 'organization': ['organization'], 'pages': ['pages', 'page', 'numPages'], 'publisher': ['publisher', 'PB', 'publishers'], 'school': ['school'], 'series': ['series'], 'title': ['title', 'TI', 'titleInfo', 'Title'], 'type': ['type', 'TY', 'genre', 'ENTRYTYPE', 'itemType'], 'volume': ['volume', 'VL'], 'year': ['year', 'PY', 'DA', 'Year', 'publish_date', 'date', 'issued'], 'author': ['author', 'AU', 'contributors', 'name', 'z_authors', 'Authors', 'creators'], 'editor': ['editor'], 'identifier': ['doi', 'identifier', 'identifierwodash', 'md5', 'issn', 'isbn', 'ID', 'SN', 'DO', 'issne', 'issnp', 'identifiers', 'journal_issns', 'ISBN-13', 'olid', 'isbn-10', 'ISBN'], 'link': ['locator', 'url', 'href', 'L1', 'UR', 'url_for_pdf', 'url_for_landing_page', 'best_oa_location', 'links', 'URL'], 'subject': ['subject', 'KW', 'subjects'], 'journal': ['journal']}

zotero_json_aliases = {'abstractNote': ['abstract', 'AB'], 'address': ['address'], 'annote': ['annote', 'descr', 'desc', 'N2'], 'bookTitle': ['booktitle'], 'chapter': ['chapter'], 'crossref': ['crossref'], 'edition': ['edition'], 'howpublished': ['howpublished'], 'institution': ['institution'], 'key': ['key'], 'month': ['month'], 'note': ['note'], 'number': ['number'], 'organization': ['organization'], 'numPages': ['pages', 'page', 'numPages'], 'publisher': ['publisher', 'PB', 'publishers'], 'school': ['school'], 'series': ['series'], 'title': ['title', 'TI', 'titleInfo', 'Title'], 'itemType': ['type', 'TY', 'genre', 'ENTRYTYPE', 'itemType'], 'volume': ['volume', 'VL'], 'date': ['year', 'PY', 'DA', 'Year', 'publish_date', 'date'], 'author': ['author', 'AU', 'contributors', 'name', 'z_authors', 'Authors', 'creators'], 'creator': ['editor', 'author'], 'identifier': ['doi', 'identifier', 'identifierwodash', 'md5', 'issn', 'isbn', 'ID', 'SN', 'DO', 'issne', 'issnp', 'identifiers', 'journal_issns', 'ISBN-13', 'olid', 'isbn-10', 'ISBN'], 'url': ['locator', 'url', 'href', 'L1', 'UR', 'url_for_pdf', 'url_for_landing_page', 'best_oa_location', 'links'], 'subject': ['subject', 'KW', 'subjects'], 'journal': ['journal']}



extra_aliases = {'coverurl': ['coverurl', 'img_href'], 'language': ['language', 'LA', 'languages'], 'pagesinfile': ['pagesinfile'], 'tags': ['tags'], 'filetype': ['extension'], 'source': ['source'], 'rank': ['rank'], 'place_published': ['CY'], 'issue': ['IS', 'issue'], 'startpage': ['SP'], 'lastpage': ['EP']}


fields = {'strings': ['abstract', 'address', 'annote', 'booktitle', 'chapter', 'crossref', 'edition', 'howpublished', 'institution', 'key', 'month', 'note', 'number', 'organization', 'pages', 'publisher', 'school', 'series', 'title', 'type', 'volume', 'year', 'journal', 'language'], 'list_of_dicts': ['author', 'editor', 'identifier', 'link', 'subject'], 'objects': ['']}

types = [{'article': {'required': ['author', 'title', 'journal', 'year', 'volume'], 'optional': ['number', 'pages', 'month', 'note', 'key'], 'aliases': ['article', 'jour']}}, {'book': {'required': ['author', 'editor', 'title', 'publisher', 'year'], 'optional': ['volume', 'number', 'series', 'address', 'edition', 'month', 'note', 'key', 'url', 'type'], 'aliases': ['book', 'edition', 'work']}}, {'booklet': {'required': ['title'], 'optional': ['author', 'howpublished', 'address', 'month', 'year', 'note', 'key'], 'aliases': ['booklet']}}, {'conference': {'required': ['author', 'editor', 'title', 'chapter/pages', 'publisher', 'year'], 'optional': ['volume', 'number', 'series', 'type', 'address', 'edition', 'month', 'note', 'key'], 'aliases': ['conference']}}, {'inbook': {'required': ['author', 'title', 'booktitle', 'publisher', 'year'], 'optional': ['editor', 'volume', 'number', 'series', 'type', 'chapter', 'pages', 'address', 'edition', 'month', 'note', 'key'], 'aliases': ['inbook']}}, {'incollection': {'required': ['author', 'title', 'booktitle', 'year'], 'optional': ['editor', 'volume', 'number', 'series', 'pages', 'address', 'month', 'organization', 'publisher', 'note', 'key'], 'aliases': ['incollection']}}, {'inproceedings': {'required': ['author', 'title', 'booktitle', 'year'], 'optional': ['editor', 'volume', 'number', 'series', 'pages', 'address', 'month', 'organization', 'publisher', 'note', 'key'], 'aliases': ['inproceedings', 'conference paper']}}, {'manual': {'required': ['title'], 'optional': ['author', 'organization', 'address', 'edition', 'month', 'year', 'note', 'key'], 'aliases': ['manual']}}, {'masterthesis': {'required': ['author', 'title', 'school', 'year'], 'optional': ['type', 'address', 'month', 'note', 'key'], 'aliases': ['masterthesis']}}, {'misc': {'required': ['none'], 'optional': ['author', 'title', 'howpublished', 'month', 'year', 'note', 'key'], 'aliases': ['misc', 'creative work', 'artwork']}}, {'phdthesis': {'required': ['author', 'title', 'school', 'year'], 'optional': ['type', 'address', 'month', 'note', 'key'], 'aliases': ['phdthesis']}}, {'proceedings': {'required': ['title', 'year'], 'optional': ['editor', 'volume', 'number', 'series', 'address', 'month', 'publisher', 'organization', 'note', 'key'], 'aliases': ['proceedings']}}, {'techreport': {'required': ['author', 'title', 'institution', 'year'], 'optional': ['type', 'number', 'address', 'month', 'note', 'key'], 'aliases': ['techreport']}}, {'unpublished': {'required': ['author', 'title', 'note'], 'optional': ['month', 'year', 'key'], 'aliases': ['unpublished']}}]

current_source = ''

resolving_nesting = [{'core': {'problem_fields': [{'field_name': 'title', 'depth_and_keys': 'title'}]}, 'aaaaarg': {'problem_fields': [{'field_name': 'language', 'depth_and_keys': 'key'}]}}]

sources_bibjson = [{'doaj': [{'level': 'hits','depth': 'results'}, {'level': 'hit', 'depth': 'bibjson'}]}]


def join_lists(slovar):
    list = []
    for key, value in slovar.items():
        if len(value)>1:
            list.append(value)
        else:
            pass
    return list

def join_lists2(slovar):
    oput = []
    for k, v in slovar.items():
        for xx in v:
            oput.append(xx)
    return oput

def dis_ambig(slovar, alias):
    for key, value in slovar.items():
        if alias in value:
            return key

def recognize_isbn(string):
    pass


def gen_dict_extract(key, var):
    all_paths = []
    if hasattr(var,'iteritems'):
        for k, v in var.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result

def get_all_keys(dict_item, key_base=''):
    all_paths = []
    if isinstance(dict_item, dict):
        for key in dict_item:
            if key_base:
                new_key = key_base + "/" + key
            else:
                new_key = key
            all_paths.extend(get_all_keys(dict_item[key], new_key))
    else:
        if key_base:
            all_paths.append(key_base)

    return all_paths

def really_get_all_keys(dict_item, key_base=''):
    all_paths = []
    if isinstance(dict_item, dict):
        for key in dict_item:
            if key_base:
                new_key = key_base + "/" + key
            else:
                new_key = key
            all_paths.extend(really_get_all_keys(dict_item[key], new_key))
    else:
        if key_base:
            all_paths.append(key_base)

    return all_paths


def dict_path(path,my_dict,out):
    for k,v in my_dict.items():
        if isinstance(v,dict):
            dict_path(path+"['"+k+"']",v,out)
        elif isinstance(v,list):
            for blj in v:
                dict_path(path+"['"+k+"']",blj,out)
        else:
            struct = {'path': path+"['"+k+"']", 'value': v}
            out.append(struct)



def parse_keys(all_paths, search_key):
    output = []

    if all_paths:
        for i in all_paths:
            op = i.split('/')
            mar = [n for n in op if op[-1] == search_key]
            if mar:
                output.append(mar)

    return output


def return_data_type(data_value):
    if isinstance(data_value, dict):
        return "dict"
    elif isinstance(data_value, list):
        return "list"
    elif isinstance(data_value, str):
        return "string"
    else:
        return None

def resolve_depth(pod, source, level):
    depth = ''
    for i in pod:
        #print i
        if source in i:
            for k, v in i.items():
                #print k, v
                for s in v:
                    #print s
                    if s['level'] == level:
                        depth = s['depth']
    return depth

def resolve_depth_new(pod, level):
    depth = ''
    for i in pod:
        #print i
        for k, v in i.items():
            #print k, v
            for s in v:
                #print s
                if s['level'] == level:
                    depth = s['depth']
    return depth


def get_it(lod, val):
    for i in lod:
        if val in i:
            return True
        else:
            return False

# start splitting on pos occurence
def skip_split(strng, sep, pos):
    strng = strng.split(sep)
    return sep.join(strng[:pos]), sep.join(strng[pos:])


def csljson_cleanup(data):
    logger.info("--- csljson_cleanup init ---")

    zotero_json_aliases = [{'zotero_key': 'author', 'alias': 'contributor'}, {'zoreto_key': 'abstractNote', 'alias': 'abstract'}, {'zoreto_key': 'date', 'alias': 'year'}, {'zoreto_key': 'url', 'alias': 'link'}, {'zoreto_key': 'itemType', 'alias': 'type'}, {'zoreto_key': 'DOI', 'alias': 'identifier'}, {'zoreto_key': 'ISBN', 'alias': 'identifier'}]

    zaliases = {'creators': ['author'], 'abstractNote': ['abstract'], 'date': ['year'], 'url': ['link'], 'itemType': ['type'], 'DOI': ['identifier'], 'ISBN': ['identifier']}

    special_treatment = ['link', 'identifier']

    item = {}


    for k, v in data.items():
        new_key = dis_ambig(zaliases, k)

        try:
            dummy = v
        except Exception as e:
            v = None

        if v != None:
            # not the case if k in special treatment!
            if k == 'identifier':
                logger.debug("key: identifier")
                logger.debug(k)
                if type(v) == list and len(v) >= 1:
                    out = ''
                    for el in v:
                        if el['type'].lower() == 'isbn':
                            out += el['id']+' '
                        elif el['type'] == 'doi':
                            out += el['id']+' '
                    if el['type'].lower() == 'isbn':
                        item['ISBN'] = out.strip()
                    elif el['type'] == 'doi':
                        item['DOI'] = out.strip()
                else:
                    try:
                        if v['type'].lower() == 'isbn':
                            item['ISBN'] = v['id']
                    except Exception as e:
                        logger.debug("Error selecting ISBN", exc_info=True)

                    try:
                        if v['type'].lower() == 'doi':
                            item['DOI'] = v['id']
                    except Exception as e:
                        logger.debug("Error selecting DOI", exc_info=True)

            elif k == 'link':
                logger.debug("key: link")
                logger.debug(k)
                if type(v) == list:
                    out = []
                    for el in v:
                        try:
                            out.append(el['href'])
                        except Exception as e:
                            logger.debug("Error selecting HREF", exc_info=True)

                    str_out = ' '.join(out)
                    item['url'] = str_out.strip()
                else:
                    item['url'] = v['href']

            else:
                if new_key != None:
                    item[new_key] = v
                else:
                    item[k] = v

    #check if it has itemType if not assign book
    if 'itemType' not in item:
        logger.debug('item does not have a type assigned')
        item['itemType'] = 'book'

    itemized_bib = {'items': {}}


    tmp = item
    tmp['id'] = 'ITEM-1'
    try:
        tmp['issued'] = {'date-parts': [[tmp['date']]]}
        del(tmp['date'])
    except Exception as e:
        pass

    try:
        tmp['author'] = tmp.pop('creators')
    except Exception as e:
        pass


    try:
        dummy_editor = tmp['editor']
    except Exception as e:
        dummy_editor = None

    if dummy_editor != None:
        for a in range(len(tmp['editor'])):
            # maybe unnecessary
            try:
                tmp['editor'][a]['family'] = tmp['editor'][a]['lastname']
                tmp['editor'][a]['given'] = tmp['editor'][a]['firstname']
            except:
                spl = tmp['editor'][a]['name'].split(' ')
                tmp['editor'][a]['family'] = spl[0]
                tmp['editor'][a]['given'] = spl[1]

            del(tmp['editor'][a]['firstname'])
            del(tmp['editor'][a]['lastname'])

    try:
        dummy_author = tmp['author']
    except Exception as e:
        dummy_author = None

    if dummy_author != None:
        for a in range(len(tmp['author'])):
            tmp['author'][a]['family'] = tmp['author'][a]['lastname']
            tmp['author'][a]['given'] = tmp['author'][a]['firstname']
            del(tmp['author'][a]['firstname'])
            del(tmp['author'][a]['lastname'])


    itemized_bib['items']['ITEM-1'] = item
    vlogger.debug(pformat(itemized_bib))


    return itemized_bib





def zotero_cleanup(data):
    logger.info("--- zotero cleanup init ---")

    zotero_json_aliases = [{'zotero_key': 'author', 'alias': 'contributor'}, {'zoreto_key': 'abstractNote', 'alias': 'abstract'}, {'zoreto_key': 'date', 'alias': 'year'}, {'zoreto_key': 'url', 'alias': 'link'}, {'zoreto_key': 'itemType', 'alias': 'type'}, {'zoreto_key': 'DOI', 'alias': 'identifier'}, {'zoreto_key': 'ISBN', 'alias': 'identifier'}]

    zaliases = {'creators': ['author'], 'abstractNote': ['abstract'], 'date': ['year'], 'url': ['link'], 'itemType': ['type'], 'DOI': ['identifier'], 'ISBN': ['identifier']}

    special_treatment = ['link', 'identifier']

    data_out = []


    for d in data:
        item = {}
        for b in d['bibjson']:
            for k, v in b.items():
                new_key = dis_ambig(zaliases, k)

                try:
                    dummy = v
                except Exception as e:
                    v = None

                if v != None:
                    # not the case if k in special treatment!
                    if k == 'identifier':
                        logger.debug("key: identifier")
                        logger.debug(k)
                        if type(v) == list and len(v) >= 1:
                            out = ''
                            for el in v:
                                if el['type'].lower() == 'isbn':
                                    out += el['id']+' '
                                elif el['type'] == 'doi':
                                    out += el['id']+' '
                            if el['type'].lower() == 'isbn':
                                item['ISBN'] = out.strip()
                            elif el['type'] == 'doi':
                                item['DOI'] = out.strip()
                        else:
                            try:
                                if v['type'].lower() == 'isbn':
                                    #print("ISBN!")
                                    item['ISBN'] = v['id']
                            except Exception as e:
                                logger.debug("Error selecting ISBN", exc_info=True)
                                pass
                            try:
                                if v['type'].lower() == 'doi':
                                    item['DOI'] = v['id']
                            except Exception as e:
                                logger.debug("Error selecting DOI", exc_info=True)
                                pass
                    elif k == 'link':
                        logger.debug("key: link")
                        logger.debug(k)
                        if type(v) == list:
                            out = []
                            for el in v:
                                try:
                                    out.append(el['href'])
                                except Exception as e:
                                    logger.debug("Error selecting HREF", exc_info=True)
                            try:
                                str_out = ' '.join(out)
                                item['url'] = str_out.strip()
                            except Exception as e:
                                logger.debug("Error assigning url to item", exc_info=True)
                        else:
                            item['url'] = v['href']

                    else:
                        if new_key != None:
                            item[new_key] = v
                        else:
                            item[k] = v

        #check if it has itemType if not assign book
        if 'itemType' not in item:
            logger.debug('item does not have a type assigned')
            item['itemType'] = 'book'

        data_out.append(item)

    return data_out





###LISTS OF DICTS
def single_author_kons(one, i, citation_style):
    try:
        one['name'] = ''
    except:
        pass
    # this is where citation_style should kick in
    if citation_style == 'chicago':
        s_author = i.split(',', 1)
    elif citation_style == 'apa':
        s_author = i.split(' ', 1)
    else:
        logger.debug("No citation style specified")
        pass

    try:
        one['firstname'] = s_author[-1]
        one['lastname'] = s_author[0]
        one['name'] = s_author[-1]+' '+s_author[0]
        one['alternate'].append(i)
    except Exception as e:
        logger.debug("Assignment error")
        one['name'] = i

    return one




def list_of_dicts(fieldname, fielddata, original_key, source, citation_style=''):
    logger.info("--- init list of dict ---")

    output = []

    # disassemble fielddata
    if type(fielddata) == list:
        nice_input = fielddata
    elif type(fielddata) == dict:
        pass
    else:
        if ";" in fielddata:
            try:
                nice_input = fielddata.split(';')
            except:
                pass
        else:
            nice_input = []
            if citation_style == 'apa':
                logger.debug('apa')
                nice_input = []
                try:
                    auth_split = re.split('\sand\s', fielddata)
                    if len(auth_split) >= 2:
                        last_author = auth_split[-1]
                    use = auth_split[0]
                    logger.debug(f'use: {use}')
                except Exception as e:
                    logger.debug("citation style exception")
                    use = fielddata

                nt = use.split(',')
                nice_input = [n for n in nt if n != '' and re.match('.et al.', n) == None]

                try:
                    nice_input.append(last_author)
                except Exception as e:
                    pass

            else:
                logger.debug('not apa')

                nice_input = []
                try:
                    auth_split = re.split('\sand\s', fielddata)

                    if len(auth_split) >= 2:
                        last_author = auth_split[-1]
                    use = auth_split[0]
                    logger.debug(f'use: {use}')
                except Exception as e:
                    use = fielddata

                # standardize - only first author's name/surname are reversed
                nt = list(skip_split(use, ',', 2))
                ni = [n for n in nt if n != '']

                nice_input = []

                nice_input.append(ni[0])
                del(ni[0])
                not_reverse = ni

                try:
                    not_reverse.append(last_author)
                except Exception as e:
                    pass

                for n in not_reverse:
                    try:
                        la = n.rsplit(' ', 1)
                        lala = [l.replace(',','') for l in la]
                        lala.reverse()
                        nice_input.append(', '.join(lala))
                    except Exception as e:
                        pass


    if fieldname == "author":
        logger.debug("fieldname == author")

        inner_aliases = {'firstname': ['firstName', 'given'], 'lastname': ['lastName', 'family'], 'name': ['name'], 'alternate': [], 'type': ['creatorType']}

        for i in nice_input:
            one =  {"name": "", "alternate": [],  "firstname": "", "lastname": "", "type": "author"}

            ftype = return_data_type(i)

            if ftype == 'dict':
                logger.debug("ftype == dict")
                ks = get_all_keys(i)

                for k in ks:
                    new_key = dis_ambig(inner_aliases, k)
                    one[new_key] = i[k]


                if len(one['name']) > 2:
                    one = single_author_kons(one, one['name'], citation_style)
                else:
                    try:
                        tmp_name = one['firstname']+' '+one['lastname']
                        if len(one['name']) < 2:
                            one['name'] = tmp_name
                    except Exception as e:
                        logger.debug("can't assign author")
                        pass

                output.append(one)
            else:
                one = single_author_kons(one, i, citation_style)
                output.append(one)

    elif fieldname == "editor":
        logger.debug("fieldname == editor")
        try:
            for i in nice_input:
                one =  {"name": "", "alternate": [""],  "firstname": "", "lastname": "", "type": "editor"}
                one['name'] = i
                output.append(one)
        except:
            logger.debug("editorial error ")
            pass

    elif fieldname == "identifier":

        def appendix(input_lst, keyname=original_key):
            for i in input_lst:
                one = {"id": "", "type": ""}
                one['type'] = keyname
                one['id'] = i

                output.append(one)

        def appendone(input_val, keyname=original_key):
                one = {"id": "", "type": ""}
                one['type'] = keyname
                one['id'] = input_val
                output.append(one)


        if type(fielddata) == list:

            br = ' '.join(fielddata)

            isbns = re.findall(r"978(?:-?\d){7,10}", br)

            dois = re.findall(r"/^10.\d{4,9}/[-._;()/:A-Z0-9]+$/i", br)

            if len(isbns)>1:
                appendix(isbns, "isbn")
            else:
                pass

            if len(dois)>1:
                appendix(dois, "doi")
            else:
                try:
                    dois2 = re.findall(r"10.[-._;()/:A-Z0-9]+$", br)
                    appendix(dois2, "doi")
                except:
                    pass
        elif type(fielddata) == dict:
            logging.debug("idenfirier inside a dict?")
            pass
        else:

            isbns = re.findall(r"978(?:-?\d){7,10}", fielddata)
            if len(isbns) == 1:
                appendone(fielddata)
            elif len(isbns) > 1:
                appendix(isbns, "isbn")


    elif fieldname == "link":
        logger.debug("fieldname == link")

        one = {"format": "", "url": ""}
        if type(fielddata) == list:

            if isinstance(fielddata[0], dict):
                for i in fielddata:
                    output.append(i)
            else:
                for i in fielddata:
                    try:
                        for key, value in i.items():
                            one['format'] = key
                            one['url'] = value
                            output.append(one)
                    except:
                        anch = "href"
                        one['format'] = anch
                        one['url'] = i
                        output.append(one)
        elif type(fielddata) == dict:
            if source =="oadoi":
                print("OADOI")
                print(fielddata)
                one['url'] = fielddata['url_for_pdf']
                one['format'] = 'pdf'
                output.append(one)
        else:
            try:
                anch = "href"
                one['anchor'] = anch
                one['url'] = fielddata
                output.append(one)
            except:
                pass

    elif fieldname == "subject":
        for i in fielddata:
            output.append(i)

    return output



###NESTED DICTS
def make_a_journal(journaldata):
    logger.info("--- make_a_journal init ---")
    j_fields = ['issns', 'language', 'publisher', 'journal', 'volume', 'pages', 'year', 'issue', 'month']

    j_dict = {}
    out = {'bibjson': {}, 'extra': {}}

    for k, v in journaldata['bibjson'][0].items():
        if k in j_fields:
            j_dict[k] = v
        else:
            out['bibjson'][k] = v

    for k, v in journaldata['extra'][0].items():
        if k in j_fields:
            j_dict[k] = v
        else:
            out['extra'][k] = v

    out['bibjson']['journal'] = j_dict
    return out


def type_maker(type, data_key, data_value, source='', citation_style=''):
    logger.info("--- init type_maker ---")
    bibjson = {}
    af2 = []
    for i in types:
        if type in i:
            af = join_lists(i[type])
            af2 = af[0]+af[1]
        else:
            pass

    new_key = dis_ambig(bibjson_aliases, data_key)

    if new_key in fields['strings']:
        logger.debug("value is a string")
        dv = return_data_type(data_value)
        if dv == 'dict':
            if new_key == 'year':
                try:
                    prob_year = data_value['date-parts'][0][0]
                    bibjson[new_key] = str(prob_year)
                except Exception as e:
                    bibjson[new_key] = data_value
        else:
            bibjson[new_key] = data_value
    elif new_key in fields['list_of_dicts']:
        logger.debug("vaule is a dict")
        lod = list_of_dicts(new_key, data_value, data_key, source, citation_style)
        bibjson[new_key] = lod
    elif new_key in fields['objects']:
        logger.debug("value is an object")
        bject = make_a_journal(new_key, data_value, data_key)

    return bibjson


#source ='stuff/arg_output.json'

def json_to_bibjson(incoming, citation_style='apa', items_key='entries'):
    logger.debug(" --- init json_to_bibjson ---")
    hits = []
    hit = {"bibjson": []}
    try:
        os.path.isfile(incoming)
        f = open(incoming)
        data = json.load(f)
        data = data[items_key]
    except TypeError:
        data = incoming[items_key]

    ea = join_lists2(extra_aliases)
    bt = join_lists2(bibjson_aliases)

    for i in data:
        hit = {"bibjson": [], "extra": []}
        bibjson_output = {}
        extra_output = {}
        extra_fields = {}
        bibjson_fields = {}
        original_type = ''
        nice_type = ''
        past_keys = []

        if isinstance(i, dict):
            for key, value in i.items():
                mua = {}
                listo = bibjson_aliases['type']

                #extracts original type value
                if key in listo:
                    if isinstance(value, (list)):
                        original_type = value[0].lower()
                    elif isinstance(value, dict):
                        tmp_typ = value[next(iter(value))]
                        try:
                            original_type = tmp_typ.split('/')[-1]
                            print(original_type)
                        except:
                            original_type = value[next(iter(value))]
                    else:
                        original_type = value.lower()

                #translates keys to standard values
                if key in ea:
                    try:
                        extra_fields[dis_ambig(extra_aliases, key)] = value
                    except:
                        pass
                elif key in bt:
                    bibjson_fields[key] = value
                else:
                    pass
        else:
            pass

        # standardizes type names based on aliases in types (top)
        for i in types:
            type_name = list(i.keys())[0]
            alia = i[type_name]['aliases']

            if original_type in alia:
                nice_type = type_name
            else:
                pass

        #print bibjson_fields
        for key, value in bibjson_fields.items():

            # if nice type is missing assign misc
            if nice_type == '':
                nice_type = 'misc'

            # use cleaned up type value
            if key == "type":
                value = nice_type

            bibjson_one = type_maker(nice_type, key, value, citation_style=citation_style)

            if bool(bibjson_one) == True:
                for k, v in bibjson_one.items():
                    #checks if value already exists in bibjson output ... if so it needs to be appended to existing bibjson differently
                    if k in past_keys:
                        if type(v)==list:
                            try:
                                for i in v:
                                    bibjson_output[k].append(i)
                            except:
                                pass
                        else:
                            try:
                                bibjson_output[k].append(v)
                            except:
                                pass

                    else:
                        try:
                            bibjson_output[k] = v
                        except:
                            pass

            if list(bibjson_one.keys())[0] not in past_keys:
                past_keys.append(list(bibjson_one.keys())[0])

        for key, data_value in extra_fields.items():
            # checks if stuff is weirdly nested
            extra_output[key] = data_value

        hit['bibjson'].append(bibjson_output)
        hit['extra'].append(extra_output)

        vlogger.debug("json_to_bibjson output")
        vlogger.debug(pformat(bibjson_output))

        try:
            if bibjson_output['type'] == 'article':
                hit = make_a_journal(hit)
        except KeyError:
            pass


        hits.append(hit)

    return hits


def standardize_links(source, data, keep=False):
    standard_type = {'original': {'test': 'url', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url'], 'href_alias': 'url'}, 'doab': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'monoskop': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url', 'PDF']}, 'libgen_book': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'libgen_article': {'test': 'type', 'download_aliases': ['download_url', 'Sci-Hub'], 'landing_aliases': ['landing_url', 'Libgen.lc'], 'open_aliases': ['open_url']}, 'doaj': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url', 'fulltext'], 'href_alias': 'url'}, 'osf': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'scielo': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'memoryoftheworld': {'test': 'format', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'core': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url', 'View in browser']}, 'aaaaarg': {'test': 'url', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url'], 'href_alias': 'url'}, 'aaaaarg': {'test': 'url', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url'], 'href_alias': 'url'}}

    try:
        test_src = standard_type[source]
    except:
        return data

    if standard_type[source]['test'] == 'type':
        if data['type'] in standard_type[source]['download_aliases']:
            data['type'] = "download_url"
            data['name'] = "download"
        elif data['type'] in standard_type[source]['landing_aliases']:
            data['type'] = "landing_url"
        elif data['type'] in standard_type[source]['open_aliases']:
            data['type'] = "open_url"
            data['name'] = "open"
        else:
            data['type'] = "other_url"

        # not all links are hrefs
        try:
            alias = standard_type[source]['href_alias']
            data['href'] = data[alias]
            del data[alias]
        except:
            pass


    elif standard_type[source]['test'] == 'format':
        if data['format'] == 'pdf':
            data['type'] = 'open_url'
            data['name'] = 'open'
        else:
            data['type'] = 'download_url'
            data['name'] = 'download'

    elif standard_type[source]['test'] == 'url':
        try:
            if data['type'] == 'landing_url':
                data['type'] = "landing_url"
                data['name'] = "landing"
        except:
            if data['url'].endswith('pdf'):
                data['type'] = "open_url"
                data['name'] = "open"
            else:
                data['type'] = "download_url"
                data['name'] = "download"

        # not all links are hrefs
        try:
            alias = standard_type[source]['href_alias']
            data['href'] = data[alias]
            del data[alias]
        except:
            pass

    else:
        pass


    return data



def mein_main(incoming):
    logger.info("--- mein_main init ---")
    hits = []

    hit = {"bibjson": []}
    try:
        os.path.isfile(incoming)
        f = open(incoming)
        data = json.load(f)
        data = data['entries']
    except TypeError:
        data = incoming['entries']

    for i in data:
        new_hits = []

        try:
            source = list(i.keys())[0]
            global current_source
            current_source = source
        except Exception as e:
            pass

        if get_it(sources_bibjson, current_source=''):
            cleaner = resolve_depth(sources_bibjson, current_source, 'hits')
            try:
                for x in i[source]['hits'][cleaner]:
                    new_hits.append(x)
            except TypeError:
                pass
        else:
            try:
                for x in i[source]['hits']:
                    new_hits.append(x)
            except TypeError:
                pass


        #rename all the compatible fields?
        ea = join_lists2(extra_aliases)
        bt = join_lists2(bibjson_aliases)



        for i in new_hits:
            hit = {"bibjson": [], "extra": []}
            bibjson_output = {}
            extra_output = {}
            extra_fields = {}
            bibjson_fields = {}
            original_type = ''
            nice_type = ''
            past_keys = []

            cs = {"source": current_source}


            # WHAT DOES THIS DO?
            if get_it(sources_bibjson, current_source):
                count = 0

                cleaner = resolve_depth(sources_bibjson, current_source, 'hit')

                hit['bibjson'].append(i[cleaner])
                hit['extra'].append({'source': current_source})
                hit['extra'].append({'rank': count})

                hits.append(hit)
                count+=1
            else:
                if isinstance(i, dict):
                    for key, value in i.items():
                        mua = {}

                        listo = bibjson_aliases['type']

                        #extracts original type value
                        if key in listo:
                            if isinstance(value, (list)):
                                original_type = value[0].lower()
                            elif isinstance(value, dict):
                                tmp_typ = value[next(iter(value))]
                                try:
                                    original_type = tmp_typ.split('/')[-1]
                                    print(original_type)
                                except:
                                    original_type = value[next(iter(value))]
                            else:
                                original_type = value.lower()


                        #translates keys to standard values
                        if key in ea:
                            try:
                                extra_fields[dis_ambig(extra_aliases, key)] = value
                            except:
                                pass
                        elif key in bt:
                            bibjson_fields[key] = value
                        else:
                            pass
                else:
                    pass


                # standardizes type names based on aliases in types (top)
                for i in types:
                    type_name = list(i.keys())[0]
                    alia = i[type_name]['aliases']

                    if original_type in alia:
                        nice_type = type_name
                    else:
                        pass


                for key, value in bibjson_fields.items():
                    # if nice type is missing assign misc
                    if nice_type == '':
                        nice_type = 'misc'

                    # use cleaned up type value
                    if key == "type":
                        value = nice_type


                    bibjson_one = type_maker(nice_type, key, value, source, citation_style)


                    if bool(bibjson_one) == True:
                        for k, v in bibjson_one.items():
                            #checks if value already exists in bibjson output ... if so it needs to be appended to existing bibjson differently
                            if k in past_keys:
                                if type(v)==list:
                                    try:
                                        for i in v:
                                            bibjson_output[k].append(i)
                                    except:
                                        pass
                                else:
                                    try:
                                        bibjson_output[k].append(v)
                                    except:
                                        pass

                            else:
                                try:
                                    bibjson_output[k] = v
                                except:
                                    pass

                    if list(bibjson_one.keys())[0] not in past_keys:
                        past_keys.append(list(bibjson_one.keys())[0])

                for key, data_value in extra_fields.items():
                    # checks if stuff is weirdly nested
                    for s in resolving_nesting:
                        if source in s:
                            pf = s[source]['problem_fields']
                            for f in pf:
                                if f['field_name'] == key:

                                    # this is not sustainable
                                    if return_data_type(data_value) == "list":
                                        data_value = data_value[0]

                                    temp = data_value[f['depth_and_keys']]
                                    data_value = temp
                        else:
                            pass

                    extra_output[key] = data_value

                extra_output['source'] = current_source

                hit['bibjson'].append(bibjson_output)
                hit['extra'].append(extra_output)


                # correction if it's a journal
                try:
                    if bibjson_output['type'] == 'article':
                        hit = make_a_journal(hit)
                except KeyError:
                    pass

                hits.append(hit)

    return hits
