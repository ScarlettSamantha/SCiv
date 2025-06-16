from typing import Dict

from managers.i18n import T_TranslationOrStr
from system.actions import Action


class ActionManager:
    registered_actions: Dict[T_TranslationOrStr, Action] = {}
    staged_actions: Dict[T_TranslationOrStr, Action] = {}
    waiting_for_player_input: bool = False
    waiting_for_player_unit_click: bool = True
    waiting_for_player_tile_click: bool = False

    keep_selection_after_action: bool = True

    @classmethod
    def add_timed_action(cls, action: Action, run_on_add: bool = True):
        cls.registered_actions[action.name] = action
        if run_on_add:
            action.run()

    @classmethod
    def register_action(cls, action: Action, staged: bool = False):
        if staged:
            cls.staged_actions[action.name] = action
        else:
            cls.registered_actions[action.name] = action

    @classmethod
    def unregister_action(cls, action_name: str, staged: bool = False):
        if staged:
            del cls.staged_actions[action_name]
        else:
            del cls.registered_actions[action_name]

    @classmethod
    def get_action(cls, action_name: str) -> Action:
        return cls.registered_actions[action_name]

    @classmethod
    def get_all_actions(cls) -> Dict[T_TranslationOrStr, Action]:
        return cls.registered_actions

    @classmethod
    def get_staged_actions(cls) -> Dict[T_TranslationOrStr, Action]:
        return cls.staged_actions

    @classmethod
    def get_staged_action(cls, action_name: str) -> Action:
        return cls.staged_actions[action_name]

    @classmethod
    def run_staged_actions(cls):
        for action in cls.staged_actions.values():
            action.run()
        cls.staged_actions = {}

    @classmethod
    def run_staged_action(cls, action_name: str):
        cls.staged_actions[action_name].run()
        del cls.staged_actions[action_name]
