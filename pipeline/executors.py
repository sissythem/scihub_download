from os import makedirs
from os.path import exists, join
from typing import AnyStr

from doi.doi_getters import CrossrefDoiComponent, DoiComponent
from downloaders.downloaders import PdfDownloader, BibExporter
from parsers.parsers import ScihubParser, Parser
from readers.readers import TxtReader, ClipboardReader, BibReader, Reader


class Executor:

    def __init__(self, logger, doi_getter, doi_resource, out_dir):
        self.logger = logger
        self.out_dir = out_dir
        if doi_getter == "crossref":
            self.doi_getter = CrossrefDoiComponent(logger=logger)
        else:
            self.doi_getter = DoiComponent(logger=logger)
        if doi_resource == "scihub":
            self.html_parser = ScihubParser(logger=logger)
        else:
            self.html_parser = Parser(logger=logger)
        self.downloader = PdfDownloader(logger=logger, out_dir=out_dir)

    def execute(self, **kwargs):
        raise NotImplementedError

    def pdf_download_pipeline(self, title, doi=None):
        self.logger.info(f"Getting pdf for article: {title}")
        if doi is None:
            doi = self.doi_getter.get_doi(title=title)
            if doi is None:
                self.logger.warning(f"Could not find doi for title {title}")
                return
        self.logger.info(f"DOI found: {doi}")
        self.logger.info("Getting pdf url from html")
        pdf_url = self.html_parser.get_pdf_url(doi=doi)
        if pdf_url is None:
            self.logger.warning("No PDF url found")
            return
        self.downloader.download(url=pdf_url)
        return pdf_url


class PdfGetterExecutor(Executor):

    def __init__(self, logger, input_kind, doi_getter, doi_resource, out_dir, path_to_file: AnyStr = None):
        super(PdfGetterExecutor, self).__init__(logger=logger, doi_getter=doi_getter, doi_resource=doi_resource,
                                                out_dir=out_dir)
        if not exists(out_dir):
            makedirs(out_dir)
        self._init_reader(input_kind, logger, path_to_file)

    def _init_reader(self, input_kind, logger, path_to_file=None):
        if input_kind == "txt":
            self.reader = TxtReader(logger=logger, path_to_file=path_to_file)
        elif input_kind == "clipboard":
            self.reader = ClipboardReader(logger=logger)
        else:
            self.reader = Reader(logger=logger)

    def read(self):
        return self.reader.read()

    def execute(self, **kwargs):
        titles = self.read()
        if titles:
            for title in titles:
                self.pdf_download_pipeline(title=title)


class BibExecutor(Executor):

    def __init__(self, logger, doi_getter, doi_resource, out_dir, path_to_file: AnyStr):
        super(BibExecutor, self).__init__(logger=logger, doi_getter=doi_getter, doi_resource=doi_resource,
                                          out_dir=out_dir)
        self.filename = path_to_file.split("/")[-1]
        self.reader = BibReader(logger=logger, path_to_file=path_to_file)
        self.html_parser = ScihubParser(logger=logger)
        self.downloader = PdfDownloader(logger=logger, out_dir=out_dir)
        self.exporter = BibExporter(logger=logger, out_dir=out_dir)

    def read(self):
        return self.reader.read()

    def execute(self, **kwargs):
        bib_database = self.read()
        if bib_database is None:
            self.logger.warning("Bibtex file not found or fialed to load it")
            return
        for entry in bib_database.entries:
            if "file" not in entry.keys():
                doi = None
                title = entry["title"]
                if "doi" in entry.keys() or "DOI" in entry.keys():
                    try:
                        doi = entry["doi"].strip()
                    except(KeyError, Exception):
                        doi = entry["DOI"].strip()
                pdf_url = self.pdf_download_pipeline(title=title, doi=doi)
                if pdf_url is not None:
                    filename = pdf_url.split("/")[-1]
                    filename = filename.split("?")[0]
                    filepath = join(self.out_dir, filename)
                    entry["file"] = filepath
        self.exporter.export(filename=self.filename, content=bib_database)
