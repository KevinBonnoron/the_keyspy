import json
from flask.json.provider import JSONProvider


def create_database_action_date():
    return {"date": "2020-01-01 00:00:00.000000", "timezone_type": 3, "timezone": "Europe/Berlin"}


class JSON_Improved(json.JSONEncoder):
    def default(self, o):
        return o.__dict__()


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=JSON_Improved)

    def loads(self, s: str | bytes, **kwargs):
        return json.loads(s, **kwargs)


class BaseMock:
    def __iter__(self):
        yield from self.__dict__.items()

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

    def __repr__(self):
        return self.__str__()


class HasId:
    def __init__(self, id: int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.with_id(id)

    def with_id(self, id: int):
        self._id = id
        return self


class HasUsername:
    def __init__(self, username: str = "username", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.with_username(username)

    def with_username(self, username: str):
        self._username = username
        return self


class HasFirstname:
    def __init__(self, firstname: str = "firstname", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.with_firstname(firstname)

    def with_firstname(self, firstname: str):
        self._firstname = firstname
        return self


class HasLastname:
    def __init__(self, lastname: str = "lastname", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.with_lastname(lastname)

    def with_lastname(self, lastname: str):
        self._lastname = lastname
        return self


class UtilisateurSerrureAccessoireMock(BaseMock, HasId):
    def __init__(self, id: int = 1):
        super().__init__(id)

    def __dict__(self):
        return {
            "id": self._id,
            "accessoire": {"id": 1, "id_accessoire": "id_accessoire", "nom": "TK Gateway", "type": 1, "configuration": []},
            "info": None,
        }


class UtilisateurSerrureMock(BaseMock, HasId, HasUsername, HasFirstname, HasLastname):
    def __init__(self, id: int = 1, username: str = "+33123456789", firstname: str = "John", lastname: str = "Doe"):
        super().__init__(id=id, username=username, firstname=firstname, lastname=lastname)
        self._accessoires: list[UtilisateurSerrureAccessoireMock] = []

    def with_accessoire(self, utilisateur_serrure_accessoire: UtilisateurSerrureAccessoireMock):
        self._accessoires.append(utilisateur_serrure_accessoire)
        return self

    def __dict__(self):
        return {
            "id": self._id,
            "id_serrure": "1",
            "code": "code",
            "code_serrure": "code_serrure",
            "etat": "open",
            "nom": "Home",
            "couleur": None,
            "qrcode": "qrcode",
            "serrure_droite": True,
            "main_libre": True,
            "longitude": 0,
            "latitude": 0,
            "radius": 100,
            "timezone": "Europe/Paris",
            "maxSpeed": 80,
            "latchDelay": 1000,
            "assistedActions": False,
            "unlockOnly": False,
            "description": None,
            "logSequence": 0,
            "public_key": "public_key",
            "message": "",
            "utilisateur": {"username": self._username, "firstname": self._firstname, "lastname": self._lastname},
            "version": 81,
            "version_cible": 81,
            "beta": 0,
            "battery": 7235,
            "battery_date": create_database_action_date(),
            "accessoires": self._accessoires,
            "produit": {"id": 1, "nom": "TK 1.5.1", "version": 81, "versionBeta": 82},
        }


class UtilisateurMock(BaseMock, HasId, HasUsername, HasFirstname, HasLastname):
    def __init__(self, id: int = 1, username: str = "+33123456789", firstname: str = "John", lastname: str = "Doe"):
        super().__init__(id=id, username=username, firstname=firstname, lastname=lastname)
        self._serrures: list[UtilisateurSerrureMock] = []

    def with_serrure(self, utilisateur_serrure: UtilisateurSerrureMock):
        utilisateur_serrure.with_username(self._username)
        self._serrures.append(utilisateur_serrure)
        return self

    def __dict__(self):
        return {
            "id": self._id,
            "type": "user_utilisateur",
            "roles": ["ROLE_UTILISATEUR"],
            "firstname": self._firstname,
            "lastname": self._lastname,
            "locale": "fr",
            "username": self._username,
            "email": "john.doe@mail.com",
            "created_at": create_database_action_date(),
            "updated_at": create_database_action_date(),
            "notification_token": "notification_token",
            "notification_enabled": True,
            "serrures": self._serrures,
            "tel": self._username,
        }


class AccessoireMock(BaseMock, HasId):
    def __dict__(self):
        return {
            "id": int(self._id),
            "id_accessoire": str(self._id),
            "nom": "TK Gateway",
            "description": None,
            "type": 1,
            "version": 65,
            "type_version": 65,
            "created_at": create_database_action_date(),
            "updated_at": create_database_action_date(),
            "public_key": "public_key",
            "info": {"last_seen": "2020-01-01 00:00", "ip": "127.0.0.1:5000"},
            "configuration": [],
            "cfg": None,
        }


class PartageUtilisateurMock(BaseMock, HasId, HasUsername, HasFirstname, HasLastname):
    def __init__(self, id: int = 1, username: str = "+33123456789", firstname: str = "John", lastname: str = "Doe"):
        super().__init__(id=id, username=username, firstname=firstname, lastname=lastname)

    def __dict__(self):
        return {
            "id": self._id,
            "nom": "John Doe",
            "actif": True,
            "role": {"id": 1, "description": "owner"},
            "date_debut": None,
            "date_fin": None,
            "heure_debut": None,
            "heure_fin": None,
            "horaires": [],
            "description": None,
            "notification_enabled": True,
            "utilisateur": {
                "username": self._username,
                "prenom": self._firstname,
                "nom": "Doe",
                "email": "john.doe@mail.com",
                "telephone": self._username,
            },
            "remoteKeySharingId": 1,
        }


class PartageAccessoireMock(BaseMock, HasId):
    def __init__(self, id: int = 1):
        super().__init__(id=id)

    def __dict__(self):
        return {
            "id": self._id,
            "iddesc": "remote",
            "nom": "TheKeysPy (Remote)",
            "actif": True,
            "date_debut": None,
            "date_fin": None,
            "heure_debut": None,
            "heure_fin": None,
            "description": None,
            "notification_enabled": True,
            "accessoire": {
                "id": 1,
                "id_accessoire": "id_accessoire",
                "nom": "TK Gateway",
                "type": 1,
                "version": 65,
                "type_version": 65,
                "configuration": [],
            },
            "horaires": [],
            "code": "code",
        }


class PartageMock(BaseMock):
    def __init__(self):
        self._partages_utilisateur: list[PartageUtilisateurMock] = []
        self._partages_accessoire: list[PartageAccessoireMock] = []

    def with_partage_utilisateur(self, partage_utilisateur: PartageUtilisateurMock):
        self._partages_utilisateur.append(partage_utilisateur)
        return self

    def with_partage_accessoire(self, partage_accessoire: PartageAccessoireMock):
        self._partages_accessoire.append(partage_accessoire)
        return self

    def __dict__(self):
        return {
            "partages_utilisateur": self._partages_utilisateur,
            "partages_accessoire": self._partages_accessoire,
            "partages_demande": [],
        }
