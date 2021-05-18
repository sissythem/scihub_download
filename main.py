import traceback
from os import getcwd, makedirs
from os.path import exists, join
from typing import List, AnyStr, Optional

import bibtexparser
import clipboard
import requests
import wget
from bs4 import BeautifulSoup
from habanero import Crossref

import utils


class CrossrefComponent:

    def __init__(self, logger):
        self.logger = logger

    def get_doi(self, title: AnyStr) -> Optional[AnyStr]:
        """
        Function to get the DOI of a publication based on its title using Crossref

        Args
            | title (str): the title of the publication

        Returns
            | str: the DOI number of the publication
        """
        title = utils.preprocess_title(title=title)
        doi = None
        cr = Crossref()
        x = cr.works(query=title)
        status = x["status"]
        if status == "ok":
            items = x["message"]["items"]
            if not items:
                return doi
            for item in items:
                item_titles = self._get_item_title(item=item)
                if not item_titles:
                    continue
                for item_title in item_titles:
                    if item_title == title:
                        doi = item["DOI"]
                        break
                if doi is not None:
                    break
        return doi

    @staticmethod
    def _get_item_title(item):
        new_item_titles = []
        item_titles = item.get("title", None)
        if item_titles:
            for item_title in item_titles:
                item_title = utils.preprocess_title(title=item_title)
                new_item_titles.append(item_title)
        return new_item_titles


class HtmlParser:
    def __init__(self, logger, base_url: AnyStr = None):
        self.base_url = base_url if base_url is not None else "https://sci-hub.do/"
        self.logger = logger

    def get_pdf_url_from_html(self, doi: AnyStr) -> Optional[AnyStr]:
        """
        Function to parse the scihub html page (based on the url with the retrieved doi) and get the URL link to
        download the pdf file

        Args
            | doi (str): the DOI number of the publication

        Returns
            | str: the URL of the PDF file
        """
        pdf_url = None
        html = self._get_html(doi=doi)
        if html is None:
            return pdf_url
        return self._get_pdf_url(html, pdf_url)

    def _get_pdf_url(self, html, pdf_url):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            onclick = link.get("onclick")
            if onclick:
                pdf_url = onclick.split("location.href=")[1]
                pdf_url = pdf_url.replace("\'", "")
                self.logger.info(f"Found pdf url: {pdf_url}")
            if pdf_url is not None:
                break
        return pdf_url

    def _get_html(self, doi: AnyStr) -> Optional[AnyStr]:
        url = self.base_url + doi
        self.logger.info(f"Getting html content from url {url}")
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return None


class FileDownloader:

    def __init__(self, logger, out_dir: AnyStr):
        self.out_dir = out_dir
        self.logger = logger

    def download(self, url):
        """
        Function to download a PDF file given it's URL and optionally an output directory. If no directory is given, the
        files will be stored in <curr_path>/output folder

        Args
            | url (str): the URL to the PDF file
        """
        self.logger.info(f"Download pdf from url: {url}")
        wget.download(url=url, out=self.out_dir)


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
        self.crossref_component = CrossrefComponent(logger=logger)
        self.html_parser = HtmlParser(logger=logger)
        self.downloader = FileDownloader(logger=logger, out_dir=out_dir)

    def update_bibtex(self):
        bib_database = self.read_bib()
        if bib_database is None:
            return

        for entry in bib_database.entries:
            if "file" not in entry.keys():
                doi = self._get_entry_doi(entry)
                if doi is None:
                    continue
                pdf_url = self.html_parser.get_pdf_url_from_html(doi=doi)
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
    crossref_component = CrossrefComponent(logger=logger)
    html_parser = HtmlParser(logger=logger)
    downloader = FileDownloader(logger=logger, out_dir=out_dir)
    logger.info(f"Getting doi for title {title}")
    doi = crossref_component.get_doi(title=title)
    if not doi:
        return
    logger.info(f"DOI found: {doi}")
    logger.info("Getting pdf url from html")
    pdf_url = html_parser.get_pdf_url_from_html(doi=doi)
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
