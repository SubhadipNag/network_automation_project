from threading import Thread

def connect(device):
    print(device)

    t1 = Thread(target=connect, args=("R2",))
    t2 = Thread(target=connect, args=("R3",))

    t1.start()
    t2.start()

    t1.join()
    t2.join()