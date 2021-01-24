import glob
import re
from multiprocessing import Pool
from pprint import pprint

REX_LINK = re.compile(r"\[\[(.+?)\]\]")


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


def main():
    files = glob.glob("notes_small/*.md")
    pool = Pool(processes=2)

    res = pool.map(get_file_outlinks, files)

    pprint(res[:50])


if __name__ == "__main__":
    main()
