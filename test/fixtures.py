import io
import json
import os
import re
import urllib.parse

import pytest
import responses

from girder.models.file import File
from girder.models.item import Item
from girder.utility import JsonEncoder

from isic_archive.models.dataset import Dataset
from isic_archive.models.image import Image
from isic_archive.tasks import app
from isic_archive.tasks.image import ingestImage


@pytest.fixture(autouse=True)
def celery_always_eager():
    app.conf.task_always_eager = True


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def dataset(server, user):
    d = Dataset().createDataset(
        "test dataset", "test dataset", "CC-BY", "test", "test", user
    )
    yield d
    Dataset().remove(d)


@pytest.fixture
def image_ingester(fsAssetstore, dataset, user, mocked_responses):
    """Require a function for synchronously ingesting an image."""
    def ingest_image(filename):
        def file_download_callback(request):
            file = File().load(request.path_url.split("/")[2], force=True)
            stream = io.BytesIO()
            for chunk in File().download(file, headers=False)():
                stream.write(chunk)
            stream.seek(0)
            return 200, {}, stream.read()

        def file_upload_callback(request):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(request.url).query)
            item = Item().load(params["parentId"][0], force=True)
            file = File().createFile(
                user,
                item,
                params["name"][0],
                int(params["size"][0]),
                fsAssetstore,
                mimeType=params["mimeType"][0] if "mimeType" in params else None,
            )
            return 200, {}, json.dumps(file, cls=JsonEncoder)

        mocked_responses.add_callback(
            mocked_responses.GET,
            re.compile("%sfile/.*/download" % os.environ["ARCHIVE_API_URL"]),
            callback=file_download_callback,
        )
        mocked_responses.add_callback(
            mocked_responses.POST,
            f"{os.environ['ARCHIVE_API_URL']}file",
            callback=file_upload_callback,
        )
        with open(filename, "rb") as imageDataStream:
            image = Dataset().addImage(
                dataset=dataset,
                imageDataStream=imageDataStream,
                imageDataSize=os.path.getsize(filename),
                filename=filename,
                signature="signature",
                user=user,
            )

        ingestImage(image["_id"])

        return Image().load(image["_id"], force=True)

    return ingest_image
