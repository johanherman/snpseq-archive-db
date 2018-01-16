import datetime as dt
import os

from arteria.web.handlers import BaseRestHandler

from archive_db.models.Model import Archive, Upload, Verification, Removal
from archive_db import __version__ as version

from peewee import *
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

class VerificationHandler(BaseHandler):

    @gen.coroutine
    def post(self):
        """
        Archive `foo` was verified (not) OK at date `bar`.

        :param description: The unique TSM description of the archive we verified
        """
        body = self.decode(required_members=["description", "path", "host"])

        archive, created = Archive.get_or_create(description=body["description"], host=body["host"], path=body["path"])

        verification = Verification.create(archive=archive, timestamp=dt.datetime.utcnow())

        self.write_json({"status": "created", "verification": 
                        {"id": verification.id, 
                         "timestamp": str(verification.timestamp), 
                         "description": verification.archive.description, 
                         "path": verification.archive.path, 
                         "host": verification.archive.host}})

class RandomUnverifiedArchiveHandler(BaseHandler): 

    @gen.coroutine
    def post(self):
        """
        Returns an unverified archive that was uploaded within the interval 
        [today - age - margin, today - margin]. The margin value is used to 
        make sure that the archived data has been properly flushed to tape
        upstreams.

        :param age: Number of days we should look back when picking an unverified archive
        :return An unverified archive within the specified date interval. 
        """
        body = self.decode(required_members=["age", "safety_margin"])
        age = int(body["age"])
        margin = int(body["safety_margin"])

        from_timestamp = dt.datetime.utcnow() - dt.timedelta(days=age+margin)
        to_timestamp = dt.datetime.utcnow() - dt.timedelta(days=margin)

        """
        give me all archives that was uploaded between date FOO and bar, 
        but has no verifications. 
        """

        """
        get all uploads -> filter out those uploads that has no verification.
        -> fetch those archive ids.
        q = Upload.select().join(Verification, JOIN.LEFT_OUTER, on=(Verification.archive_id == Upload.archive_id)).group_by(Verification).having(fn.Count(Verification.id) < 1)
q = Upload.select().join(Verification, JOIN.LEFT_OUTER, on=(Verification.archive_id == Upload.archive_id))
seems to work: q = Upload.select().join(Verification, JOIN.LEFT_OUTER, on=(Verification.archive_id == Upload.archive_id)).group_by(Upload).having(fn.Count(Verification.id) < 1)
and with unique archives:  q = Upload.select().join(Verification, JOIN.LEFT_OUTER, on=(Verification.archive_id == Upload.archive_id)).group_by(Upload.archive_id).having(fn.Count(Verification.id) < 1)
do we need to sort on date? what happens we upload many times with different dates, and we only get the group by the unique archive_id? think sqlite/peewee fetches the update record with the highest id (ie the latest)
with dates: q = Upload.select().join(Verification, JOIN.LEFT_OUTER, on=(Verification.archive_
id == Upload.archive_id)).where(Upload.timestamp >= "2018-01-12", Upload.timestamp < 
"2018-01-20").group_by(Upload.archive_id).having(fn.Count(Verification.id) < 1)
randomly pick one: q = Upload.select().join(Verification, JOIN.LEFT_OUTER, on=(Verification.archive_id == Upload.archive_id)).where(Upload.timestamp >= "2018-01-12", Upload.timestamp < "2018-01-20").group_by(Upload.archive_id).having(fn.Count(Verification.id) < 1).order_by(fn.Random()).limit(1)
"""
        query = (Upload
                .select()
                .join(Verification, JOIN.LEFT_OUTER, on=(
                    Verification.archive_id == Upload.archive_id))
                .where(Upload.timestamp.between(from_timestamp, to_timestamp))
                .group_by(Upload.archive_id)
                .having(fn.Count(Verification.id) < 1)
                .order_by(fn.Random())
                .limit(1))

        upload = next(query.execute())
        
        archive_name = os.path.basename(os.path.normpath(upload.archive.path))

        if upload.archive.description != "": 
            self.write_json({"status": "unverified", "archive": 
                            {"timestamp": str(upload.timestamp), 
                             "path": upload.archive.path, 
                             "description": upload.archive.description,
                             "host": upload.archive.host, 
                             "archive": archive_name}})
        else:
            msg = "No unverified archives uploaded between {} and {} was found!".format(from_timestamp.strftime("%Y-%m-%d %H:%M:%S"), to_timestamp.strftime("%Y-%m-%d %H:%M:%S")) 
            self.set_status(500, msg)
            self.write_json({"status": msg})

# TODO: We might have to add logic in some of the services
# that adds a file with the description inside the archive,
# so we can verify that we're operating on the correct
# archive before (verifying/)removing.


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
