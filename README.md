# Protocol/7
Skynet, but friendlier. For now.
## Presentation
### Where does the name come from ?
*Protocol Seven* is a central piece in the 1998 [*Serial Experiments Lain*](https://en.wikipedia.org/wiki/Serial_Experiments_Lain) Japanese anime TV series. In a nutshell, it's a network protocol designed by *Masami Eiri* that allow people to use a natural phenomenon known as the *Schumann resonances* to connect to the *Wired* (an enhanced Internet) directly without a computer, by using a microchip interface called the *Psyche chip*.

*Masami Eiri* illicitly included a backdoor enabling him to control the whole system at will and embedded his own mind into the network. Because of this, he was fired by *Tachibana General Laboratories*, and was found dead not long after. He believes that the only way for humans to evolve even further and develop even greater abilities is to absolve themselves of their physical and human limitations, and to live as virtual entities — or avatars — in the *Wired* for eternity.
### Crime shows & robots
I love crime shows so much that I saw every episode of the 14 seasons from [*Forensic Files*](https://en.wikipedia.org/wiki/Forensic_Files), plus most of the [*Cold Case Files*](https://en.wikipedia.org/wiki/Cold_Case_Files) and [*Faites entrer l'accusé*](https://fr.wikipedia.org/wiki/Faites_entrer_l%27accus%C3%A9) episodes.
### Good humans don't scale
```
“It occurs to me that our survival may depend upon our talking to one another.”
```
― Dan Simmons, Hyperion
As much as we care for one another, truth is a lot of people, young or old, are left completely to themselves to go through life and hardships.
### A guardian angel for everyone
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
