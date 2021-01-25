# zettelcon

> An additional helper tool to Zettlr to automatically add backlinks to your note files.
> Edits files in-place, so be careful and try on a copy of your files first.
> 
> Also check out [zettelwarmer](https://github.com/whateverforever/zettelwarmer) for finding
> new interconnections between your notes.

## Assumptions

- Note IDs are unique, also relative to the names of the notes
- The backlink section is the last thing of a page
- Two spaces are used for list indentation

## Issues

- [ ] If something is quoted in a list, the list is copied over to the backlink section messing up the alignment and formatting
  - Maybe this can be fixed by not going by paragraphs but newlines instead
- [ ] Path in backlinks needs to be relative to markdown file
- [x] Bureaucracy is fucked up
- [x] Not idempotent

## Improvements

- [ ] Only cite a few words before and after the citation
- [ ] Add horizontal break before backlinks
- [x] Put backlinks in > quotation