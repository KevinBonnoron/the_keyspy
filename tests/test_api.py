"""Test for TheKeyApi"""
import unittest
from typing import Any

from http_server_mock import HttpServerMock

from the_keyspy import TheKeysApi
from the_keyspy.errors import (
    NoAccessoriesFoundError,
    NoGatewayAccessoryFoundError,
    GatewayAccessoryNotFoundError,
    NoGatewayIpFoundError,
    NoUtilisateurFoundError,
    NoSharesFoundError,
)
from . import (
    CustomJSONProvider,
    UtilisateurMock,
    UtilisateurSerrureMock,
    UtilisateurSerrureAccessoireMock,
    AccessoireMock,
    PartageMock,
    PartageUtilisateurMock,
    PartageAccessoireMock,
)
from flask import jsonify


def login_check():
    return jsonify(
        {
            "access_token": "access_token",
            "expires_in": 3600,
            "token_type": "bearer",
            "scope": "actions",
            "refresh_token": "refresh_token",
            "token": "token",
        }
    )


def build_response(data: Any, status: int = 200):
    return jsonify(
        {
            "status": status,
            "data": data,
            "message": {"global": [], "form": []},
        }
    )


def utilisateur_without_serrure(username: str):
    return build_response(UtilisateurMock(username=username))


def utilisateur_with_serrure_without_accessoire(username: str):
    return build_response(UtilisateurMock(username=username).with_serrure(UtilisateurSerrureMock()))


def utilisateur_with_serrure_and_gateway(username: str):
    return build_response(
        UtilisateurMock(username=username).with_serrure(
            UtilisateurSerrureMock().with_accessoire(UtilisateurSerrureAccessoireMock()))
    )


def utilisateur_with_serrure_but_no_gateway_accessory(username: str):
    serrure = UtilisateurSerrureMock()

    class NonGatewayAccessoireMock(UtilisateurSerrureAccessoireMock):
        def __dict__(self):
            return {
                "id": self._id,
                "accessoire": {"id": 1, "id_accessoire": "id_accessoire", "nom": "Other Device", "type": 2, "configuration": []},
                "info": None,
            }
    serrure.with_accessoire(NonGatewayAccessoireMock())
    return build_response(UtilisateurMock(username=username).with_serrure(serrure))


def accessoire(id: int):
    return build_response(AccessoireMock(id))


def accessoire_not_found(id: str):
    return build_response(None)


def create_partage(id_serrure: int, id_accessoire: str):
    return build_response({"id": 2, "code": "code"})


def partage_without_partages(id_serrure: int):
    return build_response(PartageMock())


def partage_with_one_partage_utilisateur(id_serrure: int):
    return build_response(PartageMock().with_partage_utilisateur(PartageUtilisateurMock()).with_partage_accessoire(PartageAccessoireMock()))


def utilisateur_not_found(username: str):
    return build_response(None)


def partage_not_found(id_serrure: int):
    return build_response(None)


def locker_status():
    return jsonify({"status": "Door open", "code": 1, "id": 1, "version": 81, "position": 20, "rssi": 0, "battery": 7235})


