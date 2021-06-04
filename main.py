from os import getcwd, makedirs
from os.path import exists, join
import argparse

from pipeline.executors import PdfGetterExecutor, BibExecutor

from parsers.parsers import get_pdf_url_resolver

from downloaders.downloaders import get_bibtex_downloader, get_pdf_downloader

from utils import utils
import clipboard
import logging

def get_args():
    """Argument retrieval func"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--properties_file", help="Path to properties file (Overrides any other input argument", default=None)

    parser.add_argument("-mode", help="Operation mode(s)", choices="pdf bibtex".split(), default="bibtex", nargs="*")
    parser.add_argument("-inputs", help="Inputs, either title string / bibtex path / text file path ", default=None)

    parser.add_argument("--output_dir", help="Output directory for obtained pdfs.", default=join(getcwd(), "output", "pdfs"))

    parser.add_argument("--pdf_getter", help="How to download pdfs.", default="wget")
    parser.add_argument("--doi_getter", help="Where to fetch DOIs from.", default="crossref")
    parser.add_argument("--bibtex_getter", help="Where to fetch bibtex entries from.", choices=["gscholar", "bibsonomy"], default="bibsonomy")
    parser.add_argument("--paper_resource", help="Where to fetch pdfs from.", default="scihub")
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    args = get_args()
    if args.properties_file:
        properties = utils.load_properties()
        output_dir = properties.get("output_dir", args.output_dir)
        doi_getter = properties.get("doi_getter", "crossref")
        paper_resource = properties.get("paper_resource", "scihub")
        inputs = properties["inputs"]
        mode = properties.get("mode")
    else:
        output_dir = args.output_dir
        doi_getter = args.doi_getter
        paper_resource = args.paper_resource
        mode = args.mode
        inputs = args.inputs
        pdf_getter = args.pdf_getter
        bibtex_getter = args.bibtex_getter

    try:
        mode[0]
    except IndexError:
        mode = [mode]

    mode = list(set(mode))

    if inputs is None:
        # get from clipboard
        inputs = clipboard.paste()
        logging.info("Using inputs from clipboard:")
        logging.info(f"[{inputs}]")

    if inputs is None or len(inputs) == 0:
        print("Need explicit inputs or non-empty clipboard content!")
        exit(1)

    if not exists(output_dir):
        logging.debug(f"Creating output directory: {output_dir}")
        makedirs(output_dir)

    logger = utils.get_logger(folder=join(getcwd(), "output", "logs"))

    if exists(inputs):
        # input is a file
        if inputs.endswith(".bib"):
            # a bib file
            executor = BibExecutor(logger=logger, doi_getter=doi_getter, doi_resource=paper_resource, output_dir=output_dir, path_to_file=inputs)
            executor.execute()
        else:
            # a regular text file
            with open(inputs) as f:
                data = [x.strip() for x in f.readlines()]
                data = [x for x in data if x]
            iputs = data
    elif type(inputs) is str:
        # input
        inputs = [inputs]

    for m in mode:
        if m == "pdf":
            url_resolver = get_pdf_url_resolver()
            pdf_downloader = get_pdf_downloader(pdf_getter, output_dir)
            results = {}
            for inp in inputs:
                pdf_url = url_resolver.resolve(inp)
                if pdf_url is None:
                    continue
                res = pdf_downloader.download(url) if url is not None else None
                if res is None:
                    continue
                results[inp] = res
            logging.info(f"Fetched pdfs for {len(res)} / {len(inputs)} files.")
            # executor = PdfGetterExecutor(logger=logger, input_kind=input_kind, doi_getter=doi_getter,
            #                             doi_resource=paper_resource, out_dir=out_dir, path_to_file=path_to_file)

            # executor.execute()
        elif m == "bibtex":
            bd = get_bibtex_downloader(bibtex_getter)
            result = bd.download(inputs)
            for res in result:
                print(res["title"],res["author"][:5])



if __name__ == '__main__':
    main()
