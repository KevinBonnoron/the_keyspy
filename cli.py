"""The Keys CLI application"""
import argparse
import logging

from src.the_keyspy import Action, TheKeysApi

parser = argparse.ArgumentParser(description="The Keys CLI")
parser.add_argument("-t", dest="telephone", help="login", required=True)
parser.add_argument("-p", dest="password", help="password", required=True)
parser.add_argument("-a", dest="action", help="action",
                    required=True, type=Action, choices=list(Action))
parser.add_argument("-d", dest="device", help="device", required=False)
parser.add_argument("-g", dest="gateway_ip", help="gateway ip", required=False)
parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING",
                    "ERROR", "CRITICAL"], default="INFO", help="log level (default: INFO)")
args = parser.parse_args()

logging.basicConfig(level=args.log_level,
                    format="%(asctime)s - %(levelname)s - %(message)s")
with TheKeysApi(args.telephone, args.password, args.gateway_ip) as api:
    if args.action in [Action.STATUS, Action.UPDATE, Action.SYNCHRONIZE]:
        for device in api.get_gateways():
            match args.action:
                case Action.STATUS:
                    result = device.status()
                case Action.UPDATE:
                    result = device.update()
                case Action.SYNCHRONIZE:
                    result = device.synchronize()
                case _:
                    result = None

    if args.action in [Action.LOCKER_STATUS, Action.LOCKER_SYNCHRONIZE, Action.LOCKER_UPDATE]:
        for device in api.get_locks():
            match args.action:
                case Action.LOCKER_SYNCHRONIZE:
                    result = device.synchronize()
                case Action.LOCKER_STATUS:
                    result = device.status()
                case Action.LOCKER_SYNCHRONIZE:
                    result = device.synchronize()
                case Action.LOCKER_UPDATE:
                    result = device.update()
                case _:
                    result = None

    print(result)
