# Assetto Corsa Gym Environment

OpenAI Gym interfaces with Assetto Corsa for Autonomous Racing. This repository integrates the Assetto Corsa racing simulator with the OpenAI's Gym interface, providing a high-fidelity environment for developing and testing Autonomous Racing algorithms in realistic racing scenarios.

Features
- High-Fidelity Simulation: Realistic car dynamics and track environments.
- Customizable Scenarios: Various cars, tracks, and weather conditions.
- RL Integration: Compatible with OpenAI Gym for easy RL algorithm application.
- ROS integration (see link)


## Run

### Train
```
python sac_train.py --config ../algorithm/discor/config/assettocorsa.yaml --track <track> --car <car>
```


### Test
```
python sac_train.py --config ../algorithm/discor/config/assettocorsa.yaml --disable_wandb --track <track> --car <car> --load_path <path to model> --test 
```

# Download datasets


Create a path and navigate to it
```
mkdir data_sets && cd data_sets
```

# Tracks

## Available
Barcelona: ks_barcelona-layout_gp
Monza: monza
Austria: ks_red_bull_ring-layout_gp
Oval: indianapolis_sp

## Monza
```
wget -O downloaded_file.zip "https://www.dropbox.com/scl/fo/u8q1stkafbxw6mgavc9oo/AG64cejNqerJc8Rj9h0FTYk?rlkey=3i7hx2q7f528mkbfhy163e9r9&dl=1" && unzip downloaded_file.zip -d monza; rm downloaded_file.zip
```

## Barcelona
```
wget -O downloaded_file.zip "https://www.dropbox.com/scl/fo/jy7szdlsb6z5hceqbcipe/ABZ5IgqCLNEmoGeu-xxtRdU?rlkey=a8dketk9c77wgzx8am32dvrvy&dl=1" && unzip downloaded_file.zip -d ks_barcelona-layout_gp; rm downloaded_file.zip
```

## Indianapolis_sp (Oval)
```
wget -O downloaded_file.zip "https://www.dropbox.com/scl/fo/3vp25we2h8g7knuhpioic/ADHx7qb88-TdZk9su1KXWKg?rlkey=cgwdjdujuzhfquaiz2cjdo241&dl=1" && unzip downloaded_file.zip -d indianapolis_sp; rm downloaded_file.zip
```

## Austria
```
wget -O downloaded_file.zip "https://www.dropbox.com/scl/fo/dezimtveazd1w70ttggf0/AMmK8ue5VaKc6vYZT_t0-4Q?rlkey=mpyb2axbzzyebc6l85lnmh9ls&dl=1" && unzip downloaded_file.zip -d ks_red_bull_ring-layout_gp; rm downloaded_file.zip
```


## Python Installation

**Install Visual Studio Compiler**
- To compile the necessary components for the plugin, download and install the Visual Studio compiler from:
[Visual Studio C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Make sure to install the C++ build tools component

**Install Python using Anaconda**
```
conda create -n p309 python=3.9.13
conda activate p309

pip install setuptools==65.5.0
pip install -r requirements.txt

conda install pytorch==1.12.1 cudatoolkit=11.6 -c pytorch -c conda-forge
conda install -c conda-forge shapely # (linux) pip install shapely intersect
```

### Problems
- Complains about OpenCV. Fix:
```pip install setuptools==65.5.0 "wheel<0.40.0"```

## Assetto Corsa plugin Installation
1. **Follow the manual**

2. **Install vJoy**
   - Needed to send commands to Assetto Corsa
   -	Download and install [Vjoy](https://sourceforge.net/projects/vjoystick/)

2. **Copy the plugin files**
   - Navigate to your plugin folder:
     ```
     .\assetto-corsa-autonomous-racing-plugin\plugins\sensors_par
     ```
   - Copy it to your Assetto Corsa installation folder under `apps\python\`. The default AC installation folder is usually located at:
     ```
     <AC_installation_folder>\assettocorsa\apps\python\
     ```
     where `<AC_installation_folder>` is typically:
     ```
     C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\
     ```
   - The destination path should look something like this:
     ```
     C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\sensor_par
     ```
3. **Installation of Configuration Files**

  - **Vjoy Configuration**
    - The `Vjoy.ini` file is a configuration file for Assetto Corsa. It should be copied to:
      ```
      C:\Users\%user%\Documents\Assetto Corsa\cfg\controllers\savedsetups
      ```
  - **WASD Controls**
    - The `WASD.ini` file allows you to control the car using WASD keys. Copy it to:
      ```
      C:\Users\%user%\Documents\Assetto Corsa\cfg\controllers\savedsetups
      ```
  - **Dlls and Lib Folders**
    - These folders contain a Python version of the socket library, used by the plugin. They should be copied to:
      ```
      C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\system\x64
      ```

5. **Custom Shaders Patch**
    - This patch is needed to be able to restart the car. Install Content Manager from:
    [Content Manager Download](https://acstuff.ru/app/)
    - After installation, open Content Manager and navigate to:
    - Settings > Custom Shaders Patch
    - Click "install" to complete the setup.

----

## Citation
```
```

----

## Contributing

You are very welcome to contribute to this project. Feel free to open an issue or pull request if you have any suggestions or bug reports, but please review our [guidelines](CONTRIBUTING.md) first. Our goal is to build a codebase that can easily be extended to new environments and tasks, and we would love to hear about your experience!

----

## License

This project is licensed under the MIT License - see the `LICENSE` file for details. Note that the repository relies on third-party code, which is subject to their respective licenses.
