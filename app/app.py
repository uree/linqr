# -*- coding: utf-8 -*-
# python 3.6.9

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# flask
from flask import Flask, flash, request, redirect, url_for, render_template, jsonify, send_from_directory, after_this_request, session
from flask_session import Session
from flask_dropzone import Dropzone
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict, CombinedMultiDict

#stdlib
import os
import pprint
from pprint import pformat
import logging
import copy
from random import randrange, randint
import subprocess
import ast

# external
import requests
import pdfkit
import jinja2
import pypandoc as pd
from bs4 import BeautifulSoup

# my modules
from bibjson_methods import *
from linkbuilder_totext import *
from hypost import *



# FLASK CONFIG
allowed_ext_list = ['txt', 'docx', 'pdf', 'odt', 'bib', 'bibtex', 'json']
ALLOWED_EXTENSIONS = set(allowed_ext_list)

possible_output_formats = ['html','pdf', 'odt', 'docx', 'epub']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads/"
app.config['DOWNLOAD_FOLDER'] = "downloads/"

# session
SESSION_TYPE = 'redis'
app.config.from_object(__name__)
Session(app)

# dropzone
max_in_mb = 10
dropzone = Dropzone(app)
app.config['DROPZONE_ALLOWED_FILE_CUSTOM'] = True
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = '.txt, .pdf, .odt, .md, .bib, .bibtex, .json'
app.config['DROPZONE_MAX_FILES'] = 2
app.config['DROPZONE_MAX_FILE_SIZE'] = max_in_mb

# bypass flask to render jijnja template without request
f = open('templates/dropzone.html')
dzone_template_raw = f.read()
template = jinja2.Template(dzone_template_raw)
drop_html = template.render(formats=allowed_ext_list, max_size=max_in_mb)
app.config['DROPZONE_DEFAULT_MESSAGE'] = drop_html

# JINJA2 SETTINGS
# app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True


# LOGGING
# main logger
logger = logging.getLogger('app')
logger.setLevel(logging.ERROR)

fh = logging.FileHandler('logs/app.log')
fh.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(funcName)s :: %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# verbose logger (output data)
vlogger = logging.getLogger('app_verbose')
vlogger.setLevel(logging.ERROR)
v_fh = logging.FileHandler('logs/app_verbose.log')
v_fh.setLevel(logging.ERROR)
v_formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(funcName)s ::\n\r %(message)s')
v_fh.setFormatter(v_formatter)
vlogger.addHandler(v_fh)


# MISC
upload_path = {'bibtex': None, 'text': None}
pp = pprint.PrettyPrinter(indent=4)



# GENERAL FUNCTIONS, SIR!

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def delete_file(filename):
    if os.path.exists(filename):
        os.remove(filename)
        return ("File {} removed").format(filename)
    else:
        return ("File {} does not exist").format(filename)


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


# PARSING BIBDATA FUNCTIONS

def merge_json(data):
    for d in data['bib_and_links']:
        try:
            search_results = d['search_results']
        except Exception as e:
            search_results = None

        if search_results != None:
            for s in search_results:
                try:
                    solo = s['bibjson'][0]['link']
                except:
                    solo = None

                if solo != None:
                    for l in solo:
                        try:
                            # bibjson requires anchor instead of name
                            l['anchor'] = l.pop('name')
                            d['bibjson'][0]['link'].append(l)
                        except Exception as e:
                            d['bibjson'][0]['link'] = []
                            # possible errors if l is list
                            try:
                                l['anchor'] = l.pop('name')
                                d['bibjson'][0]['link'].append(l)
                            except Exception as e:
                                pass
                    try:
                        del d['search_results']
                    except:
                        pass

                    try:
                        del d['top_search_results']
                    except:
                        pass

    return data


