from typing import AnyStr, Optional

import requests
import logging
from bs4 import BeautifulSoup
from doi.doi_getters import CrossrefDoiComponent

class Parser:

    def get_pdf_url(self, doi: AnyStr) -> Optional[AnyStr]:
        raise NotImplementedError

def get_pdf_url_resolver(name="scihub"):
    if name == "scihub":
        return Scihub()
    raise NotImplementedError(f"Undefined PDF url resolver: {name}")

class UrlResolver:
    pass

class Scihub(UrlResolver):

    def __init__(self, doi_getter="crossref"):
        super(Scihub, self).__init__()
        self.base_url = "https://sci-hub.do/"
        if doi_getter == "crossref":
            self.doi_getter = CrossrefDoiComponent()
        else:
            raise NotImplementedError(f"Undefined DOI getter: {doi_getter}")

    def resolve(self, query):
        logging.info(f"Getting pdf for article: [{query}]")
        doi = self.doi_getter.get_doi(title=query)
        if doi is None:
            logging.error(f"Could not find doi for [{query}]")
            return None
        logging.info(f"DOI found: {doi}")

        import pdb; pdb.set_trace()
        html = self._get_html(doi=doi)
        pdf_url = self._get_pdf_url(html)
        if pdf_url is None:
            logging.error("No PDF url found")
        return pdf_url


    def get_pdf_url(self, doi: AnyStr) -> Optional[AnyStr]:
        """
        Function to parse the scihub html page (based on the url with the retrieved doi) and get the URL link to
        download the pdf file

        Args
            | doi (str): the DOI number of the publication

        Returns
            | str: the URL of the PDF file
        """
        import pdb; pdb.set_trace()
        pdf_url = None
        html = self._get_html(doi=doi)
        if html is None:
            logging.error("Cannot find document")
            return None
        return self._get_pdf_url(html, pdf_url)

    def _get_pdf_url(self, html):
        pdf_url = None
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            onclick = link.get("onclick")
            if onclick:
                pdf_url = onclick.split("location.href=")[1]
                pdf_url = pdf_url.replace("\'", "")
                logging.info(f"Found pdf url: {pdf_url}")
            if pdf_url is not None:
                break
        return pdf_url

    def _get_html(self, doi: AnyStr) -> Optional[AnyStr]:
        url = self.base_url + doi
        logging.info(f"Getting html content from url {url}")
        response = requests.get(url)
        if response.status_code == 200:
            import pdb; pdb.set_trace()
            if 'статья не найдена / article not found' != response.text:
                return response.text
        return None
