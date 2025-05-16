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

from typing import List, Optional, Dict, Any, Type, Tuple

from skill import Skill, SKILL_PRIORITY, SKILL_FACTORY
from board import Board
from ops import roll_union_dice, logger


def call_hook(priority: SKILL_PRIORITY, player: Type['Player'], *args, **kwargs) -> Any:
    if not player.skills:
        # logger.debug(f"{player} 没有任何技能")
        return
    skill = next(
        (s for s in player.skills if s.__class__ in SKILL_FACTORY[priority]),
        None
    )
    if skill:
        return skill(player, *args, **kwargs)
    # logger.debug(f"{player} 没有阶段 {priority} 的技能")
    return


class Player(object):
    """玩家类，封装选手属性和当前状态。"""
    name: str
    score: float
    skills: Optional[List[Skill]]
    stat: Dict[Any, Any]
    extra_steps: Optional[Tuple[int, List[int]]]    # 技能带来的后续回合的步数增益以及生效区间
    def __init__(
        self, name: str, score: float=1.0, skills: Optional[List[Skill]]=None
    ) -> None:
        self.name: str = name
        self.score: float = score   # 黑马值
        self.skills: Optional[List[Skill]] = skills
        self.reset()


    def reset(self) -> None:
        """重置选手状态至初始。"""
        self.stat: Dict[Any, Any] = {
            'position': 1   # 起始位置
        }   # 统计一些状态
        self.extra_steps = None
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, value):
        return isinstance(value, Player) and str(self) == str(value)
    
    @property
    def position(self, ):
        return self.stat['position']
    
    def roll_dice(self) -> int:
        dice_value = call_hook(SKILL_PRIORITY.ON_ROLL, self) or roll_union_dice()
        logger.debug(f"{self} 投出 {dice_value} 的骰子")
        return dice_value
    
    def move(self, forward_steps: int, board: Board, *args, **kwargs):
        simulator = kwargs['simulator']
        if kwargs.get("enable_skill", True):
            forward_steps = call_hook(
                SKILL_PRIORITY.ON_MOVE, self, 
                on_move_stat=dict(
                    board=board, forward_steps=forward_steps, simulator=simulator
                )
            ) or forward_steps
        
        # 前几个回合带来的技能增益
        if (self.extra_steps) and (simulator.stat['round_idx'] in self.extra_steps[1]):
            forward_steps += self.extra_steps[0]
            
        # 之前的技能增益不再生效, 清空
        if (self.extra_steps) and (simulator.stat['round_idx'] >= max(self.extra_steps[1])):
            self.extra_steps = None

        forward_steps = min(forward_steps, board.length-self.position)
        board.stacks[self.position].remove(self)
        origin_position = self.stat['position']
        self.stat['position'] += forward_steps
        board.stacks[self.position].append(self)
        logger.debug(f"{self} 前进 {forward_steps} 步, 从 {origin_position} 到 {self.position}, 同位置其他人(从下到上): {board.stacks[self.position]}")
        return
    
    def __repr__(self):
        return self.name
    
    def __str__(self):
        return self.name
