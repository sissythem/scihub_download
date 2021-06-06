from os.path import join
from typing import AnyStr

import bibtexparser
import gscholar

import wget
import logging

import json
import re
from urllib.parse import quote, quote_plus

import string

import bibsonomy

class Downloader:

    def download(self, url: AnyStr):
        raise NotImplementedError


class Exporter:

    def __init__(self, out_dir):
        self.out_dir = out_dir

    def export(self, filename: AnyStr, content):
        raise NotImplementedError

def get_pdf_downloader(name, output_dir):
    if name == "wget":
        return PdfDownloader(output_dir)
    raise NotImplementedError(f"Undefined pdf downloader {name}")

class PdfDownloader(Downloader):

    def __init__(self, out_dir: AnyStr):
        self.out_dir = out_dir

    def download(self, url: AnyStr):
        """
        Function to download a PDF file given it's URL and optionally an output directory. If no directory is given, the
        files will be stored in <curr_path>/output folder

        Args
            | url (str): the URL to the PDF file
        """
        logging.info(f"Download pdf from url: {url}")
        outpath = wget.download(url=url, out=self.out_dir)
        return outpath

def get_bibtex_downloader(name):
    if name == "gscholar":
        return GScholarBibDownloader()
    elif name == "bibsonomy":
        return BibsonomyBibDownloader("npit e95e24e225bd607046cd9cd1f47a898d".split())
    logging.error(f"Undefined bibtex downloader: {name}")
    exit(1)

class BibDownloader:
    def download(self, query: AnyStr):
        return None

    def remove_punct(self, text):
        """Purge punctuation"""
        text = re.sub("[" + string.punctuation + "]", " ", text)
        return re.sub("[ ]+", " ", text)

    def preproc_text(self, text, do_newline=True):
        """Apply basic text preprocessing"""
        if do_newline:
            text = re.sub("\\n+", " ", text)
            text = re.sub("\n+", " ", text)
        text = re.sub("\t+", " ", text)
        text = re.sub("\s+", " ",text)
        return text

class GScholarBibDownloader(BibDownloader):
    def download(self, query: AnyStr):
        logging.info("Fetching google scholar content for query: [{}]".format(query))
        res = gscholar.query(query)
        return res

class BibsonomyBibDownloader(BibDownloader):
    name = "bibsonomy"
    def __init__(self, params):
        self.base_url = "https://www.bibsonomy.org/search/"
        self.ignore_keys = "intrahash interhash href misc bibtexAbstract".split()
        self.dont_preproc_keys = "author".split()

        try:
            self.username, self.api_key = params
        except ValueError:
            logging.error("Bibsonomy parameters need to be a string list with the username and the api key")

    def get_url(self, query):
        # bibsonomy does not like punctuation
        return super().get_url(self.remove_punct(query))

    def map_keys(self, ddict):
        rdict = {k: v for (k, v) in ddict.items()}
        for k in ddict:
            if k == 'bibtexKey':
                rdict['ID'] = rdict[k]
                del rdict[k]
            elif k in self.ignore_keys:
                del rdict[k]
            elif k == "author":
                rdict[k] = [x.strip() for x in rdict[k].split("and")]
            elif k == "entrytype":
                rdict[k.upper()] = rdict[k]
                del rdict[k]
        return rdict

    def download(self, query):
        rs = bibsonomy.RestSource(self.username, self.api_key)
        query = " ".join((self.remove_punct(query).split()))

        # def func(q, start=0, end=1000):
        #     return rs._get("/posts?resourcetype=" + quote(rs._get_resource_type("publication")) + "&search={}".format(q))
        res = rs._get("/posts?resourcetype=" + quote(rs._get_resource_type("publication")) + "&search={}".format(quote_plus(query)))
        res = json.loads(res)
        if res['stat'] != 'ok':
            logging.error("Error fetching bibsonomy query '{}' : {}".format(query, res['stat']))
            return None
        try:
            res = res['posts']['post']
            res = [self.map_keys(res[i]["bibtex"]) for i in range(len(res))]
            res = [{k: self.preproc_text(dct[k]) if k not in self.dont_preproc_keys else dct[k] for k in dct} for dct in res]
            return sorted(res, key=lambda x: x['year'] if 'year' in x else x['title'])
        except KeyError:
            return []















class BibExporter(Exporter):

    def __init__(self, out_dir: AnyStr):
        super(BibExporter, self).__init__(out_dir=out_dir)
        self.out_dir = out_dir

    def export(self, filename: AnyStr, content):
        filepath = join(self.out_dir, filename)
        with open(filepath, "w", encoding="utf-8") as bibtex_file:
            bibtexparser.dump(content, bibtex_file)
