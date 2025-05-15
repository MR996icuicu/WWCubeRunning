# Copyright 2025 [996icuicu]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Optional, Dict, Any, Type

from skill import Skill, SKILL_PRIORITY, SKILL_FACTORY
from board import Board
from ops import roll_union_dice, logger


def call_hook(priority: SKILL_PRIORITY, player: Type['Player'], *args, **kwargs) -> Any:
    if not player.skill.__class__ in SKILL_FACTORY[priority]:
        # logger.debug(f"{player} 没有阶段 {priority} 的技能")
        return
    return player.call_skill(*args, **kwargs)


class Player:
    """玩家类，封装选手属性和当前状态。"""
    name: str
    score: float
    skill: Optional[Skill]
    stat: Dict[Any, Any]
    def __init__(
        self, name: str, score: float, skill: Optional[Skill]=None
    ) -> None:
        self.name: str = name
        self.score: float = score   # 黑马值
        self.skill: Optional[Skill] = skill
        self.reset()


    def reset(self) -> None:
        """重置选手状态至初始。"""
        self.stat: Dict[Any, Any] = {
            'position': 1   # 起始位置
        }   # 统计一些状态
    
    def __hash__(self):
        return str(self)
    
    def __eq__(self, value):
        return isinstance(value, Player) and str(self) == str(value)
    
    @property
    def position(self, ):
        return self.stat['position']
    
    def call_skill(self, *args, **kwargs):
        return self.skill(self, *args, **kwargs)
    
    def roll_dice(self) -> int:
        dice_value = call_hook(SKILL_PRIORITY.ON_ROLL, self) or roll_union_dice()

        return dice_value
    
    def move(self, forward_steps: int, board: Board, *args, **kwargs):
        forward_steps = call_hook(
            SKILL_PRIORITY.ON_MOVE, self, 
            on_move_stat=dict(
                board=board, forward_steps=forward_steps, simulator=kwargs['simulator']
            )
        ) or forward_steps

        forward_steps = min(forward_steps, board.length-self.position)
        board.stacks[self.position].remove(self)
        self.stat['position'] += forward_steps
        board.stacks[self.position].append(self)
        logger.debug(f"{self} 前进 {forward_steps} 步, 到 {self.position}, 同位置其他人(从下到上): {board.stacks[self.position]}")
        return
    
    def __repr__(self):
        return self.name
    
    def __str__(self):
        return self.name