def update_bibfile(data, output_format):
    logger.info("--- init update_bibfile: inserting links into bibtex ---")
    # option 1: links into .json, return json
    if output_format == 'bibjson':
        logger.info('json')
        merged = merge_json(data)

        outname = 'f'+str(randrange(10000))+'.json'
        outpath = 'downloads/'+outname
        with open(outpath, 'w+') as f:
            json.dump(merged['bib_and_links'], f, indent=4, sort_keys=True)

        dlink = 'download-file/'+outname

        merged['bib_download_link'] = outpath.replace('downloads/', 'download-file/')

        return merged

    # option 2: links into .bib, return bib
    else:
        logger.info('not json')
        merged = merge_json(data)

        # preparing for zotero
        clean = zotero_cleanup(merged['bib_and_links'])

        # post to zotero translation server
        zot_url = "http://127.0.0.1:1969/export?format="+output_format
        zot_headers = {"Content-Type": "application/json"}

        try:
            r = requests.post(zot_url, json=clean, headers=zot_headers)
        except Exception as e:
            logger.error("zotero translation server is down")


        fid = str(randrange(10000))
        bibname = 'bib_'+fid+'.'+output_format
        bibpath = 'downloads/tmp/'+bibname
        with open('downloads/tmp/'+bibname, 'w+') as f:
            f.write(r.text)

        data['zotero_api_json'] = clean
        data['bib'] = r.text
        data['bib_download_link'] = bibpath.replace('downloads/', 'download-file/')

        return data


def generate_bibliography_loop(data, format='html', style='', selection=False):
    logger.info("-- generate_bibliography_loop init ---")
    vlogger.debug(pformat(data['bib_and_links']))

    output_html = ''

    if style == 'chicago':
        style = 'chicago-author-date'

    logger.debug(f"Chosen style: {style}")

    for d in data['bib_and_links']:
        to_cite = csljson_cleanup(d['bibjson'][0])
        vlogger.debug(pformat(to_cite))

        try:
            to_link = d['top_search_results']['link']
        except Exception as e:
            to_link = None

        csl_headers = {"Content-Type": "application/json"}
        citeprocjs_url = 'http://127.0.0.1:8085?responseformat='+format+'&style='+style

        try:
            rc = requests.post(citeprocjs_url, json=to_cite, headers=csl_headers)
        except Exception as e:
            logger.error("citeprocjs server down", exc_info=True)

        reference = rc.text
        vlogger.debug("Citeprocjs returned: ")
        vlogger.debug(pformat(reference))

        prep_id = ("").join([d['bibjson'][0]['author'][0]['family'].lower(), d['bibjson'][0]['year']])

        links_html = '<br><span class="links" id="'+prep_id+'">Links: '

        # create links
        if to_link != None:
            for l in to_link:
                if selection == True:
                    try:
                        selected = l['selected']
                    except Exception as e:
                        logger.debug('True selection error', exc_info=True)
                        selected = False

                    if selected == True:
                        try:
                            link = '<a href="'+l['href']+'">'+l['type'].split('_')[0]+'</a> '
                        except Exception as e:
                            logger.debug('True selection error', exc_info=True)
                            link = ''

                        links_html += link
                else:
                    try:
                        # to keep names in sync with updated types
                        link = '<a href="'+l['href']+'">'+l['type'].split('_')[0]+'</a> '
                    except Exception as e:
                        logger.debug('True selection error', exc_info=True)
                        link = ''

                    links_html += link


            links_html += '</span><br><br>'
        else:
            logger.debug("No links found")
            links_html = '<br>'

        output_html += reference+links_html



    return output_html



