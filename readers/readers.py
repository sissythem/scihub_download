import traceback
from typing import AnyStr, List, Union

import bibtexparser
import clipboard


class Reader:

    def __init__(self, logger):
        self.logger = logger

    def read(self) -> List[AnyStr]:
        raise NotImplementedError


class FileReader(Reader):

    def __init__(self, logger, path_to_file: AnyStr):
        super(FileReader, self).__init__(logger=logger)
        self.path_to_file = path_to_file

    def read(self):
        raise NotImplementedError


class ClipboardReader(Reader):

    def __init__(self, logger):
        super(ClipboardReader, self).__init__(logger=logger)

    def read(self) -> List[AnyStr]:
        """
        Function to get a title from the clipboard. Copy the title you want to get the relevant PDF and then run the
        script

        Returns
            | str: the content of the clipboard -- the title of a publication
        """
        return [clipboard.paste()]


class BibReader(FileReader):

    def __init__(self, logger, path_to_file: AnyStr):
        super(BibReader, self).__init__(logger=logger, path_to_file=path_to_file)

    def read(self):
        try:
            with open(self.path_to_file, "r", encoding="utf-8") as bibtex_file:
                return bibtexparser.load(bibtex_file)
        except(KeyError, Exception, BaseException) as e:
            self.logger.error(e)
            self.logger.error(traceback.print_stack())
            return None


class TxtReader(FileReader):

    def __init__(self, logger, path_to_file: AnyStr):
        super(TxtReader, self).__init__(logger=logger, path_to_file=path_to_file)

    def read(self) -> List[AnyStr]:
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
