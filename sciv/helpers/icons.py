from typing import List


class Icons:
    @staticmethod
    def population_icon_gaining() -> str:
        return "assets/icons/default/ui_city_population_gain.png"

    @staticmethod
    def population_icon_losing() -> str:
        return "assets/icons/default/ui_city_population_loss.png"

    @staticmethod
    def population_icon() -> str:
        return "assets/icons/default/ui_city_population.png"

    @staticmethod
    def game_logo_512() -> str:
        return "assets/logo_512.png"

    @staticmethod
    def loading_screen_1() -> str:
        return "assets/loading_screens/1.png"

    @staticmethod
    def loading_screen_2() -> str:
        return "assets/loading_screens/2.png"

    @staticmethod
    def loading_screen_3() -> str:
        return "assets/loading_screens/3.png"

    @staticmethod
    def loading_screens(random: bool = False) -> List[str]:
        screens: List[str] = [
            Icons.loading_screen_1(),
            Icons.loading_screen_2(),
            Icons.loading_screen_3(),
        ]
        if random:
            import random as rnd

            return [rnd.choice(screens)]
        return screens
