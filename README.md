# BluetoothQuizController
A first-come-first-server system.

The server, designed to run under Python3, uses rfcomm to communicate with clients.
MIT App Inventor has been used as a convenient way of designing an Android client,
although any appropriate technology may be used.

Once connected, the client needs to supply the quizer's name before proceeding.
A button at the client may be used to signal the quizer's desire to answer a question.
That request is signalled by sending '9' to the server.  The server takes care of locking-out
other quizers.
Control of the server is via UNIX signals, delivered by the Bash wrapper.  Security has
not been implemented.
