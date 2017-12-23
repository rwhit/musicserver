from radioController import RadioController
rc = RadioController()
data = rc.get_latest()
print(data)
print("paused? " + str(rc.is_paused()))
