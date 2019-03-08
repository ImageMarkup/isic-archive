from time import sleep

import boto3
import pytest
from requests_toolbelt.sessions import BaseUrlSession


@pytest.fixture
def s():
    s = BaseUrlSession("http://isic-archive.test/api/v1/")
    r = s.get("user/authentication", auth=("admin", "password"))
    r.raise_for_status()
    s.headers.update({"Girder-Token": r.json()["authToken"]["token"]})

    yield s


@pytest.fixture
def dataset(s):
    r = s.get("dataset", params={"limit": 1})
    r.raise_for_status()

    if not r.json():
        r = s.post(
            "dataset",
            data={
                "name": "test dataset",
                "description": "test dataset",
                "license": "CC-BY",
                "attribution": "test",
                "owner": "test",
            },
        )
        r.raise_for_status()

    yield r.json()[0]

    # how to delete dataset
    r = s.get("folder", params={"text": "test dataset"})
    r.raise_for_status()
    r = s.delete("folder/%s" % r.json()[0]["_id"])
    r.raise_for_status()


def test_zip_upload(s, dataset):
    r = s.post("dataset/%s/zip" % dataset["_id"], data={"signature": "test"})
    r.raise_for_status()

    s3 = boto3.client(
        "s3",
        aws_access_key_id=r.json()["accessKeyId"],
        aws_secret_access_key=r.json()["secretAccessKey"],
        aws_session_token=r.json()["sessionToken"],
        endpoint_url="http://isic-archive.test:4572",
    )

    with open("plugin_tests/data/isic-images-uda2-female-wreadme.zip", "rb") as data:
        s3.upload_fileobj(
            Fileobj=data, Bucket=r.json()["bucketName"], Key=r.json()["objectKey"]
        )

    batch_id = r.json()["batchId"]

    import pdb
    pdb.set_trace()

    r = s.post("dataset/%s/zip/%s" % (dataset["_id"], batch_id))
    r.raise_for_status()

    sleep(50)

    r = s.get("folder", params={"text": "review"})
    r.raise_for_status()
    r = s.get("item", params={"folderId": r.json()[0]["_id"]})
    r.raise_for_status()

    assert r.json() == False, r.json()[0]
