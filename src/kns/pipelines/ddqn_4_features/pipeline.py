"""
This is a boilerplate pipeline 'ddqn_daafa_4_features'
generated using Kedro 0.19.7
"""

from kedro.pipeline import Pipeline, pipeline, node
from .nodes import construct_infrastructure_generators, construct_infrastructure_managers, \
construct_nspr_generators, construct_nsprs_lifecycle_managers, construct_environments, construct_nn, \
construct_replay_buffer, construct_explorer, construct_optimizer_and_ddqn_agent, \
agent_and_envs_interaction, plotting_performance_results

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=construct_infrastructure_generators,
            inputs="params:infragen",
            outputs=["train_infra_gen", "eval_infra_gen"],
            name="infras_gen_node"
        ),
        node(
            func=construct_infrastructure_managers,
            inputs=["train_infra_gen", "eval_infra_gen"],
            outputs=["train_infra_man", "eval_infra_man"],
            name="infras_man_node"
        ),
        node(
            func=construct_nspr_generators,
            inputs="params:nsprgen",
            outputs=["train_nspr_gen", "eval_nspr_gen"],
            name="nspr_gen_node"
        ),
        node(
            func=construct_nsprs_lifecycle_managers,
            inputs=None,
            outputs=["train_nsprs_man", "eval_nsprs_man"],
            name="nspr_life_node"
        ),
        node(
            func=construct_environments,
            inputs=["train_infra_man", "eval_infra_man", "train_nspr_gen", "eval_nspr_gen", "train_nsprs_man", "eval_nsprs_man", "params:envs"],
            outputs=["train_env", "eval_env"],
            name="envs_node"
        ),
        node(
            func=construct_nn,
            inputs=["params:nn", "params:n_cnode_features", "params:n_vnf_features", "params:infragen.n_cnodes"],
            outputs="model",
            name="nn_node"
        ),
        node(
            func=construct_replay_buffer,
            inputs="params:rbuf",
            outputs="replay_buffer",
            name="buffer_node"
        ),
        node(
            func=construct_explorer,
            inputs=["params:explor", "params:infragen.n_cnodes"],
            outputs="explorer",
            name="explorer_node"
        ),
        node(
            func=construct_optimizer_and_ddqn_agent,
            inputs=["model", "params:opt", "replay_buffer", "explorer", "params:ddqn"],
            outputs="ddqn_agent",
            name="ddqn_node"
        ),
        node(
            func=agent_and_envs_interaction,
            inputs=["ddqn_agent", "train_env", "eval_env", "params:loop"],
            outputs="performance_records",
            name="interaction_node"
        ),
        node(
            func=plotting_performance_results,
            inputs="performance_records",
            outputs=None,
            name="plotting_node"
        )
    ])