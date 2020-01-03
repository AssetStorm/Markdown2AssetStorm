# Markdown2AssetStorm
Convert Markdown to AssetStorm-JSON using PyPandoc and Flask

## Dependencies
See requirements.txt. This project uses type annotations which 
need at least Python 3.5.

## Running the development Server
Just execute:

```shell script
python converter.py
```

Do not use the development server for production! See the 
Flask-Documentation on how to setup a production server
(for example with Nginx and uWSGI).

## Running tests
Install `nose2` as a test runner:

```shell script
pip install nose2
```

Execute in verbose mode to see all the single tests:

```shell script
nose2 -v
```

You may run mutation tests with `mutmut`:

```shell script
pip install mutmut
mutmut run
mutmut show
```
