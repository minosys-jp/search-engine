# search-engine
Search Engine Collections

This project contains the various types of the search engines.

## ngram
There contains the N-gram based search engine programs.<br>
scrayping.py is the Python script for scrayping https://www.teqstock.tokyo/ .<br>
It creates 3 files: search_hash.bin, search_classify.bin, search_docs.bin,
which contains the bi-gram hash values, the transpose matrix, the consolidated document file
for each.<br>
search.php is the wrapper program for the search_engine.php to provide the user interface.<br>
search_engine.php implements the core N-gram (the bi-gram in this case) searching technology.
