<h1>Assetto Corsa Gym Linux Setup</span></h1>

Instructions on how to run Assetto Corsa on Linux, partially based on this [guide](https://www.youtube.com/watch?v=8qy_RQr8LbM). tested on Ubuntu 24.04.

**IMPORTANT: When training RL agents, use the lowest resolution in Assetto Corsa, lower all graphics settings, and avoid full-screen mode. Close all applications, as network traffic or background applications can cause jitter, especially on slow hardware. Content Manager is useful for creating different profiles.**


## **1. Proton Setup**
To run Assetto Corsa on Linux, we need to first install Proton. 

### **1.1 Enable Assetto Corsa to use Steam Compatibility Tool**
Go to Steam Library > Assetto Corsa

`Manage > Properties > Compatibility > Check 'Force the use of a specific Steam Play compaitbility tool`

After checking the box, you are expected to see a list of available Proton version attached below. 

Next we will install and add a specific Proton version: **GE-Proton9-2**.  

### **1.2 Download ProtonUp-Qt** 
ProtonQT is needed to install GE-Proton-9-2.

🔗 **[Download ProtonUp-Qt](https://davidotek.github.io/protonup-qt/)** 

Mark the AppImage as executable and run ProtonUp-Qt, and double-click to execute the AppImage. 
```sh
chmod +x ProtonUp-Qt*.AppImage
```

### **1.3 Install GE-Proton-9-2 with ProtonUp-Qt**
#### **Step 1: Locate Installation Folder**
Under `Install for:`, ProtonUp-Qt will automatically locate the position of `compatibilitytools.d`. If not, you can manually locate the folder's position or customize the installing position. 

#### **Step 2: Install GE-Proton9-2**
Click `Add version`, choose `GE-Proton` for `Compatibility Tool` and `GE-Proton9-2` for `Version`, and click `Install`.

#### **Step 3: Set GE-Proton9-2 as the Proton version for Assetto Corsa**
Click `Show game list`, choose `GE-Proton9-2` as the compatibility tool, and click `apply`. 

Then reboot Steam, you would expect GE-Proton9-2 to be the default Proton version under `Manage > Compatibility`. If not, you can find GE-Proton9-2 in the list and choose it as the Proton version. 

#### **Step 4: Install missing fonts**
Install missing fonts with the following scripts:
```sh
wget -O "$HOME/.local/share/Steam/steamapps/compatdata/244210/pfx/drive_c/windows/Fonts/Verdana.ttf" \
      https://raw.githubusercontent.com/matomo-org/travis-scripts/master/fonts/Verdana.ttf

wget -O "$HOME/.local/share/Steam/steamapps/compatdata/244210/pfx/drive_c/windows/Fonts/segoeuiz.ttf" \
      https://raw.githubusercontent.com/xamarin/evolve-presentation-template/master/Fonts/Segoe%20UI/segoeuiz.ttf

wget -O "$HOME/.local/share/Steam/steamapps/compatdata/244210/pfx/drive_c/windows/Fonts/segoeui.ttf" \
      https://raw.githubusercontent.com/xamarin/evolve-presentation-template/master/Fonts/Segoe%20UI/segoeui.ttf

wget -O "$HOME/.local/share/Steam/steamapps/compatdata/244210/pfx/drive_c/windows/Fonts/verdanai.ttf" \
      https://raw.githubusercontent.com/dolbydu/font/master/Sans/Verdana/verdanai.ttf
```

### **1.4 Initiate Assetto Corsa**
Start Assetto Corsa, and expect to wait about 3 to 5 minutes for Proton to install and initialize.
If the program crashes, start Steam from the command line. The installation details of Proton will be displayed when Assetto Corsa is running. A quick fix for Proton crashes is to switch to a different version.

**Note**: On some systems, the Assetto Corsa main screen worked, but the race would not start. Switching to GE-Proton9-26 resolved the issue.



## **2. Content Manager Installation**
### **2.1 Download Content Manager**
Download and unzip Content Manager.

🔗 [Content Manager Download](https://acstuff.ru/app/)

### **2.2 Create hard link for Content Manager**
We run `Content Manager.exe` by creating a hard link to `AssettoCorsa.exe`, such that Proton will execute the content manager as if it is running Assetto Corsa. 

#### **Step 1: Move the downloaded exe to Assetto Corsa local folder**
1. Locate Assetto Corsa local folder by 

    `Manage > Manage > Browse local files`. 

    The folder will usually be in the form of 
    ```
    <path/to/steamapps>/steamapps/common/assettocorsa
    ```

2. Move the downloaded `Content Manager.exe` to Assetto Corsa local folder location. 

#### **Step 2: Rename AssettoCorsa.exe**
Rename the original `AssettoCorsa.exe` to `AssettoCorsaBackup.exe` to avoid conflict. We will retreive its name later. 

### **2.3 Create a hard link for Content Manager.exe**
```sh
ln Content\ Manager.exe AssettoCorsa.exe
```
You would expect `AssettoCorsa.exe` is generated, and it is linked to `Content Manager.exe`. 

### **2.3.5 (Optional):  Create a soft link for Steam user config**
1. First locate the user config folder in Proton. Naviagate the parent folder (usually `steamapps`) of Assetto Corsa local folder, and locate to 
`~/.local/share/Steam/steamapps/compatdata/244210/pfx/drive_c/Program Files (x86)/Steam/config`. 



2. Then locate the local user config, for example `~/.steam/root/debian-installation/config`
3. Create a softlink to user config folder in Proton, for example

```sh
ln -s "~/.steam/root/debian-installation/config" "/home/<user>/.local/share/Steam/steamapps/compatdata/244210/pfx/drive_c/Program Files (x86)/Steam/config"
```

### **2.4 Initiate Content Manager**
Go to Steam Assetto Corsa page, and start Assetto Corsa. Due to the hard link created, the Content Manager will be initiated rather than the Assetto Corsa game itself. 

In the setting page, for `Assetto Corsa root folder`, set

`\home\<user>\.local\share\Steam\steamapps\common\assettocorsa\`

### **2.5 Install Custom Shader Patch**

1. Download CSP v0.2.1 (other versions have a bug that makes the screen too dark, and the stable version crashes) from [https://acstuff.club/patch/?info=0.2.1](https://acstuff.club/patch/?info=0.2.1).

2. Install it by dragging and dropping the downloaded ZIP file into Content Manager Window.

**WARNING**: if `INIReader::cache error` is reported when running Assetto Corsa game, you need to switch to a upgraded version of custom shader patch (e.g. ver 0.2.7), though the game graphics may be affected. 

### **2.6 Rename back the original AssettoCorsa.exe**
Rename the current `AssettoCorsa.exe` (the content manager) into `AssettoCorsa_content_manager.exe`, and rename `AssettoCorsaBackup.exe` (the "true" AC game) into `AssettoCorsa.exe`.  


---
## **4. Assetto Corsa game configuration**
### **4.1 Copy the Plugin Files**  
1. Locate the plugin folder in this repository:  
   ```sh
   .\assetto_corsa_gym\AssettoCorsaPlugin\plugins\sensors_par
   ```
2. Copy this folder to the Assetto Corsa installation directory under `apps\python\`.  
   - The default AC installation path is:  
     ```sh
     <path/to/steamapps>\steamapps\common\assettocorsa\
     ```
3. The final destination should look like this:  
   ```sh
   <path/to/steamapps>\steamapps\common\assettocorsa\apps\python\sensor_par
   ```


### **4.2 Install Configuration Files**  
Copy the necessary configuration files from:  
```sh
assetto_corsa_gym\AssettoCorsaPlugin\windows-libs
```

```sh
mkdir -p "$HOME/.local/share/Steam/steamapps/common/assettocorsa/cfg/controllers/savedsetups"
mkdir -p "$HOME/.local/share/Steam/steamapps/common/assettocorsa/system/x64"


cp assetto_corsa_gym/AssettoCorsaPlugin/windows-libs/Vjoy_linux.ini \
   "$HOME/.local/share/Steam/steamapps/common/assettocorsa/cfg/controllers/savedsetups/"

cp assetto_corsa_gym/AssettoCorsaPlugin/windows-libs/WASD.ini \
   "$HOME/.local/share/Steam/steamapps/common/assettocorsa/cfg/controllers/savedsetups/"

cp -r assetto_corsa_gym/AssettoCorsaPlugin/windows-libs/DLLs \
   "$HOME/.local/share/Steam/steamapps/common/assettocorsa/system/x64/"


cp -r assetto_corsa_gym/AssettoCorsaPlugin/windows-libs/Lib \
   "$HOME/.local/share/Steam/steamapps/common/assettocorsa/system/x64"

```


## **3. Setup xbox input device**
Linux uses virtual xbox as a substitute for Windows Vjoy to communicate with AC server. 
### **Step 3.1: Install xboxdrv**
```sh
sudo apt-get install xboxdrv
```
### **Step 3.2: Turn on virtual xbox**
```sh
sudo xboxdrv --daemon --silent --mimic-xpad --type xbox360 --dbus disabled
```

### **4.3 Configuring Assetto Corsa**  

#### **4.3.1: Enable the Plugin**  
1. Open **Assetto Corsa**  
2. Go to **Options > General > UI Modules**  
3. Enable `sensor_par`  

#### **4.3.2 Configure Controls**  
1. Navigate to **Options > Controls**  
2. Ensure that both **vJoy** and **WASD** are available  
3. Load **vJoy Linux** as the active input

#### **4.3.3 Set Video and Display Settings**  
- **Frame Rate Limit:** `50 FPS`  
  - *(Located in `Options > Video > Display > Framerate Limit`)*  

#### **4.3.4 Start a Hotlap Session**  
- **Mode:** `Challenge > Hotlap`  

#### **4.3.5 Adjust Driving Assists**  
| Setting                   | Recommended Value |
|---------------------------|------------------|
| Automatic Gearbox         | **ON** |
| Ideal Racing Line         | **As Preferred** |
| Automatic Clutch          | **Enabled** |
| Automatic Throttle Blip   | **Disabled** |
| Traction Control          | **OFF** |
| Stability Control         | **OFF** |
| Mechanical Damage         | **OFF** |
| Tyre Blankets             | **ON** |
| ABS                       | **OFF** |
| Fuel Consumption          | **OFF** |
| Tyre Wear                 | **OFF** |
| Slipstream Effect         | **1x** |
| Time of Day               | **10:00 AM** |
| Weather                  | **Mid Clear** |
| Ambient Temperature       | **26°C** |
| Time Multiplier           | **1x** |
| Track Surface             | **Optimum** |
| Penalties                 | **ON** |

---
## **5. Test interface**
1. Start AC

2. Run `test_maps_creator.ipynb`.  
   You should see an output like:

   ```
   Closest Steering Command to reach 240.0°: 0.5342
   ```

   It will also display a figure showing the input-output mapping in Assetto Corsa:

   <img src="docs/steer_ranges_f317.jpg" alt="Steering Range Mapping" width="400"/>

   If the result matches, it means the Xbox controller is properly configured.


## **6. Report bugs**

### Plugin:
   - Paste the logs from:
      ```sh
      cat "$HOME/.local/share/Steam/steamapps/compatdata/244210/pfx/drive_c/users/steamuser/Documents/Assetto Corsa/logs/py_log.txt"
      ```