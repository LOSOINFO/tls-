import numpy
from typing import Any
from pfrl.agents import DoubleDQN


class DDQN(DoubleDQN):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def act(self, obs: Any) -> Any:
        return super().act(numpy.array(obs[0] + obs[1]))
    
    def observe(self, obs: Any, reward: float, done: bool, reset: bool) -> None:
        return super().observe(numpy.array(obs[0] + obs[1]), reward, done, reset)