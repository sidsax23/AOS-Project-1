import grpc
import GRID_RPC_pb2
import GRID_RPC_pb2_grpc
import threading
import time
from classes import Soldier
import os
import sys
from random import randint
from colorama import just_fix_windows_console
from termcolor import colored
from dotenv import load_dotenv

#Loading Environment variables
load_dotenv('Environment.env')

# use Colorama to make Termcolor work on Windows too
just_fix_windows_console()



#Convert Python class to Proto Class
def pyToProto(soldier):
    protoSoldier = GRID_RPC_pb2.Soldier()
    protoSoldier.SoldierID = soldier.SoldierID
    protoSoldier.isCommander = soldier.isCommander
    protoSoldier.isAlive = soldier.isAlive
    protoSoldier.currentLocation.extend(soldier.currentLocation)
    protoSoldier.speed = soldier.speed
    return protoSoldier

#Convert Array of [x,y] coordinates from proto(intPairs) to python [type=0] or 2D Array from proto(int2DArray) to python [type=1]
def protoToPythonArr(protoArr,type):
    if type==0:
        return [[pair.x, pair.y] for pair in protoArr.positions]
    else:
        return [list(row.values) for row in protoArr.rows]


#Checking if soldier was hit
def was_hit(soldier,positions):
    if soldier.currentLocation in positions:
        return True
    return False

#Checking Status of soldiers
def status_all(positions,stub):
    for soldier in soldiers:
        if was_hit(soldier,positions):
            soldier.isAlive = False
    #Checking if Commander is dead
    for soldier1 in soldiers:
        if soldier1.isAlive==False and soldier1.isCommander:
            for soldier in soldiers:
                if soldier.isAlive:
                    soldier.isCommander=True
                    #Update commander on server side
                    stub.commanderUpdater(GRID_RPC_pb2.commanderUpdaterRequest(Commander=pyToProto(soldier)))
                    break
            soldier1.isCommander=False



def observer(M,stub,N):
    while True:
        os.system('cls')
        print("------------- BATTLEFIELD SIMULATOR -------------\n")
        print("\n1.) View Battlefield")
        print("\n2.) View Battalion")
        print("\n3.) Exit Simulator")
        option = int(input(f"\nEnter Command (1/2/3) : "))
        options = [1,2,3]
        if option not in options:
            print("\nInvalid Option. Please Retry. (Press enter to go back)")
            input()
            continue
        else:

            #View Battlefield (IMPLEMENTATION LEFT)
            if option==1:
                while True:
                    os.system('cls')
                    print("--------------------- BATTLEFIELD ---------------------\n")
                    #Print Battalion details
                    battlefield = stub.printLayout(GRID_RPC_pb2.printLayoutRequest(req=1))
                    grid = protoToPythonArr(battlefield.grid,1)
                    deadSoldiers=0
                    for soldier in soldiers:
                        if soldier.isAlive==False:
                            deadSoldiers+=1
                    print(f"\nBattle Status : {battleStatus}")
                    print(f"\nCasualties : {deadSoldiers}/{len(soldiers)}")
                    print(f"\nCurrent Iteration : {iteration}\n\nBattlefield:-")
                    print("Legend :-")
                    print(colored("R = Red Zone",'red'))
                    print(colored("D = Dead Soldier",'yellow'))
                    print("_ = Empty")
                    print(colored("<Number> : Soldier ID (Alive)\n",'green'))
                    for row in range(0,N):
                        for col in range(0,N):
                            elem = grid[row][col]
                            numSpaces = len(str(M))-len(str(abs(elem)))
                            spaces=""
                            color = 'green' #green - 
                            for i in range(0,numSpaces):
                                spaces+=" "
                            if elem == -2:
                                elem="R"
                                color='red' #red
                            elif elem == -1:
                                elem="D"
                                color='yellow' #yellow
                            elif elem == 0:
                                elem="_" 
                                color='white' #Default Color
                            print(colored(str(elem)+spaces,color),end='   ')
                        print("\n")
                    option = int(input(f"\n\nEnter 1 to return to simulator : "))
                    if option != 1:
                        print("\nInvalid Option. Please Retry. (Press enter to go back)")
                        input()
                        continue
                    else:
                        break
                continue

            #View Battalion
            elif option==2:
                while True:
                    os.system('cls')
                    print("------------------------- BATTALION -------------------------\n")
                    #Print Battalion details
                    liveCount=0
                    for soldier in soldiers:
                        if soldier.isAlive:
                            liveCount+=1
                    print(f"\n------- Total Soldiers : {M} --- Alive : {liveCount} --- Dead : {M-liveCount} -------\n")
                    for soldier in soldiers:
                        print(f"\nID:{soldier.SoldierID} Status:{'Alive' if soldier.isAlive else 'Dead'} Location[x,y]:[{soldier.currentLocation[0]},{soldier.currentLocation[1]}] Speed:{soldier.speed} {'(Commander)' if soldier.isCommander else ''}")
                    option = int(input(f"\n\nEnter 1 to return to simulator : "))
                    if option != 1:
                        print("\nInvalid Option. Please Retry. (Press enter to go back)")
                        input()
                        continue
                    else:
                        break
                continue

            #Exit
            elif option==3:
                break
    return 0

