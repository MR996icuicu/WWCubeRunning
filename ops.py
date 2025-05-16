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

import numpy as np

from typing import List, Optional

from logger import LoggerSingleton

logger = LoggerSingleton().logger

def roll_union_dice(values: Optional[List[int]]=None) -> int:
    if not values:
        values = [1, 2, 3]
    
    return np.random.choice(np.array(values), size=1)[0]


if __name__ == "__main__":
    print([ roll_union_dice() for i in range(10) ])
