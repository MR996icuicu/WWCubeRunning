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

import logging
from simulator import GameSimulator
from player import Player
from skill import (
    JinXiSkill,
    ChangLiSkill,
    KaKaLuoSkill,
    ShouAnRenSkill,
    ChunSkill,
    KeLaiTaSkill,
    LuoKeKeSkill,
    BuLanTeSkill,
    ZanNiSkill_ON_MOVE,
    ZanNiSkill_ON_ROLL,
    FeiBiSkill,
    KanTeLeiLaSkill,
    KaTiXiYaSkill
)

from ops import logger

if __name__ == "__main__":

    logger.setLevel(logging.DEBUG)

    sim = GameSimulator(
        board_length=24,
        players=[
            # 15日比赛顺序, 按照14日比赛名次顺序
            # 名称, 黑马值, 技能(概率)
            # Player("卡卡罗", 1.28, [KaKaLuoSkill(1.0)]),
            # Player("珂莱塔", 1.74, [KeLaiTaSkill(0.28)]),
            # Player("长离", 1.6, [ChangLiSkill(0.65)]),
            # Player("今汐", 1.1, [JinXiSkill(0.4)]),
            # Player("椿", 1.3, [ChunSkill(0.5)]),
            # Player("守岸人", 1.17, [ShouAnRenSkill(1.0)]),
            Player('洛可可', 1.0, [LuoKeKeSkill(1.0)]),
            Player('布兰特', 1.0, [BuLanTeSkill(1.0)]),
            Player('赞妮', 1.0, [ZanNiSkill_ON_ROLL(1.0), ZanNiSkill_ON_MOVE(0.4)]),
            Player('菲比', 1.0, [FeiBiSkill(0.5)]),
            Player('坎特雷拉', 1.0, [KanTeLeiLaSkill(1.0)]),
            Player('卡提希娅', 1.0, [KaTiXiYaSkill(1.0)]),    # 卡提希娅的技能概率比较特殊, 这里的1.0指处于最后一名时100%触发
        ],
    )
    # 指定次数
    results = sim.simulate(n_runs=100)
    
