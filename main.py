import discord
import config
import random
import os
from threading import Timer
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from game import Game
from stats import Statistics
from data_manager import Data_Manager


client = discord.Client()

class Reminder:
    def __init__(self, message_obj):
        args = message_obj.content.split(" ")
        self.args = args
        self.time_arg = False

    def remind(self):
        if self.args[0] == "min" or self.args[0] == "mins" or self.args[0] == "minute" or self.args[0] == "minutes" or self.args[0] == "m":
            self.time *= 60
            self.time_arg = True
        elif self.args[0] == "hour" or self.args[0] == "hours" or self.args[0] == "hr" or self.args[0] == "hrs" or self.args[0] == "h":
            self.time *= 3600
            self.time_arg = True
        elif self.args[0] == "day" or self.args[0] == "days" or self.args[0] == "d":
            self.time *= 86400
            self.time_arg = True

        t = Timer(self.time, self.handle_command)
        t.start()


    def handle_command(self):
        reponse_str = " ".join(self.args)
        print(response_str)

class Lobby:
    def __init__(self, name):
        self.game = None
        self.name = name
        self.players = []
    
    def add_player(self, player):

        if not player == self.players:
            self.players.append(player)
            return "{player} has joined **{lobby}**.".format(player=player, lobby=self.name)
        else:
            return "{player} is already in **{lobby}**.".format(player=player, lobby=self.name)

    def remove_player(self, player):
        try:
            self.players.remove(player)
            return "{player} has left **{lobby}**.".format(player=player, lobby=self.name)
        except ValueError:
            return "Error — attempted to remove non-existant player {player} from lobby **{lobby}**!".format(player=player, lobby=self.name)

    def list_players(self):
        if self.players:
            response = "["
            list_str = ""
            for player in self.players:
                list_str += ", {player}".format(player=player)
            response += list_str[2:]
            response += "]"
            return response
        else:
            return ""

