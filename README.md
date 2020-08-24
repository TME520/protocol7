# Protocol/7

Protocol/7 (P7) is an Open Source GPLv3 web monitoring system that can:

- Generate a nice HTML dashboard showing the status of your web apps,
- Control a BlinkStick USB RGB LED light that changes color depending on the condition of your services,
- Send messages and alerts to Slack,
- Send its logs to Sumologic,
- Communicate with you via a ex-Anki / Digital Dream Labs Cozmo robot,
- Monitor your mailbox.

## Presentation

### Where does the name come from ?

*Protocol Seven* is a central piece in the 1998 [*Serial Experiments Lain*](https://en.wikipedia.org/wiki/Serial_Experiments_Lain) Japanese anime TV series. In a nutshell, it's a network protocol designed by *Masami Eiri* that allow people to use a natural phenomenon known as the *Schumann resonances* to connect to the *Wired* (an enhanced Internet) directly without a computer, by using a microchip interface called the *Psyche chip*.

*Masami Eiri* illicitly included a backdoor enabling him to control the whole system at will and embedded his own mind into the network. Because of this, he was fired by *Tachibana General Laboratories*, and was found dead not long after. He believes that the only way for humans to evolve even further and develop even greater abilities is to absolve themselves of their physical and human limitations, and to live as virtual entities — or avatars — in the *Wired* for eternity.

### The dashboard

![Protocol/7 dashboard preview](p7dashboard01.png)

Protocol/7 dashboard is made of cards (one per monitored URL) and shows the following info:

- Application name & environment,
- Failtage: failure percentage over the last 6 test cycles,
- Response time in seconds over the last 6 test cycles,
- The status of the service, with the time and date of the current failure if required,
- A link to the current deployment job (in Azure DevOps).

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
Download and install [AWS DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html).

```
$ apt install openjdk-14-jre
$ aws configure
```

```
[default]
aws_access_key_id = AAAABBBBCCCCDDDD
aws_secret_access_key = EEEEFFFFGGGGHHHH
region = ap-southeast-2
```

```
aws configure list
```

### Blinkstick

Plug your Blinkstick Nano in a USB port.

Use `lsusb` in order to get idVendor and idProduct.

`$ vi /etc/udev/rules.d/99-blinkstick.rules`

`SUBSYSTEM=="usb", ATTR{idVendor}=="20a0", ATTR{idProduct}=="41e5", MODE="666"`

`$ /etc/init.d/udev restart`

## Usage

- I'm currently preparing a set made of 2 Jenkins pipelines and a CloudFormation template to get P7 deployed to AWS,
- I will create a Docker image of this once I get the deployment right.