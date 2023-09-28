class Soldier:
    #Private Members
    __SoldierID = None #Range from 1 to Soldier Count
    __isCommander = None  # Boolean
    __isAlive = None     # Boolean
    __currentLocation = None  #x,y coordinates in range ([0,N-1],[0,N-1])
    __speed = None #Range = [0,4]

    #Constructor
    def __init__(self,SoldierID,isCommander,isAlive,currentLocation,speed):
        self.__SoldierID=SoldierID
        self.__isCommander=isCommander
        self.__isAlive=isAlive
        self.__currentLocation=currentLocation
        self.__speed=speed

    #Getters 
    @property
    def SoldierID(self):
        return self.__SoldierID

    @property
    def isCommander(self):
        return self.__isCommander
    
    @property
    def isAlive(self):
        return self.__isAlive

    @property
    def currentLocation(self):
        return self.__currentLocation

    @property
    def speed(self):
        return self.__speed


    #Setters
    @isCommander.setter
    def isCommander(self, value):
        if isinstance(value, bool):
            self.__isCommander = value
        else:
            raise ValueError("isCommander must be a boolean value.")

    @isAlive.setter
    def isAlive(self, value):
        if isinstance(value, bool):
            self.__isAlive = value
        else:
            raise ValueError("isAlive must be a boolean value.")

    @currentLocation.setter
    def currentLocation(self, value):
        if len(value)==2:
            self.__currentLocation = [int(value[0]),int(value[1])]
        else:
            raise ValueError("currentLocation must contain x,y coordinates.")
        
    #Can only occur for commander object on server side (if killed)
    @SoldierID.setter
    def SoldierID(self, value):
        if self.__isCommander==False:
            raise TypeError("Only Commander can change his/her Soldier ID.")
        else:
            if isinstance(value, int):
                self.__SoldierID = value
            else:
                raise ValueError("SoldierID must be an integer value.")
    
    #Can only occur for commander object on server side (if killed)
    @speed.setter
    def speed(self, value):
        if self.__isCommander==False:
            raise TypeError("Only Commander can change his/her speed")
        else:
            if 0<=value<=4:
                self.__speed = value
            else:
                raise ValueError("Speed must be an integer value between 0 and 4 (inclusive).")


    #Sending Warning
    def missile_approaching(self,positions,time,type):
        if(self.__isCommander):
            return positions,time,type
        else:
            raise TypeError("Only Commander may issue a warning.")
    
    #Taking Shelter
    def take_shelter(self,redZonePositions,N,soldierPositions): # N = Grid size
        if self.__currentLocation in redZonePositions and self.__speed>0:
            curr_x = self.__currentLocation[0]
            curr_y = self.__currentLocation[1]
            foundFlag=0
            for speedLevel in range(0,self.__speed+1):
                for row in range(curr_x-speedLevel,curr_x+speedLevel+1):
                    for col in range(curr_y-speedLevel,curr_y+speedLevel+1):
                        if 0<=row<=N-1 and 0<=col<=N-1 and [row,col] not in redZonePositions and [row,col] not in soldierPositions:
                            self.__currentLocation=[row,col]
                            foundFlag=1
                            break
                    if foundFlag==1:
                        break
                if foundFlag==1:
                        break


        
    

    
class Battlefield:
    #Private Members
    __grid = None #0 represents blank, -1 represents a dead solider, -2 represents red zone. Any number >=1 represents Soldier ID

    #Constructor
    def __init__(self,size):
        self.__grid=[[0 for _ in range(size)] for _ in range(size)] #Creating the grid 
    
    #Getters 
    @property
    def gridSize(self):
        return len(self.__grid)
    
    @property
    def grid(self):
        return self.__grid

    
    #Updating Status
    def updateGridSoldiers(self,Soldiers):
        for soldier in Soldiers:
            if(soldier.isAlive):
                self.__grid[soldier.currentLocation[0]][soldier.currentLocation[1]]=soldier.SoldierID
            else:
                self.__grid[soldier.currentLocation[0]][soldier.currentLocation[1]]=-1
    
    def updateGridRedZones(self,positions):
        #Clearing any existing red zone
        for x_coord in range(0,len(self.__grid)):
            for y_coord in range(0,len(self.__grid)):
                if(self.__grid[x_coord][y_coord]==-2):
                    self.__grid[x_coord][y_coord]=0
        #Updating new red zone
        for position in positions:
            self.__grid[position[0]][position[1]]=-2
     

class Missile:
    #Private Members
    __type = None #1,2,3,4
    __positions = [] 
    __epicenter = None #Coordinates of the epicenter of the missile

    #Constructor
    def __init__(self,type,epicenter,N): # N = Grid size
        self.__type=type
        self.__epicenter=epicenter
        epi_x = epicenter[0]
        epi_y = epicenter[1] 
        self.__positions=[]
        for iteration in range(0,type):
            for row in range(epi_x-iteration,epi_x+iteration+1):
                for col in range(epi_y-iteration,epi_y+iteration+1):
                    #Only including valid coordinates
                    if 0<=row<=N-1 and 0<=col<=N-1 and [row,col] not in self.__positions:
                        self.__positions.append([row,col])
    
    #Getters 
    @property
    def positions(self):
        return self.__positions
