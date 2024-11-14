<h1>Assetto Corsa Gym</span></h1>

Plug-in installation instructions

## Assetto Corsa plugin Installation
1. **Install vJoy**
   - Needed to send commands to Assetto Corsa
   -	Download and install [Vjoy](https://sourceforge.net/projects/vjoystick/)

2. **Copy the plugin files**
   - Navigate to the plugin folder located in this repo:
     ```
     .\assetto_corsa_gym\assetto-corsa-autonomous-racing-plugin\plugins\sensors_par
     ```
   - Copy this folder to the Assetto Corsa installation folder under `apps\python\`. The default AC installation folder is usually located at:
     ```
     <AC_installation_folder>\assettocorsa\apps\python\
     ```
     where `<AC_installation_folder>` is typically in:
     ```
     C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\
     ```
   - The destination path should look like this:
     ```
     C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\sensor_par
     ```
4. **Installation of Configuration Files**
Install the following configurations from `assetto_corsa_gym\assetto-corsa-autonomous-racing-plugin\windows-libs`

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

4. **Custom Shaders Patch**
    - This patch is needed to be able to restart the car. Install Content Manager from:
    [Content Manager Download](https://acstuff.ru/app/)
    - After installation, open Content Manager and navigate to:
    - Settings > Custom Shaders Patch
    - Click "install" to complete the setup.

5. **Run Assetto Corsa**
    - In `options -> general -> UI Modules`: **enable sensor_par**
    - In `options -> control`: you should have vJoy and WASD. Load **vJoy**
    - In `options -> video -> Display -> Framerate limit` set to **50fps**
    See `assetto_corsa_gym\assetto-corsa-autonomous-racing-plugin\plugins\sensors_par\config.py`


    - Use Challenge -> hotlap
    - Config the following:
      - Automatic gearbox:          **on**
      - Ideal Racing line:          **as preferred**
      - Automatic clutch:           **enabled**
      - Automatic throttle blip:    **disabled**
      - Traction control:           **off**
      - Stability control:          **off**
      - Mechanical damage:          **off**
      - Tyre blankets:              **on**
      - ABS:                        **off**
      - Fuel consumption:           **off**
      - Tyre wear:                  **off**
      - Slipstream effect:          **1x**
      - Time of the day:            **10:00**
      - Weather:                    **Mid Clear**
      - Ambient Temp.:              **26**
      - Time multiplier:            **1x**
      - Track Surface:              **Optimum**
      - Penalties:                  **on**

6. ***(Optional) install the Dallara F317 Car***

    - Download it from here (you need to be registered):

        [RSR Formula 3 Download](https://www.overtake.gg/downloads/rsr-formula-3.8040/)

    - Uncompress and place the files in the following directory:

      ```C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\content```

---

## Acknoledgements

- Adrian Remonda (TU Graz)
- Francesco Gatti (TII EuroRacing - Hipert)
- Andrea Serafini (TII EuroRacing - Unimore)
- Francesco Moretti (TII EuroRacing - Unimore)
- Ayoub Raji (TII EuroRacing - Unimore)
