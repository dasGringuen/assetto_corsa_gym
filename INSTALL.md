<h1>Assetto Corsa Gym</span></h1>

Plug-in installation instructions.
This is the installation guide for **Windows**. For **Linux**, refer to [this guide](./INSTALL_Linux.md).

## **1. Assetto Corsa Plugin Installation**  

### **1.1 Install vJoy**  
vJoy is required to send commands to Assetto Corsa.  

🔗 **[Download and install vJoy](https://sourceforge.net/projects/vjoystick/)**  

---

### **1.2 Copy the Plugin Files**  
1. Locate the plugin folder in this repository:  
   ```sh
   .\assetto_corsa_gym\AssettoCorsaPlugin\plugins\sensors_par
   ```
2. Copy this folder to the Assetto Corsa installation directory under `apps\python\`.  
   - The default AC installation path is:  
     ```sh
     C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\
     ```
3. The final destination should look like this:  
   ```sh
   C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\sensor_par
   ```

---

### **1.3 Install Configuration Files**  
Copy the necessary configuration files from:  
```sh
assetto_corsa_gym\AssettoCorsaPlugin\windows-libs
```

- **VJoy Configuration**  
  - Copy `Vjoy.ini` to:  
    ```sh
    C:\Users\%user%\Documents\Assetto Corsa\cfg\controllers\savedsetups
    ```
- **WASD Controls**  
  - Copy `WASD.ini` to:  
    ```sh
    C:\Users\%user%\Documents\Assetto Corsa\cfg\controllers\savedsetups
    ```
- **DLLs and Library Folders**  
  - Copy these folders (Python socket library) to:  
    ```sh
    C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\system\x64
    ```

---

### **1.4 Install Custom Shaders Patch**  
The **Custom Shaders Patch** is required to restart the car.  

1. **Download and install Content Manager**:  
   🔗 [Content Manager Download](https://acstuff.ru/app/)  
2. Open **Content Manager** → Navigate to:  
   ```sh
   Settings > Custom Shaders Patch
   ```
3. Click **Install** to complete the setup.

---

## **2. Configuring Assetto Corsa**  

### **2.1 Enable the Plugin**  
1. Open **Assetto Corsa**  
2. Go to **Options > General > UI Modules**  
3. Enable `sensor_par`  

### **2.2 Configure Controls**  
1. Navigate to **Options > Controls**  
2. Ensure that both **vJoy** and **WASD** are available  
3. Load **vJoy** as the active input  

### **2.3 Set Video and Display Settings**  
- **Frame Rate Limit:** `50 FPS`  
  - *(Located in `Options > Video > Display > Framerate Limit`)*  

### **2.4 Start a Hotlap Session**  
- **Mode:** `Challenge > Hotlap`  

### **2.5 Adjust Driving Assists**  
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

## **3. (Optional) Install the Dallara F317 Car**  

1. **Download the RSR Formula 3 mod:**  
   🔗 [RSR Formula 3 Download](https://www.overtake.gg/downloads/rsr-formula-3.8040/) *(Requires Registration)*  

2. **Extract and install the mod**  
   - Unzip the downloaded files.  
   - Move them to:  
     ```sh
     C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\content
     ```

---

## **4. (Optional) Enable Screen Capture Support**  

Assetto Corsa runs on **Python 3.3**, which **cannot be upgraded**.  
To enable screen capture, we spawn an additional process using a newer **Python interpreter (3.9+)**.  

- This new process **captures images** and writes them to **shared memory** using a dual buffer.  
- The **AC client (`ac_client.py`) and AC environment (`ac_env.py`)** then copy these images for further processing.  
- Images can be saved directly to the hard drive.

### **4.2 Configure Screen Capture**  
Modify the following files:  
- `<AC_installation_folder>/apps/python/sensor_par/config.py`  
- `./config.yml`  

Ensure these settings are enabled:  
```python
# config.py
screen_capture_enable = True
screen_capture_save_to_disk = True  # (Optional) Save images to disk
```
```yaml
# config.yml
screen_capture_enable: True
```

---

### **4.3 Install Required Dependencies**  

#### **Step 1: Install Python 3.3.5**  
Assetto Corsa uses **Python 3.3.5**, and since its built-in distribution **cannot be modified**, we need to install the same version externally. This is required to install additional packages needed to **spawn the new interpreter (3.9+)** and **establish communication between both processes**.  

🔗 **[Download Python 3.3.5](http://www.python.org/ftp/python/3.3.5/python-3.3.5.amd64.msi)**  

- Install it in `C:\Python33\`.  
- During installation, check **"Add Python to PATH"**.  

#### **Step 2: Set Up `pip` for Python 3.3**  
```sh
curl https://bootstrap.pypa.io/pip/3.3/get-pip.py -o get-pip.py
C:\Python33\python get-pip.py
```
#### **Step 3: Install `pywin32`**  
- Download and install manually:  
  🔗 [Download pywin32-221](https://sourceforge.net/projects/pywin32/files/pywin32/Build%20221/pywin32-221.win-amd64-py3.3.exe/download)  


#### **Step 4: Install Additional Dependencies in Your Current Environment (Python 3.9+)**  
- Install the required dependencies in your **current Python 3.9+ environment**:  

```sh
conda activate p309
pip install mss pygetwindow opencv-python
```  

- If your `p309` interpreter is **not in the default path**, set it manually in `<sensor_par>/config.py`:

```python
self.config_python_executable = r"C:\Users\<user>\anaconda3\envs\p309\python.exe"
```

#### **Step 5: Check That It Works**  
Enable screen capture in `<sensor_par>/config.py`:

```python
self.screen_capture_enable = True
self.screen_capture_save_to_disk = True
```

If image saving is enabled, you should see images in:

```sh
C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\captures
```

---

## **5. Debugging & Logs**  
- To modify the plugin without exiting Assetto Corsa completely, you can leave the Assetto Corsa Launcher running or use Content Manager.
- Useful debug messages can be found in:  
  ```sh
  C:\Users\<user>\Documents\Assetto Corsa\logs\py_log.txt
  ```
- For the new interpreter in the secondary process:  
  ```sh
  C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\sensor_par_subprocess_log.txt
  ```

