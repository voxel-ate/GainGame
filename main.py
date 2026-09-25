import os, time, math
import sqlite3
import hashlib
import json


# runtime variables
debugging = False

# hardcoded values
max_age = 99
min_age = 16
userDataPath = "DATA/userdata.db"

def goalsPath(user):
    return f"DATA/usergoals/{user}/goals.json"
def macrogoalsPath(user):
    return f"DATA/usergoals/{user}/macrogoals.json"
def settingsPath(user):
    return f"DATA/usergoals/{user}/settings.json"

conn = sqlite3.connect(userDataPath)
cursor = conn.cursor()

remove_profile_command = "DELETE FROM PROFILES WHERE ACC_NAME = "
# In most cases, along with the profile row in Profiles, remove all associated (by name) data in other tables

BannedTextInputs = ["+"]
profile_select_input_message = "\nType the username of the profile you want to sign in to, or type '+' to create a new profile\n"
prompts_dictionary = {  "ACC_NAME": "\nMake an account name/handle. This will be a unique identifer for your profile: ",
                        "ACC_PASSWORD": "\nOptionally, set a strong password / PIN for your profile. Don't lose it, passwords cannot be recovered or reset (yet)\n",
                        "USER_NAME": "\nSet a display name for yourself: ",
                        "USER_AGE": "\nEnter your Age. This would be used in calculations such as calorie planning and growth projection: ",
                        "USER_GENDER": "\nChoose a Gender (M/F): ",
                        "USER_HEIGHT":  "\nEnter your height in centimetres: ",
                        "USER_WEIGHT":  "\nEnter your weight in kilograms: ",
                        "USER_MOTIVE": "\nWhat's your main motivation for signing up? " }

def ClearTerminal(): os.system('cls' if os.name == 'nt' else 'clear')

# Reset 'Profiles' if I need to
if debugging:
    if input("RESET Profiles Table?") == "y":
        cursor.execute("DROP TABLE Profiles")

def CreateDirectoryIfNotExists(directory):
    try:
        os.mkdir(directory)
    except FileExistsError:
        pass

def CreateJsonIfNotExists(filepath):
    if CheckIfFilePathExists(f"{filepath}") == False: # check if goals.json exists - If so, leave it alone - If not, create with an empty table
        os.system(f"echo {'{}'} > {filepath}")

def CheckIfFilePathExists(filepath):
    try:
        os.mkdir(filepath)
        os.rmdir(filepath)
        return False
    except FileExistsError:
        return True

ListProfilesCommand = "SELECT ACC_NAME FROM Profiles ORDER BY ACCOUNTID"
CreateProfilesStatement = """ CREATE TABLE IF NOT EXISTS "Profiles" (
	"ACCOUNTID"	INTEGER NOT NULL UNIQUE,
	"ACC_NAME"	TEXT NOT NULL UNIQUE COLLATE NOCASE,
	"ACC_PASSWORD"	TEXT COLLATE BINARY,
	"ACC_SIGNUPDATEANDTIME"	TEXT,
	"USER_NAME"	TEXT,
	"USER_AGE"	INTEGER CHECK(16 <= "USER_AGE" AND "USER_AGE" <= 99),
	"USER_GENDER"	TEXT CHECK("USER_GENDER" LIKE 'M' OR "USER_GENDER" LIKE 'F'),
	"USER_WEIGHT"	REAL,
	"USER_HEIGHT"	REAL,
	"USER_MOTIVE"	TEXT,
	"USER_EXP"	INTEGER DEFAULT 0,
	"USER_LEVEL"	INTEGER DEFAULT 1,
	PRIMARY KEY("ACCOUNTID" AUTOINCREMENT),
	CONSTRAINT "CheckCharactersAllowed" CHECK("ACC_NAME" NOT GLOB '*[^A-Za-z0-9_]*' AND "ACC_NAME" NOT LIKE '% %')
); """
cursor.execute(CreateProfilesStatement)
conn.commit()


# accounts_present = 0
# for i in ListProfilesCommand: 
#     accounts_present += 1 
#
# if accounts_present <= 0:
#     print("Welcome!")
# else:
#     print("Welcome back!")

def TimedMessage(message, duration = 0, newline = 0, doesDisappear = False, focus = False):  # The latter arguments are given default values so they don't always have to be fufilled
    # message = string message. 
    # duration = time the program is halted for to display the message.
    # newline = An integer telling how many newlines should follow the message
    # doesDisappear = If the terminal should be cleared after the messages duration is over
    # focus = If the terminal should be cleared beforehand to show the message
    
    if focus:
        ClearTerminal()
    print(message)
    for i in range(0,newline):
        print("")
    time.sleep(duration)

    if doesDisappear:
        ClearTerminal()

def GetDataFromUser(user, attribute, table = "Profiles"):
    data = None

    try:
        for i in cursor.execute(f"SELECT {attribute} FROM {table} WHERE ACC_NAME = ('{user}')"):  # Still needs to be a for loop despite returing one entry ☠  
            data = i[0]  # [0] because sql returns data in tuple format
        return data
    
    except TypeError:
        print("There was an error retrieving data")
        raise sqlite3.DatabaseError

