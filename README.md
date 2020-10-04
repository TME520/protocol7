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

This dashboard is generated by Protocol/7 and can be automatically stored on Azure Blob Storage and/or AWS S3 bucket.

### BlinkStick USB RGB LED light

Protocol/7 can control one or more BlinkStick USB RGB LED light. The models currently supported are [BlinkStick Nano](https://www.blinkstick.com/products/blinkstick-nano) and [BlinkStick Flex](https://www.blinkstick.com/products/blinkstick-flex).

You need to setup [p7devices](https://github.com/TME520/p7devices) in order to enable a BlinkStick on your local laptop/desktop computer.

## Setup

### Deploy a Protocol/7 stack in AWS

#### Prerequisites

1. You need a AWS account. You can create one for free and you can use some resources for free too,
2. You need a Sumologic account. You can also create one for free,
3. You need a Slack workspace. You can create one for free too,
4. You need a BlinkStick. These must be ordered from UK [here](https://www.blinkstick.com/),
5. The deployment must be triggered from Jenkins.

#### Preparation

1. Clone [my Jenkins repo](https://github.com/TME520/jenkinslab) and [my CloudFormation repo](https://github.com/TME520/cloudformation),
2. Setup your own [Jenkins](https://www.jenkins.io/),
3. Create a Jenkins pipeline named `prepareP7ParamsFile`,
4. In the Jenkins home directory (usually /var/lib/jenkins), locate its `config.xml` file (should be `/var/lib/jenkins/jobs/prepareP7ParamsFile/config.xml`) and [update it with this content](https://github.com/TME520/jenkinslab/blob/master/declarative/prepareP7ParamsFile.config.xml),
5. Create another Jenkins pipeline named `deployProtocol7`,
6. In the Jenkins home directory, locate its `config.xml` file and [update it with this content](https://github.com/TME520/jenkinslab/blob/master/declarative/deployProtocol7.config.xml),
7. Time to configure some credentials: `slack_token` (secret text), `sumo_endpoint` (secret text) and `aws_access_key` (username with password).

#### Deployment

1. Run Jenkins pipeline `prepareP7ParamsFile` and wait for it to complete,
2. Go to the AWS console, CloudFormation | Outputs and keep note of the information displayed there.

### Protocol/7 Docker image

N/A

### Run Protocol/7 locally

1. Download and install [AWS DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html),
2. Install OpenJDK

```
$ apt install openjdk-14-jre
```

3. Install AWS CLI

```
$ apt install awscli
```

4. Configure AWS access (required even for local DynamoDB)

`$ aws configure`

```
[default]
aws_access_key_id = AAAABBBBCCCCDDDD
aws_secret_access_key = EEEEFFFFGGGGHHHH
region = ap-southeast-2
```

5. Check your config

```
$ aws configure list
```

6. Start DynamoDB

`nohup java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -port 8001 > foo.out 2> foo.err < /dev/null &`

7. Install Python3

`$ apt install build-essential libssl-dev libffi-dev python3 python3-pip python3-dev python3-venv python3-pil.imagetk`

8. Install Python pip and some modules

`pip3 install --upgrade pip`

`pip-3.6 install cozmo exchangelib slackclient blinkstick sklearn pandas nltk joblib argparse boto3 colorama notify2 azure-storage-blob azure-mgmt-compute azure-mgmt-storage azure-mgmt-resource azure-keyvault-secrets azure-storage-blob requests_toolbelt requests azure-devops msrest`

`pip-3.6 install --user 'cozmo[camera]'`

9. Clone the Protocol/7 repository

`git clone https://github.com/TME520/protocol7.git`

10. Create a startup file and follow the configuration instructions from the README file

```
cd ./protocol7/
cp -pv ./startTemplate.sh.template ./startProtocol7.sh
chmod +x ./startProtocol7.sh
```

11. Start Protocol/7

`nohup ./startProtocol7.sh > foo.out 2> foo.err < /dev/null &`

12. Clone the Persona/7 repository

`git clone https://github.com/TME520/persona7.git`

13. Create a startup file and follow the configuration instructions from the README file

```
cd ./persona7/
cp -pv ./startTemplate.sh.template ./startPersona7.sh
chmod +x ./startPersona7.sh
```

14. Start Persona/7

`nohup ./startPersona7.sh > foo.out 2> foo.err < /dev/null &`

15. Clone the p7devices repository

`git clone https://github.com/TME520/p7devices.git`

16. Create a startup file and follow the configuration instructions from the README file

```
cd ./p7devices/bstick_nano/
cp -pv ./startBStick.sh.template  ./startBStick.sh
chmod +x ./startBStick.sh
```

17. Start BlinkStick

### Deploy a Protocol/7 stack in Azure

N/A

### Deploy a Protocol/7 stack in Google Cloud

N/A

## Usage
