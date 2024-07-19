import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
import copy
from omegaconf import OmegaConf
import torch

# Add paths
sys.path.extend([os.path.abspath('./assetto_corsa_gym'), './algorithm/discor'])

# Custom module imports
import AssettoCorsaEnv.assettoCorsa as assettoCorsa
import AssettoCorsaEnv.data_loader as data_loader
from discor.algorithm import SAC, DisCor
from discor.agent import Agent
import common.misc as misc
import common.logging_config as logging_config
from common.logger import Logger

logger = logging.getLogger(__name__)

def parse_args(hardcode=None):
    parser = argparse.ArgumentParser(description="Description of your program.")
    parser.add_argument("--config", default="config.yml", type=str, help="Path to configuration file")
    parser.add_argument("--load_path", type=str, default=None, help="Path to load the model from (default: None)")
    parser.add_argument("--algo", type=str, default="sac", help="Algorithm type (default: sac)")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("overrides", nargs=argparse.REMAINDER, help="Any key=value arguments to override config values")
    if hardcode is not None:
        args = parser.parse_args(hardcode.split())
    else:
        args = parser.parse_args()
    args.load_path = os.path.abspath(args.load_path) + os.sep if args.load_path is not None else None
    return args

def main():
    args = parse_args()

    # Load base configuration
    config = OmegaConf.load(args.config)

    # Apply command line overrides
    cli_conf = OmegaConf.from_dotlist(args.overrides)
    config = OmegaConf.merge(config, cli_conf)

    if config.work_dir is not None:
        work_dir = os.path.abspath(args.work_dir) + os.sep + config.track + os.sep + config.car + os.sep
        os.makedirs(work_dir, exist_ok=True)
    else:
        work_dir = "outputs" + os.sep + datetime.now().strftime('%Y%m%d_%H%M%S.%f')[:-3]
        work_dir = os.path.abspath(work_dir) + os.sep
        os.makedirs(work_dir, exist_ok=True)
    config.work_dir = work_dir

    logging_config.create_logging(level=logging.DEBUG, file_name=work_dir + "log.log")
    logging.getLogger().setLevel(logging.INFO)

    # log system and git info
    misc.get_system_info()
    misc.get_git_commit_info()

    logger.info("Configuration:")
    logger.info(OmegaConf.to_yaml(config))
    logger.info("work_dir: " + work_dir)

    env = assettoCorsa.make_ac_env(cfg=config, work_dir=work_dir)

    # Device to use
    device = torch.device("cuda")
    assert device.type == "cuda", "Only cuda is supported"

    if args.algo == 'discor':
        algo = DisCor(
            state_dim=env.observation_space.shape[0],
            action_dim=env.action_space.shape[0],
            device=device, seed=config.seed,
            **OmegaConf.to_container(config.SAC), **OmegaConf.to_container(config.DisCor))
    elif args.algo == 'sac':
        algo = SAC(
            state_dim=env.observation_space.shape[0],
            action_dim=env.action_space.shape[0],
            device=device, seed=config.seed,
            **OmegaConf.to_container(config.SAC))
    else:
        raise Exception('You need to set algo sac or discor')


    # Update the logger configuration with dynamic values
    config.exp_name = f'{config.AssettoCorsa.car}-{config.AssettoCorsa.track}'
    config.action_dim = env.action_dim
    config.steps = config.Agent.num_steps

    # Initialize wandb logger
    if not config.disable_wandb:
        wandb_logger = Logger(config.copy())
    else:
        wandb_logger = None

    agent = Agent(env=env, test_env=env, algo=algo, log_dir=config.work_dir,
                  device=device, seed=config.seed, **config.Agent, wandb_logger=wandb_logger)

    if not args.test and config.load_offline_data:
        data_config_file = os.path.abspath(r"./ac_offline_train_paths.yml")
        logger.info("Loading offline dataset...")
        assert config.dataset_path, "dataset_path not set in config"
        dataset_path = Path(config.dataset_path + os.sep)

        # load data set
        data = data_loader.read_yml(data_config_file)

        for track in data:
            for car in data[track]:
                paths = data[track][car]
                paths = [dataset_path / Path(f"{track}/{car}") / p["id"] / "laps" for p in paths]
                env_load_config = copy.deepcopy(config)
                env_load_config.AssettoCorsa.track = track
                env_load_config.AssettoCorsa.car = car
                env_load = assettoCorsa.make_ac_env(cfg=env_load_config, work_dir=work_dir)
                for laps_path in paths:
                    assert laps_path.exists(), f"{laps_path} not found"
                    agent.load_pre_train_data(laps_path.as_posix(), env_load)

        if config.Agent.use_offline_buffer:
            agent._replay_buffer.online(True)

    if config.pre_train:
        agent.pre_train()

    if args.load_path is not None:
        load_buffer = False if args.test else True
        agent.load(args.load_path, load_buffer=load_buffer)

    if args.test:
        agent._env.set_eval_mode()
        agent.evaluate()
        logger.info("done evaluation")
    else:
        agent.run()
        logger.info("done training")

if __name__ == "__main__":
    main()