def HashString(string):
    string = string.encode("utf-8") # Convert to bytestring

    h = hashlib.new('sha256') # sha256 hashing method
    h.update(string)

    return str(h.hexdigest()) # return hashed string to be stored

def AuthenticateUser(user):
    GetPasswordCommand = f"SELECT ACC_PASSWORD FROM Profiles WHERE ACC_NAME = ('{user}')"

    for password in cursor.execute(GetPasswordCommand):
        if password[0] != None: # If password is not null          
            input_accepted = False    
            
            while not input_accepted:
                passkey = input("\nEnter Password, or enter nothing to log into a different profile: ")
                
                if len(passkey) == 0: # Return to Profile Selection
                    break
                               
                elif HashString(passkey) == password[0]: # If the password matches the hash exactly...
                    input_accepted = True
                    time.sleep(1.2)

                    print("User authenticated! Signing in...\n")
                    return input_accepted

                else:
                    time.sleep(1.2)
                    print("Wrong Password. Try again\n")
                    time.sleep(.8)

            

        else: # If password is null
            TimedMessage("Account has no password, signing in...", .5)
            return True
           
def AskForField(attribute, user):  # user = acc_name, and indicates which users data should be updated  
    if debugging: print("selected field:", attribute)
    inputVerified = False
    Input = None
    
    while not inputVerified:
        inputVerified = True  # Innocent until proven guilty

        try:
            Input = input(prompts_dictionary[attribute]) 

        except:
            Input = input(f"{attribute}:")
            # If the attribute has no associated prompt, just display the attribute name so the user know what the input is for
        
        try:  # In a Try/Except, if anything fails the except clause is ran and the input won't be verified           
            
                    
            if Input == "/skip" and attribute == "ACC_NAME":
                inputVerified = False
                print("Can't leave this field blank!")
                
            elif Input == "/skip":  # if user wants to skip and is a skippable field
                Input = None
                print("Skipping field... (you can still fill this in later)")

            elif len(Input) < 1:  # if only whitespace and whether it's a skippable field
                inputVerified = False
                if attribute == "ACC_NAME":
                    print("Can't leave this particular field blank!")
                else:
                    print("If you wish to skip this field, type /skip")               
            
            else:                        
                try:
                    command = None

                    if user is not None and inputVerified: # 'Update' the existing entry with the users account name              
                        if attribute == "USER_GENDER":
                            Input = Input.upper()

                        if attribute == "ACC_PASSWORD":
                            ClearTerminal()
                            confirm_password = input("Confirm your password:") 

                            if Input == confirm_password:                  
                                Input = HashString(Input)
                                print("Storing password...")
                                time.sleep(.8)

                            else:
                                inputVerified = False
                                print("That wasn't the same password. Try again")
                                continue

                        command =  f"UPDATE Profiles SET {attribute} = '{Input}' WHERE ACC_NAME = '{user}'"
                        cursor.execute(command)
                        conn.commit()

                    else: # Make a new entry
                        command =  f"INSERT INTO Profiles ({attribute}) VALUES ('{Input}')"

                        cursor.execute(command)
                        conn.commit()
                        user = Input 
                    
                except sqlite3.IntegrityError as message: # An integrity error will be raised if the data doesn't follow index / check constraints                                       
                    if str(message).count("UNIQUE constraint failed") >= 1:
                        inputVerified = False
                        print("This username is taken")
                        time.sleep(.3)

                    elif attribute == "ACC_NAME":
                        inputVerified = False
                        print("Account name can only contain letters, numbers, and underscores\n")
                        time.sleep(.3)

                    else:
                        inputVerified = False
                        print("Input couldn't be accepted. Try checking your spelling?")
                        time.sleep(.3)

        except:
            inputVerified = False
            print("Input couldn't be accepted. Try checking your spelling?")

    return Input


attributes_to_skip_when_registering = ["ACCOUNTID", "ACC_SIGNUPDATEANDTIME", "USER_LEVEL", "USER_EXP"]

def GetDateandTime():
                timetuple = time.localtime(time.time())

                def ForceTwoDigits(number): # E.g '9' gets extended to '09' to fit the format
                    if len(number) == 1:
                        number = "0" + number
                    return number

                Year = str(timetuple[0])
                Month = ForceTwoDigits(str(timetuple[1]))
                Day = ForceTwoDigits(str(timetuple[2]))
                Hour = ForceTwoDigits(str(timetuple[3]))
                Minute = ForceTwoDigits(str(timetuple[4]))
                Second = ForceTwoDigits(str(timetuple[5]))

                timenow = f"{Year}/{Month}/{Day}-{Hour}:{Minute}:{Second}"
                return timenow