class TheKeyApiTest(unittest.TestCase):
    """The KeysApi test class"""

    def setUp(self):
        super().setUp()
        self.app = HttpServerMock(__name__)
        self.app.add_url_rule("/api/login_check", None,
                              view_func=login_check, methods=["POST"])
        self.app.json = CustomJSONProvider(self.app)

    def test_utilisateur_without_serrure(self):
        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>",
                              None, view_func=utilisateur_without_serrure, methods=["GET"])
        with self.app.run("localhost", 5000):
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000")
            self.assertEqual(controller.get_devices(), [])

    def test_utilisateur_with_serrure_without_accessoire(self):
        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_with_serrure_without_accessoire, methods=["GET"])
        with self.app.run("localhost", 5000):
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000")
            with self.assertRaises(NoAccessoriesFoundError):
                controller.get_devices()

    def test_utilisateur_with_serrure_gateway_without_partage(self):
        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_with_serrure_and_gateway, methods=["GET"])
        self.app.add_url_rule(
            "/fr/api/v2/accessoire/get/<id>", None, view_func=accessoire)
        self.app.add_url_rule("/fr/api/v2/partage/all/serrure/<id_serrure>",
                              None, view_func=partage_without_partages)
        self.app.add_url_rule("/fr/api/v2/partage/create/<id_serrure>/accessoire/<id_accessoire>",
                              None, view_func=create_partage, methods=["POST"])
        self.app.add_url_rule("/locker_status", None,
                              view_func=locker_status, methods=["POST"])
        with self.app.run("localhost", 5000):
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000")
            self.assertEqual(len(controller.get_devices()), 2)

    def test_utilisateur_with_serrure_gateway_partage(self):
        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_with_serrure_and_gateway, methods=["GET"])
        self.app.add_url_rule(
            "/fr/api/v2/accessoire/get/<id>", None, view_func=accessoire)
        self.app.add_url_rule("/fr/api/v2/partage/all/serrure/<id_serrure>",
                              None, view_func=partage_with_one_partage_utilisateur)
        self.app.add_url_rule("/locker_status", None,
                              view_func=locker_status, methods=["POST"])
        with self.app.run("localhost", 5000):
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000")
            self.assertEqual(len(controller.get_devices()), 2)

    def test_utilisateur_with_serrure_but_no_gateway_accessory(self):
        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_with_serrure_but_no_gateway_accessory, methods=["GET"])
        with self.app.run("localhost", 5000):
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000")
            with self.assertRaises(NoGatewayAccessoryFoundError):
                controller.get_devices()

    def test_gateway_accessoire_not_found(self):
        def utilisateur_with_gateway_but_accessoire_not_found(username: str):
            return build_response(UtilisateurMock(username=username).with_serrure(UtilisateurSerrureMock().with_accessoire(UtilisateurSerrureAccessoireMock())))

        def accessoire_not_found(id: str):
            return build_response(None)
        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_with_gateway_but_accessoire_not_found, methods=["GET"])
        self.app.add_url_rule("/fr/api/v2/accessoire/get/<id>",
                              None, view_func=accessoire_not_found)
        with self.app.run("localhost", 5000):
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000")
            with self.assertRaises(GatewayAccessoryNotFoundError):
                controller.get_devices()

    def test_utilisateur_not_found(self):
        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_not_found, methods=["GET"])
        with self.app.run("localhost", 5000):
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000")
            with self.assertRaises(NoUtilisateurFoundError):
                controller.get_devices()

    def test_partage_not_found(self):
        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_with_serrure_and_gateway, methods=["GET"])
        self.app.add_url_rule(
            "/fr/api/v2/accessoire/get/<id>", None, view_func=accessoire)
        self.app.add_url_rule("/fr/api/v2/partage/all/serrure/<id_serrure>", None,
                              view_func=partage_not_found)
        with self.app.run("localhost", 5000):
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000")
            with self.assertRaises(NoSharesFoundError):
                controller.get_devices()

    def test_gateway_without_ip_but_provided_ip(self):
        """Test case where API doesn't return gateway IP but IP is provided as parameter"""
        from . import create_recent_last_seen

        def utilisateur_with_gateway_without_ip(username: str):
            serrure = UtilisateurSerrureMock()
            accessoire = UtilisateurSerrureAccessoireMock()
            # Simulate gateway accessory without IP in info
            accessoire.accessoire._info = {}
            serrure.with_accessoire(accessoire)
            return build_response(UtilisateurMock(username=username).with_serrure(serrure))

        def accessoire_without_ip(id: int):
            # Return gateway accessory without IP but with recent last_seen
            return build_response(AccessoireMock(id, info={"last_seen": create_recent_last_seen(5)}))

        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_with_gateway_without_ip, methods=["GET"])
        self.app.add_url_rule("/fr/api/v2/accessoire/get/<id>", None,
                              view_func=accessoire_without_ip)
        self.app.add_url_rule("/fr/api/v2/partage/all/serrure/<id_serrure>",
                              None, view_func=partage_without_partages)
        self.app.add_url_rule("/fr/api/v2/partage/create/<id_serrure>/accessoire/<id_accessoire>",
                              None, view_func=create_partage, methods=["POST"])
        self.app.add_url_rule("/locker_status", None,
                              view_func=locker_status, methods=["POST"])
        with self.app.run("localhost", 5000):
            # Test with provided gateway IP
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000", gateway_ip="192.168.1.100")
            devices = controller.get_devices()
            self.assertEqual(len(devices), 2)  # Should work with provided IP

    def test_gateway_without_ip_and_no_provided_ip(self):
        """Test case where API doesn't return gateway IP and no IP is provided as parameter"""
        from . import create_recent_last_seen

        def utilisateur_with_gateway_without_ip(username: str):
            serrure = UtilisateurSerrureMock()
            accessoire = UtilisateurSerrureAccessoireMock()
            # Simulate gateway accessory without IP in info
            accessoire.accessoire._info = {}
            serrure.with_accessoire(accessoire)
            return build_response(UtilisateurMock(username=username).with_serrure(serrure))

        def accessoire_without_ip(id: int):
            # Return gateway accessory without IP but with recent last_seen
            return build_response(AccessoireMock(id, info={"last_seen": create_recent_last_seen(5)}))

        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_with_gateway_without_ip, methods=["GET"])
        self.app.add_url_rule("/fr/api/v2/accessoire/get/<id>", None,
                              view_func=accessoire_without_ip)
        with self.app.run("localhost", 5000):
            # Test without provided gateway IP
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000", gateway_ip="")
            with self.assertRaises(NoGatewayIpFoundError):
                controller.get_devices()

    def test_multiple_gateways_select_most_recent(self):
        """Test that the most recent gateway is selected when multiple gateways exist"""
        from . import create_recent_last_seen

        def utilisateur_with_multiple_gateways(username: str):
            serrure = UtilisateurSerrureMock()
            # Add first gateway seen 5 minutes ago
            accessoire1 = UtilisateurSerrureAccessoireMock(id=1, minutes_ago=5)
            # Add second gateway seen 2 minutes ago (more recent)
            accessoire2 = UtilisateurSerrureAccessoireMock(id=2, minutes_ago=2)
            # Add third gateway seen 15 minutes ago (too old, should be ignored)
            accessoire3 = UtilisateurSerrureAccessoireMock(id=3, minutes_ago=15)
            serrure.with_accessoire(accessoire1)
            serrure.with_accessoire(accessoire2)
            serrure.with_accessoire(accessoire3)
            return build_response(UtilisateurMock(username=username).with_serrure(serrure))

        def accessoire_multiple(id: str):
            # Flask passes route parameters as strings, convert to int
            id_int = int(id)
            # Return different IPs for different gateways
            if id_int == 1:
                return build_response(AccessoireMock(id_int, minutes_ago=5))
            elif id_int == 2:
                return build_response(AccessoireMock(id_int, minutes_ago=2))
            else:  # id_int == 3
                return build_response(AccessoireMock(id_int, minutes_ago=15))

        self.app.add_url_rule("/fr/api/v2/utilisateur/get/<username>", None,
                              view_func=utilisateur_with_multiple_gateways, methods=["GET"])
        self.app.add_url_rule("/fr/api/v2/accessoire/get/<id>", None,
                              view_func=accessoire_multiple)
        self.app.add_url_rule("/fr/api/v2/partage/all/serrure/<id_serrure>",
                              None, view_func=partage_without_partages)
        self.app.add_url_rule("/fr/api/v2/partage/create/<id_serrure>/accessoire/<id_accessoire>",
                              None, view_func=create_partage, methods=["POST"])
        self.app.add_url_rule("/locker_status", None,
                              view_func=locker_status, methods=["POST"])
        with self.app.run("localhost", 5000):
            controller = TheKeysApi(
                "+33123456789", "password", base_url="http://localhost:5000")
            devices = controller.get_devices()
            # Should have 2 devices: 1 gateway (the most recent one with id=2) + 1 lock
            self.assertEqual(len(devices), 2)
            # Check that the gateway selected is the most recent one (id=2)
            gateway = devices[0]
            self.assertEqual(gateway.id, 2)