class State_Manager:
    def __init__(self):
        # Channel setup
        self.game_channel = None
        
        # Lobby setup; "open" libraries are potential lobbies with no activity; "active" libraries can be joined and host games; "closed" libraries have active games and are not available for the state machine to start new games
        self.open_lobbies = ["Jace","Chandra","Nissa","Liliana","Gideon","Sorin","Venser","Elspeth","Ajani","Bolas","Vraska","Tamiyo","Nahiri"]
        random.shuffle(self.open_lobbies)
        self.active_lobbies = {}
        self.closed_lobbies = []
        
        # Player -> Lobby assignment
        self.player_assign = {}

        # alias setup
        self.aliases = {}

        # load any existing aliases
        if os.path.exists("alias.txt"):
            with open("alias.txt", "r", -1, "utf8") as alias_list:
                alias_data = alias_list.read().split("\n")

                # delete the newline at the end
                del alias_data[-1]

                # add each alias to the state machine
                for alias in alias_data:
                    alias = alias.split("&separator;")
                    self.aliases[alias[0]] = alias[1]
                # note that this collapses duplicate entries to whatever the player entered last

                # save dict back to file (which removes duplicate entries)

                # Make a string out of alias dict
                alias_str = ""
                for key in self.aliases:
                    alias_str += "{account}&separator;{alias}\n".format(account=key, alias=self.aliases[key])

                # save to file
                with open("alias.txt","w",-1,"utf8") as alias_list:
                    alias_list.write(alias_str)

        # game count; currently this value is set by counting the number of games set in the stat manager, so we can't set it here
        self.game_count = 0

        # legacy game storage; removing this will break any $game commands that don't use the lobby architecture, which is all of them at this point
        self.current_game = None


    ##################################
    #       player lookup methods
    ##################################

    # given a player name, finds the lobby they're in
    def get_player_alias(self, author_name):
        alias = None
        try:
            alias = self.aliases[author_name]
        except KeyError:
            response = "get_player_alias call failed: '{author}' is not a key".format(author=author_name)
            print(response)
            return response

        return alias

    # given a player name, looks them up in the player assignment dict and returns the name of the lobby they're in or throws a KeyError exception
    def get_player_lobby(self, player):

        # get reference to lobby
        lobby_name = self.player_assign[player]
        return lobby_name

    ##################################
    #      game / lobby creation
    ##################################

    # Used to create a new lobby
    def activate_lobby(self):

        new_lobby = self.open_lobbies.pop(0)
        self.active_lobbies[new_lobby] = Lobby(new_lobby)
        
        return new_lobby

    # command to create new Game object inside an available lobby
    def new_game(self):
        # set up output str and lobby key
        response = ""
        lobby_name = ""

        # check if there's an open lobby
        if len(self.active_lobbies) == len(self.closed_lobbies):

            # if not, make one
            new_lobby = self.open_lobbies.pop(0)
            self.active_lobbies[new_lobby] = Lobby(new_lobby)                

            lobby_name = new_lobby

            response += "Opened **{lobby}** lobby.\n".format(lobby=new_lobby)

        else:
            # if there is, find it
            for lobby in self.active_lobbies:
                if not lobby in self.closed_lobbies:
                    lobby_name = lobby
        
        # make new game in the open lobby
        self.game_count += 1
        self.active_lobbies[lobby_name].game = Game(self.game_count)

        # this lobby is now closed, so add it to the list
        self.closed_lobbies.append(lobby_name)

        response += "Created a new game in **{lobby}**.".format(lobby=lobby_name)
        return response         

    # creates a new game in the specified lobby if one does not already exist
    def new_game_in_lobby(self, lobby_name):
        
        # get ref to lobby
        lobby = self.active_lobbies[lobby_name]

        # if no game, make a new one
        if lobby.game == None:
            
            # increment game count
            self.game_count += 1

            # new game
            lobby.game = Game(self.game_count)
            return "Started a new game in **{lobby_name}**.".format(lobby_name=lobby_name)
        
        # if there's already a game, let them know
        else:
            return "There is already an active game in **{lobby_name}**.".format(lobby_name=lobby_name)

    # if there is no game in the given lobby, creates a game there.  Must be wrapped in a try/except block to catch KeyErrors in case the lobby is not active.
    def ensure_game_exists(self, lobby_name):

        # get the lobby        
        lobby = self.active_lobbies[lobby_name]
        
        # if no game, make one
        if lobby.game == None:
            lobby.game = Game(self.game_count)
            self.game_count += 1

        # return game
        return lobby.game

    ##################################
    #       discord interaction
    ##################################

    # executes a user command entered into discord, then sends back a response
    async def route_message(self, message, stats, dm):

        # Nope out if the message is from this bot
        if message.author == client.user:
            return
        
        # write message to console
        print(message)

        # grab message content so we don't have to type "message.content" a million times
        content = message.content

        # set up response string
        response = ""

        # Command to start a new lobby
        if content.startswith("$new lobby"):

            # Open a new lobby and store the return string
            new_lobby = self.activate_lobby()
            response = "Opened lobby **{lobby}**.".format(lobby=new_lobby)

        # Command to print active lobbies
        elif content.startswith("$lobbies"):

            # start response string
            response = "Open lobbies: \n"

            # iterate through active lobbies and add to string
            lobby_list_str = ""
            for lobby in self.active_lobbies:
                lobby_list_str += ", {lobby}".format(lobby=lobby)

                # if there are players, list them
                lobby_list_str += self.active_lobbies[lobby].list_players() 

            response += lobby_list_str[2:]

        # Command to start new game
        elif content.startswith("$new game"):
            response = self.new_game()
        
        # Variant 'new game' command that starts a game in the player's lobby 
        elif content.startswith("$start") or content.startswith("$game start"):
            # get the lobby of the player entering the command
            try:
                player_lobby = self.get_player_lobby(message.author.name)
                response = self.new_game_in_lobby(player_lobby)
            except KeyError:
                response = "Join a lobby with ``$join`` to use this command."

        # Command to join a lobby
        elif content.startswith("$join"):

            # get names of player and intended lobby
            player = message.author.name
            join_target = content[6:]

            # if we didn't get a lobby name, join the first available open lobby
            if join_target == "" or join_target == " ":

                # If we're already in a lobby, don't go anywhere 
                try:
                    current_lobby = self.player_assign[player]
                    await self.game_channel.send("You're in **{lobby}** right now. You can add the name of a different lobby, e.g. ``$join Venser`` to leave your current lobby and join that one.".format(lobby=current_lobby))
                    return
                # If we're not in a lobby, the above block throws a KeyError and we find a lobby to join
                except KeyError:
                    if self.active_lobbies:
                        for lobby in self.active_lobbies:
                            if not lobby in self.closed_lobbies:
                                join_target = lobby.name
                                break
                    
                    # if there are no available lobbies, make one active
                    else:
                        join_target = self.activate_lobby()
                        response += "Opened lobby **{lobby}**.\n".format(lobby=join_target)

            # if we're already in a lobby, check if it's the one we're trying to join
            try:
                current_lobby = self.player_assign[player]
                if join_target == current_lobby:
                    await self.game_channel.send("You're already in **{lobby}**.".format(lobby=current_lobby))
                    return
                # Otherwise, add a "player left **lobby**" message to the response and remove them from the lobby
                else:
                    self.active_lobbies[current_lobby].remove_player(player)

                    response += "{player} left **{lobby}**.\n".format(player=player, lobby=current_lobby) 
            except KeyError:
                pass

            # if lobby is not active, pull it off the open_lobbies list and make it active
            if not join_target in self.active_lobbies:
                try:
                    self.open_lobbies.remove(join_target)
                    self.active_lobbies[join_target] = Lobby(join_target)

                except ValueError:
                    await self.game_channel.send("Couldn't find lobby '{lobby}'".format(lobby=join_target))
                    return

            # Add player to lobby and update player_assign
            response += self.active_lobbies[join_target].add_player(player)
            self.player_assign[player] = join_target

        # data commands
        elif message.content.startswith('$data'):
            # global game_channel
            response = dm.handle_command(message)

            if response == "":
                pass
            else:
                await self.game_channel.send(response)

        # Command to rename commander name in an active game; this has to come *after* the $data commands, which currently use > for renaming database entries
        elif " > " in content:
            
            # check lobby
            try:
                lobby_name = self.get_player_lobby(message.author.name)
            except KeyError:
                await self.game_channel.send("Join a lobby with ``$join`` to use this command.")
                return

            # Get game reference; technically thish should be in a try/except block, but anything that would throw an error will already have thrown an error in the previous try/except block
            game = self.ensure_game_exists(lobby_name)

            # retrieve command information
            content = content.replace("$ ", "")
            content = content.replace("$", "")
            names = content.split(" > ")

            # fire off the rename
            response = game.rename_cmdr(names[0], names[1])

        # $Game commands
        elif content.startswith("$game"):

            # get lobby or return error message if there isn't one
            try:
                lobby_name = self.get_player_lobby(message.author.name)
                player_lobby = self.active_lobbies[lobby_name]
            except KeyError:
                await self.game_channel.send("Join a lobby with ``$join`` to use this command.")
                return

            # if there's no game, we might have to start one            
            if player_lobby.game == None:
                # If they're just checking on game status, let them know there's no game
                if content.startswith("$game status"):
                    await self.game_channel.send("**{lobby_name}** currently has no active game.".format(lobby_name=lobby_name))
                    return
                # otherwise start a new game in the lobby and continue
                else:
                    response += self.new_game_in_lobby(lobby_name)
                    response += "\n"
            # if there's a game but it's a cancel command, we deal with it before it would be handed off to the game object
            elif content.startswith("$game cancel"):
                player_lobby.game = None
                self.game_count -= 1
                await self.game_channel.send("I have cancelled the game for you.")
                return

            # get alias
            alias = self.get_player_alias(message.author.name)
            
            # Pass the message on to the game lobby, then store the result
            game_str = player_lobby.game.handle_command(message, alias, stats)
            
            # If the game ended, clean up
            if game_str == "end":
                # store data
                player_lobby.game.store_data("gamehistory.txt")

                # close the game
                player_lobby.game = None

                # add to response
                response += "Thanks for playing!"
            # otherwise add the return string to the response
            else:
                response += game_str

        # sets bot output to the specified channel
        elif content.startswith("$set output"):
            response = self.set_channel(message.channel)

        # Send confirmation message to Discord
        if response != "":
            await self.game_channel.send(response)
        else:
            # Eventually we'll just end the function call, but right now we're in the middle of a refactor and this lets us access the non-transitioned code below
            # return
            pass





        ######
        # These functions use the pre-lobby architecture
        ######

        if message.content.startswith('$hello'):

            alias = self.get_player_alias(message.author.name)

            if alias:
                await message.channel.send('Hello {alias}!'.format(alias=alias))

            else:
                await message.channel.send('Hello {message.author.name}!'.format(message=message))

        if message.content.startswith("$lorem"):
            lorem = "Token engine firebreathing blinking mono blue Rakdos Steve stabilize Grixis interrupt restricted mono white Rakdos 4 turn clock decking fixing sideboard Selesnya dome Chimney Pimp big butt decking gas bolt 3 drop chump tank token enchantment topdeck mana pool tank dork utility land standard race card swing race nut draw artifact Golgari dig beatstick race hate mono green Sultai pro mana rock Naya pro-blue Vorthos pop off dig for an answer Orzhov CMC wheel Canadian Threshold land for turn Abzan tank maindeck grindy trade blow up Temur nut draw Sultai chump meta top 8 meta combat trick fatty sorcery Blinky power 9 hate mono black pro-black 2 drop drain fixing in the air modern beatstick prison Vorthos stabilize artifact mirror match Chimney Pimp moxen hard cast hydra land drop grinder aggro aggro Simic Esper weenie 4 turn clock 4 turn clock hate exile enchantment Naya Naya big butt cantrip fetch dig reanimate restricted proxy go off legacy grinder protection interrupt maindeck decking Naya Grixis prison creatureball 2 drop hate bear beats wedge 2 drop wheel enchantment vintage playset Temur 4 turn clock mana birds decking vanilla pro-blue EDH shock land wedge crack fetch wheel durdler mill Blinky chump block mana pool curve card pool mana hose dragon reanimate moxes glass cannon Gruul mana dork sorcery clock hate bear fetch token engine mana hose tempo pro-black card Timmy Grixis\n\nCheck land playset threat Izzet shock on a stick allied colors blow up bomb grind in response Grixis value legacy fixing race legacy glass cannon land for turn combo shock land durdler Grixis mulligan reanimate deck hoser Steve proxy wedge Gruul reanimate jankey mana hose aggro response pro-white pro-red combat trick CMC board state token ping Academy bolt mill he's got a bit of an ass on him hate mana pool Jund board presence blow up Canadian Threshold dig color Timmy pro-red prime time mana pool ping reanimator bomb reanimator mulligan dragon gas dork shock keeper man land wheel shock on a stick aggro big butt playset on a stick beefcake synergy reanimate allied colors control Jeskai fixing jankey 1 drop bear Esper 1 drop board presence bomb shell mana birds go wide Boros grindy hard cast pain land vintage cut interrupt sorcery blink Selesnya finisher metagame control reanimate mana screwed beatstick blow up ping board presence Mardu ritual out of gas Gruul card pool bolt archetype stabilize mono black beefcake pro-white chump block dead card bomb pain land blow up pump jankey combo pain land tutor 2 drop beatdown Mardu planeswalker dragon swing hydra fixing Izzet allied colors mana pool nut draw prison control hate bear modern run Jund land for turn legendary cut fixing ETB lethal shock chump voltron Gruul mana dork chump block pro-black moxen restricted playset Bob card pool"
            await self.send_multiple_responses(lorem)

        if message.content.startswith('$randomEDH'):
            await message.channel.send(stats.random_game().game_state())

        if message.content.startswith('$register'):
            # retrieve Discord name and given name from message
            author_name = message.author.name
            alias = message.content
            alias = alias.replace("$register ","")
            alias = alias.replace("$register","")

            if alias:
                # set that value in the alias list
                self.aliases[author_name] = alias
                
                alias_str = "{author_name}&separator;{alias}\n".format(author_name=author_name, alias=alias)

                # save alias to alias list
                with open("alias.txt", "a", -1, "utf8") as alias_list:
                    alias_list.write(alias_str)

                # confirmation message
                await self.game_channel.send("Registered {author} as {alias}!".format(author=author_name, alias=alias))

            else:
                await self.game_channel.send("You need to provide a name to use that command.")

        if message.content.startswith('$notif') or message.content.startswith('$remind'):
            remind = Reminder(message)
            remind.remind()

        if message.content.startswith('$stats'):
            response = await stats.handle_command(message)

            if response == "":
                pass
            else:
                await self.send_multiple_responses(response)

    # Breaks a string into multiple chunks and sends them separately (allowing the bot to send strings larger than Discord's per-message character limit)
    async def send_multiple_responses(self, response):
        while len(response) > 1949:
            await self.game_channel.send(response[:1950])
            response = response[1950:]
        await self.game_channel.send(response)

    # sets the bot's output channel to the given channel
    def set_channel(self, channel_obj):
        self.game_channel = channel_obj
        print( "Set output channel to {channel}.".format(channel=channel_obj))
        return "Set output channel to {channel}.".format(channel=channel_obj)



# create instances of stats engine, data manager, and state manager
stats = Statistics()
dm = Data_Manager()
state_manager = State_Manager()

# We set this value here because the state manager and the stats engine don't talk to each other right now
state_manager.game_count = len(stats.games)

@client.event
async def on_ready():
    print('Bot successfully logged in as: {user}'.format(user=client.user))
    state_manager.set_channel(client.get_channel(config.game_channel_id))
    await state_manager.game_channel.send("Archivist online!")

@client.event
async def on_message(message):
    await state_manager.route_message(message, stats, dm)

client.run(config.bot_token)