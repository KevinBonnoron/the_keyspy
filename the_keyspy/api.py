"""
Python library to handle the keys api
"""
from typing import Any, List

import requests

from .dataclasses import Accessoire, Partage, PartageAccessoire, Utilisateur
from .devices import TheKeysDevice, TheKeysGateway, TheKeysLock

BASE_URL = "https://api.the-keys.fr"
SHARE_NAME = "TheKeysPy (Remote)"
ACCESSORY_GATEWAY = 1


class TheKeysApi:
    """TheKeysApi class"""

    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        self.access_token = None

    @property
    def authenticated(self):
        """Get the token"""
        return not self.access_token is None

    def find_utilisateur_by_username(self, username: str) -> Utilisateur:
        """Return user matching the passed username"""
        return Utilisateur.from_dict(self.__http_get(f"utilisateur/get/{username}")["data"])

    def find_accessoire_by_id(self, id: int) -> Accessoire:
        """Return accessory matching the passed id"""
        return Accessoire.from_dict(self.__http_get(f"accessoire/get/{id}")["data"])

    def find_partage_by_lock_id(self, lock_id: int) -> Partage:
        """Return share matching the passed lock_id"""
        return Partage.from_dict(self.__http_get(f"partage/all/serrure/{lock_id}")["data"])

    def create_accessoire_partage_for_serrure_id(self, lock_id: int, share_name: str, accessory_id: str) -> PartageAccessoire:
        """Create a share for the passed lock_id and accessory_id"""
        data = {}
        data["partage_accessoire[description]"] = ""
        data["partage_accessoire[nom]"] = share_name
        data["partage_accessoire[iddesc]"] = "remote"

        response = self.__http_post(f"partage/create/{lock_id}/accessoire/{accessory_id}", data)["data"]
        partage_accessoire = {}
        partage_accessoire["id"] = response["id"]
        partage_accessoire["code"] = response["code"]
        partage_accessoire["nom"] = share_name
        partage_accessoire["actif"] = True
        partage_accessoire["iddesc"] = "remote"
        partage_accessoire["accessoire"] = None
        return PartageAccessoire.from_dict(partage_accessoire)

    def get_locks(self) -> List[TheKeysLock]:
        return list(device for device in self.get_devices() if isinstance(device, TheKeysLock))

    def get_gateways(self) -> List[TheKeysGateway]:
        return list(device for device in self.get_devices() if isinstance(device, TheKeysGateway))

    def get_devices(self, share_name=SHARE_NAME) -> List[TheKeysDevice]:
        """Return all devices"""
        devices = []
        user = self.find_utilisateur_by_username(self.username)
        for serrure in user.serrures:
            accessoire = next((x for x in serrure.accessoires if x.accessoire.type == ACCESSORY_GATEWAY)).accessoire
            if not accessoire:
                return devices

            gateway_accessoire = self.find_accessoire_by_id(accessoire.id)
            gateway = TheKeysGateway(gateway_accessoire.id, gateway_accessoire.info.ip)
            devices.append(gateway)

            partages_accessoire = self.find_partage_by_lock_id(serrure.id).partages_accessoire
            partage = next((x for x in partages_accessoire if x.nom == SHARE_NAME and x.accessoire.id == accessoire.id))

            if partage is None:
                partage = self.create_accessoire_partage_for_serrure_id(serrure.id, share_name, accessoire.id_accessoire)

            devices.append(TheKeysLock(serrure.id, gateway, serrure.nom, serrure.id_serrure, partage.code))

        return devices

    def __http_get(self, url: str):
        if not self.authenticated:
            self.__authenticate()

        response = requests.get(f"{BASE_URL}/fr/api/v2/{url}", headers={"Authorization": f"Bearer {self.access_token}"})
        if response.status_code != 200:
            raise RuntimeError()

        return response.json()

    def __http_post(self, url: str, data: Any):
        if not self.authenticated:
            self.__authenticate()

        response = requests.post(f"{BASE_URL}/fr/api/v2/{url}", headers={"Authorization": f"Bearer {self.access_token}"}, data=data)
        if response.status_code != 200:
            raise RuntimeError()

        return response.json()

    def __authenticate(self):
        response = requests.post(
            f"{BASE_URL}/api/login_check",
            data={"_username": self.username, "_password": self.password},
        )

        if response.status_code != 200:
            raise RuntimeError()

        json = response.json()
        self.access_token = json["access_token"]
        self.expires_in = json["expires_in"]

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is not None:
            print(exception_type, exception_value)

        return True
