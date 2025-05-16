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

from __future__ import annotations

import enum
from copy import deepcopy
from collections import defaultdict
from abc import abstractmethod, ABC
from typing import Type, Dict, List

import numpy as np

from ops import roll_union_dice, logger
from board import Board


class SKILL_PRIORITY(enum.Enum):
    """技能的执行优先级"""

    BEFORE_ROUND    = 0     # 当前轮次开始前
    ON_ENTER_TURN   = 10    # 进入角色回合时执行
    BEFORE_ROLL     = 20    # 投骰子之前执行
    ON_ROLL         = 30    # 投骰子时执行
    AFTER_ROLL      = 40    # 投骰子后执行
    BEFORE_MOVE     = 50    # 移动前执行
    ON_MOVE         = 60    # 移动时执行
    AFTER_MOVE      = 70    # 移动后执行
    ON_EXIT_TURN    = 80    # 退出角色回合时执行
    AFTER_ROUND     = 90    # 当前轮次结束后


class Skill(ABC):
    """所有技能的抽象类，定义触发时机和触发概率，并提供触发判定和效果应用接口。

    Attributes:
        name: 技能名称。
        priority: 触发阶段标识，如 'before_move', 'dice', 'during_move', 'after_move'。
        probability: 技能触发概率。
    """
    _PRIORITY: SKILL_PRIORITY
    def __init__(self, probability: float) -> None:
        self.name = self.__class__.__name__
        self.probability: float = probability
    
    def __call__(self, player: Type['Player'], *args, **kwargs):
        prob = np.random.random()
        if prob <= self.probability:
            return self._apply(player, *args, **kwargs)
        return
    
    @abstractmethod
    def _apply(self, player: Type['Player'], *args, **kwargs):
        raise NotImplementedError


# 每个优先级对应一组技能类
SKILL_FACTORY: Dict[SKILL_PRIORITY, List[Skill]] = defaultdict(list)


def register_skill(cls):
    if not issubclass(cls, Skill):
        raise TypeError("只能注册 Skill 的子类")
    if not hasattr(cls, '_PRIORITY'):
        raise AttributeError("Skill 子类必须定义 _PRIORITY 属性")
    SKILL_FACTORY[cls._PRIORITY].append(cls)
    return cls


@register_skill
class JinXiSkill(Skill):
    """如果玩家头顶有其他玩家，则有概率将自身移到堆叠顶部。**在每轮结束后触发**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.AFTER_ROUND
    def __init__(self, probability: float=0.4) -> None:
        super().__init__(probability=probability)
    
    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat = kwargs.get('after_round_stat')
        # 第一轮不执行
        if stat['simulator'].stat['is_first_round']:
            return
        board: Board = stat['board']
        origin_stack = deepcopy(board.stacks[player.position])
        if board.stacks[player.position].index(player) < len(origin_stack)-1:
            board.stacks[player.position].remove(player)
            board.stacks[player.position].append(player)
            logger.debug(f"{player} 发动技能将自己移动到最顶部! 原始排列 {origin_stack}, 新排列 {board.stacks[player.position]}")
        return


@register_skill
class ChangLiSkill(Skill):
    """如果玩家在堆叠中位于下层，则有概率在下一轮行动中成为最后一个行动者。**在每轮开始前触发**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.BEFORE_ROUND
    def __init__(self, probability: float=0.65) -> None:
        super().__init__(probability=probability)
    
    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat = kwargs.get('before_round_stat')
        # 第一轮不发动
        if stat['simulator'].stat['is_first_round']:
            return
        board: Board = stat['board']
        simulator_order = stat['simulator'].stat['order']
        origin_order = deepcopy(simulator_order)
        # 当同位置player数量大于1, 且player处于下层时发动
        if (len(board.stacks[player.position]) > 1) \
            and (board.stacks[player.position].index(player) < len(board.stacks[player.position])-1) \
                and (simulator_order[-1] != player):
            simulator_order.remove(player)
            simulator_order.append(player)
            logger.debug(f"{player} 发动技能最后一个执行回合! 原始顺序 {origin_order}, 新顺序 {simulator_order}")
        return


