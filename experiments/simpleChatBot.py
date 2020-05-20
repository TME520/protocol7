import time
import os
import re
from slackclient import SlackClient

BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
CHANNEL_NAME = "example-channel"

def main():
    # Create the slackclient instance
    sc = SlackClient(BOT_TOKEN)

    # Connect to slack
    if sc.rtm_connect():
        # Send first message
        sc.rtm_send_message(CHANNEL_NAME, "I'm ALIVE!!!")

        while True:
            # Read latest messages
            for slack_message in sc.rtm_read():
                message = slack_message.get("text")
                user = slack_message.get("user")
                if not message or not user:
                    continue
                sc.rtm_send_message(CHANNEL_NAME, "<@{}> wrote something...".format(user))
            # Sleep for half a second
            time.sleep(0.5)

if __name__ == '__main__':
    main()