def generate_linked_reference(match, bibdata, quotes=False, twoway=False, src_url=None):
    logger.info("--- inint generate linked reference ---")
    logger.debug(f'quotes: {quotes}, twoway: {twoway}, src_url: {src_url}')

    groups = match['groups']

    try:
        has_quotes = match['groups']['works'][0]['quote']
    except:
        has_quotes = False


    output = {'hl_quotes': [], 'main': []}
    count=0

    for f in groups['works']:
        out = {'author': '', 'year': '', 'page': '', 'ttipid': '', 'bibkey': ''}

        try:
            out['ttipid'] = str(match['start'])+str(match['end'])+str(count)
        except Exception as e:
            logger.error('tooltip id generation error', exc_info=True)

        # inline_muster = '<a href="#">{ author } { year }:</a> <a href="" class="tooltip" data-tooltip-content="{ #start-end }">{ page }</a>'
        #
        # content_one_muster = '<a href="{ href }">{ name }</a>'
        #
        # content_muster = '<span id="{ start-end }">{ content_one_muster }</span>'


        try:
            intext_author_dirt = re.split(r"\,|\sand\s", f['author'])
            tmp_author_1 = [n.strip() for n in intext_author_dirt]
            logger.debug(f'split authors {tmp_author_1}')
        except Exception as e:
            tmp_author_1 = []


        if 'et al' in tmp_author_1[0]:
            etal = True
            tmp_author = [tmp_author_1[0].split(' ',-1)[0].replace('et al','').strip()]
        else:
            etal = False
            tmp_author = tmp_author_1

        try:
            id_author = tmp_author[0]
        except Exception as e:
            id_author = ''

        logger.debug(f'id_author: {id_author}')

        out['author'] = f['author']

        try:
            out['year'] = f['year'].strip()
        except Exception as e:
            pass

        try:
            out['page'] = f['page'].strip()
        except Exception as e:
            pass

        try:
            out['in_pdf_page'] = f['page'].strip()
        except Exception as e:
            pass


        # refined results
        logger.info("Processing links, almost hyposting ...")

        try:
            tmp_author.remove('')
        except:
            pass


        new_links = []

        if len(tmp_author) > 1 or etal == True:
            f_id = id_author.lower()+'_etal_'+f['year'].strip()
        else:
            f_id = id_author.lower()+f['year'].strip()

        out['bibkey'] = f_id

        try:
            links = bibdata[f_id]['link']
        except Exception as e:
            logger.debug("no links made it till here")
            links = None


        if links:
            for item in bibdata[f_id]['link']:
                item['selected'] = True

                if (item['type'] == 'open_url' and quotes and has_quotes) or (item['type'] == 'open_url' and twoway and has_quotes):
                    logger.debug(f"Hypothesisize this link: {item}")
                    try:
                        logger.debug("Using this quote: {f['quote']} ")
                        output['hl_quotes'].append(f['quote'])
                    except Exception as e:
                        logger.debug("Unless there's no quote and it throws an error: ", exec_info=True)

                    item_upd = copy.deepcopy(item)

                    if twoway:
                        logger.debug("hypo linkback")
                        # call hypost with appropriate parameter url
                        # citation = groups[0]['quote']
                        try:
                            hypo_callback = hypost(item['href'], citation=groups['works'][0]['quote'], twoway=twoway, src_url=src_url, tooltip_id=out['ttipid'])
                        except Exception as e:
                            logger.error('Error posting to hypothes.is')
                            vlogger.debug(pformat(item))
                            vlogger.debug(pformat(groups))
                    else:
                        logger.debug("hypo no linkback")

                        try:
                            hypo_callback = hypost(item['href'], groups['works'][0]['quote'])
                        except Exception as e:
                            logger.error('Error posting to hypothes.is')
                            vlogger.debug(pformat(item))
                            vlogger.debug(pformat(groups))

                    vlogger.debug(pformat(hypo_callback))

                    # update the link
                    item_upd['hypo_id'] = hypo_callback['id']
                    item_upd['href'] = hypo_callback['links']['incontext']
                    item_upd['type'] = 'direct_url'
                    item_upd['name'] = 'direct'

                    new_links.append(item_upd)
                else:
                    new_links.append(item)


            out['links'] = new_links
            output['main'].append(out)
            vlogger.debug("outlinks baby")
            vlogger.debug(pformat(out))

        else:
            output['main'].append(out)

    return output



@app.errorhandler(500)
def internal_error(error):
    logger.error("An internal server error occured and was handled by the error handler.")
    return render_template('error.html'), 500


# routes
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    logger.info('\n\n###  NEW REQUEST ###')
    logger.info('--- upload_file init ---')
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        files = request.files
        logger.debug(files)

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            global upload_path
            filename = secure_filename(file.filename)
            destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(destination)
            if filename.endswith('.bib') or filename.endswith('.json') :
                upload_path['bibtex'] = destination
            else:
                upload_path['text'] = destination


    return render_template('index.html')

