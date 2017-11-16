Arteria Archive DB
==================

A self contained (Tornado) REST service that serves as a frontend for a simple SQL db that contains the state of our uploads, verifications and removals done by other Arteria archive services.  

Trying it out
-------------

    python3 -m pip install pipenv
    pipenv install --deploy


Try running it:

     pipenv run ./archive-db-ws --config=config/ --port=8888 --debug

And then you can find a simple API documentation by going to:

    http://localhost:8888/api/1.0

Running tests
-------------

    pipenv install --dev
    pipenv run nosetests tests/


REST endpoints
--------------

# FIXME: Update example
