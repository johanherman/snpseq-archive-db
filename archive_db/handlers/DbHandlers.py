import datetime as dt

from arteria.web.handlers import BaseRestHandler

from archive_db.models.Model import Archive, Upload, Verification, Removal
from archive_db import __version__ as version

from tornado import gen
from tornado.web import RequestHandler, HTTPError
from tornado.escape import json_decode, json_encode

# TODO: Shall we implement a handler for something like:
# "Has any package been verified since date `bar`?
# At the moment this can be solved in the client by comparing
# with `last verified date`.

"""
Our handlers are supposed to work as following:

POST /upload/ - create a new archive entry + upload entry
GET /upload/ - get last global upload
GET /upload/<archive> - get last upload for <archive>
POST /verification/ - create a new verification entry
GET /verification/ - get last global verification
GET /verification/<archive> - get last verification for <archive>
POST /removal/<archive> - create a new removal entry for <archive>
"""


class BaseHandler(BaseRestHandler):
    # BaseRestHandler.body_as_object() does not work well
    # in Python 3 due to string vs byte strings.

    def decode(self, required_members=[]):
        obj = json_decode(self.request.body)

        for member in required_members:
            if member not in obj:
                raise HTTPError(400, "Expecting '{0}' in the JSON body".format(member))
        return obj


class UploadHandler(BaseHandler):

    @gen.coroutine
    def post(self):
        """
        Archive `path` was just now uploaded (not?) OK.

        :param path: Path to archive uploaded
        :param description: The TSM description of the archive
        :param host: From which host the archive was uploaded
        """

        body = self.decode(required_members=["path", "description", "host"])
        archive, created = Archive.get_or_create(
            description=body["description"], path=body["path"], host=body["host"])

        upload = Upload.create(archive=archive, timestamp=dt.datetime.utcnow())

        self.write_json({"status": "created", "upload":
                         {"id": upload.id,
                          "timestamp": str(upload.timestamp),
                          "description": upload.archive.description,
                          "path": upload.archive.path,
                          "host": upload.archive.host}})

    @gen.coroutine
    def get(self, archive):
        """
        Archive `foo` was last uploaded OK at date `bar`.

        :param archive: Path to archive uploaded
        :param description: The TSM description of the archive
        :param host: From which host the archive was uploaded
        :return The `archive` when it was last uploaded. If no `archive` specified, then it will
        return the last global upload archive.
        """
        # Step 1 - get date when archive was last updated
        pass

# TODO: We might have to add logic in some of the services
# that adds a file with the description inside the archive,
# so we can verify that we're operating on the correct
# archive before verifying/removing.


class VerificationHandler(BaseHandler):

    @gen.coroutine
    def post(self, archive):
        """
        Archive `foo` was verified (not) OK at date `bar`.

        :param archive: Path to archive verified
        :param description: The TSM description of the archive we verified
        """
        pass
        # Step 1 - set date when archive was verified OK

    @gen.coroutine
    def get(self, archive):
        """
        Give me the date for when any archive was last verified (OK).

        :param archive: Path to archive we want to check
        :return The `archive` when it was last verified. If no `archive` specified, then it will
        return the last globally verified archive.
        """
        pass


class RemovalHandler(BaseHandler):

    @gen.coroutine
    def post(self, archive):
        """
        Archive `foo` was removed from disk at date `bar`.

        :param archive: Path to archive removed from disk
        :param description: The TSM description of the archive we removed
        """
        pass


class VersionHandler(BaseHandler):

    """
    Get the version of the service
    """

    def get(self):
        """
        Returns the version of the checksum-service
        """
        self.write_object({"version": version})
