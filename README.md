# protocol/7
Protocol/7
## Setup
### Android Debug Bridge
```
$ cd $HOME/Downloads
$ wget https://dl.google.com/android/repository/platform-tools-latest-linux.zip
$ unzip ./platform-tools-latest-linux.zip
$ mkdir android-sdk-linux
$ mv ./platform-tools android-sdk-linux
$ cd android-sdk-linux/platform-tools
$ ls adb
$ mv /home/tme520/Downloads/android-sdk-linux/ /home/tme520/
$ vi ~/.bashrc
```
`export PATH=${PATH}:~/android-sdk-linux/platform-tools`
```
$ source ~/.bashrc
$ which adb
```
### Python
`$ apt install build-essential libssl-dev libffi-dev python3 python3-pip python3-dev python3-venv python3-pil.imagetk`
### PIP modules
`$ pip3 install --user 'cozmo[camera]'`

`$ pip3 install cozmo exchangelib slackclient blinkstick sklearn pandas nltk joblib argparse boto3 colorama notify2 azure-storage-blob azure json requests_toolbelt requests azure-devops msrest`
### DynamoDB
```
$ mkdir $HOME/.aws/
$ vi $HOME/.aws/credentials
$ apt install openjdk-14-jre
```
```
[default]
aws_access_key_id = AAAABBBBCCCCDDDD
aws_secret_access_key = EEEEFFFFGGGGHHHH
region = ap-southeast-2
```
### Blinkstick
Use `lsusb` in order to get idVendor and idProduct.

`$ vi /etc/udev/rules.d/99-blinkstick.rules`

`SUBSYSTEM=="usb", ATTR{idVendor}=="20a0", ATTR{idProduct}=="41e5", MODE="666"`

`$ /etc/init.d/udev restart`
## Usage
