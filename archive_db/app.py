import datetime

from archive_db.models.Model import init_db, Archive, Upload, Verification, Removal
from archive_db.handlers.DbHandlers import UploadHandler, VerificationHandler, RemovalHandler, VersionHandler

from arteria.web.app import AppService
from peewee import *
from tornado.web import URLSpec as url


def routes(**kwargs):
    """
    Setup routes and feed them any kwargs passed, e.g.`routes(config=app_svc.config_svc)`
    Help will be automatically available at /api, and will be based on the
    doc strings of the get/post/put/delete methods
    :param: **kwargs will be passed when initializing the routes.
    """

    return [
        url(r"/api/1.0/version", VersionHandler, name="version", kwargs=kwargs),
        url(r"/api/1.0/upload", UploadHandler, name="upload"),
        url(r"/api/1.0/verifification/([\w_-]+)",
            VerificationHandler, name="verification", kwargs=kwargs),
        url(r"/api/1.0/removal/([\w_-]+)", RemovalHandler, name="removal", kwargs=kwargs)
    ]


def start():
    """
    Start the archive-db-ws app
    """
    app_svc = AppService.create(__package__)

    db_path = app_svc.config_svc["archive_db_path"]
    init_db(db_path)

    app_svc.start(routes(config=app_svc.config_svc))

if __name__ == '__main__':
    start()
