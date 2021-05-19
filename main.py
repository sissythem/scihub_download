from os import getcwd, makedirs
from os.path import exists, join

from pipeline.executors import PdfGetterExecutor, BibExecutor
from utils import utils


def main():
    properties = utils.load_properties()
    custom_output_dir = join(getcwd(), "output", "pdfs")
    out_dir = properties.get("output_dir", custom_output_dir)
    if out_dir == custom_output_dir and not exists(custom_output_dir):
        makedirs(custom_output_dir)
    logger = utils.get_logger(folder=join(getcwd(), "output", "logs"))
    input_kind = properties["input"]
    doi_getter = properties.get("doi_getter", "crossref")
    paper_resource = properties.get("paper_resource", "scihub")
    path_to_file = properties.get("path_to_file", None)
    if input_kind == "bib":
        executor = BibExecutor(logger=logger, doi_getter=doi_getter, doi_resource=paper_resource, out_dir=out_dir,
                               path_to_file=path_to_file)
    else:
        executor = PdfGetterExecutor(logger=logger, input_kind=input_kind, doi_getter=doi_getter,
                                     doi_resource=paper_resource, out_dir=out_dir, path_to_file=path_to_file)
    executor.execute()


if __name__ == '__main__':
    main()
