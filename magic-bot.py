import discord
import config
import random

client = discord.Client()
current_game = None

class Game:
    def __init__(self):
        self.players = []
        self.first = []
        self.eliminated = []
        self.winner = []
        self.notes = []
        self.begin = False
        self.game_over = False

    # Given the name of a player, tracks them down in the player list. Returns -1 if not found.  Used to get deck information with spellchecking as a useful consequence.
    def get_player_index(self, player_name):
        
        # search for player in the player list
        index = 0
        for p in self.players:
            # break out of the for loop if we found the name
            if self.players[index][0] == player_name:
                return index
            # otherwise increment
            else:
                index += 1
        # We only get here if the name wasn't in the list, so return -1
        return -1

    # Checks to see if a player has been eliminated
    def get_elim_index(self, player_name):
        # search for player in the elimination list
        index = 0
        for p in self.eliminated:
            # break out of the for loop if we found the name
            if self.eliminated[index][0] == player_name:
                return index
            # otherwise increment
            else:
                index += 1
        # We only get here if the name wasn't in the list, so return -1
        return -1

    def pod_size(self):
        return len(self.players)

    # the main workhorse function of the class; performs a number of basic data commands based on user input
    def handle_command(self, message_obj):
        command = message_obj.content[6:]
        args = command.split(" ")

        if args[0] == "player":
            if not self.begin:
                self.players.append( [args[1], args[2]] )
                return "{player} is playing {deck}".format(player=args[1], deck=args[2])
            else:
                return "Can't add player—game has already started"

        if args[0] == "rename":
            player_index = self.get_player_index(args[1])


        if args[0] == "first":
            if not self.begin:

                player_index = self.get_player_index(args[1])

                # -1 is our failure mode
                if player_index == -1:
                    return 'I was unable to find "{player}" in the list of players for this game.'.format(player=args[1])

                # If the player was found, we get their information from the player list and mark them as eliminated
                else:
                    self.first = self.players[player_index]
                    self.begin = True
                    return "{player} goes first!  Good luck!".format(player=args[1])

            else:
                return "{player} can't go first because the game has already started!".format(player=args[1])

        if args[0] == "elim" or args[0] == "eliminated" or args[0] == "defeat":
            if self.begin:

                player_index = self.get_player_index(args[1])

                # -1 is our failure mode
                if player_index == -1:
                    return 'I was unable to find "{player}" in the list of players for this game.'.format(player=args[1])

                # If the player was found, we get their information from the player list and mark them as eliminated
                else:
                    self.eliminated.append(self.players[player_index])
                    return "Ouch! Better luck next time, {player}!".format(player=args[1])
            else:
                return "{player} could not have been eliminated because the game has not started yet!".format(player=args[1])

        if args[0] == "win" or args[0] == "victory" or args[0] == "winner":
            if self.begin:

                if args[1] == "draw":
                    self.winner = "draw"
                    return "Welp, that must have been interesting."

                else:
                    player_index = self.get_player_index(args[1])

                    if player_index > -1:
                        self.winner = self.players[player_index]
                        self.game_over = True

                        win_str = "Congratulations {player}!".format(player=args[1])

                        win_str += "\n Anyone who wants to comment on the game can now do so by typing:\n```$game note [your note here]```\n"

                        return win_str
                    else:
                        return 'I was unable to find "{player}" in the list of players for this game.'.format(player=args[1])
            else:
                return "{player} could not have been won because the game has not started yet!".format(player=args[1])

        if args[0] == "state" or args[0] == "status":
            self.game_state()
            
        if args[0] == "threat":
            target = random.choice(self.players)
            return "Considered analysis of the situation suggests that {target} is the biggest threat".format(target=target)

        if args[0] == "note":
            if self.game_over:
                # Get author of message
                author = message_obj.author.name
                # Delete the first word of the note (which is "note")
                del args[0]
                # Rejoin to store as a single string
                note_str = " ".join(args)

                note_str = note_str.replace(":", " ")
                note_str = note_str.replace("&", " ")
                note_str = note_str.replace("|", " ")

                self.notes.append( (author, note_str) )
                return "Thanks, {player}".format(player=author)
            else:
                return "The game is not over.  History cannot be written until after it happens."

        if args[0] == "end":
            return "end"

        else:
            return ""

    def game_state(self):
        state_str = ""

        player_str = ""

        if self.players:
            
            pl_list = []

            # for each player
            for pl in self.players:
                elim_index = self.get_elim_index(pl[0])

                pl_str = pl[0] + " (" + pl[1] + ")"

                # if they're eliminated, add strikethrough
                if elim_index > -1:
                    pl_list.append("~~" + pl_str + "~~")
                # otherwise just add the name
                else:
                    pl_list.append(pl_str)

            player_str += "Players: "
            player_str += ", ".join(pl_list)

        else:
            player_str += "No players have been added yet."
        
        state_str += player_str

        first_str = "\n"

        if self.first:
            first_str += self.first[0] + " went first."
        else:
            first_str += "The game has not started yet."

        state_str += first_str

        death_str = ""

        if self.eliminated:
            death_str += "\n" + self.eliminated[0][0] + " died first."
        elif len(self.players) < 3:
            pass
        elif self.game_over:
            death_str += "\nNo one died early."
        else:
            death_str += "\nEveryone's still alive... for now."

        state_str += death_str

        win_str = "\n"

        if self.winner:
            if self.winner == "draw":
                win_str += "The game was a draw.  Somehow."
            else:
                win_str += self.winner[0] + " won the game!"
        else:
            win_str += "The game is not finished yet."

        state_str += win_str

        if self.notes:
            notes_str = "\n\n Contemporary witnesses said:"
            for note in self.notes:
                notes_str += '\n"' + note[1] + '"'
                notes_str += '\n — ' + note[0] + '\n'
            
            state_str += notes_str

        return state_str

    # Parses information from stored games
    def parse_data(self, game_data):
        # Break up the string into data chunks
        data_arr = game_data.split("|")

        # Start by separating the players
        player_arr = data_arr[0].split("&")
        # split up players and their decks, then append to player list
        for player in player_arr:
            self.players.append(player.split(":"))

        # We need to split player from deck but otherwise first player can slot right in
        self.first = data_arr[1].split(":")

        # There might not have been eliminations so we check first
        if data_arr[2]:
            elim_arr = data_arr[2].split("&")
            for victim in elim_arr:
                self.eliminated.append(victim.split(":"))
        
        # Winner is simple like first player
        self.winner = data_arr[3].split(":")

        # Finally we get the notes
        if data_arr[4]:
            notes_arr = data_arr[4].split("&")
            for note in notes_arr:
                self.notes.append(note.split(":"))

        # This probably won't come up, but if we're reading data the game is long over
        self.begin = True
        self.game_over = True

    # Writes the game state to a text file
    def store_data(self, destination):
        if not self.players:
            return
        else:
            player_arr = map(lambda p: p[0] + ":" + p[1], self.players)
            player_str = "&".join(player_arr)

            first_str = self.first[0] + ":" + self.first[1]

            elim_arr = map(lambda p: p[0] + ":" + p[1], self.eliminated)
            elim_str = "&".join(elim_arr)

            win_str = ""
            if self.winner == "draw":
                win_str += "draw"
            else:
                win_str = self.winner[0] + ":" + self.winner[1]

            note_arr = map(lambda n: n[0] + ":" + n[1], self.notes)
            note_str = "&".join(note_arr)
            
            game_str = "|".join([player_str, first_str, elim_str, win_str, note_str])

            with open(destination, "a") as gamehist:
                gamehist.write(game_str + "\n")

