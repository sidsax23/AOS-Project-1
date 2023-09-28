Languages neeeded:
Python 3

Following packages need to be installed : 
pip install grpcio
pip install grpcio-tools
pip install protobuf
pip install colorama
pip install termcolor
Pip install dotenv

The proto file has already been compiled but the following command can be run on the proto file (if not complied) :
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./GRID_RPC.proto

Flow :-
1.)Set up the enciornment (Host (localhost/server IP Address) and port name)
2.)Run server file : python server.py
3.)Run client file python client.py

