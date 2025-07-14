"""
Python library to handle the keys api
"""
from typing import Any, List, TypeVar, Type

import requests
from urllib3 import response

from .dataclasses import Accessoire, Partage, PartageAccessoire, Utilisateur, UtilisateurSerrureAccessoireAccessoire
from .devices import TheKeysDevice, TheKeysGateway, TheKeysLock
from .errors import (
    NoUtilisateurFoundError,
    TheKeysApiError,
    NoAccessoriesFoundError,
    NoGatewayAccessoryFoundError,
    GatewayAccessoryNotFoundError,
    NoSharesFoundError,
)

BASE_URL = "https://api.the-keys.fr"
SHARE_NAME = "TheKeysPy (Remote)"
ACCESSORY_GATEWAY = 1

T = TypeVar('T')


def deserialize_dataclass(cls: Type[T], data: Any) -> T:
    """Helper function to deserialize dataclass from dict"""
    if data is None:
        raise ValueError("Cannot deserialize None data")
    return cls.from_dict(data)  # type: ignore


class TheKeysApi:
    """TheKeysApi class"""

    def __init__(self, username: str, password: str, base_url=BASE_URL) -> None:
        self._username = username
        self._password = password
        self._base_url = base_url
        self._access_token = None

    @property
    def authenticated(self):
        """Get the token"""
        return not self._access_token is None

    def find_utilisateur_by_username(self, username: str) -> Utilisateur:
        """Return user matching the passed username"""
        response_data = self.__http_get(f"utilisateur/get/{username}")["data"]
        if response_data is None:
            raise NoUtilisateurFoundError(
                "User could not be retrieved from the API.")
        return deserialize_dataclass(Utilisateur, response_data)

    def find_accessoire_by_id(self, id: int) -> Accessoire:
        """Return accessory matching the passed id"""
        response_data = self.__http_get(f"accessoire/get/{id}")["data"]
        if response_data is None:
            raise GatewayAccessoryNotFoundError(
                "Gateway accessory could not be retrieved from the API.")
        return deserialize_dataclass(Accessoire, response_data)

    def find_partage_by_lock_id(self, lock_id: int) -> Partage:
        """Return share matching the passed lock_id"""
        response_data = self.__http_get(
            f"partage/all/serrure/{lock_id}")["data"]
        if response_data is None:
            raise NoSharesFoundError(
                "No shares found for this lock.")
        return deserialize_dataclass(Partage, response_data)

    def create_accessoire_partage_for_serrure_id(
        self, serrure_id: int, share_name: str, accessoire: UtilisateurSerrureAccessoireAccessoire
    ) -> PartageAccessoire:
        """Create a share for the passed serrure_id and accessoire"""
        data = {}
        data["partage_accessoire[description]"] = ""
        data["partage_accessoire[nom]"] = share_name
        data["partage_accessoire[iddesc]"] = "remote"

        response = self.__http_post(
            f"partage/create/{serrure_id}/accessoire/{accessoire.id_accessoire}", data)["data"]
        partage_accessoire = {}
        partage_accessoire["id"] = response["id"]
        partage_accessoire["iddesc"] = "remote"
        partage_accessoire["nom"] = share_name
        partage_accessoire["actif"] = True
        partage_accessoire["date_debut"] = None
        partage_accessoire["date_fin"] = None
        partage_accessoire["heure_debut"] = None
        partage_accessoire["heure_fin"] = None
        partage_accessoire["description"] = None
        partage_accessoire["notification_enabled"] = True
        partage_accessoire["accessoire"] = accessoire
        partage_accessoire["horaires"] = []
        partage_accessoire["code"] = response["code"]
        return deserialize_dataclass(PartageAccessoire, partage_accessoire)

    def get_locks(self) -> List[TheKeysLock]:
        return list(device for device in self.get_devices() if isinstance(device, TheKeysLock))

    def get_gateways(self) -> List[TheKeysGateway]:
        return list(device for device in self.get_devices() if isinstance(device, TheKeysGateway))

    def get_devices(self, share_name=SHARE_NAME) -> List[TheKeysDevice]:
        """Return all devices"""
        devices = []
        user = self.find_utilisateur_by_username(self._username)
        for serrure in user.serrures:
            if not serrure.accessoires:
                raise NoAccessoriesFoundError(
                    "No accessories found for this lock.")

            accessoire = next(
                (x for x in serrure.accessoires if x.accessoire.type == ACCESSORY_GATEWAY), None)
            if not accessoire:
                raise NoGatewayAccessoryFoundError(
                    "No gateway accessory found for this lock.")
            accessoire = accessoire.accessoire

            gateway_accessoire = self.find_accessoire_by_id(accessoire.id)
            if not gateway_accessoire:
                raise GatewayAccessoryNotFoundError(
                    "Gateway accessory could not be retrieved from the API.")

            gateway = TheKeysGateway(
                gateway_accessoire.id, gateway_accessoire.info.ip)
            devices.append(gateway)

            partages_accessoire = self.find_partage_by_lock_id(
                serrure.id).partages_accessoire
            if not partages_accessoire:
                partages_accessoire = []

            partage = next((x for x in partages_accessoire if x.nom ==
                           SHARE_NAME and x.accessoire.id == accessoire.id), None)
            if partage is None:
                partage = self.create_accessoire_partage_for_serrure_id(
                    serrure.id, share_name, accessoire)

            devices.append(TheKeysLock(serrure.id, gateway,
                           serrure.nom, serrure.id_serrure, partage.code))

        return devices

    def __http_get(self, url: str):
        if not self.authenticated:
            self.__authenticate()

        response = requests.get(f"{self._base_url}/fr/api/v2/{url}",
                                headers={"Authorization": f"Bearer {self._access_token}"})
        if response.status_code != 200:
            raise RuntimeError(response.text)

        return response.json()

    def __http_post(self, url: str, data: Any):
        if not self.authenticated:
            self.__authenticate()

        response = requests.post(f"{self._base_url}/fr/api/v2/{url}", headers={
                                 "Authorization": f"Bearer {self._access_token}"}, data=data)
        if response.status_code != 200:
            raise RuntimeError(response.text)

        return response.json()

    def __authenticate(self):
        response = requests.post(
            f"{self._base_url}/api/login_check",
            data={"_username": self._username, "_password": self._password},
        )

        if response.status_code != 200:
            raise RuntimeError(response.text)

        json = response.json()
        self._access_token = json["access_token"]
        self.expires_in = json["expires_in"]

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is not None:
            print(exception_type, exception_value)

        return True