@app.route('/download/<option>/<format>', methods=['GET', 'POST'])
def resulting_choices(option, format):
    logger.info("--- resulting_choices init ---")
    if request.method == "POST":
        json_load = request.get_json()
        selected_format = format

        try:
            selected_style = session['citation_style_bib']
        except Exception as e:
            selected_style = 'chicago'


        logger.debug(f"Option {option} Format {selected_format}")
        vlogger.debug(pformat(json_load))


        if option == 'file':
            output = update_bibfile(json_load, format)
            download_link = output['bib_download_link']

        elif option == "bibliography":
            output = generate_bibliography_loop(json_load, format='html', style=selected_style)

            vlogger.debug("generate_bibliography_loop returns")
            vlogger.debug(pformat(output))

            fid = str(randrange(10000))
            f_name = 'output'+fid
            f_name_html = f_name+'.html'
            # a separate html file, without tooltips, for conversion
            conv_f_name_html = 'conv_'+f_name_html
            path = 'downloads/tmp/'
            html_path = path+f_name_html

            # write the generated text to file here
            with open(html_path, 'w+') as f:
                f.write('<h2>References</h2>')
                f.write(output)

            if selected_format == 'html':
                download_link = html_path
            else:
                output_path = path+f_name+'.'+selected_format
                logger.debug(f"Output path: {output_path}")
                options = {
                    'page-size': 'A4',
                    'margin-top': '1in',
                    'margin-right': '1in',
                    'margin-bottom': '1in',
                    'margin-left': '1in',
                    'encoding': "UTF-8",
                    '--enable-internal-links': ''
                }

                if selected_format == 'pdf':
                    pdfkit.from_file(html_path, output_path, options=options)
                else:
                    pd.convert_file(html_path, selected_format, outputfile=output_path)

                #remove temporary html file
                os.remove(conv_html_path)

                #redirect to download page
                download_link = output_path
        else:
            download_link = '/error'
            pass

        logger.debug(f"DL LINK: {download_link}")

        dl_path = download_link.replace('downloads/', 'download-file/')
        logger.debug(f"DL PATH: {dl_path}")

    return jsonify({'response' : 200, 'download_link': dl_path})



@app.route('/download-file/<path:path>', methods=['GET'])
def serve_download(path):
    logger.info("--- serve_download init: serving download ---")

    @after_this_request
    def remove_file(response):
        os.remove("downloads/"+path)
        return response

    try:
        return send_from_directory(app.config["DOWNLOAD_FOLDER"], filename=path, as_attachment=True)
    except FileNotFoundError:
        logger.error("404 when serving download")
        abort(404)


def pandoc_bib2json(bibpath):
    logger.info("--- pandoc_bib2json init ---")
    spl = bibpath.split('/', -1)
    cwd = os.getcwd()+'/'+spl[0]

    options = ["pandoc-citeproc", "--bib2json", spl[1]]
    proc = subprocess.check_output(options, cwd=cwd)

    str = proc.decode("UTF-8")
    d = ast.literal_eval(str)
    return d


