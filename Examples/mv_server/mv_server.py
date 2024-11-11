import zmq

context = zmq.Context()

# PULL socket for gathering data from producers
pull_socket = context.socket(zmq.PULL)
pull_socket.bind("tcp://*:5555")

# REP socket to serve the latest data to a client
rep_socket = context.socket(zmq.REP)
rep_socket.bind("tcp://*:5556")

last_received_message = b""  # Initialize as bytes

poller = zmq.Poller()
poller.register(pull_socket, zmq.POLLIN)
poller.register(rep_socket, zmq.POLLIN)

while True:
    socks = dict(poller.poll())

    # Check for new data from producers
    if pull_socket in socks:
        last_received_message = pull_socket.recv()  # receive as bytes
        print(f"Received data of length: {len(last_received_message)} bytes")

    # Check for request for latest data from client
    if rep_socket in socks:
        _ = rep_socket.recv()  # receive request (even this can be bytes)
        print("sending data");
        rep_socket.send(last_received_message)  # send latest data (bytes)
