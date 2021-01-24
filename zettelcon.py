from collections import defaultdict
import os
import glob
import re
from multiprocessing import Pool, Value
from pprint import pprint

REX_LINK = re.compile(r"\[\[(.+?)\]\]")
FOLDER = "notes_small"
SUFFIX = ".md"
NPROCS = 2
BACKLINK_START = "## Backlinks"

def main():
    files = glob.glob(os.path.join(FOLDER, f"*{SUFFIX}"))
    pool = Pool(processes=NPROCS)

    links = []
    res = pool.map(get_file_outlinks, files)
    
    for outlinks in res:
        links.extend(outlinks)

    pprint(links[:50])    
    links = change_ids_to_filepaths(links, files)

    backlinks_per_targetfile = collect_backlinks_per_file(links)
    pprint(backlinks_per_targetfile)
    
    for filename, backlinks in backlinks_per_targetfile.items():
        write_backlinks_to_file(backlinks)

def collect_backlinks_per_file(links):
    backlinks_for_file = defaultdict(list)

    for link_i in links:
        filename = link_i["link_target"]
        backlinks_for_file[filename].append(link_i)
    
    return backlinks_for_file

def write_backlinks_to_file(backlinks):
    """
    Assumes all the backlinks point to the same file
    """

    target_file = backlinks[0]["link_target"]

    with open(target_file, "r+") as fh:
        contents = fh.read()
        
        try:
            backlink_sec_idx = contents.index(BACKLINK_START)
            add_newline = False
        except ValueError:
            # no backlink section in file
            backlink_sec_idx = -1
            add_newline = True
        
        backlink_section = "\n" if add_newline else ""
        backlink_section += BACKLINK_START + "\n\n"

        for backlink in backlinks:
            backlink_section += "* [[{}]]\n".format(backlink["link_source"])

        contents = contents[:backlink_sec_idx] + backlink_section
        print(contents)
        #fh.write(contents)

        """
        backlink_start = a.index("# Backlinks")
        # ValueError if not found

        a = a[:backlink_start] + "# AYAYAYAYAY"
        """


def change_ids_to_filepaths(links, all_filenames):
    out = []

    for entry in links:
        target_candidates = []

        for filename in all_filenames:
            if entry["link_target"] in filename:
                target_candidates.append(filename)
        
        if len(target_candidates) == 1:
            entry["link_target_orig"] = entry["link_target"]
            entry["link_target"] = target_candidates[0]
            out.append(entry)
        elif len(target_candidates) == 0:
            print("NO TARGET FOUND FOR {}".format(entry))
            pass # no possible target found
        elif len(target_candidates) > 1:
            print("MULTIPLE TARGETS FOUND FOR {}: {}".format(
                entry,
                target_candidates
            ))
            pass # multiple targets found
    
    return out


def get_file_outlinks(path):
    with open(path, "r") as fh:
        contents = fh.read()

    paragraphs = [para.strip() for para in contents.split("\n\n")]

    outlinks = []
    for para in paragraphs:
        reached_backlink_section = BACKLINK_START in para
        if reached_backlink_section:
            break

        links = find_links_in_text(para)
        links = [{"link_source": path, **entry} for entry in links]
        outlinks.extend(links)

    return outlinks


def find_links_in_text(paragraph):
    out = []

    for res in REX_LINK.finditer(paragraph):
        link = {
            "link_target": res.group(1),
            "link_context": paragraph,
            "context_pos_start": res.start(),
            "context_pos_end": res.end(),
        }

        out.append(link)

    return out


if __name__ == "__main__":
    main()
