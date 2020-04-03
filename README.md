# Linqr - Commonify your links

Linqr is a citation assistant. It helps a user enrich their citations in several ways:
- by improving the accessibility of sources (inserting links to unpaywalled content),
- by increasing the precision of links (option to link to cited text),
- by adding two-directionality to them (option to link back from the cited text),
- by increasing the linguistic diversity of cited works.

[Demo](https://yurisearch.coventry.ac.uk/linqr/) (pending).
[More info](https://yurisearch.coventry.ac.uk/linqr/about) (pending).


## Dependencies

Install [zotero translation-server](https://github.com/zotero/translation-server) and run it on port 1969:

```
docker pull zotero/translation-server
docker run -d -p 1969:1969 --rm zotero/translation-server
```

Install [zotero citeproc-js-server](https://github.com/zotero/citeproc-js-server) and run it on port 8085:

```
docker pull librecat/citeproc-node
docker run -d -p 8085:8085 -t myciteproc
```

## Installation

To be able to use Linqr with [hypothes.is](https://web.hypothes.is/) (for deep and bi-directional linking) create keys.py inside the app directory and add save two variables in it:

```
hypo_api_token = 'your api tokern'
hypo_account = 'your hypothesis username'
```

The code on the master branch is set up to run behind a (nginx) proxypass at /linqr. To change this adjust the gunicorn SCRIPT_NAME setting in the Dockerfile accordingly.

In any case ...

```
docker-compose up -d --build
```

... will start the app at port 9900.

Add this to sites-enabled in nginx (minimal example):

```
location /linqr/ {
        proxy_pass http://127.0.0.1:9900;
}
```

Done.

## Known issues

<p>Linqr is in beta. Issues are to be expected at this point. Report them <a href="https://github.com/uree/linqr/issues">here</a>. Some are conscious omissions due to temporal limitations and are thus worth mentioning in advance:</p>
<ul>
    <li>The layout/design/pagination of the uploaded texts is not kept and reproduced in the output.</li>
    <li>Very long queries time out.</li>
    <li>When open, neighbouring tooltips overlap.</li>
</ul>
