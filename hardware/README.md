<h1 align="center" color="blue">
  <br>
  Hardware Build Guide
  <br>
</h1>

<p align="center">
  <img src="../assets/img/hardware_ad.png" alt="Pixel Art Advertisement" width="60%">
</p>

## Parts

Welcome! To begin, buy all the [parts](BOM.md) for a Pixel Art base build, including for any additional features (ex. game controller).

## Build steps

1. Setup Raspberry Pi by following the official guide [Install an operating system](https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system).
    - Install the Raspberry Pi OS Lite (64-bit)
    - Set your Wi-Fi credentials
    - Enable SSH and save password for later use

1. 3D print all [3mf files](prints) for the Pixel Art case (also the RGB matrix spacer not shown here).
   Tested on a Bambu Lab X1C 3D printer.
    <br><img src="../assets/img/hardware/1_prints.jpeg" alt="Prints" width="60%"><br>

1. Prepare RGB Bonnet by soldering necessary pins.
    - Solder a jumper wire between `GPIO4` and `GPIO18`
    <br><img src="../assets/img/hardware/2_bonnet.jpeg" alt="Bonnet jumper wire" width="60%"><br>
    - Melt a blob of solder on the bottom solder jumper so the middle pad is "shorted" to `8`
    <br><img src="../assets/img/hardware/3_bonnet.jpeg" alt="Bonnet solder pad" width="60%"><br>
    - Optional [ Button ]: Solder alligator clip wires to `SCL` and `GND`
    <br><img src="../assets/img/hardware/4_bonnet.jpeg" alt="Bonnet button pins" width="60%"><br>

1. Connect RGB Bonnet to Raspberry Pi 4 using 2x20 pin riser header.
<br><img src="../assets/img/hardware/5_compute.jpeg" alt="RPI and Bonnet stack" width="60%">
<br><img src="../assets/img/hardware/6_compute.jpeg" alt="RPI and Bonnet stack alt" width="60%"><br>

1. Tape top and bottom case together to keep the case steady.
<br><img src="../assets/img/hardware/7_tape.jpeg" alt="Tape case" width="60%"><br>

1. Screw top and bottom case together with 2 x M3x8mm screws and nuts.
<br><img src="../assets/img/hardware/8_case_tab.jpeg" alt="Screw case tab" width="60%"><br>

1. Screw Raspberry Pi onto case with 2 x M2.5x4mm and 2 x M2.5x20mm.
<br><img src="../assets/img/hardware/9_rpi_screw.jpeg" alt="Screw in RPI" width="60%"><br>

1. Optional [ Panel Mount USB ]: Screw in USB panel mounts and plug into Raspberry Pi USB 2.0 ports.
<br><img src="../assets/img/hardware/10_usb_extend.jpeg" alt="Panel mounts" width="60%"><br>

1. Plug in power cables by feeding cables through the case's power cable hole (hole printed with slit if needed to cut open).
<br><img src="../assets/img/hardware/11_power.jpeg" alt="Power cables" width="60%"><br>

1. Optional [ Button ]: Attach button to case and attach RGB Bonnet alligator clips to button.
<br><img src="../assets/img/hardware/12_button.jpeg" alt="Button connection" width="60%"><br>

1. Attach RGB matrix by aligning matrix screw holes with the four circle stands in case. Screw in from back of the case using 4 x M3x12mm screws.
*Warning*: Treat RGB matrix as fragile or else you risk permanently damaging the LEDs.
<br><img src="../assets/img/hardware/13_rgb_screw.jpeg" alt="Screw in RGB matrix" width="60%"><br>

1. Connect RGB matrix data and power cables to the RGB Bonnet.
<br><img src="../assets/img/hardware/15_rgb_connect.jpeg" alt="RGB matrix data and power" width="60%"><br>

1. Connect speaker to Raspberry Pi USB 3.0 port. If keeping speaker inside the case, use an adhesive to keep from moving and potentially damaging the RGB LED matrix.
Alternatively, you can plugin from outside the case if Panel Mount USB is installed.
<br><img src="../assets/img/hardware/16_speaker.jpeg" alt="Speaker" width="30%"><br>

1. Cut your RGB diffuser acrylic to size 195mm x 214mm. Cut your Raspberry Pi clear acrylic to size 60mm x 94mm. You can use an acrylic scoring tool to cut sizes.
<br><img src="../assets/img/hardware/17_acrylic.jpeg" alt="Acrylic dimensions" width="60%"><br>

1. Drill 1/8in holes into RGB diffuser acrylic using the RGB matrix spacer's print holes as guides, this way holes align exactly.
*Warning*: Drill slow and work up drill bit sizes to avoid chipping or cracking acrylic's edge.
<br><img src="../assets/img/hardware/18_drill_acrylic.jpeg" alt="Acrylic drill holes" width="60%"><br>

1. Stack the RGB matrix spacer, then RGB diffuser acrylic (rough side down), onto the RGB matrix.
   Align holes with the case's square stands and screw into the case using 4 x M3x20mm screws.
<br><img src="../assets/img/hardware/19_rgb_diffuse.jpeg" alt="Stack screen" width="30%">
<img src="../assets/img/hardware/20_rgb_diffuse.jpeg" alt="Screw screen" width="30%"><br>

1. Tape or glue clear acrylic to top cover.
<br><img src="../assets/img/hardware/21_rpi_acrylic.jpeg" alt="Tape RPI acrylic" width="60%"><br>

1. Screw nameplate onto bottom cover using 4 x M3x6mm screws and nuts.
<br><img src="../assets/img/hardware/22_nameplate.jpeg" alt="Screw nameplate" width="60%"><br>

1. Plug in microphone to Raspberry Pi USB 3.0 port and clip onto top cover's microphone tab.
<br><img src="../assets/img/hardware/23_mic.jpeg" alt="Connect microphone" width="60%"><br>

1. Snap on top and bottom cover.
<br><img src="../assets/img/hardware/24_final_off.jpeg" alt="Snap on cover" width="30%"><br>

1. Power on Pixel Art!
Below is an example of an image generated by [Retro Diffusion Plugins](../plugins/ai/retro_diffusion/README.md).
<br><img src="../assets/img/hardware/25_final_on.jpeg" alt="Pixel Art powered on" width="30%"><br>