@app.route('/searching', methods=['GET'])
def searching():
    logger.info('--- upload_file init ---')
    global upload_path
    global possible_output_formats

    ######### LIVESEARCH ############

    #if bibtex/bibjson was uploaded
    if upload_path['bibtex']:
        citation_style = ''
        f = open(upload_path['bibtex'])

        if upload_path['bibtex'].endswith('.bib'):
            #print("bibliography uploaded as file")
            citation_style = 'chicago'
            references = {'items': []}
            references['items'] = pandoc_bib2json(upload_path['bibtex'])
        else:
            references = json.load(f)

        f.close()

        try:
            del references['config']
            del references['collections']
        except Exception as e:
            #print(e)
            pass

        # convert to bibjson, clean up any pandoc mistakes
        query_material = json_to_bibjson(references, citation_style=citation_style, items_key='items')
        #pp.pprint(query_material)

    # if text was uploaded
    if upload_path['text']:

        # convert the file to text
        rawtext = delegate(upload_path['text'])

        # extract all the references
        references = extract_ref_list(rawtext)
        session['citation_style_bib'] = references['citation_style_bib']
        #pp.pprint(references)

        # convert them to bibjson (for bulk query)
        if not upload_path['bibtex']:
            query_material = json_to_bibjson(references, citation_style= references['citation_style_bib'])


    logger.debug(f"This is how many bib items there are: {len(query_material)}")
    vlogger.debug(pformat(query_material))


    # and query radovan bulk based on bibjson
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    #set length of query_material here
    try:
        results_inc = requests.get('http://localhost:9003/v1.0/bulk', json=query_material, headers=headers)
    except Exception as e:
        logger.error(f"Querying Radovan failed: {results.status_code} ", exec_info=True)
        return render_template('no_links_found.html')


    results = results_inc.json()
    vlogger.debug("Radovan query results")
    vlogger.debug(pformat(results))



    if results['references_with_new_links'] == 0:
       return render_template("no_links_found.html")


    try:
        results['begin_reflist'] = references['reflist_beginnig']
    except Exception as e:
        #print(e)
        pass
    try:
        results['thetext'] = rawtext[:references['reflist_beginnig']]
    except Exception as e:
        #print(e)
        pass

    # #uncomment to save last query
    # f = open("tests/last_query_apa.json", 'w+')
    # json.dump(results, f, sort_keys=True, indent=4)
    # f.close()

    ######## LIVESEARCH ############


    ######## SAVED SEARCH ##########
    # with open("tests/last_query.json", "r") as f:
    #     results = json.load(f)
    #     #pp.pprint(results)
    #
    # # extra section for testing ... keep reference list!
    # rawtext = delegate(upload_path['text'])
    # #print("RAWTEXT")
    # #print(rawtext)
    # session['rawtext'] = rawtext
    # references = extract_ref_list(rawtext)
    #
    # session['citation_style_bib'] = references['citation_style_bib']
    #end extra section for testing
    ####### SAVED SEARCH ##########



    # filter the dictionary so that it only contains one hit per source
    def extract_top_results(results):
        logger.info("--- extract_top_results init ---")
        vlogger.debug(pformat(results))

        for b in results['bib_and_links']:

            new_links = {'link': []}

            # we have the right data here
            try:
                original_link = b['bibjson'][0]['link']
                logger.debug("Orignal link available")
            except Exception as e:
                original_link = None
                logger.debug("Orignal link unavailable")

            # avoid a number of silly errors
            try:
                dummy = b['search_results']
            except Exception as e:
                dummy = None

            if dummy != None:
                for n in b['search_results']:
                    try:
                        amp = n['extra'][0]['rank']
                    except:
                        logger.debug("Missing rank info from result")
                        vlogger.debug(pformat(n))
                        pass

                try:
                    tmp_search_results = [n for n in b['search_results'] if n['extra'][0]['rank'] == 0]

                    for r in tmp_search_results:
                        src = r['extra'][0]['source']
                        for l in r['bibjson'][0]['link']:
                            l['source'] = src

                            new_links['link'].append(l)
                except Exception as e:
                    logger.debug("Missing rank info from result", exec_info=True)

            if original_link != None:
                for l in original_link:
                    std = standardize_links('original', l)
                    new_links['link'].append(std)

            b['top_search_results'] = new_links

        return results



    refined_results = extract_top_results(results)
    vlogger.debug("Refined results")
    vlogger.debug(pformat(refined_results))


    return render_template('resulting_choices.html', results=refined_results, formats=possible_output_formats)



@app.route('/processing/<option>', methods=['GET', 'POST'])
def processing(option):
    logger.info("--- processing init ---")

    allowed_options = ['pages', 'quotes', 'twoway']


    if request.method == 'POST':
        logger.info("post request received")
        logger.debug(f"option: {option}")

        nice_load = request.get_json()
        session['results'] = nice_load
        vlogger.debug(pformat(nice_load))


        # thetext
        # this is where we convert the file to text w textract
        # use the text from extract_ref_list if present
        try:
            thetext = nice_load['thetext']
        except Exception as e:
            global upload_path
            rawtext = delegate(upload_path['text'])
            references = extract_ref_list(rawtext)
            thetext = rawtext[:references['reflist_beginnig']][0]

        session['thetext'] = thetext
        vlogger.debug("uploaded text:")
        vlogger.debug(pformat(thetext))

        # extract citations
        # switch here for text integrated with search results (thetext) vs original upload (session['rawtext'])
        citations = extract_refs(thetext)
        #citations = extract_refs(session['rawtext'])

        vlogger.debug("Debugging matches")
        vlogger.debug(pformat(citations))

        session['matches'] = citations
        session['citation_style_refs'] = citations['citation_style_refs']

        logger.debug(f"Reference style refs outer: {session['citation_style_refs']}")

        redirect_url = "preview"

        if option in allowed_options:
            session['option'] = option
        else:
            return render_template('error.html')

        if option == 'twoway':
            logger.debug(f"linkback: {session['results']['linkback']}")
            pass


    return jsonify({'response' : 200, 'redirect_url': redirect_url})



