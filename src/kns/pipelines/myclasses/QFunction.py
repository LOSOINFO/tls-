import pfrl
import torch

class QFunction(torch.nn.Module):
    def __init__(self, input_size, hidden_sizes, n_actions, nonlinearity) -> None:
        super().__init__()
        assert nonlinearity in ['relu', 'tanh']
        activ_func = torch.relu
        if nonlinearity == 'tanh':
            activ_func = torch.tanh

        self.learner_head = torch.nn.Sequential(
            pfrl.nn.MLP(in_size=input_size,
                        hidden_sizes=hidden_sizes,
                        nonlinearity=activ_func,
                        out_size=n_actions,
                        last_wscale=1),
            pfrl.q_functions.DiscreteActionValueHead(),
        )
    
    def forward(self, x):
        x = self.learner_head(x)
        return x