class Statistics:
    def __init__(self):
        # We start with an empty games array and read all past games from memory
        self.games = []
        self.refresh()

        self.pods = [True, True, True, True, True, True]
        self.require_players = []
        self.block_players = []
        self.require_cmdrs = []
        self.block_cmdrs = []
        self.require_elim = []
        self.block_elim = []

    # filters the total set of games according to criteria
    def set_filters(self, args):

        allow_pod_modifier: True
        log_str = "Filtering game data..."

        for arg in args:

            # pod size filters
            if "pod" in arg:
                arg = arg.replace("pod", "")

                # do we allow or disallow these pod sizes?
                permission = False
                perm_str = "Disallowed"

                if "+" in arg:
                    permission = True
                    perm_str = "Allowed"
                    arg = arg.replace("+", "")

                elif "-" in arg:
                    arg = arg.replace("-", "")


                # "hard equals" that restricts all results to a specific size; only works on true
                if "==" in arg:
                    arg = arg.replace("==", "")
                    for size in pods:
                        size = False
                    self.pods[int(arg) - 2] = True
                    log_str += "\n • Restricted pod size to {num}".format(num=int(arg))

                # pods with smaller sizes than the given number
                if "<" in arg:
                    arg = arg.replace("<", "")
                    index = int(arg) - 3
                    while index > -1:
                        self.pods[index] = permission
                        index -= 1

                    log_str += "\n • {permission} pod sizes below {index}".format(permission=perm_str, index=index+2)

                # pods larger than the given number
                if ">" in arg:
                    arg = arg.replace(">", "")
                    index = int(arg) - 2
                    while index < 6:
                        self.pods[index] = permission
                        index += 1

                    log_str += "\n • {permission} pod sizes above {index}".format(permission=perm_str, index=int(arg) - 2)

                # pods equal to the given number
                if "=" in arg:
                    arg = arg.replace("=", "")
                    self.pods[int(arg) - 2] = permission
                    log_str += "\n • {permission} pod sizes of {index}".format(permission=perm_str, index=int(arg))

        self.filter_games()
        return log_str

    def filter_games(self):
        # set up new array to filter into
        new_game_array = []

        # iterate through games
        for game in self.games:

            # check against pod size constraints and append if they check out
            index = game.pod_size() - 2
            if self.pods[index]:
                new_game_array.append(game)

        # once we're done, change the games reference to the new array
        self.games = new_game_array

    def reset_filters(self):
        self.pods = [True, True, True, True, True, True]
        self.require_players = []
        self.block_players = []
        self.require_cmdrs = []
        self.block_cmdrs = []
        self.require_elim = []
        self.block_elim = []

    def refresh(self):
        # Read game history from file
        with open("gamehistory.txt", "r") as gamehistory:
            history_arr = gamehistory.read().split("\n")
            # delete the last entry because we know it's a newline
            del history_arr[-1]
            # For each game, create a Game object and append it to the Stats object
            for game_data in history_arr:
                new_game = Game()
                new_game.parse_data(game_data)
                self.games.append(new_game)
        
        return "Successfully loaded game history!"

    def handle_command(self, message_obj):
        args = message_obj.content[7:].split(" ")

        if args[0] == "games" or args[0] == "game":
            del args[0]
            return self.game_stats(args)

        if args[0] == "filter":
            if args[1] == "reset":
                self.reset_filters()
                return "All filters reset."
            else:
                del args[0]
                return self.set_filters(args)

        if args[0] == "refresh":
            return self.refresh()

        else:
            return ""

    def game_stats(self, args):

        # "$stats game totals"
        if args[0] == "total" or args[0] == "totals":
            return "I have records of {total} games.".format(total=len(self.games))

        # "$stats games by ..."
        if args[0] == "by":

            # "...pod"
            if args[1] == "pod":
                # define an array of possible pod sizes, with the first index representing 1v1
                pod_size = [0, 0, 0, 0, 0]
                # For each game, count the players and increment appropriately
                for game in self.games:
                    pod_size[game.pod_size()-2] += 1
                
                response_str = "Here's a breakdown of my records by pod size:"

                # define an index to iterate with the array
                index = 0
                for tally in pod_size:
                    # if there's no games with that pod size we don't print them
                    if tally > 0:
                        response_str += "\n• [{index_value}]: {tally} games".format(index_value=index+2, tally=tally)
                    # increment the index either way
                    index += 1

                return response_str

            # "...deck"
            if args[1] == "deck" or args[1] == "commander":

                # Empty array of commanders to start
                commanders = []
                arr_length = 0

                # Iterate through all games
                for game in self.games:

                    # Get commander names
                    for player in game.players:
                        deck_str = player[1] + " (" + player[0] + ")"

                        # search for it in the arr
                        index = 0
                        for deck in commanders:
                            # if the name matches, increment the count
                            if deck[0] == deck_str:
                                deck[1] += 1
                                break
                            index += 1

                        # if the index matches the array length, our target wasn't there, so we add it with a count of 1
                        if index == len(commanders):
                            commanders.append([deck_str, 1])
                            arr_length += 1
                
                # then we sort the array; NB sort() modifies the original array
                commanders.sort(reverse=True, key=lambda d: d[1])

                # Now that we have our data, we can present it
                response_str = "Here are the most common commanders in my records:"
                display_size = 20
                index = 0
                # we limit display using the above variable
                for deck in commanders:
                    if index < display_size:
                        response_str += "\n • {cmdr}: {total} games".format(cmdr=deck[0], total=deck[1])
                        index += 1
                    else:
                        break
                # then we close up
                if arr_length > display_size:
                    response_str += "\n ...along with {arr_length} more entries.".format(arr_length=arr_length-display_size)

                return response_str

            # "...player"
            if args[1] == "player" or args[1] == "players":
                # Empty array of players to start
                players = []
                arr_length = 0

                # Iterate through all games
                for game in self.games:

                    # Get player names
                    for player in game.players:
                        name_str = player[0]

                        # search for it in the arr
                        index = 0
                        for player_name in players:
                            # if the name matches, increment the count
                            if player_name[0] == name_str:
                                player_name[1] += 1
                                break
                            index += 1

                        # if the index matches the array length, our target wasn't there, so we add it with a count of 1
                        if index == len(players):
                            players.append([name_str, 1])
                            arr_length += 1
                
                # then we sort the array; NB sort() modifies the original array
                players.sort(reverse=True, key=lambda d: d[1])

                # Now that we have our data, we can present it
                response_str = "These are the players in my records:"
                index = 0
                # we only return the 10 most played
                for player in players:
                    if index < 10:
                        response_str += "\n • {player}: {total} games".format(player=player[0], total=player[1])
                        index += 1
                    else:
                        break
                # then we close up
                if arr_length > 10:
                    response_str += "\n ...along with {arr_length} more competitors.".format(arr_length=arr_length-10)

                return response_str


            else:
                return ""


        else: return ""

    def random_game(self):
        return random.choice(self.games).game_state()

