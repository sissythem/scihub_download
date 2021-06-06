from os import getcwd, makedirs
from os.path import exists, join
import argparse

from pipeline.executors import PdfGetterExecutor, BibExecutor

from parsers.parsers import get_pdf_url_resolver

from downloaders.downloaders import get_bibtex_downloader, get_pdf_downloader

from writers.bibtex import JsonToBibtexWriter
from utils import utils
import clipboard
import logging
import time
from tqdm import tqdm

def get_args():
    """Argument retrieval func"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--properties_file", help="Path to properties file (Overrides any other input argument", default=None)

    parser.add_argument("-mode", help="Operation mode(s)", choices="pdf bibtex".split(), default="bibtex", nargs="*")
    parser.add_argument("-inputs", help="Inputs, either title string / bibtex path / text file path ", default=None)

    parser.add_argument("--output_dir", help="Output directory for obtained pdfs.", default=join(getcwd(), "output"))

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

    if exists(inputs):
        # input is a file
        if inputs.endswith(".bib"):
            # a bib file
            executor = BibExecutor(logger=logger, doi_getter=doi_getter, doi_resource=paper_resource, output_dir=output_dir, path_to_file=inputs)
            executor.execute()
            inputs_type = "bibfile"
        else:
            # a regular text file
            with open(inputs) as f:
                data = [x.strip() for x in f.readlines()]
                data = [x for x in data if x]
            inputs = data
            inputs_type = "textfile"
    elif type(inputs) is str:
        # input
        inputs = [inputs]
        inputs_type = "string"

    for m in mode:
        if m == "pdf":
            url_resolver = get_pdf_url_resolver()
            pdf_downloader = get_pdf_downloader(pdf_getter, output_dir)
            results = {}
            for inp in inputs:
                pdf_url = url_resolver.resolve(inp)
                if pdf_url is None:
                    continue
                res = pdf_downloader.download(pdf_url) if pdf_url is not None else None
                if res is None:
                    continue
                results[inp] = res
            logging.info(f"Fetched pdfs for {len(res)} / {len(inputs)} files.")
            # executor = PdfGetterExecutor(logger=logger, input_kind=input_kind, doi_getter=doi_getter,
            #                             doi_resource=paper_resource, out_dir=out_dir, path_to_file=path_to_file)

            # executor.execute()
        elif m == "bibtex":
            bd = get_bibtex_downloader(bibtex_getter)
            no_result_queries = []
            all_results = []
            with tqdm() as pbar:
                for i, query in tqdm(enumerate(inputs)):
                    # logging.info(f"querying [{bibtex_getter}] with query {i+1}/{len(inputs)}: [{query}]")
                    pbar.set_description(desc=f"querying [{bibtex_getter}] with query {i+1:4d}/{len(inputs):4d}: [{query}]")
                    result = bd.download(query)
                    for res in result:
                        if res is None:
                            no_result_queries.append((i, query))
                        else:
                            all_results.append(res)
                        # print(res["title"],res["author"][:5])

            output_file = join(output_dir, inputs_type + "_bibtexs_" + time.strftime("%d%m%y_%H%M%S") + ".bib")
            wr = JsonToBibtexWriter()
            wr.write_jsons(all_results, output_file)

            for idx, query in no_result_queries:
                logging.warning(f"Could not find [{bibtex_getter}] results for {idx+1:4d}/{len(inputs):4d} [{query}]")

            





if __name__ == '__main__':
    main()
