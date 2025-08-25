#!/bin/sh

# Setup script. Run inside Pixel Art.

################
# SETUP CHECKS #
################

# Install gum if missing
echo "Checking if charmbracelet gum is installed...\n"
if dpkg -s gum &>/dev/null; then
    echo "Installing gum cli..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg
    echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list
    sudo apt-get update -y
    sudo apt-get install gum -y
fi

# Setup gum aliases
alias gum-header='gum style --foreground "#A1FFAC" --border-foreground "#7AC0E9" --border double --align center --width 50 --margin "1 2" --padding "1 2"'
alias gum-print='gum style --foreground "#A1FFAC"'
alias gum-print-err='gum style --foreground "#F17B8F"'
alias gum-spinner='gum spin -s points --show-output --spinner.foreground="#7AC0E9" --title.foreground="#A1FFAC" --title'

gum-header "Running script checks"

# Script must run as root
gum-print "Verify running as root..."
if [ $(id -u) -ne 0 ]; then
	gum-print-err "Must run as root user"
    echo "\n"
	gum confirm "Switch to root user?" --affirmative="Root" --negative="Exit" --no-show-help && sudo su
	exit 1
fi

gum-print "Verify Pixel Art software cloned to path '/opt/pixel-art'..."
if [ -d "/opt/pixel-art" ]; then
    gum-print "Pixel Art found at path '/opt/pixel-art'."
else
    gum-print-err "Pixel Art not found at path '/opt/pixel-art'. Clone Pixel Art repo inside '/opt' and try again. Exiting."
    exit 1
fi

gum-print "==> Done"

############
# SETUP OS #
############

gum-header "Installing OS packages"

# Install Pixel Art APT packages
gum-print "Updating APT repositories..."
apt-get update -y

gum-print "Installing required APT packages..."
apt-get install python3-dev cython3 python3-pil ffmpeg python3-pyaudio git -y

gum-print "==> Done"
echo "\n"

##################
# SETUP FIRMWARE #
##################

gum-header "Configuring firmware"

# Disable sound for quality images
gum-print "Disabling sound subsystem for performance (USB speakers allowed)..."
sed -i 's/dtparam=audio=on/dtparam=audio=off/g' /boot/firmware/config.txt
echo "blacklist snd_bcm2835" >> /etc/modprobe.d/alsa-blacklist.conf

# Isolate RGB Bonnet pixel driver to single cpu
gum-print "Isolating RGB Bonnet pixel driver to single cpu..."
sed -i 's/$/ isolcpus=3/' /boot/firmware/cmdline.txt

# Setup Power Button
gum-print "Setting up power button..."
echo "dtoverlay=gpio-shutdown" >> /boot/firmware/config.txt

# Increase speaker volume
gum-print "Increase speaker volume to 80%..."
amixer -c UACDemoV10 sset PCM 80%

# Increase microphone capture volume
gum-print "Increase microphone capture volume to 80%..."
amixer -c HIDMediak sset Mic 80%

gum-print "==> Done"
echo "\n"

#############
# SETUP RGB #
#############

gum-header "Installing RGB Software"

# Download RGB software (TODO: change to git clone?)
gum-print "Downloading RGB matrix software..."
cd /opt
gum-spinner "Progress..." -- \
    curl -L https://github.com/hzeller/rpi-rgb-led-matrix/archive/7a503494378a67f3baa4ac680cecbae2703cc58f.zip -o rpi-rgb-led-matrix.zip && \
    unzip -q rpi-rgb-led-matrix.zip && \
    rm -rf rpi-rgb-led-matrix rpi-rgb-led-matrix.zip  && \
    mv rpi-rgb-led-matrix-7a503494378a67f3baa4ac680cecbae2703cc58f rpi-rgb-led-matrix

# Install RGB matrix python binding
gum-print "Installing RGB matrix python binding..."
cd /opt/rpi-rgb-led-matrix
make clean
make build-python
make install-python HARDWARE_DESC=adafruit-hat-pwm PYTHON=$(which python3)
chown -R $SUDO_USER:$(id -g $SUDO_USER) `pwd`

# Install RGB matrix utilities
gum-print "Installing RGB matrix utilities..."
cd /opt/rpi-rgb-led-matrix/utils
apt-get install libgraphicsmagick++-dev libwebp-dev -y
make led-image-viewer
mv led-image-viewer /usr/local/bin/
chmod 511 /usr/local/bin/led-image-viewer

gum-print "==> Done"
echo "\n"

###################
# SETUP PIXEL ART #
###################

gum-header "Installing Pixel Art Software"

# Install Pixel Art software
gum-print "Installing Pixel Art software..."
cd /opt/pixel-art
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
chown -R $SUDO_USER:$(id -g $SUDO_USER) `pwd`
cd /opt/rpi-rgb-led-matrix/bindings/python/
pip install .

# Set API keys as system and service environment variables
gum-print "Enter your Picovoice API Key"
PICOVOICE_TOKEN=$(gum input --placeholder "Picovoice API Key...")
echo "PICOVOICE_TOKEN=${PICOVOICE_TOKEN}" >> /etc/environment
sed -i "s/\"PICOVOICE_TOKEN=.*\"/\"PICOVOICE_TOKEN=${PICOVOICE_TOKEN}\"/g" /opt/pixel-art/config/pixel-art.service

gum-print "Enter your Retro Diffusion API Key"
RETRO_DIFFUSION_TOKEN=$(gum input --placeholder "Retro Diffusion API Key...")
echo "RETRO_DIFFUSION_TOKEN=${RETRO_DIFFUSION_TOKEN}" >> /etc/environment
sed -i "s/\"RETRO_DIFFUSION_TOKEN=.*\"/\"RETRO_DIFFUSION_TOKEN=${RETRO_DIFFUSION_TOKEN}\"/g" /opt/pixel-art/config/pixel-art.service

gum-print "Enter your OpenAI API Key"
OPENAI_API_KEY=$(gum input --placeholder "OpenAI API Key...")
echo "OPENAI_API_KEY=${OPENAI_API_KEY}" >> /etc/environment
sed -i "s/\"OPENAI_API_KEY=.*\"/\"OPENAI_API_KEY=${OPENAI_API_KEY}\"/g" /opt/pixel-art/config/pixel-art.service

# Setup pixel-art.service
gum-print "Creating pixel-art.service..."
gum-spinner "Progress..." -- \
    cp /opt/pixel-art/config/pixel-art.service /etc/systemd/system/pixel-art.service && \
    chmod 644 /etc/systemd/system/pixel-art.service && \
    systemctl daemon-reload && \
    systemctl enable pixel-art.service

gum-print "==> Done"
echo "\n"

##########
# REBOOT #
##########

# Reboot
gum-print "Rebooting now..."
reboot