def RegisterProfile():

    user = None
    cursor.execute('PRAGMA table_info(Profiles)') # Get data dictionary of Profiles 

    for column in cursor.fetchall():
        attribute = column[1] # column[1] Refers to the columns name - i.e where the data should be inserted

        skip = False
        for attr in attributes_to_skip_when_registering:
            if attribute == attr: # Skip all non-user submitted fields
                if debugging: print(f"skipping {attribute} because it is a non user-submitted field")
                skip = True
        
        if skip == True:
            continue
        

        if user == None: # This gets the account name from the first loop so it knows where to store the other fields
            user = AskForField(attribute, user)
            
            # Assign ACC_SignUpDateAndTime (YYYY/MM/DD-HH:MM:SS)
            command =  f"UPDATE Profiles SET ACC_SIGNUPDATEANDTIME = '{GetDateandTime()}' WHERE ACC_NAME = '{user}'"
            cursor.execute(command)
            conn.commit()


        else:
            AskForField(attribute, user) 
    
      
    CreateDirectoryIfNotExists(f"DATA/usergoals/{user}") # The user's folder must be established first before adding content inside
    CreateJsonIfNotExists(goalsPath(user))
    CreateJsonIfNotExists(macrogoalsPath(user))
        

        
    TimedMessage("Account successfully registered!", 1, 2)

# Exp equation figures
equation_scale = 250
equation_power = 3/2 # Larger figures = Slower level growth

def GetLevelFromExp(exp):
        return math.floor(((exp / equation_scale) ** (equation_power ** -1))) + 1 # Return the floor of the inverse exp formula -exp must be in float

def DrawProgressBar(value, target, start = 0):
    percentage = (value - start) / (target - start)
    barlength = 30
    bar = ""
    
    characters_to_fill = int(math.floor(barlength * (percentage)))

    for i in range(0, characters_to_fill): # fill in the bar
        bar = bar + "█"
    for i in range(0,barlength - characters_to_fill): # for the rest, print empty bar
        bar = bar + "▁"

    #print(" |█████████████████████████▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁|") # 50 Chars
    #print("▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱") # 50 Chars

    return bar

# To get one macro count, I need to get every mealrecord from the user made today, and add up all of that nutrient from each meal in each record

def GetDateToday(offset = 0):
                timetuple = time.localtime(time.time() - offset)

                def ForceTwoDigits(number): # E.g '9' gets extended to '09' to fit the format
                    if len(number) == 1:
                        number = "0" + number
                    return number

                Year = str(timetuple[0])
                Month = ForceTwoDigits(str(timetuple[1]))
                Day = ForceTwoDigits(str(timetuple[2]))

                timenow = f"{Year}/{Month}/{Day}"
                return timenow


def ReturnUserMealsConsumedToday(user):
    table = []
    try:
        for i in cursor.execute(f"""SELECT Meal, MealRecords.DateAdded
                                    FROM MealRecords 
                                    WHERE USER = ('{user}') AND DateAdded = '{GetDateToday()}' """):
            data = i[0]  # [0] because sql returns data in tuple format
            table.append(data)
        return table
    except:
        print("uh oh")


def GetMacroCountToday(nutrient, user):
    table = []
    try:
        for i in cursor.execute(f"SELECT Meal FROM MealRecords WHERE USER = ('{user}')"): 
            data = i[0]  # [0] because sql returns data in tuple format
            table.append(data)
        return table
    
    except TypeError:
        print("There was an error retrieving data")
        raise sqlite3.DatabaseError 

def GetSingleField(command):
    for i in cursor.execute(command):
        return i[0]

def IncrementDisplayNumber(number,Initial = 0,refresh_rate = 10):
    for i in range(0,refresh_rate+1):
        ClearTerminal()
        print(round(number * (i/refresh_rate)))
        print("")
        
        time.sleep(1/refresh_rate)


