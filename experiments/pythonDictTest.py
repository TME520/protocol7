eventsList = {
    'UF8442X5F':{'ts': 1550045118.000300, 'expires': 1550111111.000300, 'option1': 'Yes', 'action1': 'Albert', 'option2': 'No', 'action2': 'Bertrand', 'option3': None, 'action3': 'Corentin', 'step': 'ping'},
    'UFX10C9A8':{'ts': 1550056556.000300, 'expires': 1550111111.000300, 'option1': 'Yes', 'action1': 'Didier', 'option2': 'No', 'action2': 'Eric', 'option3': None, 'action3': None, 'step': 'ping'}
}

print("=PING=")
for key in eventsList:
    print("\n--- " + key + " ---")
    print("ts: " + str(eventsList[key]['ts']))
    print("expires: " + str(eventsList[key]['expires']))
    print("o1: " + str(eventsList[key]['option1']))
    print("a1: " + str(eventsList[key]['action1']))
    print("o2: " + str(eventsList[key]['option2']))
    print("a2: " + str(eventsList[key]['action2']))
    print("o3: " + str(eventsList[key]['option3']))
    print("a3: " + str(eventsList[key]['action3']))
    print("step: " + eventsList[key]['step'])

eventsList['POPOL'] = {'ts': 1550056556.000300, 'expires': 1550111111.000300, 'option1': 'Low', 'action1': 'Fabien', 'option2': 'Medium', 'action2': 'Georges',  'option3': 'High', 'action3': 'Henri', 'step': 'ping'}

targetUser = 'UFX10C9A8'

eventsList['UFX10C9A8']['step'] = 'pong'

print("\n\n=PONG=")
for key in eventsList:
    print("\n--- " + key + " ---")
    print("ts: " + str(eventsList[key]['ts']))
    print("expires: " + str(eventsList[key]['expires']))
    print("o1: " + str(eventsList[key]['option1']))
    print("a1: " + str(eventsList[key]['action1']))
    print("o2: " + str(eventsList[key]['option2']))
    print("a2: " + str(eventsList[key]['action2']))
    print("o3: " + str(eventsList[key]['option3']))
    print("a3: " + str(eventsList[key]['action3']))
    print("step: " + eventsList[key]['step'])

if 'TME520' in eventsList:
    print("\nTME520 found !")
else:
    print("\nTME520 not found !")

if 'UFX10C9A8' in eventsList:
    print("\nUFX10C9A8 found !")
else:
    print("\nUFX10C9A8 not found !")