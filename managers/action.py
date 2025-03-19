from typing import Dict

from system.actions import Action


class ActionManager:
    registered_actions = {}
    staged_actions = {}

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
    def get_all_actions(cls) -> Dict:
        return cls.registered_actions

    @classmethod
    def get_staged_actions(cls) -> Dict:
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
