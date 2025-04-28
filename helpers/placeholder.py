from typing import Literal


class Placeholder:
    @staticmethod
    def getPlaceholderImagePathSmallIcon() -> Literal["assets/placeholders/icon_small.png"]:
        return "assets/placeholders/icon_small.png"

    @staticmethod
    def get_glb_model_path() -> Literal["assets/placeholders/default_model.glb"]:
        return "assets/placeholders/default_model.glb"
