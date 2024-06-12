import os
import sys
import logging
from pathlib import Path
import argparse
from omegaconf import OmegaConf

# Custom module imports
sys.path.append(os.path.abspath('./assetto_corsa_gym'))
import AssettoCorsaEnv.ac_env as ac_env
import AssettoCorsaEnv.motec_loader as motec_loader
import AssettoCorsaEnv.data_loader as data_loader
import AssettoCorsaEnv.assettoCorsa as assettoCorsa

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process dataset for Assetto Corsa.")
    parser.add_argument("--config", default="config.yml", type=str, help="Path to configuration file")
    parser.add_argument("overrides", nargs=argparse.REMAINDER, help="Any key=value arguments to override config values")
    return parser.parse_args()

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    # cmd line args and config
    args = parse_arguments()
    config = OmegaConf.load(args.config)
    cli_conf = OmegaConf.from_dotlist(args.overrides)
    config = OmegaConf.merge(config, cli_conf)

    # Path configurations
    dataset_path = Path(config.dataset_path)
    work_dir = "outputs"

    # Module configuration
    config.AssettoCorsa.enable_out_of_track_termination = False
    config.AssettoCorsa.enable_low_speed_termination = False

    load_paths = data_loader.get_all_paths_in_file(dataset_path=dataset_path, file='motec_to_pickle_config.yml', filter_tags={"type": "human", "data_type": "motec"})

    for laps_path, car, track in load_paths:
        logger.info(f"******************************************")
        logger.info(f"Processing {track} {car}")
        logger.info(f"from {laps_path}")
        logger.info(f"******************************************")
        laps_path = Path(laps_path)
        assert laps_path.exists(), f"{laps_path} not found"

        config.AssettoCorsa.track = track
        config.AssettoCorsa.car = car
        env = assettoCorsa.make_ac_env(cfg=config, work_dir=work_dir)
        motec_loader.convert_all_in_path(laps_path.as_posix(), env, ac_fps=50, target_freq=25, ignore_fps_missmatch=True)

if __name__ == "__main__":
    main()