@register_skill
class KaKaLuoSkill(Skill):
    """若玩家目前排名最后，开始移动时额外前进3步。**在每回合移动时触发**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.ON_MOVE
    def __init__(self, probability: float=1.0) -> None:
        super().__init__(probability=probability)

    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat = kwargs.get('on_move_stat')
        if stat['simulator'].stat['is_first_round']:
            return
        board: Board = stat['board']
        forward_steps: int = stat['forward_steps']
        if board.get_last_player() == player:
            stat['simulator'].stat['override_forward_steps'] = forward_steps + 3
            logger.debug(f'{player} 发动技能, 由于进度最后多执行3步!')
            return forward_steps + 3
        return forward_steps


@register_skill
class ShouAnRenSkill(Skill):
    """骰子结果仅限指定面[2,3]。在每回合投骰子时执行"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.ON_ROLL
    def __init__(self, probability: float=1.0) -> None:
        super().__init__(probability=probability)
    
    def _apply(self, player: Type['Player'], *args, **kwargs):
        dice_value = roll_union_dice(values=[2, 3])
        logger.debug(f'{player} 发动技能掷出 {dice_value} 的骰子')
        return dice_value


@register_skill
class ChunSkill(Skill):
    """玩家移动时，根据堆叠上方玩家数额外前进，但自身不携带其他玩家。**在每回合移动时触发**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.ON_MOVE
    def __init__(self, probability: float=0.5) -> None:
        super().__init__(probability=probability)

    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat = kwargs['on_move_stat']
        if stat['simulator'].stat['is_first_round']:
            return
        board: Board = stat['board']
        forward_steps: int = stat['forward_steps']
        extra_steps = len(board.stacks[player.position]) - 1
        if extra_steps > 0:
            forward_steps += extra_steps
            logger.debug(f'{player} 发动技能, 多执行 {extra_steps}步!')
        return forward_steps


@register_skill
class KeLaiTaSkill(Skill):
    """玩家有概率执行第二次相同点数的移动。但是会带着别人一起移动**在每回合移动后触发,不可递归触发**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.ON_MOVE
    def __init__(self, probability: float=0.28) -> None:
        super().__init__(probability=probability)

    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat=kwargs['on_move_stat']
        forward_steps: int = stat['forward_steps']
        if stat['simulator'].stat['is_first_round']:
            return forward_steps

        other_players = stat['board'].stacks[player.position][stat['board'].stacks[player.position].index(player):]
        forward_steps *= 2
        logger.debug(f'{player} 发动技能, 背着 {other_players} 一起前进两倍的步数 {forward_steps}!')
        stat['simulator'].stat['override_forward_steps'] = forward_steps
        return forward_steps

@register_skill
class LuoKeKeSkill(Skill):
    """如果是最后一个执行,额外执行2格**在每回合移动时触发**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.ON_MOVE
    def __init__(self, probability: float=1.0) -> None:
        super().__init__(probability=probability)

    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat=kwargs['on_move_stat']
        forward_steps: int = stat['forward_steps']
        player_order: List[Type['Player']] = stat['simulator'].stat['order']
        # 是否是最后一个执行
        if player_order[-1] == player:
            # 覆盖堆叠在上方的所有其他团子的步数
            stat['simulator'].stat['override_forward_steps'] = forward_steps + 2
            other_players = stat['board'].stacks[player.position][stat['board'].stacks[player.position].index(player):]
            logger.debug(f"{player} 发动技能背着 {other_players} 一起前进 {forward_steps+2} 格!")
            return forward_steps + 2
        return forward_steps


@register_skill
class BuLanTeSkill(Skill):
    """如果是第一个执行,额外执行2格.**在每回合移动时触发**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.ON_MOVE
    def __init__(self, probability: float=1.0) -> None:
        super().__init__(probability=probability)

    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat=kwargs['on_move_stat']
        forward_steps: int = stat['forward_steps']
        player_order: List[Type['Player']] = stat['simulator'].stat['order']
        # 是否是第一个执行
        if player_order[0] == player:
            # 覆盖堆叠在上方的所有其他团子的步数
            stat['simulator'].stat['override_forward_steps'] = forward_steps + 2
            other_players = stat['board'].stacks[player.position][stat['board'].stacks[player.position].index(player):]
            logger.debug(f"{player} 发动技能背着 {other_players} 一起前进 {forward_steps+2} 格!")
            return forward_steps + 2
        return forward_steps
        

