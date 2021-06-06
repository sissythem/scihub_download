import logging

class JsonToBibtexWriter:
    def write_jsons(self, json_list, output_file):
        """Write references presented in the dictionary list in a bibtex format

        Args:
            ref_dict (dict): The referencei n dict format
            output_file (dict): Where to write
        """
        strings = []
        for ref in json_list:
            string_content = self.reference_json_to_str(ref)
            strings.append(string_content)
        strings = "\n".join(strings)
        # write
        with open(output_file, "w") as f:
            logging.info(f"Writing {len(json_list)} bibtex entries to {f.name}")
            f.write(strings)

    def reference_json_to_str(self, ref_dict):
        """Convert json reference to string

        Args:
            ref_dict (dict): The reference n dict format
        Returns:
            res (str): The content in string format
        """
        # gather / convert relevant data
        citation_key = None
        entrytype = None
        bib_dict = {}
        for key, value in ref_dict.items():
            if key == "ENTRYTYPE":
                entrytype = value
            elif key == "ID":
                citation_key = value
                continue
            elif key == "author":
                value = " and ".join(value)
            bib_dict[str(key)] = str(value)
        
        for k in (key, entrytype):
            if k is None:
                logging.error(f"Undefined {k} in bibtex json contents: {ref_dict}")
        if any(x is None for x in (key, entrytype)):
            return
        res = ["@" + entrytype + "{" + citation_key]
        for k, v in bib_dict.items():
            res.append(" " + k + " = { " + v + " }")
        res = ",\n".join(res) + "\n}"
        return res
