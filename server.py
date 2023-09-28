from concurrent import futures
import grpc
import GRID_RPC_pb2
import GRID_RPC_pb2_grpc
from classes import Battlefield,Soldier,Missile
import os
from dotenv import load_dotenv

#Loading Environment variables
load_dotenv('Environment.env')

totalSimulationTime = 0
missileFrequency = 0
Commander = None

def pyToProtoList(reqArray,type): #type = 0 indicates a list of [x,y] co-ordinates. type = 1 indicates a 2D square matrix (grid) of order N
    # Populate the message with data from positions
    if(type==0):
        ans = GRID_RPC_pb2.intPairs()
        for pair in reqArray:
            int_pair = ans.positions.add()  # This adds a new IntPair to the repeated field
            int_pair.x, int_pair.y = pair
    else:
        ans = GRID_RPC_pb2.int2DArray()
        for row in reqArray:
            int_row = ans.rows.add()
            int_row.values.extend(row)
    return ans

class battleServicer(GRID_RPC_pb2_grpc.battleServicer):
    def battleGenerator(self, request, context):
        global battlefield 
        global totalSimulationTime
        global missileFrequency
        global Commander
        battlefield = Battlefield(request.size)
        battlefield.updateGridSoldiers(request.soldiers)
        totalSimulationTime = request.totalSimulationTime
        missileFrequency = request.missileFrequency
        for soldier in request.soldiers:
            if soldier.isCommander==True:
                Commander = Soldier(soldier.SoldierID,True,True,soldier.currentLocation,soldier.speed)
        return GRID_RPC_pb2.battleGenerationResponse(result=1)
    
    def missileLauncher(self, request, context):
        #Launching Missile
        missile = Missile(request.missileType,request.missileEpicenter,battlefield.gridSize)
        #Broadcast Message
        broadcast = Commander.missile_approaching(missile.positions,request.time,request.missileType)
        #Updating Grid
        print(f"Type : {request.missileType}\nEpicenter : {request.missileEpicenter}\nRed Zone : {missile.positions}")
        battlefield.updateGridRedZones(missile.positions)
        #Broadcasting it to all soldiers on client side
        return GRID_RPC_pb2.missileLauncherResponse(positions=pyToProtoList(broadcast[0],0),time=broadcast[1],type=broadcast[2])
    
    def commanderUpdater(self,request,context):
        newCommander = request.Commander
        Commander.SoldierID = newCommander.SoldierID
        Commander.currentLocation= newCommander.currentLocation
        Commander.speed = newCommander.speed
        return GRID_RPC_pb2.commanderUpdaterResponse(result=1)

    def gridUpdater(self,request,context):
        battlefield.updateGridSoldiers(request.soldiers)
        return GRID_RPC_pb2.gridUpdaterResponse(result=1)

    def printLayout(self,request,context):
        return GRID_RPC_pb2.printLayoutResponse(grid=pyToProtoList(battlefield.grid,1))




def serve():
    port = os.getenv('PORT')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    GRID_RPC_pb2_grpc.add_battleServicerServicer_to_server(battleServicer(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()