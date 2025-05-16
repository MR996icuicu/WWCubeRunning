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
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict

import numpy as np

from board import Board
from player import Player, call_hook
from skill import SKILL_PRIORITY
from ops import logger

class GameSimulator:
    """
    回合制竞速游戏模拟器，支持技能系统、骰子投掷、玩家移动与模拟统计分析。
    """

    def __init__(
        self,
        board_length: int,
        players: List[Player],
    ) -> None:
        """
        初始化游戏模拟器。

        Args:
            board_length: 棋盘格子总数。
            players: 初始玩家列表。
            log_level: 日志记录等级。
        """
        self.board: Board = Board(board_length)
        self.players: List[Player] = players or []
        self.stat: Dict[Any, Any] = {}
    
    def game_ends(self) -> bool:
        """
        判断当前游戏是否结束。

        Returns:
            布尔值，表示游戏是否结束。
        """
        return self.board.is_reached()

    def setup(self) -> None:
        """
        设置新一局游戏，包括洗牌、玩家位置初始化与技能 hook 注册。
        """
        
        # player重置
        for player in self.players:
            player.reset()
        
        # board重置
        self.board.reset(self.players)
        
        # 顺序重置, 初始顺序是players的倒序

        self.stat['order'] = self.players[::-1]
        self.stat['is_first_round'] = True
        self.stat['round_idx'] = 0


    def roll_dice(self, player: Player) -> int:
        """
        为指定玩家投掷骰子，并判断是否有技能可以修改骰面。

        Args:
            player: 当前回合的玩家。

        Returns:
            投掷结果的整数值。
        """
        call_hook(
            SKILL_PRIORITY.BEFORE_ROLL, player, 
            before_roll_stat=dict(simulator=self, board=self.board)
        )
        dice_value = player.roll_dice()
        call_hook(
            SKILL_PRIORITY.AFTER_ROLL, player, 
            after_roll_stat=dict(simulator=self, board=self.board)
        )
        return dice_value
        

    def move_player(self, player: Player, forward_steps: int) -> None:
        """
        执行玩家的移动操作，包括骰子投掷、技能触发与位置更新。

        Args:
            player: 当前进行移动的玩家。
        """
        # 找到在当前玩家头上开始的所有玩家
        player_index = self.board.stacks[player.position].index(player)
        forward_players = list(self.board.stacks[player.position][player_index:])
        call_hook(
            SKILL_PRIORITY.BEFORE_MOVE, player, 
            before_move_stat=dict(simulator=self, board=self.board)
        )
        # 更新这些玩家的位置
        for player_idx, each_player in enumerate(forward_players):
            # 部分技能会覆盖一起移动的所有角色的步数
            forward_steps_ = self.stat.get('override_forward_steps', None) or forward_steps
            # 只有最下方的团子可以发动技能
            # 因为上方的团子是被带动的
            enable_skill = player_idx==0
            each_player.move(forward_steps_, board=self.board, simulator=self, enable_skill=enable_skill)
        
        call_hook(
            SKILL_PRIORITY.AFTER_MOVE, player, 
            after_move_stat=dict(simulator=self, board=self.board)
        )
        # 清空可以覆盖后续player步数的技能的覆盖效果, 只在当前回合中有效
        if self.stat.get('override_forward_steps', None) is not None:
            del self.stat['override_forward_steps']
            
    def random_order(self, ):
        """随机产生一个执行顺序, 但是第一轮的顺序是固定的"""
        if self.stat['is_first_round']:
            # 第一轮固定顺序
            self.stat['order'] = self.players[::-1]
        else:
            self.stat['order'] = np.random.permutation(self.players).tolist()
        
    def play_each_round(self, ):
        """进行一轮游戏"""
        self.stat['round_idx'] += 1
        self.stat['is_first_round'] = self.stat['round_idx']==1
        cur_round_idx = self.stat['round_idx']
        # 随机决定顺序
        self.random_order()
        logger.debug(f"第 {cur_round_idx} 轮开始, 执行顺序: {self.stat['order']}")
        # 先调用每轮前的hook
        for player in self.players:
            call_hook(
                SKILL_PRIORITY.BEFORE_ROUND, player, 
                before_round_stat=dict(simulator=self, board=self.board)
            )
        
        
        # 按顺序遍历player
        for player in self.stat['order']:
            logger.debug(f"{player} 开始回合, 当前位置 {player.position}, 同位置所有人 {self.board.stacks[player.position]}")
            call_hook(
                SKILL_PRIORITY.ON_ENTER_TURN, player, 
                on_enter_turn_stat=dict(simulator=self, board=self.board)
            )
            forward_steps = self.roll_dice(player)
            self.move_player(player, forward_steps)
            call_hook(
                SKILL_PRIORITY.ON_EXIT_TURN, player,
                on_exit_turn_stat=dict(simulator=self, board=self.board)
            )
            
            logger.debug(f"{player} 回合结束")
        
        # 最后调用每轮结束的hook
        for player in self.players:
            call_hook(
                SKILL_PRIORITY.AFTER_ROUND, player, 
                after_round_stat=dict(simulator=self, board=self.board)
            )
        logger.debug(f"第 {cur_round_idx} 轮结束, 当前所有选手位置 {[ (p, p.position) for p in self.players ]}\n")

    def play(self) -> Player:
        """
        执行一场完整游戏，直到有玩家到达终点。

        Returns:
            获胜玩家, 如果多个玩家同时到终点, 则最上方的获胜
        """
        self.setup()
        while (not self.game_ends()):
            self.play_each_round()
            
        # 找到在终点的最上方的player
        return self.board.stacks[self.board.length][-1]
        
                

    def simulate(self, n_runs: int = 10000) -> List[Tuple[Player, float, float]]:
        """
        执行多次模拟实验，统计各玩家的胜率。

        Args:
            n_runs: 模拟次数。

        Returns:
            元组组成的列表, 包含玩家名称，胜率和收益期望
        """
        win_counts: Dict[Player, float] = defaultdict(float)

        for run in range(1, n_runs + 1):

            winner = self.play()
            win_counts[winner] += 1

            if logger.level <= logging.DEBUG:
                ranks = sorted(self.players, key=lambda p: p.position, reverse=True)
                logger.debug(f"Run {run} | 冠军 = {winner}")
                logger.debug(
                    "  最终排名和位置 | "
                    + " | ".join(f"{p.name}({p.position})" for p in ranks)
                )
            elif logger.level <= logging.INFO:
                if run % 1000 == 0:
                    logger.info(f"已完成 {run}/{n_runs} 次模拟")

        results = [ (player, count / n_runs, player.score * count / n_runs) for player, count in win_counts.items() ]
        logger.info(f"模拟结束 | (夺冠概率, 收益期望, 玩家) 如下:")
        for player, win_rate, return_estimation in results:
            logger.info(f"{win_rate:.4f}, {return_estimation:.4f}, {str(player):<4s}")
        return results