stats = Statistics()

@client.event
async def on_ready():
    print('Bot successfully logged in as: {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    print(message)

    if message.content.startswith('$hello'):
        await message.channel.send('Hello {message.author.name}!'.format(message=message))

    if message.content.startswith('$randomEDH'):
        await message.channel.send(stats.random_game())

    if message.content.startswith('$stats'):
        response = stats.handle_command(message)

        if response == "":
            pass
        else:
            await message.channel.send(response)



    if message.content.startswith('$game'):
        # Check if there is is a game
        global current_game

        # user might just be checking if there's a game; we don't need to start a new one in that case
        status_update = message.content.startswith('$game status') or message.content.startswith('$game state')

        if status_update and current_game is None:
            await message.channel.send("There is currently no active game.")
            return


        elif current_game is None:
            # Make a new game
            current_game = Game()
            await message.channel.send("Started a new game!")

        # There's an active game either way at this point, so we have it handle the message
        response = current_game.handle_command(message)

        if response == "end":
            # store game data
            current_game.store_data("gamehistory.txt")
            
            # close out the game
            current_game = None

            # confirmation message
            await message.channel.send("Thanks for playing!")

        elif response == "":
            pass

        else:
            # send the reponse as a message
            await message.channel.send(response)

client.run(config.bot_token)