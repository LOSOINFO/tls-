"""
This is a boilerplate pipeline 'ddqn_daafa_4_features'
generated using Kedro 0.19.7
"""

import copy
import pfrl
import numpy
from typing import Any
from kns.pipelines.myclasses.InfrastructureGenerator import InfrastructureGenerator
from kns.pipelines.myclasses.InfrastructureManager import InfrastructureManager
from kns.pipelines.myclasses.NSPRGenerator import NSPRGenerator
from kns.pipelines.myclasses.NSPRLifecycleManager import NSPRLifecycleManager
from kns.pipelines.myclasses.Environment import Environment
from kns.pipelines.myclasses.QFunction import QFunction
from kns.pipelines.myclasses.lion_pytorch import Lion
from kns.pipelines.myclasses.DDQN import DDQN

def construct_infrastructure_generators(infragen: dict):
    train_infragen = copy.deepcopy(infragen)
    train_infragen["is_for_train"] = True
    eval_infragen = copy.deepcopy(infragen)
    eval_infragen["is_for_train"] = False
    return InfrastructureGenerator(parameters=train_infragen), InfrastructureGenerator(parameters=eval_infragen)


def construct_infrastructure_managers(train_infra_gen: Any, eval_infra_gen: Any):
    return InfrastructureManager(infrastructure_generator=train_infra_gen), InfrastructureManager(infrastructure_generator=eval_infra_gen)


def construct_nspr_generators(nsprgen: dict):
    train_nsprgen = copy.deepcopy(nsprgen)
    train_nsprgen["is_for_train"] = True
    eval_nsprgen = copy.deepcopy(nsprgen)
    eval_nsprgen["is_for_train"] = False
    return NSPRGenerator(parameters=train_nsprgen), NSPRGenerator(parameters=eval_nsprgen)


def construct_nsprs_lifecycle_managers():
    return NSPRLifecycleManager(), NSPRLifecycleManager()


def construct_environments(train_infra_man, eval_infra_man, train_nspr_gen, eval_nspr_gen, train_nsprs_man, eval_nsprs_man, envs: dict):
    return Environment(infrastructure_manager=train_infra_man, nsprs_generator=train_nspr_gen, nsprs_lifecycle_manager=train_nsprs_man, failed_nspr_strategy=envs["failed_nspr_strategy"], keep_information=envs["keep_information"]), \
            Environment(infrastructure_manager=eval_infra_man, nsprs_generator=eval_nspr_gen, nsprs_lifecycle_manager=eval_nsprs_man, failed_nspr_strategy=envs["failed_nspr_strategy"], keep_information=envs["keep_information"])


def construct_nn(nn: dict, n_cnode_features: int, n_vnf_features: int, n_cnodes: int):
    input_size = (n_cnode_features * n_cnodes) + n_vnf_features
    return QFunction(input_size=input_size, hidden_sizes=nn["hidden_sizes"], n_actions=n_cnodes, nonlinearity=nn["activation_func"])


def construct_replay_buffer(rbuf: dict):
    return pfrl.replay_buffers.PrioritizedReplayBuffer(
            capacity=rbuf['capacity'],
            alpha=rbuf['alpha'],
            beta0=rbuf['beta0'],
            betasteps=rbuf['betasteps'],
            eps=rbuf['epsilon'],
            normalize_by_max=rbuf["normalize_by_max"],
            num_steps=rbuf['num_steps'] )


def construct_explorer(explor: dict, n_cnodes: int):
    return pfrl.explorers.LinearDecayEpsilonGreedy(
            start_epsilon=explor['start_epsilon'],
            end_epsilon=explor['end_epsilon'],
            decay_steps=explor['decay_steps'],
            random_action_func=lambda : numpy.random.randint(low=0, high=n_cnodes) )


def construct_optimizer_and_ddqn_agent(model, opt: dict, replay_buffer, explorer, ddqn: dict):
    optimizer = Lion(params=model.parameters(), lr=opt["learning_rate"], betas=opt["betas"], weight_decay=opt['weight_decay'])
    return DDQN(
            q_function=model,
            optimizer=optimizer,
            # optimizer=Lion(params=model.parameters(), lr=1e-4),
            replay_buffer=replay_buffer,
            explorer=explorer,
            phi=lambda x: x.astype(numpy.float32, copy=False),
            **ddqn )


def agent_and_envs_interaction(ddqn_agent, train_env, eval_env, loop: dict):
    performance_records = []
    actions_records = []
    #=======================
    best_performance = 0 # number of placed NSPRs
    for episode in range(1, loop["max_episodes"]+1): # training episodes loop
        if episode % 100 == 0: print("Training episode:",episode) ; print("P: ", performance_records[-10:]) ; print("A: ", actions_records[-20:])
        obs = train_env.reset()
        iteration = loop["max_iterations"]
        while iteration is None or iteration > 0: # iterations loop
            action = ddqn_agent.act(obs)
            obs,reward,done,info = train_env.step(action)
            reset = done or (iteration is not None and iteration==1)
            ddqn_agent.observe(obs, reward, done, reset)
            if iteration is not None:
                iteration -= 1
            if done: break
            #-----------------------------------------------------------------------------------
        if episode % loop["eval_episodes_interval"] == 0: # start an evaluation if condition met
            performance = 0
            with ddqn_agent.eval_mode():
                e_obs = eval_env.reset()
                e_iteration = loop["eval_max_iterations"]
                while e_iteration is None or e_iteration > 0:
                    e_action = ddqn_agent.act(e_obs)
                    actions_records.append(e_action)
                    e_obs,e_reward,e_done,e_info = eval_env.step(e_action)
                    e_reset = e_done or (e_iteration is not None and e_iteration==1)
                    ddqn_agent.observe(e_obs, e_reward, e_done, e_reset)
                    if e_iteration is not None:
                        e_iteration -= 1
                    if e_done:
                        performance = eval_env.nsprs_lifecycle_manager.running_and_successfully_terminated_nsprs()
                        performance_records.append( performance )
                        break
                    #-----------------------------
                if performance > best_performance:
                    best_performance = performance
                    ddqn_agent.save( "myagent" )
    return performance_records


def plotting_performance_results(performance_records: list):
    import matplotlib.pyplot as plt
    plt.plot(performance_records)
    plt.show()
