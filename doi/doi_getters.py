from typing import AnyStr, Optional

from habanero import Crossref

from utils import utils


class DoiComponent:

    def __init__(self, logger):
        self.logger = logger

    def get_doi(self, title: AnyStr) -> Optional[AnyStr]:
        raise NotImplementedError


class CrossrefDoiComponent(DoiComponent):

    def __init__(self, logger):
        super(CrossrefDoiComponent, self).__init__(logger=logger)

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
