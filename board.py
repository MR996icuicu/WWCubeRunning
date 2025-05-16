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

from collections import defaultdict
from typing import Dict, List, Type


class Board(object):
    """棋盘类，管理总格数和格上玩家堆叠状态。"""

    def __init__(self, length: int=24) -> None:
        self.length: int = length
        self.stacks: Dict[int, List[Type['Player']]] = defaultdict(list)

    def reset(self, players: List[Type['Player']]) -> None:
        """清空所有格子的堆叠信息。"""
        self.stacks.clear()
        self.stacks[1] = players.copy()
        self.players = players.copy()
    
    def is_reached(self, ):
        """是否已经有选手到了终点"""
        return len(self.stacks[self.length]) > 0

    def get_last_position(self, ):
        return min([p.position for p in self.players])
    
    def is_last(self, player: Type['Player']) -> bool:
        """判断player是否是最后一个(不一定是唯一最后一个)

        Args:
            player (Type[&#39;Player&#39;]): _description_

        Returns:
            bool: _description_
        """
        return player.position == self.get_last_position()
