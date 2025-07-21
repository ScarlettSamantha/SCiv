from direct.showbase import MessengerGlobal


class InputHelper:
    @staticmethod
    def lock_input() -> None:
        MessengerGlobal.messenger.send("system.input.camera_lock")
        MessengerGlobal.messenger.send("system.input.disable_control")
        MessengerGlobal.messenger.send("system.input.disable_zoom")

    @staticmethod
    def unlock_input() -> None:
        MessengerGlobal.messenger.send("system.input.camera_unlock")
        MessengerGlobal.messenger.send("system.input.enable_control")
        MessengerGlobal.messenger.send("system.input.enable_zoom")
