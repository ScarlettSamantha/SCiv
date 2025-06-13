import uuid
from direct.interval.LerpInterval import LerpPosInterval, LerpColorScaleInterval
from direct.interval.FunctionInterval import Func
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import TextNode, NodePath, Vec3, Vec4, TransparencyAttrib, BillboardEffect
from typing import Dict, List, Optional

from helpers.cache import Cache
from managers.combat import T_TARGET


class FloatingText3D:
    default_parent: Optional[NodePath] = None
    _queues: Dict[int, List["FloatingText3D"]] = {}
    _spacing: float = 0.7  # Vertical spacing between stacked texts
    _head_offset: float = 0.5  # Vertical offset above the unit's position
    _rise_distance: float = 2.0  # How far each text rises from its start

    def __init__(
        self,
        text: str,
        target: T_TARGET,
        color: Vec4,
        duration: float = 1.5,
        scale: float = 1.0,
    ):
        if FloatingText3D.default_parent is None:
            FloatingText3D.default_parent = Cache.get_showbase_instance().render

        x, y, z = target.get_pos()
        self._target_id = uuid.uuid4().int  # Unique ID for the target to manage text queues

        queue = FloatingText3D._queues.setdefault(self._target_id, [])
        index = len(queue)
        start_z = z + FloatingText3D._head_offset + index * FloatingText3D._spacing

        start_pos = Vec3(x, y, start_z)
        tn = TextNode("floating_text")
        tn.setText(text)
        tn.setTextScale(0.25)
        tn.setAlign(TextNode.A_center)
        tn.setTextColor(color)

        # Attach to scene
        self.np = FloatingText3D.default_parent.attachNewNode(tn)
        self.np.setScale(scale)
        effect = BillboardEffect.makeAxis()
        self.np.setEffect(effect)
        self.np.setPos(start_pos)
        self.np.setTransparency(TransparencyAttrib.M_alpha)
        self.np.setBin("fixed", 100)

        queue.append(self)

        end_pos = Vec3(start_pos.x, start_pos.y, start_pos.z + FloatingText3D._rise_distance)
        move = LerpPosInterval(self.np, duration, end_pos)
        fade = LerpColorScaleInterval(self.np, duration, Vec4(1, 1, 1, 0))
        self.seq = Sequence(move, fade, Func(self.cleanup))  # type: ignore
        self.seq.start()

    def cleanup(self):
        # Finish animation and remove node
        self.seq.finish()
        if self.np and not self.np.isEmpty():
            self.np.removeNode()
        # Remove from queue
        queue = FloatingText3D._queues.get(self._target_id, [])
        if self in queue:
            queue.remove(self)


def spawn_damage_text(target_np: T_TARGET, amount: float):
    FloatingText3D(str(round(amount, 2)), target_np, Vec4(1, 0, 0, 1))


def spawn_dealing_damage_text(source_np: T_TARGET, amount: float):
    FloatingText3D(str(round(amount, 2)), source_np, Vec4(1, 0.5, 0, 1))


def spawn_heal_text(source_np: T_TARGET, amount: float):
    FloatingText3D(str(round(amount, 2)), source_np, Vec4(0, 0.7, 1, 1))
