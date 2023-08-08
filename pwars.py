from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
import random
from typing import Any, Callable, Iterable, List, Literal, Tuple

from predicate import Statement

#TODO: Add features in order, in separate commits, one by one...

def _allUnique(iter: Iterable, key: Callable = lambda x: x) -> bool:
    seenKeys = list()
    return not any(key(i) in seenKeys or seenKeys.append(key(i)) for i in iter)

class CardTag(Enum):
    ROCK = 0
    PAPER = 1
    SCISSORS = 2

@dataclass
class Card:
    blank: bool = True
    tag: CardTag | None = None
    powerCost: int | None = None
    effect: Statement | None = None
    creator: int | None = None
    def edit(self, tag: CardTag, powerCost: int, effect: Statement, creator: int):
        self.tag = tag
        self.powerCost = powerCost
        self.effect = effect
        self.creator = creator
        self.blank = False



@dataclass
class Player:
    health: int
    power: int = 100
    cards: List[Card] = field(default_factory=list)
    potency: int = 25
    def editCard(self, cardID: int, toCard: Card) -> bool:
        if self.cards[cardID] == Card():
            self.cards[cardID] = toCard
            return True
        if self.power >= 2 * self.cards[cardID].powerCost:
            self.power -= 2 * self.cards[cardID].powerCost
            self.cards[cardID] = toCard
            return True
        return False



class GameStateType(Enum):
    INITIAL = 0
    CREATION = 1
    EDITING = 2
    CLAIMING = 3
    MAIN = 4

    FINAL = 5
    SUBPROOF = 6
    ADDRULE = 7
    REMOVERULE = 8

    TURN = 9

    RANDPLAYER = 10

GStateInfoType = {
    GameStateType.INITIAL: None,
    GameStateType.CREATION: None,
    GameStateType.EDITING: None,
    GameStateType.CLAIMING: None,

    GameStateType.TURN: int,

    GameStateType.RANDPLAYER: int,
}

@dataclass
class GameState:
    layer: int
    type: GameStateType
    info: Any = None
    @staticmethod
    def randPlayer(self: 'PWars', layer: int) -> 'GameState':
        return GameState(layer, GameStateType.RANDPLAYER, random.randint(0, len(self.players) - 1))
    @staticmethod
    def nextTurn(self: 'PWars', turn: 'GameState') -> 'GameState':
        if turn.type == GameStateType.TURN:
            return GameState(turn.layer, GameStateType.TURN, turn.info + 1 % len(self.players))
        else: raise ValueError("Not a Turn")

class PlayerActionType(Enum):
    EDIT = 0
    TAKEBLANK = 1
    CLAIM = 2

    PLAY = 3
    DISCARD = 4
    CLAIMPLAY = 5
    UNREMAIN = 6
    PROVE = 7

    SUBPROOF = 8
    ADDRULE = 9
    REMOVERULE = 10

@dataclass
class PlayerAction:
    player: int
    type: PlayerActionType
    info: Any = None
    def valid(self, typeReq = None) -> bool:
        if not (typeReq == None or self.type == typeReq): return False
        #Specific checks
        if self.type == PlayerActionType.EDIT: return self.info[1] != Card()
        if self.type == PlayerActionType.TAKEBLANK: return isinstance(self.info, bool)
        if self.type == PlayerActionType.CLAIM: return isinstance(self.info, list) and all(isinstance(claim, tuple) and len(claim) == 2 and all(isinstance(num, int) for num in claim) for claim in self.info)
        ...

        return True

PActInfoType = {
    PlayerActionType.EDIT: Tuple[int, Card],
    PlayerActionType.TAKEBLANK: bool,
    PlayerActionType.CLAIM: List[Tuple[int, int]], #[playerID, cardID]
}

class GameException(Exception): pass