@register_skill
class KanTeLeiLaSkill(Skill):
    """移动过程中首次遇到团子,和此格子中所有团子堆叠,**在每回合移动时触发,一场比赛只能触发一次**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.ON_MOVE
    def __init__(self, probability: float=1.0) -> None:
        super().__init__(probability=probability)
        self.triggered = False  # 一场比赛只能出发一次

    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat = kwargs['on_move_stat']
        board: Board = stat['board']
        forward_steps: int = stat['forward_steps']
        # 一场比赛只能出发一次
        if self.triggered:
            return forward_steps
        self.triggered = True
        
        # 找到前进步数可以达到的格子中, 是否有其他角色, 有的话直接进入该格子
        any_stack_with_players = next(
            (i for i in range(player.position + 1, player.position + forward_steps + 1)
            if board.stacks[i]),
            None
        )
        if any_stack_with_players is not None:
            forward_steps = any_stack_with_players - player.position
            logger.debug(f"{player} 发动技能, 重写前进步数为 {forward_steps}")
        
        return forward_steps
        
        

@register_skill
class ZanNiSkill_ON_ROLL(Skill):
    """骰子只能掷出1或者3"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.ON_ROLL
    def __init__(self, probability: float=1.0) -> None:
        super().__init__(probability=probability)

    def _apply(self, player: Type['Player'], *args, **kwargs):
        dice_value = roll_union_dice(values=[1, 3])
        logger.debug(f'{player} 发动技能掷出 {dice_value} 的骰子')
        return dice_value
        

@register_skill
class ZanNiSkill_ON_MOVE(Skill):
    """开始移动时如果处于堆叠状态,下回合有40%概率额外前进2格"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.BEFORE_MOVE
    def __init__(self, probability: float=0.4) -> None:
        super().__init__(probability=probability)

    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat = kwargs['before_move_stat']
        # 第一轮不触发
        if stat['simulator'].stat['is_first_round']:
            return
        board: Board = stat['board']
        if len(board.stacks[player.position]) > 1:
            setattr(player, "extra_steps", (lambda _: 2, (stat['simulator'].stat['round_idx'] + 1, 1)))
            logger.debug(f'{player} 发动技能, 下回合多执行 2 步!')
        
    
@register_skill
class FeiBiSkill(Skill):
    """50%概率额外前进1格. **在每回合移动时触发,不可递归触发**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.ON_MOVE
    def __init__(self, probability: float=0.5) -> None:
        super().__init__(probability=probability)

    def _apply(self, player: Type['Player'], *args, **kwargs):
        stat=kwargs['on_move_stat']
        forward_steps: int = stat['forward_steps']
        stat['simulator'].stat['override_forward_steps'] = forward_steps + 1
        other_players = stat['board'].stacks[player.position][stat['board'].stacks[player.position].index(player):]
        logger.debug(f"{player} 发动技能背着 {other_players} 一起前进 {forward_steps+1} 格!")
        return forward_steps + 1


@register_skill
class KaTiXiYaSkill(Skill):
    """自身移动结束后,若处于最后一名,本场比赛剩余回合都会以60%概率额外前进2格.**在每回合移动后执行,每场比赛只能出发一次**"""
    _PRIORITY: SKILL_PRIORITY = SKILL_PRIORITY.AFTER_MOVE
    def __init__(self, probability: float=1.0) -> None:
        super().__init__(probability=probability)
        self.triggered = False  # 只能触发一次

    def _apply(self, player: Type['Player'], *args, **kwargs):
        if self.triggered:
            return
        stat = kwargs['after_move_stat']
        board: Board = kwargs['after_move_stat']['board']
        self.triggered = board.get_last_player() == player
        if self.triggered:
            setattr(
                player, "extra_steps", 
                (
                    lambda _: 2 if np.random.random() < 0.6 else 0, 
                    (stat['simulator'].stat['round_idx'] + 1, np.inf)
                )
            )
            logger.debug(f"{player} 发动技能! 本场比赛后续所有回合都有概率额外前进 2 格!")

if __name__ == "__main__":
    print(SKILL_FACTORY)
