## Assumptions

- Note IDs are unique, also relative to the names of the notes
- The backlink section is the last thing of a page
- two spaces are used for list indentation

## Issues

- If something is quoted in a list, the list is copied over to the backlink section messing up the alignment and formatting
  - Maybe this can be fixed by not going by paragraphs but newlines instead
- Path in backlinks needs to be relative to markdown file
- Bureaucracy is fucked up
- ~~Not idempotent~~

## Improvements

- Add horizontal break before backlinks
- Put backlinks in > quotation
- Only cite a few words before and after the citation