@dataclass
class PWars:
    """
    A game of Predicate Wars.
    """
    INITHEALTHMULT: int = 50
    INITCARDDECK: int = 128
    INITPOWER: int = 100
    INITPOTENCY: int = 128
    INITPLAYER: int = 4
    INITCARDPLAYER: int = 2
    players: List[Player] = field(default_factory=list)
    deck: List[Card] = field(default_factory=list)
    history: List[Tuple[GameState | PlayerActionType]] = field(default_factory=list)
    def __post_init__(self):
        self.players = [Player(self.INITHEALTHMULT * self.INITPLAYER, self.INITPOWER, [Card()] * self.INITCARDPLAYER, self.INITPOTENCY)] * self.INITPLAYER
        self.deck = [Card()] * self.INITCARDDECK
    def currentGameStates(self) -> Tuple[GameState]:
        """
        Get current game states, with layers.
        """
        #TODO: Test this method
        res = ()
        highestLayer = 100000
        state: GameState
        for state in reversed(tuple(filter(lambda x: isinstance(x, GameState), self.history))):
            if state.layer < highestLayer:
                highestLayer = state.layer
                res = (state, ) + res
        return res
    def recentPlayerActions(self) -> Tuple[PlayerAction]:
        """
        Return a list of actions taken by each player in order from most recently played action first, since the latest game state.
        """
        latestGameState = next((len(self.history) - index for index, element in enumerate(self.history[::-1]) if isinstance(element, GameState)), -1)
        return tuple(self.history[latestGameState:])

    #Main functions
    #REFACTOR: Argh-
    def nextGameState(self) -> List[GameState]:
        """
        Returns the next game state.
        """
        #TODO: Implement this method
        #TODO: Test this method

        #Initial gameplay
        if self.history == []: return [GameState(0, GameStateType.INITIAL)]

        gameStates = self.currentGameStates()
        playerActs = self.recentPlayerActions()

        if gameStates == (GameState(0, GameStateType.INITIAL),): return [GameState(0, GameStateType.CREATION)]
        elif gameStates == (GameState(0, GameStateType.CREATION),):
            #On creation phase, handle player choices of taking blanks
            votes = {**{i: False for i in range(len(self.players))}, **{i: bl for i, bl in ((playerAct.player, playerAct.info) for playerAct in playerActs)}}
            count = len(tuple(0 for i in votes.values() if i))
            if count > len(tuple(0 for card in self.deck if Card() == card)): return [GameState.randPlayer(self, 1), GameState(0, GameStateType.EDITING)]
            else: return [GameState(0, GameStateType.EDITING)]
        elif gameStates[0] == GameState(0, GameStateType.EDITING): return [GameState(0, GameStateType.CLAIMING), GameState.randPlayer(self, 1)]
        elif gameStates[0] == GameState(0, GameStateType.CLAIMING) and len(gameStates) == 2 and gameStates[1].type == GameStateType.RANDPLAYER: return [GameState(2, GameStateType.TURN, gameStates[1].info)]
        elif gameStates[0] == GameState(0, GameStateType.CLAIMING) and len(gameStates) == 3 and gameStates[1].type == GameStateType.RANDPLAYER and gameStates[2].type == GameStateType.TURN:
            if GameState.nextTurn(self, gameStates[2]) != GameState(2, GameStateType.TURN, gameStates[1].info): return [GameState.nextTurn(self, gameStates[2])]
            else: return [GameState(0, GameStateType.MAIN)]

        raise GameException('W.I.P')
    def advance(self):
        """
        Advances to a new game state and returns self.
        """
        #TODO: Implement this method

        oldGameStates = self.currentGameStates()
        playerActs = self.recentPlayerActions()
        nextGameStates = self.nextGameState()
        self.history += nextGameStates
        newGameStates = self.currentGameStates()

        if oldGameStates == (GameState(0, GameStateType.CREATION),):
            if nextGameStates[0].type == GameStateType.RANDPLAYER:
                self.players[nextGameStates[0].info].cards.append(Card())
                assert Card() in self.deck, 'Undesired error'
                self.deck.remove(Card())
            else:
                votesInd = (i for i, bl in ((playerAct.player, playerAct.info) for playerAct in playerActs) if bl)
                for i in votesInd:
                    self.players[i].cards.append(Card())
                    self.deck.remove(Card())

        return self
    def action(self, playerAct: PlayerAction) -> bool:
        """
        Executes an action on this game instance, if it's valid.
        Returns whether the action is valid or not.
        """
        #TODO: Test this method
        valid = self.actionValid(playerAct)
        if valid:
            playerActs = self.recentPlayerActions()
            self.history.append(playerAct)
            gameStates = self.currentGameStates()

            #On initial gameplay, edit a card based on the player action
            if gameStates == (GameState(0, GameStateType.INITIAL),):
                self.players[playerAct.player].editCard(playerAct.info[0], playerAct.info[1])

            #On editing phase, edit a card based on the player action
            elif gameStates == (GameState(2, GameStateType.EDITING, None),):
                self.players[playerAct.player].editCard(playerAct.info[0], playerAct.info[1])

            #On claiming phase, claim any card from any player hand and buy it
            elif gameStates[0] == GameState(2, GameStateType.CLAIMING, None):
                powerSpent = sum(self.players[playerId].cards[cardId].power for playerId, cardId in playerAct.info)
                if powerSpent <= self.players[playerAct.player].power:
                    for playerId, cardId in sorted(playerAct.info, key=lambda x: x[1], reverse=True): #sorted function prevents deleting elements affecting indexes
                        self.players[playerAct.player].cards.append(self.players[playerId].cards[cardId])
                        del self.players[playerId].cards[cardId]
            ...

        return valid
    def actionValid(self, playerAct: PlayerAction) -> bool:
        """
        Checks whether the given action is valid.
        """
        #TODO: Implement this method
        #TODO: Test this method
        gameStates = self.currentGameStates()
        playerActs = self.recentPlayerActions()

        if len(gameStates) == 0: return False

        #Initial gameplay
        if gameStates == (GameState(0, GameStateType.INITIAL, None),) and \
        all(playerAct.valid(PlayerActionType.EDIT) for playerAct in playerActs + (playerAct,)): return True

        #Creation phase
        if gameStates == (GameState(0, GameStateType.CREATION, None),) and \
        all(playerAct.valid(PlayerActionType.TAKEBLANK) for playerAct in playerActs + (playerAct,)) and \
        _allUnique(playerActs + (playerAct,), key=lambda x: x.player): return True

        #Editing phase
        if gameStates == (GameState(0, GameStateType.EDITING, None),) and \
        all(playerAct.valid(PlayerActionType.EDIT) for playerAct in playerActs + (playerAct,)) and \
        _allUnique(playerActs + (playerAct,), key=lambda x: x.player): return True

        #Claiming phase
        if gameStates[0] == GameState(0, GameStateType.CLAIMING, None) and \
        len(gameStates) == 3 and gameStates[2].type == GameStateType.TURN and \
        all(playerAct.valid(PlayerActionType.CLAIM) for playerAct in playerActs + (playerAct,)) and \
        len(playerActs) == 0 and playerAct.player == gameStates[2].info and playerAct.type == PlayerActionType.CLAIM and \
        len(playerAct.info) <= 8: return True
        ...
        return False
