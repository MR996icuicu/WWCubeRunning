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
import numpy as np

from typing import List, Optional

logging.basicConfig()  # 保证根 logger 有 handler
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        "%(asctime)s | %(levelname)5s | %(filename)12s:%(lineno)4s | %(message)s", datefmt="%H:%M:%S"
    )
)
logger.propagate = False
logger.handlers.clear()
logger.addHandler(handler)

def roll_union_dice(values: Optional[List[int]]=None) -> int:
    if not values:
        values = [1, 2, 3]
    
    return np.random.choice(np.array(values), size=1)[0]


if __name__ == "__main__":
    print([ roll_union_dice() for i in range(10) ])
