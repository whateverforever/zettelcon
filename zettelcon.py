import os
import glob
import re
from multiprocessing import Pool
from pprint import pprint

REX_LINK = re.compile(r"\[\[(.+?)\]\]")
FOLDER = "notes"
SUFFIX = ".md"
NPROCS = 2

def main():
    files = glob.glob(os.path.join(FOLDER, f"*{SUFFIX}"))
    pool = Pool(processes=NPROCS)

    links = []
    res = pool.map(get_file_outlinks, files)
    
    for outlinks in res:
        links.extend(outlinks)

    pprint(links[:50])    
    links = change_ids_to_filepaths(links, files)


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
