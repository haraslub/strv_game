from brownie import NFTMediavalSTRVGame, network
from scripts.helpers import get_gear, GEAR_MAPPING
from metadata.sample_metadata import metadata_template
from pathlib import Path
import json, os, requests

gear_to_image_uri = {
    "ARMOR": "https://gateway.pinata.cloud/ipfs/QmRqzvXBczpaEnECijuk1VZEkaBgoDi62JrcsYyue86s87?preview=1",
    "SHIELD": "https://gateway.pinata.cloud/ipfs/QmUQ3sEhcnSuyv4o4fBSyEGtecDbyGNrDHFy6N1a6V6XfJ?preview=1",
    "SWORD": "https://gateway.pinata.cloud/ipfs/QmeVH5pGYBbT793DbrZtG4XHRvz4UCdHbW337EEZTACS5L?preview=1",
}


def main():
    for token_id, gear in GEAR_MAPPING.items():
        id = "{0:064x}".format(token_id)
        metadata_filename = "./metadata/{}/{}.json".format(network.show_active(), id)
        metadata_token = metadata_template
        if Path(metadata_filename).exists():
            print("{} already exists! Delete it to overwrite".format(metadata_filename))
        else:
            print("Creating Metadata file: {}".format(metadata_filename))
            metadata_token["name"] = gear
            metadata_token["description"] = "STRV awesome {}".format(gear)
            # @NOTE here would be a script uploading gear image to some server (ipfs, STRVs server, ...)
            # let us pretend we have an image and we upload it to pinata
            image_path = "./img/{}_{}.PNG".format(token_id, gear.upper())
            # if we want to upload image to pinata ipfs server, else put links to gear_to_image_uri
            image_uri = None
            if os.getenv("UPLOAD_IMAGE_URI") == "True":
                pinata_upload = upload_to_pinata(image_path)
                ipfs_hash = pinata_upload["IpfsHash"]
                image_uri = "https://gateway.pinata.cloud/ipfs/{}?preview=1".format(ipfs_hash)
            image_uri = image_uri if image_uri else gear_to_image_uri[gear]
            metadata_token["image"] = image_uri
            # create json file of metadata
            with open(metadata_filename, "w") as file:
                json.dump(metadata_token, file)


def upload_to_pinata(filepath):
    PINATA_BASE_URL = "https://api.pinata.cloud"
    endpoint = "/pinning/pinFileToIPFS"
    headers = {
        "pinata_api_key": os.getenv("PINATA_API_KEY"),
        "pinata_secret_api_key": os.getenv("PINATA_API_SECRET")
    }
    filename = filepath.split("/")[-1:][0]
    print(filename)

    with Path(filepath).open("rb") as fp:
        image_binary = fp.read()
        response = requests.post(
            PINATA_BASE_URL + endpoint,
            files={"file": (filename, image_binary)},
            headers=headers
        )
        return response.json()