def war(missileCount,freq,stub,N,M):
    global iteration
    global battleStatus
    for i in range(0,missileCount):
        try:
            start=time.time()
            iteration=i+1
            #Launch Missile, then in the response get the data from Commander
            #Missile's type (random):
            missileType = randint(1,4)
            #Missile's epicenter on the grid (random):
            x_coord = randint(0,N-1)
            y_coord = randint(0,N-1)
            missileEpicenter = [x_coord,y_coord]
            broadcast = stub.missileLauncher(GRID_RPC_pb2.missileLauncherRequest(missileType=missileType,missileEpicenter=missileEpicenter,time=i+1)) #freq-missileCount gives the current iteration
            #Soldiers reacting to the broadcast by taking shelter
            positions = protoToPythonArr(broadcast.positions,0)
            for soldier1 in soldiers:
                if soldier1.isAlive:
                    soldierPositions=[]
                    for soldier in soldiers:
                        if soldier.isAlive:
                            soldierPositions.append(soldier.currentLocation)
                    soldier1.take_shelter(positions,N,soldierPositions)
            #Checking status and taking any other necssary action(s) (like re-electing Commander if dead)
            status_all(positions,stub)
            #Updating grid (Soldier Locations)
            battleStatus="Ongoing"
            deadSoldiers=0
            for soldier in soldiers:
                if soldier.isAlive==False:
                    deadSoldiers+=1
            if int(100*deadSoldiers/M) >= 50:
                battleStatus="Lost"
            #The last missile has hit the battlefield.
            if i==missileCount-1 and int(100*deadSoldiers/M) < 50:
                battleStatus="Won"
            protoSoldiers = []
            for soldier in soldiers:
                protoSoldiers.append(pyToProto(soldier))
            stub.gridUpdater(GRID_RPC_pb2.gridUpdaterRequest(soldiers=protoSoldiers))
            end=time.time()
            time.sleep(freq-int(end-start)) # Same as  : elapsedTime = end-start, then sleepTime=freq-elapsedTime
        except Exception as e:
            print(f"Exception occurred in war: {e}")



def main():
    #Getting host and port from env file
    hostName=os.getenv('HOST_NAME') # Replace localhost in env file according to the setup being used (IP Address)
    port=os.getenv('PORT')
    channel = grpc.insecure_channel(hostName+':'+port)  
    stub = GRID_RPC_pb2_grpc.battleServicerStub(channel)
    while True:
        os.system('cls')
        print("-------------BATTLEFIELD SIMULATOR-------------\n")
        print("Enter the Battlefield Grid Size (N) : ")
        try:
            N = int(input())
        except:
            print("\nGrid Size is needed! Please Retry. (Press enter to go back)")
            input()
            continue
        if not isinstance(N,int) or N<4 :
            print("\nInvalid value entered for N. N should be at least 4. Please Retry. (Press enter to go back)")
            input()
            continue
        print("\nEnter the Number of Soldiers (M) : ")
        try:
            M = int(input())
        except:
            print("\nNumber of Soldiers is needed! Please Retry. (Press enter to go back)")
            input()
            continue
        if not isinstance(M,int) or not 10<=M<=N*N :
            print(f"\nInvalid value entered for M. Must be between 10 and {N*N}(N*N). Please Retry. (Press enter to go back)")
            input()
            continue
        #Initializing soldiers on client side
        protoSoldiers = [] # To convert to proto class and transfer to server
        global soldiers # For use on client side
        soldiers = [] 
        positions = []
        #Selecting a random soldier as Commander initially
        CommanderID = randint(1,M)
        for i in range(1,M+1):
            #Soldier's initial location on the grid (random): Ensuring no position has more than 1 soldier
            x_coord = randint(0,N-1)
            y_coord = randint(0,N-1)
            while True:
                if [x_coord,y_coord] in positions:
                    x_coord = randint(0,N-1)
                    y_coord = randint(0,N-1)
                else:
                    break
            positions.append([x_coord,y_coord])
            location = [x_coord,y_coord]
            #Soldier's speed (random):
            speed=randint(0,4)
            #Determining Commander Status:
            isCommander=False
            if i==CommanderID:
                isCommander=True
            soldier = Soldier(i,isCommander,True,location,speed)
            soldiers.append(soldier)
            protoSoldiers.append(pyToProto(soldier))
        print("\nEnter the Missile Frequency (t) (seconds after which a missile is fired) : ")
        try:
            t = int(input())
        except:
            print("\nMissile Frequency is needed! Please Retry. (Press enter to go back)")
            input()
            continue
        if not isinstance(t,int) or t<=0 :
            print("\nInvalid value entered for t. Please Retry. (Press enter to go back)")
            input()
            continue
        print("\nEnter the Total Battle Time (T) (seconds) : ")
        try:
            T = int(input())
        except:
            print("\nTotal Battle Time is needed! Please Retry. (Press enter to go back)")
            input()
            continue
        if not isinstance(T,int) or T<t :
            print(f"\nInvalid value entered for T. Must be at least {t}(t). Please Retry. (Press enter to go back)")
            input()
            continue
        break
    #Initializing Battle:
    stub.battleGenerator(GRID_RPC_pb2.battleGenerationRequest(size=N,soldiers=protoSoldiers,totalSimulationTime=T,missileFrequency=t,CommanderID=int(CommanderID)))
    missileCount = int(T/t)
    thread1 = threading.Thread(target=observer,args=(M,stub,N))
    thread2 = threading.Thread(target=war,args=(missileCount,t,stub,N,M))
    thread2.start()
    thread1.start()
    thread1.join()
    if thread2.is_alive():
        print("\nWaiting for simulation to finish...")
    thread2.join()
    print("\nSimulation Terminated.\n") 
    sys.exit()


if __name__ == '__main__':
    main()