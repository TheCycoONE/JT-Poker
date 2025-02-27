from ..game_logic.dealer import Dealer
from ..game_logic.message_tracker import MessageTracker

class PlayGame(object):

    instance_count = 0  # Class variable to track the number of instances

    def __init__(self, chips=500, ante=5, opponents=["John Wayne", "Jeff Tabb", "Ted Williams"]):
        # Increment the instance count
        PlayGame.instance_count += 1

        # Get the message_tracker game instance 
        self.mtracker = MessageTracker.instance() 

        # store input parameters
        self.mtracker.add_message(f"PlayGame is executing... Instance count: {PlayGame.instance_count}")
        self.OPPONENTS = opponents
        self.CHIPS = chips
        self.ANTE = ante
        
        # initialise game
        self.Configuration()

        # gameloop
        while self.NewHand():
            self.BettingPhase("preflop")
            self.SwitchingPhase()
            self.BettingPhase("postflop")
            self.EvaluationPhase()
        else:
            self.EndGame()

    def Configuration(self):
        #print("Configuring game...")  # Debug print
        # initialise dealer
        self.dealer = Dealer(len(self.OPPONENTS) + 1)
        # get name and begin tracking human
        #player = input("What's your name?")
        player = "Jeff"
        self.HUMAN = player
        # initialise table and economy
        self.dealer.InitializeTable([player], self.OPPONENTS, self.CHIPS)
        self.dealer.UpdateAnte(self.ANTE)

    def NewHand(self):
        # check human has chips
        if not self.dealer.chips.players[self.HUMAN]["stack"]:
            print(f"[END] Game over {self.HUMAN}, better luck next time.")
            self.mtracker.add_message(f"[END] Game over {self.HUMAN}, better luck next time.")
            return False

        # kick bots with few chips
        self.dealer.KickPlayers(self.dealer.SkintPlayers())

        # check amount of players remaining
        if len(self.dealer.TrackedPlayers()) < 2:
            print(f"[END] {self.HUMAN} has won!")
            self.mtracker.add_message(f"[END] {self.HUMAN} has won!")
            return False

        # begin new round
        print(f"\n[NEW ROUND]")
        self.mtracker.add_message(f"\n[NEW ROUND]")
        self.dealer.ShuffleDeck()
        self.dealer.MoveButton()
        self.dealer.TakeAnte()
        self.dealer.DealHands()
        return True

    def BettingPhase(self, phase):
        # determine betting order
        if phase == "preflop":
            action_order = self.dealer.PreflopOrder()
        if phase == "postflop":
            action_order = self.dealer.DealingOrder()
        
        # determine if betting phase can be skipped
        if len(self.dealer.action.ActingPlayers(action_order)) < 2:
            return True

        # begin betting loop
        unfinished = True
        while unfinished:
            # check if each player needs to act
            for name in action_order:
                # skip player if no action is needed
                if self.dealer.action.PlayerHasActed(name):
                    continue
                # get action from player
                info = self.dealer.TableView(name)
                while True:
                    amount = self.dealer.action.SelectAmount(name, info)
                    if self.dealer.TakeBet(name, amount):
                        break
            # track if more actions are needed
            players_are_done = [self.dealer.action.PlayerHasActed(name) for name in action_order]
            unfinished = not all(players_are_done)

        # update player statuses for next round
        self.dealer.action.ExtendRound()
        return True

    def SwitchingPhase(self):
        # determine if switching phase can be skipped
        dealing_order = self.dealer.seats
        if len(self.dealer.action.ShowdownPlayers(dealing_order)) < 2:
            return True

        # begin switching loop
        for name in dealing_order:
            # check if player is allowed to switch cards
            if self.dealer.action.players[name]["has_folded"]:
                continue
            # get action from player
            info = self.dealer.TableView(name)
            while True:
                discards = self.dealer.action.SelectDiscards(name, info)
                if self.dealer.EditHand(name, discards):
                    if name == self.HUMAN and discards:
                        print(f"[CARDS] Your new hand is {self.dealer.cards.players[name]['cards']}")
                        self.mtracker.add_message(f"[CARDS] Your new hand is {self.dealer.cards.players[name]['cards']}")
                    break
        return True

    def EvaluationPhase(self):
        # reward players, collect cards and log player standings
        self.dealer.Payout()
        self.dealer.CollectCards()
        self.dealer.Summary()
    
    def EndGame(self):
        print("[END] Thanks for playing!")
        self.mtracker.add_message("[END] Thanks for playing!")

#if __name__ == "__main__":
    # This runs if the file is executed directly only
    # print("File is trying to execute...")  # Debug print
    # tracker = MessageTracker()  # Use the singleton instance
    # game = PlayGame(message_tracker=tracker)
