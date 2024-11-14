# Instructions to collect data using Assetto Corsa ACTI plugin

## To record human laps in Motec format
### Install Assetto Corsa Telemetry Interface (ACTI)
-   Needed to record laps in Motec format.
-   Download from the link and follow the instructions from the PDF. https://www.racedepartment.com/downloads/acti-assetto-corsa-telemetry-interface.3948/
-   Install the plugin.
-   Install the ACTI client.
-   (optional) Install Motec. Nice data viewer.
-   Ensure the FPS in Assetto Corsa is higher than 50fps.
-   **Set the frequency in the ACTI client to 50Hz. The default setting is 20Hz. -> IMPORTANT**
-   Steer Force Feedback channel:
    Overwrite the file `steam\assettocorsa\apps\python\acti\acti.py` using this [file](../assetto_corsa_gym/assetto-corsa-autonomous-racing-plugin/plugins/acti/acti.py)

    Alternatively, manually update line 514 as follows:
    ```
    #PackingString += "f"; PackingList.append(float(sim_info_obj.static.aidMechanicalDamage))
    PackingString += "f"; PackingList.append(float(ac.getCarState(0, acsys.CS.LastFF)))
    ```
    Note: The Steer Force Feedback channel is vital for telemetry. However, it is not recorded by the ACTI plugin. Since the aidMechanicalDamage channel is not needed, we repurpose it for recording the Steer Force Feedback.

### Assetto Corsa settings:
- Challenge -> hotlap
- Automatic gearbox:          as preferred
- Ideal Racing line:          as preferred
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

## Data Collection Protocol
### Tracks (priority top to bottom):
-	Barcelona GP
- 	Austria
-	Monza

### Cars (priority top to bottom):
- Dallara F317 Formula 3 from here: https://www.racedepartment.com/downloads/rsr-formula-3.8040/
- BMW Z4 GT3
- Mazda Miata NA


### For each track and each car
- Out lap + 5 laps
- Approximate 1.5hs drive
- If there is no enough time filter by priority.
