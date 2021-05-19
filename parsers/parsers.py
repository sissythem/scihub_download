from typing import AnyStr, Optional

import requests
from bs4 import BeautifulSoup


class Parser:

    def __init__(self, logger):
        self.logger = logger

    def get_pdf_url(self, doi: AnyStr) -> Optional[AnyStr]:
        raise NotImplementedError


class ScihubParser(Parser):

    def __init__(self, logger):
        super(ScihubParser, self).__init__(logger=logger)
        self.base_url = "https://sci-hub.do/"

    def get_pdf_url(self, doi: AnyStr) -> Optional[AnyStr]:
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