def DashboardHub(user): # See a user's dashboard.
    
    # Remove outdated exercise and meal logs
    # For each, remove logs that don't match today or yesterday's date - Simple!

    cursor.execute(f"DELETE FROM ExercisesLogged WHERE (User IS NULL) OR (User = '{user}' AND DatePerformed != '{GetDateToday()}' AND DatePerformed != '{GetDateToday(84600)}')") 
    cursor.execute(f"DELETE FROM MealsLogged WHERE (User IS NULL) OR (User = '{user}' AND DateAdded != '{GetDateToday()}' AND DateAdded != '{GetDateToday(84600)}')")
    conn.commit()
    # (The offset by 84600 should return tommorow's date)

    # Create usergoals folder, because macro data must be accessed to be displayed on the hud
    CreateDirectoryIfNotExists(f"DATA/usergoals/{user}")
    CreateJsonIfNotExists(macrogoalsPath(user))
    CreateJsonIfNotExists(goalsPath(user))

    logout = False
    while not logout:
        DisplayName = GetDataFromUser(user, "USER_NAME")
        if DisplayName == None: # If the user has no display name, use their account name
            DisplayName = user
        
        TimedMessage(f"Welcome {DisplayName}!", .5, 2)
        
        user_exp = GetDataFromUser(user, "USER_EXP", "Profiles")
        user_level = GetLevelFromExp(user_exp)
        exp_to_reach_next_level = math.floor(equation_scale * (user_level) ** (equation_power)) - math.floor(equation_scale * (user_level-1) ** (equation_power))
        exp_gained_at_current_level = user_exp - math.floor(equation_scale * (user_level-1) ** (equation_power))
        exp_gained_at_current_level = int(exp_gained_at_current_level)
        
        # Read users macrogoals.json data and assign to content as a string
        with open(macrogoalsPath(user), 'r') as file:
            content = file.read()

        # Convert json to a python dictionary
        macrogoals_dictionary = json.loads(content)

        # Do the same with goals.json
        with open(goalsPath(user), 'r') as file:
            content = file.read()
        goals_dictionary = json.loads(content)


        
        print(f"| {user} : Level {user_level} ")
        print(f' \\ EXP: {exp_gained_at_current_level} |{DrawProgressBar(exp_gained_at_current_level, exp_to_reach_next_level)}| {exp_to_reach_next_level}')
        print('  ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾')

        # All functions
        # 1 - Add a new (Exercise/Meal/Goal)  # Allows the user to register a new exercise/meal to be used in logging, or new goals to track. 
        # 2 - Log Data (Sessions, Meals, Goals)  # Allows the user to log: -exercises they did and their performance  -meals they had today  -new progress towards a goal
        # 3 - Undo log (Session, Meal)  # Allows the user to discard the last log made, in case they need to make corrections
        # 4 - Set Nutrient goals 
        # 5 - View Nutrient intake and Goals  # Shows the user the sum of all nutritional values of the meals they had today and compare them to nutrient goals.
        # 6 - View Exercise library  # The user can search through every listed exercise and remove one (has to be user created)
        # 7 - View Goals
        #
        # 8 - Establish a routine  # Allows the user to create a personal exercise routine which are daily (Day 1, D2, D3, Break) or weekly (Mon, Tue, Thu, Fri, Sun)
        # 9 - Daily challenges  # The user can opt into being given extra stretch challenges on routine days that also increase in difficulty once completed (e.g 40 pushups, 7km run) 
        # 10 - A tutorial to help people figure out all this bullshit

        # Tabs/Inputs:
        # -Goals -  --Shows every active goal 
        # . ('+') - Allows the user to create a new goal
        # . ('-' followed by goalname) - Opens more information about that goal, including every log and it's date
        #   . ('1') - Declare a new progress point for that goal
        #   . ('*') - Discard last progress log
        #   . ('q') - Back to dashboard
        # . ('*' followed by goalname) - Deletes the specified goals
        # . ('q') - Back to dashboard
        # -Exercises-
        # . ('+') - Allows the user to log an exercise performed today (or on routine day/yesterday) ("Is this info correct? prompt" at the end)
        # . ('-') - Allows the user to discard the last log made
        # . ('1') - Shows the user a list of all the available exercises (x at a time, which may require multiple pages, or all at once), including ones they've registered
        #   . ('+') - Create a new exercise
        #   . ('-' followed by exercise name) - If it finds an exact match(case insensitive) it will bring up more info about the exercise. If not, it will show filtered results of names containing the query
        #   . ('*' followed by exercise name) - to remove it
        # -Diet data- -- Displays today's nutritional totals
        # . ('+') - log a meal
        # . ('-') - Discard the last meal log
        # . ('1') - Set/Change Nutrient goals
        # . ('2') - See all meal logs for today
        # . ('3') - See all selectable meals
        #   . ('+') - Register a new meal
        #   . ('-' followed by meal name) - If it finds an exact match(case insensitive) it will bring up more info about the meal. If not, it will show filtered results of names containing the query
        #   . ('*' followed by meal name) - to remove it
        # -More User Info- -- Displays all profile fields plus Total Exp and Sign-up date and time
        # .(input a fieldname) - to edit it

        choice = None
        while choice == None:
            TimedMessage("",.65,1)
            print("Tabs and navigation:")
            print("------------------------------")
            print("(1) -> Goals")
            TimedMessage("------------------------------", .05)
            print("(2) -> Exercises")
            TimedMessage("------------------------------", .05)
            print("(3) -> Diet Data")
            TimedMessage("------------------------------", .05)
            print("(4) -> More User Info")
            TimedMessage("------------------------------", .05)
            print("(Q) -> Log Out")
            TimedMessage("------------------------------", .05)

            # If pathways and If checks
            choice = input()

        if choice == "1":  # Goto Goals Hub       
            # Show every active goal
            TimedMessage("Goals:", .5, 1, False, True)
            for i in goals_dictionary:
                # Display current value(latest value), target value, and how long it's been since they started
                # Current Value is the most recently logged value, which should be the last index of the entries(at index 4) dict

                goal_entries = list(goals_dictionary[i]["entries"])
                starting_value = float(list(goals_dictionary[i]["entries"].values())[0])  # The oldest entry
                current_value = float(list(goals_dictionary[i]["entries"].values())[-1])  # The latest entry
                measurement = goals_dictionary[i]["measurement"] 
                try:
                    target_value = float(goals_dictionary[i]["target"])  # target_value requires a try as it can be left null
                except:
                    target_value = None
                goal_time_tuple = (int(goal_entries[0][0:4]),int(goal_entries[0][6:7]),int(goal_entries[0][9:10]),0,0,0,0,0,0)  # This should return a time tuple of (Year, Month, Day)
                days_since_goal_begun = (time.time() - time.mktime(goal_time_tuple)) // 86400 # time now - time the goal was created (rounded to days)
        
                print("- ",i,"-") # Display current value and end goal if one is declared
                # Only draw a progress bar if a target value is determined
                if target_value != None:
                    print(f"{current_value}{measurement}|{DrawProgressBar(current_value, target_value, starting_value)}|{target_value}{measurement}")
                else:
                    print(f"{current_value}{measurement}")

                print(f". Goal begun {int(days_since_goal_begun)} day(s) ago")
                print("--------------------------------------------------------")

            if len(goals_dictionary) == 0:  # -must make sure that when all goals are deleted the length is 0
                TimedMessage("No goals yet...", .5, 1)
            
            print("")
            print(". Enter '+' to Create a new goal")
            print(". Enter '-' followed by the goal's name (Excatly as displayed on the menu) -> to see more info (Ensure your input is case sensitive)")  # There must be no spaces after the '-'
            print(". or 'Q' to Return to dashboard")

            choice = str(input())

            print("")

            if choice == "Q" or choice == "q":
                choice = None  
                continue  # break the while loop and return to dashboard
            
            if choice == "+":  # Create a new goal
                goal_name = str(input("Enter the name of your goal."))
                goal_measurement = str(input("Is this goal measured by any specific unit? (e.g kg, stone, cm, BMI, %)")) # % e
                goal_target = None
                while goal_target == None:
                    try:  # The input must be a float, so handle the exception if not
                        goal_starting_value = float(input("Where are you at currently? (What value)"))
                        goal_target = str(input("Does this goal have an end value? If so type a number, if not leave this blank"))
                        if len(goal_target.strip()) == 0:  # If nothing lol -.strip() removes leading and trailing whitespace characters
                            continue  # Break the while despite input being None
                        else:
                            goal_target = float(goal_target)  # convert to a number       

                    except:
                        goal_target = None
                        print("message.invalid.input")
                
                # Append values to goal dictionary and save to JSON

                goals_dictionary.update({goal_name : {"measurement":goal_measurement,
                                                        "target": goal_target,
                                                        "date_undertaken": GetDateToday(),
                                                        "date_completed": 0,
                                                        "entries": {GetDateToday(): goal_starting_value}}})
                
                # Open user's goal.json and overwrite dictionary with the updated table
                with open(goalsPath(user), 'w') as file:
                    file.write(json.dumps(goals_dictionary))
                continue

            elif choice[0] == "-":  # Read goal info
                choice = choice[1:]  # String slicing = [1:] to exclude the required '-'

                # Read goals.json to retrive info
                with open(goalsPath(user), 'r') as file:
                    content = file.read()
                goals_dictionary = json.loads(content)

                try:
                    goals_dictionary[choice]
                except:
                    TimedMessage("Couldn't find that goal.", 1)
                    choice = None
                    continue

                """
                count = 0  # times the query appears in the dictionary
                for goalname in goals_dictionary:
                    if goalname == choice:
                        count += 1

                if count == 0:  # If the goal can't be found in the dictionary. 
                    choice = None
                    TimedMessage("Couldn't find that goal.", 1)
                    continue    
                """
                TimedMessage(f"{choice}:", 0.1, 0, 0, 1)
                for key, value in goals_dictionary[choice].items():  # Retrive info from given goal
                    print(f"{key}: {value}")

                Goal = choice

                # Option to add new entry and remove goal (possibly to remove last log in the future)
                choice = str(input("\n. '+' -> Add new entry\n. '*' -> Delete goal \n. Any other key -> Back to dashboard"))

                if choice == "+":
                    value = float(input("Enter new value:"))
                    confirm = str(input(f"Enter {value}? (y/n):"))

                    # If not yes, don't go on with the procedure
                    if confirm != "y" and confirm != "Y":
                        continue

                    goals_dictionary[Goal]["entries"].update({GetDateToday():value})

                    # Open user's goal.json and write data
                    print("Saving progress")
                    with open(goalsPath(user), 'w') as file:
                            file.write(json.dumps(goals_dictionary))

                elif choice == "*":
                    choice = str(input("Are you sure? (y/n)"))
                    if choice == 'y' or choice == 'Y':
                        goals_dictionary.pop(Goal)
                        
                        # Open user's goal.json and overwrite data
                        with open(goalsPath(user), 'w') as file:
                            file.write(json.dumps(goals_dictionary))

                        TimedMessage("Goal removed", 1, 0, True)

                continue

            print("Invalid choice")
            choice = None

        elif choice == "2":  # Goto Exercises Hub
            print("-Exercises Hub-\n")
            print("------------------------------")
            print("('+') -> Log an exercise")
            print("------------------------------")
            print("('*') ->  Discard the last log made")  # There must be no spaces after the '*'
            print("------------------------------")
            print("('1') ->  Goto Exercise Library")
            print("------------------------------")
            print("(Q) -> Return to dashboard")

            choice = str(input())

            if choice == "Q" or choice == "q":
                choice = None

            elif choice == "+":  # log an exercise
                # List all exercises
                ClearTerminal()

                exer_list = {}  # Key / Value
                Index = 0
                for i in cursor.execute("SELECT ExerciseName FROM Exercises"):
                    Index = Index + 1
                    print(f". ({Index}): {i[0]}")
                    exer_list[str(Index)] = i
                TimedMessage("-Exercise Library-", .5, 1)

                print(". Enter the number of the exercise you did to add it")

                try:
                    choice = input()
                    choice = exer_list[choice][0]
                except:
                    TimedMessage("Invalid Input", .1)
                    choice = None
                    continue
                
                # More fields
                exer_sets = int(input("How many sets of the exercise was done?"))
                exer_reps = int(input("Average reps per set?"))  # Introduce exponents for sets reps so that they rise in exp less the more that are done
                exer_weight = float(input("Weight lifted in kg? (If none, enter 0)"))

            
                if exer_weight <= 0.0:
                    exer_weight = 1.0

                exer_intensity = GetSingleField(f"SELECT ExerciseIntensity FROM Exercises WHERE ExerciseName = '{choice}' ")

                if exer_intensity == 'Body':
                    exer_intensity = 10.0 * (GetDataFromUser(user, "USER_WEIGHT") / 45)
                elif exer_intensity == 'Heavy' or exer_intensity == 'H':
                    exer_intensity = 20.0
                elif exer_intensity == 'Light' or exer_intensity == 'L':
                    exer_intensity = 5.0
                else:
                    exer_intensity = 10.0


                exp = exer_sets * exer_reps * exer_weight * exer_intensity
                exp = round(exp, 0)

                # Log values to SQL
                cursor.execute(f"INSERT INTO ExercisesLogged (Exercise, User, DatePerformed, WeightLifted, Sets, Reps, ExpAwarded)" \
                                f"VALUES ('{choice}','{user}','{GetDateToday()}',{exer_weight},{exer_sets},{exer_reps},{exp})")
                # Give EXP
                cursor.execute(f"UPDATE Profiles SET USER_EXP = USER_EXP + {exp} WHERE ACC_NAME = '{user}'")

                conn.commit()
                TimedMessage("Exercise Logged Succesfully!",.75)

                # Display Awarded EXP
                TimedMessage(f"+{int(exp)} EXP", .75)

                """
                for i in range(0,61):
                    ClearTerminal()
                    user_exp += (exp * (i/61))
                    user_level = GetLevelFromExp(user_exp)
                    exp_to_reach_next_level = math.floor(equation_scale * (user_level) ** (equation_power)) - math.floor(equation_scale * (user_level-1) ** (equation_power))
                    exp_gained_at_current_level = int(user_exp - math.floor(equation_scale * (user_level-1) ** (equation_power)))


                    print(f"| Level {user_level} ")
                    print(f' \\ EXP: {exp_gained_at_current_level} |{DrawProgressBar(exp_gained_at_current_level, exp_to_reach_next_level)}| {exp_to_reach_next_level}')
                    print('  ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾')
                    time.sleep(1/15)
                """

            elif choice == "*":  
                # Find latest log from user
                exercise_name = GetSingleField(f"SELECT Exercise FROM ExercisesLogged WHERE USER = '{user}' ORDER BY ID DESC LIMIT 1")  # Limit to return one result (The most recent one)
                choice = input(f"Are you sure you want to delete the last log ({exercise_name})? (y/n)")

                if choice == "n":  # Opt out
                    choice = None
                    continue
                
                # Exp awarded must be reverted before the field is deleted
                exp = GetSingleField(f"SELECT EXPAwarded FROM ExercisesLogged WHERE USER = '{user}' ORDER BY ID DESC LIMIT 1")
                print(f"-{exp} EXP")

                # Deduct exp
                cursor.execute(f"UPDATE Profiles SET USER_EXP = USER_EXP - {exp} WHERE ACC_NAME = '{user}'")

                # Delete log
                cursor.execute(f"DELETE FROM ExercisesLogged \
                                WHERE ID IN ( \
                                    SELECT ID FROM ExercisesLogged \
                                    WHERE User = 'user1' \
                                    ORDER BY ID DESC \
                                    LIMIT 1 \
                            );")
                conn.commit()
                TimedMessage("Deleting log...", .75)

            elif choice == "1":  # Goto Exercise library
                # Show a list of registered exercises
                ClearTerminal()

                exer_list = {}  # Key / Value
                Index = 0
                for i in cursor.execute(f"SELECT ExerciseName FROM Exercises WHERE (IsPublic IS NULL) OR (IsPublic != 'N') OR (IsPublic == 'N' AND CreatedBy == '{user}')"):  # The user can access their private exercises
                    Index = Index + 1
                    print(f". ({Index}): {i[0]}")
                    exer_list[str(Index)] = i

                TimedMessage("-Exercise Library-", .5, 1)
                print(". Enter the number of the exercise you want to remove, or enter a new exercise to create it\n. Q to return to dashboard")

                choice = str(input())

                if choice == "q" or choice == "Q":
                    choice = None
                    continue
                
                try:  # If the try succeeds, it means that the choice actually matches a listed exercise
                    if exer_list[choice] != None:
                        print("")

                    created_by = None
                    for i in cursor.execute(f"SELECT CreatedBy FROM Exercises WHERE ExerciseName = '{exer_list[choice][0]}'"):
                        created_by = i[0]

                    if created_by != user:
                        TimedMessage("Cannot remove exercises you didn't create!", 1,1)
                        continue
                    
                    cursor.execute(f"DELETE FROM Exercises WHERE ExerciseName = '{exer_list[choice][0]}'")
                    conn.commit()
                    TimedMessage("Exercise Deleted!", .75, 1)
                    continue 
                    
                except:
                    pass
                
                print(f"Exercise Name: {choice}")
                exer_ispublic = str(input("Make this exercises public for other profiles to see and use? (y/n)"))

                if exer_ispublic == "n":
                    cursor.execute(f"INSERT INTO Exercises (ExerciseName, CreatedBy, IsPublic, ExerciseIntensity) VALUES ('{choice}', '{user}', '{'N'}', '{'M'}')")
                elif exer_ispublic == "y":
                    cursor.execute(f"INSERT INTO Exercises (ExerciseName, CreatedBy, IsPublic, ExerciseIntensity) VALUES ('{choice}', '{user}', '{'Y'}', '{'M'}')")
                else:
                    print("Input unacceptable. try lowercase only")
                    continue
                
                conn.commit()
                print("Exercise created!")
                
        elif choice == "3":
            # Display today's nutritional totals

            calories = 0
            protein = 0
            carbs = 0
            fat = 0

            meals_today = []
            for i in cursor.execute(f"SELECT Meal FROM MealsLogged WHERE DateAdded = ('{GetDateToday()}') AND User = '{user}'"):  # Get all logged meals today
                meals_today.append(i[0])

            print("-Diet data (Macro Hub)-\n")
            print("Totals:")
            for i in meals_today:
                calories += int(GetSingleField(f"SELECT Calories FROM Meals WHERE MealName = '{i}'")) 
                protein += int(GetSingleField(f"SELECT Protein FROM Meals WHERE MealName = '{i}'"))
                carbs += int(GetSingleField(f"SELECT Carbohydrates FROM Meals WHERE MealName = '{i}'"))     
                fat += int(GetSingleField(f"SELECT Fat FROM Meals WHERE MealName = '{i}'"))
            print(f"Calories: {calories}\nProtein: {protein}\nCarbohydrates: {carbs}\nFat: {fat}")

            print("------------------------------")
            print("('+') -> Log a meal")
            print("------------------------------")
            print("('1') ->  See all meal logs made today")
            print("------------------------------")
            #print("('2') -> Set/Change Nutrient goals")
            #print("------------------------------")
            print("('2') -> See Meal library")
            print("------------------------------")
            print("('Q') -> Return to dashboard")

            choice = str(input())

            if choice == "q" or choice == "Q":
                choice = None

            if choice == "+":  # Log a meal

                ClearTerminal()
            
                # List all meals
                meal_list = {}  # Key / Value
                Index = 0
                for i in cursor.execute("SELECT MealName FROM Meals"):
                    Index = Index + 1
                    print(f". ({Index}): {i[0]}")
                    meal_list[str(Index)] = i[0]
                TimedMessage("-Meals Library-", .5, 1)

                print(". Enter the number of a food to add it (search the terminal for your food if the list too long)\n. 'Q' to return to hub ")
                choice = str(input())
                if choice == "q" or choice == "Q":
                    continue
                
                # See if choice is actually in the list
                try:
                    choice = meal_list[choice]
                except:
                    TimedMessage("error 🥀💀", 1)
                    continue

                """
                Count = 0
                for i in meal_list.keys():
                    if choice == i:
                        Count += 1
                if Count == 0:
                    TimedMessage("Can't find that meal.", .5)
                    continue
                """

                # List all values about the chosen meal
                values = {"Calories": 0,
                            "Carbohydrates": 0,
                            "Protein": 0,
                            "Fat": 0}
                
                for i in cursor.execute(f"SELECT Calories, Carbohydrates, Protein, Fat FROM Meals WHERE MealName = '{choice}'"):              
                    values = {"Calories": i[0],
                            "Carbohydrates": i[1],
                            "Protein": i[2],
                            "Fat": i[3]}
                    
                print(values)
                c = str(input("Log these values? (y/n)"))

                if c == 'n':
                    print("Meal not logged")
                    continue

                cursor.execute(f"INSERT INTO MealsLogged (Meal, User, DateAdded) VALUES ('{choice}', '{user}', '{GetDateToday()}')")
                conn.commit()
                print("Meal successfully logged!")

            if choice == "1":  # See meal logs
                # Get all meals logged today that belong to the user and were made today
                ClearTerminal()

                logs = []
                for i in(cursor.execute(f"SELECT Meal FROM MealsLogged WHERE User = '{user}' AND DateAdded = '{GetDateToday()}'")):
                    logs.append(i[0])
                for i in logs:
                    print(f"({logs.index(i) + 1}): {i}")

                choice = str(input("\n. Enter the number of a log to remove it\n. 'Q' to return to the dash"))

                if choice == "Q" or choice == 'q':
                    continue

                try:
                    choice = int(choice) - 1
                except:
                    TimedMessage("Couldn't find that log",.75)
                    continue

                TimedMessage("Deleting...", .75, 1)
                cursor.execute(f"DELETE FROM MealsLogged WHERE Meal = '{logs[choice]}'")
                conn.commit()
                
            if choice == "2":  # See meal library
                TimedMessage("-Meals Library-", .5, 1, False, True)

                meal_list = []
                # List all meals
                for i in cursor.execute("SELECT MealName FROM Meals"):
                    meal_list.append(i)
                    print(f"{meal_list.index(i) + 1}. -", i[0])

                print("")
                print(". Enter the number asociated with a meal to see more info")
                print(". Enter '+' to Register a new meal")
                print(". Enter 'Q' to return to hub")
    
                choice = str(input())

                if choice == 'q' or choice == 'Q':
                    continue
                
                # Create a meal
                if choice == '+': 
                    meal_name = str(input("Enter meal name:"))
                    calories = int(input("Enter calories (kcal):"))
                    protein = int(input("Enter Protein (in grams):"))
                    carbohydrates = int(input("Enter Carbohydrates (in grams):"))
                    fat = int(input("Enter Fat (in grams):"))

                    TimedMessage("Creating Meal...",.75)
                    cursor.execute(f"INSERT INTO Meals (MealName, CreatedBy, Calories, Carbohydrates, Protein, Fat) VALUES ('{meal_name}', '{user}', {calories}, {protein}, {carbohydrates}, {fat})")
                    conn.commit()
                    continue

                # Look at meal
                try:
                    choice = meal_list[int(choice) - 1][0]  # If OutOfRange error, except
                    print("\nSelected Meal:",choice)     
                except:
                    print("Not a listed meal")

                values = {"Calories":None,"Carbohydrates":None,"Protein":None,"Meals":None}
                
                # Show meal nutritional values
                for i in cursor.execute(f"SELECT Calories, Carbohydrates, Protein, Fat FROM Meals WHERE MealName = '{choice}'"):
                    values.update({"Calories":i[0],"Carbohydrates":i[1],"Protein":i[2],"Meals":i[3]})
                print(values)        

                meal = choice
                choice = str(input("\n. Enter '*' to delete this meal\n. Enter 'Q' to return to hub"))

                if choice != '*':
                    continue
                
                # Delete if possible
                if GetSingleField(f"SELECT CreatedBy FROM Meals WHERE MealName = '{meal}'") != user:  # If the meal was not created by the user
                    TimedMessage("You can only delete meals you've created at the moment...", 1.25)
                    continue

                TimedMessage("Deleting...",.75)
                # Delete from meals AND anywhere it's mentioned in mealslogged
                cursor.execute(f"DELETE FROM Meals WHERE MealName = '{meal}'")
                cursor.execute(f"DELETE FROM MealsLogged WHERE Meal = '{meal}'")
                conn.commit()
                
        elif choice == "4":
            # Display the users Profile fields and allow them to change them here.

            # --ACC_Name (ACC ID)
            # --SIGNUPDATE
            # --TOTAL EXP EARNED

            print(f"Account Name: {GetDataFromUser(user, "ACC_NAME")} (Account ID: {(GetDataFromUser(user, "ACCOUNTID"))})")
            print(f"Account Created: {GetDataFromUser(user, "ACC_SIGNUPDATEANDTIME")}")
            print(f"Total EXP Earned: {GetDataFromUser(user, "USER_EXP")}")

            print(f"username: {GetDataFromUser(user, "USER_NAME")}")
            print(f"age: {GetDataFromUser(user, "USER_AGE")}")
            print(f"gender: {GetDataFromUser(user, "USER_GENDER")}")
            print(f"weight: {GetDataFromUser(user, "USER_WEIGHT")}")
            print(f"height: {GetDataFromUser(user, "USER_HEIGHT")}")

            print("(1). Update Weight")
            print("(Q). Back to Dash")
            choice = str(input())

            if choice == "1":
                weight = float(input("Enter new weight (kg):"))
                cursor.execute(f"UPDATE Profiles SET USER_WEIGHT = '{weight}' WHERE ACC_NAME = '{user}'")
                conn.commit()
                


        elif choice == "Q":
            logout = True
            TimedMessage("Signing out...", .5, 1)

        else:
            choice = None
            print("invalid option. try again")


def ProfileSelect():
    selection = None
    while selection is None:  # This makes it so that if AuthenticateUser() fails, repeat the input
        profilesArray = []

        print("-Profile Selection-")
        time.sleep(.5)
        print("\nSelect From:\n")
        print("(+) New Profile")

        for row in cursor.execute(ListProfilesCommand):  # returns the row in array format
            profilesArray.append(row[0])
            print('(-)', row[0])  # the first (and only) value in each row will be the username
            # if USER_NAME != None: ...
        
        selection = input(profile_select_input_message)  # If the user decides to create a new profile
        if selection == "+":
            selection = None
            RegisterProfile()
            
        else: 
            if profilesArray.count(selection) >= 1:  # Determine if the input entered matches an actual account name
                if AuthenticateUser(selection):  # If AuthenticateUser is a success, then proceed
                    DashboardHub(selection)
                    selection = None
                else:
                    selection = None
            else:
                selection = None
                print("specified user does not exist. Try checking your spelling/casing")
                time.sleep(1.5)


ClearTerminal()
print("~-GainGame-~\n")
time.sleep(.8)


ProfileSelect()

# buttons = [Play, Leaderboards, Exit]

# Assign exercise EXP values individually/into groups and muscle groups