@app.route('/preview', methods=['GET', 'POST'])
def preview():
    logger.info("--- preview init ---")
    # match results and matches?
    combined = session['results']
    vlogger.debug("Combined data")
    vlogger.debug(pformat(combined))
    vlogger.debug("Found in text references/macthes")
    vlogger.debug(pformat(session['matches']))


    # option control
    quotes = False
    twoway = False
    if session['option'] == 'quotes':
        quotes = True
    elif session['option'] == 'twoway':
        twoway = True


    # this happens in any case
    tmp = []
    all_quotes_to_hl = []


    for m in session['matches']['matches']:

        muster = {'original_metadata': {'bibjson': '', 'extra': ''}, 'match': m, 'search_results': {}, 'top_search_results': {}}

        for w in m['groups']['works']:

            # for each of these append a bibliography
            for b in session['results']['bib_and_links']:
                try:
                    bibjson_year = b['bibjson'][0]['year']
                    author_count = len(b['bibjson'][0]['author'])
                except Exception as e:
                    logger.error("Error getting name or author count bibdata")

                intext_year = w['year'].strip()

                if author_count > 1:
                    logger.info("many authors")
                    vlogger.debug(pformat(b['bibjson'][0]['author']))


                    # add the etal option
                    # the only real difference between the top and bottom part, could be combined

                    if 'et al' in w['author']:
                        logger.debug("author includes et al")
                        bibjson_author = [b['bibjson'][0]['author'][0]['lastname']]
                        intext_author = [w['author'].split(' ',-1)[0].replace('et al','').strip()]
                    elif 'et al.' in w['author']:
                        logger.debug("author includes et al.")
                        bibjson_author = [b['bibjson'][0]['author'][0]['lastname']]
                        intext_author = [w['author'].split(' ',-1)[0].replace('et al.','').strip()]
                    else:
                        logger.debug("dealing with listed authors here")
                        bibjson_author = [n['lastname'] for n in b['bibjson'][0]['author']]
                        intext_author_dirt = re.split(r"\,|\sand\s", w['author'])
                        intext_author = [n.strip() for n in intext_author_dirt]


                    logger.debug(f"Comparing (multiple authors): {bibjson_author} {bibjson_year} : {intext_author} {intext_year}")

                    # this whole matching thing is not super accurate
                    if sorted(intext_author) == bibjson_author and intext_year == bibjson_year:

                        try:
                            dummy = b['top_search_results']['link']
                        except Exception as e:
                            dummy = None


                        if dummy != None:
                            # a different kind of object
                            muster['original_metadata']['bibjson'] = b['bibjson'][0]
                            try:
                                muster['original_metadata']['extra'] = b['bibjson']['extra'][0]
                            except Exception as e:
                                pass

                            bibkey = bibjson_author[0].lower()+'_etal_'+bibjson_year
                            logger.debug(f"Bibkey generated {bibkey}")

                            try:
                                muster['search_results'][bibkey] = b['search_results'][0]
                            except Exception as e:
                                pass


                            try:
                                muster['top_search_results'][bibkey] = b['top_search_results']
                            except Exception as e:
                                logger.error("Error reassigning top search results")

                    else:
                        logger.debug("NO MATCH")
                        pass
                else:
                    try:
                        # bibjson_author = b['bibjson'][0]['author'][0]['name'].split(' ')[0]
                        bibjson_author = b['bibjson'][0]['author'][0]['lastname']
                    except Exception as e:
                        logger.error("Error fetching author's lastname from bibjson")


                    intext_author = w['author'].replace(',','').strip()


                    logger.debug(f"Comparing (single author): {bibjson_author} {bibjson_year} : {intext_author} {intext_year}")

                    # this whole matching thing is not super accurate
                    if intext_author == bibjson_author and intext_year == bibjson_year:
                        try:
                            dummy = b['top_search_results']['link']
                        except Exception as e:
                            dummy = None

                        if dummy != None:
                            # a different kind of object
                            muster['original_metadata']['bibjson'] = b['bibjson'][0]

                            try:
                                muster['original_metadata']['extra'] = b['bibjson']['extra'][0]
                            except Exception as e:
                                pass

                            bibkey = bibjson_author.lower()+bibjson_year
                            logger.debug(f"Bibkey generated {bibkey}")

                            try:
                                muster['search_results'][bibkey] = b['search_results'][0]
                            except Exception as e:
                                pass


                            try:
                                muster['top_search_results'][bibjson_author.lower()+bibjson_year] = b['top_search_results']
                            except Exception as e:
                                logger.error("Error reassigning top search results")

                    else:
                        logger.debug("NO MATCH")


        tmp.append(muster)


    # generate the text with links
    preview_text = []
    raw_text = session['thetext']
    start = 0
    iteration = 0


    # with refined search results (processed per match?)
    for t in tmp:
        logger.debug("### next t ###")

        if bool(t['top_search_results']):
            res = t['top_search_results']
        else:
            res = None

        one = {}

        if res:

            try:
                # remove any parentheses which might be part of the match
                apart = raw_text[start:t['match']['start']].strip()
                part = rreplace(apart, '(', '', 1)
            except Exception as e:
                logger.debug("Error extracting text part", exc_info=True)

            try:
                # gets assigned to old match
                cit = raw_text[start:t['match']['end']]
            except Exception as e:
                logger.debug("Error extracting citation part", exc_info=True)

            try:
                src_url = session['results']['linkback']
            except:
                src_url = None


            # insert stuff
            try:
                # this function switches between hypothesis links and others
                gen_results = generate_linked_reference(t['match'], t['top_search_results'], quotes=quotes, twoway=twoway, src_url=src_url)
                new_cit = gen_results['main']

            except Exception as e:
                logger.error("Error when running linked reference generation", exc_info=True)
                vlogger.debug("This is the error", exc_info=True)


            try:
                if gen_results['hl_quotes']:
                    for h in gen_results['hl_quotes']:
                        all_quotes_to_hl.append(h)
            except Exception as e:
                logging.debug("Error extracting quotes to highlight ", exc_info=True)

            one['old_cit'] = t['match']['groups']['all']
            one['old_match'] = cit

        # no results use original text
        else:
            part = raw_text[start:t['match']['start']]
            new_cit = raw_text[start:t['match']['end']]
            vlogger.debug(pformat(t['match']))

        one['part'] = part
        one['new_cit'] = new_cit
        one['rank'] = start
        one['match_type'] = t['match']['name']

        logger.debug(f"This is end value right before assignment: {t['match']['end']} It should equal end of last match.")

        start = t['match']['end']
        iteration+=1


        #print("This is one: ")
        vlogger.debug("This is one match")
        vlogger.debug(pformat(one))

        preview_text.append(one)


    #append the last bit of text after the last match
    if iteration == len(tmp):
        one_more = {}
        if start != len(raw_text):
            one_more['new_cit'] = raw_text[start:]
            preview_text.append(one_more)


    combined['preview_text'] = preview_text
    combined['matches_and_links'] = tmp
    combined['all_quotes_to_hl'] = all_quotes_to_hl

    vlogger.debug("This is preview_text")
    vlogger.debug(pformat(preview_text))


    # this is necessary for cases when references are not extracted because the user provides bibinfo in a file
    if session['citation_style_bib']:
        use_style_info =  session['citation_style_bib']
    else:
        use_style_info =  session['citation_style_refs']

    logger.debug(f"Citation style used: {use_style_info}")

    return render_template('processing.html', results=session['results'], thetext=session['thetext'], matches=session['matches'], combined=combined, option=session['option'], style=use_style_info)


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    logger.info("--- generate init: generating since 2020 ---")
    if request.method == 'POST':

        nice_load = request.get_json()

        selected_format = nice_load['format']

        logger.debug(f"Citaton style: {session['citation_style_bib']} Selected format: {selected_format}" )

        main_load = nice_load['data']

        new_main_load = copy.deepcopy(main_load)
        new_bib_and_links = []


        # prepare data
        # match chosen links from preview text with bibliographic data via citekeys
        for bib in main_load['bib_and_links']:
            try:
                if len(bib['bibjson'][0]['author']) == 1:
                    id_key = bib['bibjson'][0]['author'][0]['lastname'].lower()+bib['bibjson'][0]['year'].strip()
                else:
                    id_key = bib['bibjson'][0]['author'][0]['lastname'].lower()+'_etal_'+bib['bibjson'][0]['year'].strip()
                logger.debug(f"ID key: {id_key}")
            except Exception as e:
                id_key = None

            if id_key != None:
                for m in main_load['preview_text']:
                    try:
                        lookup = m['new_cit'][0]['bibkey']
                        linksos = [l for l in m['new_cit'][0]['links'] if l['selected'] == True]
                    except Exception as e:
                        logger.debug("Missing bibkey or links", exc_info=True)
                        lookup = None
                        linksos = None

                    # not once does this happen
                    if id_key == lookup:
                        bib['top_search_results']['link'] = linksos


            new_bib_and_links.append(bib)


        main_load['bib_and_links'] = new_bib_and_links
        vlogger.debug("Updated bib and links")
        vlogger.debug(pformat(main_load['bib_and_links']))

        # generate bibliography
        output = generate_bibliography_loop(main_load, format='html', style=session['citation_style_bib'], selection=True)

        fid = str(randrange(10000))
        f_name = 'output'+fid
        f_name_html = f_name+'.html'
        # a separate html file, without tooltips, for conversion
        conv_f_name_html = 'conv_'+f_name_html
        path = 'downloads/tmp/'
        html_path = path+f_name_html
        conv_html_path = path+conv_f_name_html

        # generate new text and references
        if selected_format == 'html':
            logger.info("generating html")
            html_template_path = 'templates/tooltips_'+session['citation_style_bib']+'.html'
            template = jinja2.Template(open(html_template_path).read())

            drop_html = template.render(data=main_load['preview_text'], references=output)

            with open(html_path, 'w+') as f:
                f.write(drop_html)

            dl_path = html_path
        else:
            logger.info("generating non html")
            conv_template_path = 'templates/tooltips_conv_'+session['citation_style_bib']+'.html'
            template = jinja2.Template(open(conv_template_path).read())
            drop_html = template.render(data=main_load['preview_text'], references=output)

            with open(conv_html_path, 'w+', encoding='utf-8') as g:
                g.write(str(drop_html))

            output_path = path+f_name+'.'+selected_format

            options = {
                'page-size': 'A4',
                'margin-top': '1in',
                'margin-right': '1in',
                'margin-bottom': '1in',
                'margin-left': '1in',
                'encoding': "UTF-8",
                '--enable-internal-links': ''
            }

            if selected_format == 'pdf':
                pdfkit.from_file(conv_html_path, output_path, options=options)
            else:
                pd.convert_file(conv_html_path, selected_format, outputfile=output_path)


            #remove temporary html file
            os.remove(conv_html_path)

            #redirect to download page
            dl_path = output_path


        redirect_url = dl_path.replace('downloads/', 'download-file/')
        logger.debug(f"Redirect URL: {redirect_url}")

        logger.info("cleanup deselected hypo highlights")
        # cleanup deselected hypo highlights
        delete_highlights = []

        # isolate hypo_ids to delete
        ts = []
        for n in main_load['preview_text']:
            try:
                # if it has old_cit then new_cit has been updated
                ts.append(n['new_cit'])
            except:
                pass


        for t in ts:
            vlogger.debug('this is t:')
            vlogger.debug(pformat(t))
            for a in t:
                try:
                    links = a['links']
                except Exception as e:
                    links = None
                if links:
                    for l in links:
                        if l['selected'] == False:
                            try:
                                delete_highlights.append(l['hypo_id'])
                            except Exception as e:
                                logger.debug("Couldn't fetch hypo_id")
                                pass


        #delete highlights
        for d in delete_highlights:
            hc = hypodelete(d)
            logger.info("attempting to delete hypothesis annotation")
            logger.info(hc)

    return jsonify({'response' : 200, 'redirect_url': redirect_url})

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/error', methods=['GET'])
def error():
    return render_template('error.html')



if __name__ == '__main__':
    app.run(host ='0.0.0.0', port = 9900, debug=True)
