from os.path import join
from typing import AnyStr

import bibtexparser
import wget


class Downloader:

    def __init__(self, logger):
        self.logger = logger

    def download(self, url: AnyStr):
        raise NotImplementedError


class Exporter:

    def __init__(self, logger, out_dir):
        self.logger = logger
        self.out_dir = out_dir

    def export(self, filename: AnyStr, content):
        raise NotImplementedError


class PdfDownloader(Downloader):

    def __init__(self, logger, out_dir: AnyStr):
        super(PdfDownloader, self).__init__(logger=logger)
        self.out_dir = out_dir

    def download(self, url: AnyStr):
        """
        Function to download a PDF file given it's URL and optionally an output directory. If no directory is given, the
        files will be stored in <curr_path>/output folder

        Args
            | url (str): the URL to the PDF file
        """
        self.logger.info(f"Download pdf from url: {url}")
        wget.download(url=url, out=self.out_dir)


class BibExporter(Exporter):

    def __init__(self, logger, out_dir: AnyStr):
        super(BibExporter, self).__init__(logger=logger, out_dir=out_dir)
        self.out_dir = out_dir

    def export(self, filename: AnyStr, content):
        filepath = join(self.out_dir, filename)
        with open(filepath, "w", encoding="utf-8") as bibtex_file:
            bibtexparser.dump(content, bibtex_file)
