devs = int(input())
requests_for_conf = int(input())
conf_dict = {}
for i in range(requests_for_conf):
    dev1, dev2 = input().split()
    if dev1 not in conf_dict:
        conf_dict[dev1] = list(dev2)
    else:
        conf_dict[dev1].append(dev2)
for dev in range(devs):
    if str(dev) not in conf_dict.keys():
        if str(dev) not in conf_dict.values():
                conf_dict[str(dev)] = ('alone')
for dev, guests in conf_dict.items():
    for guest in guests:
        if guest in conf_dict:
            if conf_dict[guest] not in ['alone', 'replaced']:
                conf_dict[guest].append(dev)
                conf_dict[dev] = 'replaced'
for dev, guests in conf_dict.items():
    if guests not in ['alone', 'replaced']:
        for guest in guests:
            if guest in conf_dict:
                conf_dict[guest] = 'replaced'
room_kinds = int(input())
rooms = {}
for room in range(room_kinds):
    room_vmestimost, room_amount = [int(i) for i in input().split()]
    rooms[room_vmestimost] = room_amount
devs_in_room = []
wanna_meet = 0
for dev, guests in conf_dict.items():
    if guests != 'replaced':
        wanna_meet += 1
        for room_vmestimost, room_amount in rooms.items():
            if room_amount > 0:
                if guests == 'alone':
                    peoples = 1
                else:
                    peoples = len(guests) + 1
                if  peoples <= room_vmestimost:
                    rooms[room_vmestimost] -= 1
                    devs_in_room.append(dev)
                    break
            else:
                continue
if len(devs_in_room) == wanna_meet:
    print(1)
else:
    print(0)
