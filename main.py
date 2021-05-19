import traceback
from os import getcwd, makedirs
from os.path import exists, join
from typing import List, AnyStr

import bibtexparser
import clipboard

from doi.doi_getters import CrossrefDoiComponent
from downloaders.downloaders import PdfDownloader
from parsers.parsers import ScihubParser
from utils import utils


class TitleReader:

    def __init__(self, logger, path_to_file: AnyStr = None):
        self.path_to_file = path_to_file
        self.logger = logger

    def get_titles_from_txt(self) -> List[AnyStr]:
        """
        Function to get a list with publications' titles from a txt file. Each line of the file should be a title.

        Args
            | path_to_txt (str): the path to the txt file

        Returns
            | list: the list with the titles
        """
        with open(self.path_to_file, "r") as f:
            titles = f.readlines()
        return titles

    @staticmethod
    def get_title_from_clipboard() -> AnyStr:
        """
        Function to get a title from the clipboard. Copy the title you want to get the relevant PDF and then run the
        script

        Returns
            | str: the content of the clipboard -- the title of a publication
        """
        return clipboard.paste()


class BibtexComponent:

    def __init__(self, path_to_file, out_dir, logger):
        self.path_to_file = path_to_file
        self.logger = logger
        self.out_dir = out_dir
        self.crossref_component = CrossrefDoiComponent(logger=logger)
        self.html_parser = ScihubParser(logger=logger)
        self.downloader = PdfDownloader(logger=logger, out_dir=out_dir)

    def update_bibtex(self):
        bib_database = self.read_bib()
        if bib_database is None:
            return

        for entry in bib_database.entries:
            if "file" not in entry.keys():
                doi = self._get_entry_doi(entry)
                if doi is None:
                    continue
                pdf_url = self.html_parser.get_pdf_url(doi=doi)
                if pdf_url is not None:
                    self.downloader.download(url=pdf_url)
                    filename = pdf_url.split("/")[-1]
                    filename = filename.split("?")[0]
                    filepath = join(self.out_dir, filename)
                    entry["file"] = filepath
                else:
                    self.logger.warning(f"PDF not found for doi {doi}")
        self.export_bib(bib_database=bib_database)

    def _get_entry_doi(self, entry):
        if "doi" in entry.keys() or "DOI" in entry.keys():
            try:
                doi = entry["doi"]
            except(KeyError, Exception):
                doi = entry["DOI"]
        else:
            doi = self.crossref_component.get_doi(title=entry["title"])
        return doi

    def read_bib(self):
        try:
            with open(self.path_to_file, "r", encoding="utf-8") as bibtex_file:
                return bibtexparser.load(bibtex_file)
        except(KeyError, Exception, BaseException) as e:
            self.logger.error(e)
            self.logger.error(traceback.print_stack())
            return None

    def export_bib(self, bib_database):
        with open(self.path_to_file, "w", encoding="utf-8") as bibtex_file:
            bibtexparser.dump(bib_database, bibtex_file)


def run_for_title_reader(title, logger, out_dir):
    crossref_component = CrossrefDoiComponent(logger=logger)
    html_parser = ScihubParser(logger=logger)
    downloader = PdfDownloader(logger=logger, out_dir=out_dir)
    logger.info(f"Getting doi for title {title}")
    doi = crossref_component.get_doi(title=title)
    if not doi:
        return
    logger.info(f"DOI found: {doi}")
    logger.info("Getting pdf url from html")
    pdf_url = html_parser.get_pdf_url(doi=doi)
    if not pdf_url:
        return
    downloader.download(url=pdf_url)


def main():
    properties = utils.load_properties()
    custom_output_dir = join(getcwd(), "output", "pdfs")
    if not exists(custom_output_dir):
        makedirs(custom_output_dir)
    out_dir = properties.get("output_dir", custom_output_dir)
    logger = utils.get_logger(folder=join(getcwd(), "output", "logs"))
    resource = properties["resource"]
    if resource == "bib":
        bib_component = BibtexComponent(path_to_file=properties["path_to_file"], out_dir=out_dir, logger=logger)
        bib_component.update_bibtex()
    else:
        file_reader = TitleReader(path_to_file=properties.get("path_to_file", None), logger=logger)
        if resource == "txt":
            logger.info("Reading titles from file")
            titles = file_reader.get_titles_from_txt()
            if not titles:
                return
            for title in titles:
                run_for_title_reader(title=title, logger=logger, out_dir=out_dir)
        else:
            logger.info("Reading title from clipboard")
            title = file_reader.get_title_from_clipboard()
            run_for_title_reader(title=title, logger=logger, out_dir=out_dir)


if __name__ == '__main__':
    main()
