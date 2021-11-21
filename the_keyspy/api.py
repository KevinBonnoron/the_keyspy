"""Api class for the_keys"""
from typing import Any, List, Optional
from dataclasses import dataclass, field
from dataclasses_json import LetterCase, config, dataclass_json
import requests

from devices import TheKeysDevice
from devices.lock import TheKeysLock

BASE_URL = "https://api.the-keys.fr"


@dataclass_json
@dataclass
class DatabaseActionDate:
    """Data class for timestamp"""
    date: str
    timezone_type: int
    timezone: str


@dataclass_json
@dataclass
class LockUser:
    """Data class for lock user"""
    username: str
    firstname: str
    lastname: str


@dataclass_json
@dataclass
class AccessoryInfo:
    """Data class for accessory info"""
    last_seen: str
    ip: str


@dataclass_json
@dataclass
class Accessory:
    """Data class for accessory"""
    id: int
    id_accessoire: str
    nom: str
    type: int
    version: int
    type_version: int
    created_at: DatabaseActionDate
    updated_at: DatabaseActionDate
    public_key: str
    info: AccessoryInfo


@dataclass_json
@dataclass
class LockAccessory:
    """Data class for lock accessory"""
    id: int
    id_accessoire: str
    nom: str
    type: int
    configuration: Any


@dataclass_json
@dataclass
class LockAccessoryHolder:
    """Data class for lock accessory"""
    id: int
    accessoire: LockAccessory
    info: Optional[str]


@dataclass_json
@dataclass
class LockProduct:
    """Data class for lock product"""
    id: int
    nom: str
    version: int
    version_beta: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass_json
@dataclass
class Lock:
    """Data class for lock"""
    id: str
    id_serrure: str
    code: str
    code_serrure: str
    etat: str
    couleur: Optional[str]
    nom: str
    qrcode: str
    serrure_droite: bool
    main_libre: bool
    longitude: int
    latitude: int
    radius: int
    timezone: str
    max_speed: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    latch_delay: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    assisted_actions: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    unlock_only: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    description: Optional[str]
    log_sequence: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    public_key: str
    message: str
    utilisateur: LockUser
    version: int
    version_cible: int
    beta: int
    battery: int
    battery_date: DatabaseActionDate
    accessoires: List[LockAccessoryHolder]
    produit: LockProduct


@dataclass_json
@dataclass
class User:
    """Data class for user"""
    id: str
    type: str
    roles: List[str]
    firstname: str
    lastname: str
    locale: str
    username: str
    email: str
    created_at: DatabaseActionDate
    updated_at: DatabaseActionDate
    notification_token: str
    notification_enabled: bool
    serrures: List[Lock]
    tel: str


@dataclass_json
@dataclass
class ShareRole:
    """Data class for share role"""
    id: int
    description: str


@dataclass_json
@dataclass
class ShareUser:
    """Data class for share user"""
    username: str
    prenom: str
    nom: str
    email: str
    telephone: str


@dataclass_json
@dataclass
class AbstractShare:
    """Data class for abstract share"""
    id: int
    nom: str
    actif: bool
    date_debut: Optional[str]
    date_fin: Optional[str]
    heure_debut: Optional[str]
    heure_fin: Optional[str]
    description: Optional[str]
    notification_enabled: bool
    horaires: List[Any]


@dataclass_json
@dataclass
class UserShare:
    """Data class for user share"""
    role: ShareRole
    utilisateur: ShareUser
    remote_key_sharing_id: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass_json
@dataclass
class ShareAccessory:
    """Data class for share accessory"""
    id: int
    id_accessoire: str
    nom: str
    type: int
    version: int
    type_version: int
    configuration: List[Any]


@dataclass_json
@dataclass
class AccessoryShare:
    """Data class for accessory share"""
    iddesc: str
    accessoire: ShareAccessory
    code: str


@dataclass_json
@dataclass
class Share:
    """Data class for share"""
    partages_utilisateur: List[UserShare]
    partages_accessoire: List[AccessoryShare]


class TheKeyApi:
    """TheKeysApi class"""

    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        self.access_token = None
        self.__authenticate()

    @property
    def authenticated(self):
        """Get the token"""
        return not self.access_token is None

    def find_user_by_username(self, username: str) -> User:
        """Return user matching the passed username"""
        return User.from_dict(self.__http_get(f"utilisateur/get/{username}")["data"])

    def find_lock_by_id(self, id: int) -> Lock:
        """Return lock matching the passed id"""
        return Lock.from_dict(self.__http_get(f"serrure/get/{id}")["data"])

    def find_accessory_by_id(self, id: int) -> Accessory:
        """Return accessory matching the passed id"""
        return Accessory.from_dict(self.__http_get(f"accessoire/get/{id}")["data"])

    def find_share_by_lock_id(self, lock_id: int) -> Share:
        """Return share matching the passed lock_id"""
        return Share.from_dict(self.__http_get(f"partage/all/serrure/{lock_id}")["data"])

    def get_devices(self) -> List[TheKeysDevice]:
        """Return all devices"""
        devices = []
        user = self.find_user_by_username(self.username)
        for lock in user.serrures:
            shares = self.find_share_by_lock_id(lock.id)

            accessory = next(
                (x for x in lock.accessoires if x.accessoire.type == 1),
                None,
            )
            gateway = self.find_accessory_by_id(accessory.accessoire.id)

            share = next(
                x
                for x in shares.partages_accessoire
                if x.accessoire.id == gateway.id
            )

            devices.append(
                TheKeysLock(
                    name=lock.nom,
                    host=f"http://{gateway.info.ip}",
                    identifier=lock.id_serrure,
                    share_code=share.code,
                )
            )

        return devices

    def __http_get(self, url: str):
        if not self.authenticated:
            self.__authenticate()

        response = requests.get(
            f"{BASE_URL}/fr/api/v2/{url}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        if response.status_code != 200:
            raise RuntimeError()

        return response.json()

    def __authenticate(self):
        response = requests.post(
            f"{BASE_URL}/api/login_check",
            data={"_username": self.username, "_password": self.password},
        )
        if response.status_code == 200:
            json = response.json()
            self.access_token = json["access_token"]
            self.expires_in = json["expires_in"]
        else:
            raise RuntimeError("Access denied")

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is not None:
            print(exception_value)

        return True
