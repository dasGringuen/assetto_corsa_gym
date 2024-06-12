import gym
from gym.envs.registration import register
# from metaworld.envs.mujoco.env_dict import ALL_ENVIRONMENTS

# gym.logger.set_level(40)


# def assert_env(env):
#     assert isinstance(env.observation_space, gym.spaces.Box)
#     assert isinstance(env.action_space, gym.spaces.Box)
#     assert hasattr(env, '_max_episode_steps')


# METAWORLD_TASKS = (
#     'hammer-v1', 'stick-push-v1', 'push-wall-v1',
#     'stick-pull-v1', 'dial-turn-v1', 'peg-insert-side-v1')

# for task in METAWORLD_TASKS:
#     register(
#         id=task,
#         entry_point=ALL_ENVIRONMENTS[task],
#         max_episode_steps=150)
#     assert_env(gym.make(task))


# def make_env(env_id):
#     env = gym.make(env_id)
#     setattr(env, 'is_metaworld', env_id in METAWORLD_TASKS)
#     return env
