# BluetoothQuizController
A first-come-first-server system.

The server, designed to run under Python3, uses rfcomm to communicate with clients.
MIT App Inventor has been used as a convenitent way of designing an Android client,
although any appropriate technology may be used.

Once connected, the client needs to supply the quizers name before proceeding.
A button at the client may be used to signal the quizer's desire to answer a question.
That request is signalled by sending '9' to the server.