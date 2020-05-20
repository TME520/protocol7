from exchangelib import DELEGATE, Account, Credentials

credentials = Credentials(
    username='xxx\\yyy',  # Or myusername@example.com for O365
    password='zzz'
)
account = Account(
    primary_smtp_address='xxxx', 
    credentials=credentials, 
    autodiscover=True, 
    access_type=DELEGATE
)

my_folder = account.inbox / 'Sumo'
unreadSumoAlerts = my_folder.unread_count
print("Unread emails: " + str(unreadSumoAlerts))
for i in my_folder.all().order_by('-datetime_received')[:unreadSumoAlerts]:
    print(i.subject)
