"""The Keys CLI application"""
import argparse
import logging

from src.the_keyspy import Action, TheKeysApi

parser = argparse.ArgumentParser(description="The Keys CLI")
parser.add_argument("-t", dest="telephone", help="login", required=True)
parser.add_argument("-p", dest="password", help="password", required=True)
parser.add_argument("-a", dest="action", help="action", required=True, type=Action, choices=list(Action))
parser.add_argument("-d", dest="device", help="device", required=False)
parser.add_argument("--debug", action="store_true", help="debug")
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
with TheKeysApi(args.telephone, args.password) as api:
    for device in api.get_locks():
        match args.action:
            case Action.OPEN:
                result = device.open()
            case Action.CLOSE:
                result = device.close()
            case Action.CALIBRATE:
                result = device.calibrate()
            case Action.LOCKER_STATUS:
                result = device.status()
            case Action.SYNCHRONIZE_LOCKER:
                result = device.synchronize()
            case Action.UPDATE_LOCKER:
                result = device.update()
            case Action.STATUS:
                result = device.status()
            case _:
                result = None

        print(result)
