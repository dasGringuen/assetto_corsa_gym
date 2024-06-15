# Data collection

## Record human laps in the Motec format
Follow the instructions from [here](./data_collection_instructions.pdf)

## **Convert MoTeC files**
  - Converts MoTeC files recorded by ACTI (ld files) to pickle. Only the telemetry is used. The state, reward, and actions are reconstructed when loading the offline data.
  - Steps to update and run:
    1. Copy the new MoTeC file to your dataset path and follow the structure
    1. Update `motec_to_pickle_config.yml` (see available data in `data/paths.yml`).
    1. Run the following command:
       ```sh
       python motec_to_pickle.py dataset_path=<dataset_path>
       ```

