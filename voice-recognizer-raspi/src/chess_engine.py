# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Carry out voice commands by recognising keywords."""

import datetime
import logging
import subprocess

import actionbase

import chess
import chess.uci

import inspect

board = chess.Board()
engines = chess.uci.popen_engine("/usr/games/stockfish")
engines.uci()

# =============================================================================
#
# Hey, Makers!
#
# This file contains some examples of voice commands that are handled locally,
# right on your Raspberry Pi.
#
# Do you want to add a new voice command? Check out the instructions at:
# https://aiyprojects.withgoogle.com/voice/#makers-guide-3-3--create-a-new-voice-command-or-action
# (MagPi readers - watch out! You should switch to the instructions in the link
#  above, since there's a mistake in the MagPi instructions.)
#
# In order to make a new voice command, you need to do two things. First, make a
# new action where it says:
#   "Implement your own actions here"
# Secondly, add your new voice command to the actor near the bottom of the file,
# where it says:
#   "Add your own voice commands here"
#
# =============================================================================

# Actions might not use the user's command. pylint: disable=unused-argument


# Example: Say a simple response
# ================================
#
# This example will respond to the user by saying something. You choose what it
# says when you add the command below - look for SpeakAction at the bottom of
# the file.
#
# There are two functions:
# __init__ is called when the voice commands are configured, and stores
# information about how the action should work:
#   - self.say is a function that says some text aloud.
#   - self.words are the words to use as the response.
# run is called when the voice command is used. It gets the user's exact voice
# command as a parameter.

class SpeakAction(object):

    """Says the given text via TTS."""

    def __init__(self, say, words):
        self.say = say
        self.words = words

    def run(self, voice_command):
        self.say(self.words)


# Example: Tell the current time
# ==============================
#
# This example will tell the time aloud. The to_str function will turn the time
# into helpful text (for example, "It is twenty past four."). The run function
# uses to_str say it aloud.

class SpeakTime(object):

    """Says the current local time with TTS."""

    def __init__(self, say):
        self.say = say

    def run(self, voice_command):
        time_str = self.to_str(datetime.datetime.now())
        self.say(time_str)

    def to_str(self, dt):
        """Convert a datetime to a human-readable string."""
        HRS_TEXT = ['midnight', 'one', 'two', 'three', 'four', 'five', 'six',
                    'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']
        MINS_TEXT = ["five", "ten", "quarter", "twenty", "twenty-five", "half"]
        hour = dt.hour
        minute = dt.minute

        # convert to units of five minutes to the nearest hour
        minute_rounded = (minute + 2) // 5
        minute_is_inverted = minute_rounded > 6
        if minute_is_inverted:
            minute_rounded = 12 - minute_rounded
            hour = (hour + 1) % 24

        # convert time from 24-hour to 12-hour
        if hour > 12:
            hour -= 12

        if minute_rounded == 0:
            if hour == 0:
                return 'It is midnight.'
            return "It is %s o'clock." % HRS_TEXT[hour]

        if minute_is_inverted:
            return 'It is %s to %s.' % (MINS_TEXT[minute_rounded - 1], HRS_TEXT[hour])
        return 'It is %s past %s.' % (MINS_TEXT[minute_rounded - 1], HRS_TEXT[hour])


# Example: Run a shell command and say its output
# ===============================================
#
# This example will use a shell command to work out what to say. You choose the
# shell command when you add the voice command below - look for the example
# below where it says the IP address of the Raspberry Pi.

class SpeakShellCommandOutput(object):

    """Speaks out the output of a shell command."""

    def __init__(self, say, shell_command, failure_text):
        self.say = say
        self.shell_command = shell_command
        self.failure_text = failure_text

    def run(self, voice_command):
        output = subprocess.check_output(self.shell_command, shell=True).strip()
        if output:
            self.say(output)
        elif self.failure_text:
            self.say(self.failure_text)


# Example: Change the volume
# ==========================
#
# This example will can change the speaker volume of the Raspberry Pi. It uses
# the shell command SET_VOLUME to change the volume, and then GET_VOLUME gets
# the new volume. The example says the new volume aloud after changing the
# volume

class VolumeControl(object):

    """Changes the volume and says the new level."""

    GET_VOLUME = r'amixer get Master | grep "Front Left:" | sed "s/.*\[\([0-9]\+\)%\].*/\1/"'
    SET_VOLUME = 'amixer -q set Master %d%%'

    def __init__(self, say, change):
        self.say = say
        self.change = change

    def run(self, voice_command):
        res = subprocess.check_output(VolumeControl.GET_VOLUME, shell=True).strip()
        try:
            logging.info("volume: %s", res)
            vol = int(res) + self.change
            vol = max(0, min(100, vol))
            subprocess.call(VolumeControl.SET_VOLUME % vol, shell=True)
            self.say(_('Volume at %d %%.') % vol)
        except (ValueError, subprocess.CalledProcessError):
            logging.exception("Error using amixer to adjust volume.")

class VolumeChange(object):

    """Changes the volume and says the new level."""

    GET_VOLUME = r'amixer get Master | grep "Front Left:" | sed "s/.*\[\([0-9]\+\)%\].*/\1/"'
    SET_VOLUME = 'amixer -q set Master %d%%'

    def __init__(self, say):
        self.say = say

    def run(self, voice_command):
        res = subprocess.check_output(VolumeControl.GET_VOLUME, shell=True).strip()
        try:
            logging.info("volume: %s", res)
            vol = int(voice_command[14:])
            subprocess.call(VolumeControl.SET_VOLUME % vol, shell=True)
            self.say(_('Volume at %d %%.') % vol)
        except (ValueError, subprocess.CalledProcessError):
            logging.exception("Error using amixer to adjust volume.")

# Example: Repeat after me
# ========================
#
# This example will repeat what the user said. It shows how you can access what
# the user said, and change what you do or how you respond.

class RepeatAfterMe(object):

    """Repeats the user's command."""

    def __init__(self, say, keyword):
        self.say = say
        self.keyword = keyword

    def run(self, voice_command):
        # The command still has the 'repeat after me' keyword, so we need to
        # remove it before saying whatever is left.
        to_repeat = voice_command.replace(self.keyword, '', 1)
        self.say(to_repeat)


class Test(object):

    """Says the given text via TTS."""

    def __init__(self, say):
        self.say = say

    def run(self, voice_command):
        self.say(voice_command)

class NewGame(object):

    def __init__(self, say):
        self.say = say

    def run(self, voice_command):
        global board 
        board = chess.Board()
        if "black" in voice_command:
            self.say(engine())
        else:
            self.say("Your Move")

class PawnMove(object):

    def __init__(self, say, takes):
        self.say = say
        self.takes = takes
    def run(self, voice_command):
        voice_command = voice_command.lower()
        if "be" in voice_command:
            voice_command = voice_command[:-4] + "b" + voice_command[len(voice_command) - 1:]
        try:
            print(voice_command[:2] + voice_command[14:])
            board.push_san(board.san(chess.Move.from_uci(voice_command[:2] + voice_command[14:]))) if self.takes else board.push_san(voice_command[8:])
            self.say(engine())                    
        except ValueError:
            self.say("Invalid Move. Please Try Again")
	
class KnightMove(object):

    def __init__(self, say, takes):
        self.say = say
        self.takes = takes
    def run(self, voice_command):
        voice_command = voice_command.lower()
        if "be" in voice_command:
            voice_command = voice_command[:-4] + "b" + voice_command[len(voice_command) - 1:]
        try:
            if len(voice_command) > 12:
                board.push_san(board.san(chess.Move.from_uci(voice_command[:2] + voice_commnad[-2:])))
            else:
                board.push_san("N" + "x" + voice_command[13:]) if self.takes else board.push_san("N" + voice_command[10:])
            self.say(engine())
        except ValueError:
            self.say("Invalid Move. Please Try Again")

class BishopMove(object):
    def __init__(self, say, takes):
        self.say = say
        self.takes = takes
    def run(self, voice_command):
        voice_command = voice_command.lower()
        if "be" in voice_command:
            voice_command = voice_command[:-4] + "b" + voice_command[len(voice_command) - 1:]
        try:
            if len(voice_command) > 12:
                board.push_san(board.san(chess.Move.from_uci(voice_command[:2] + voice_commnad[-2:])))
            else:
                board.push_san("B" + "x" + voice_command[13:]) if self.takes else board.push_san("B" + voice_command[10:])
            self.say(engine())   
        except ValueError:
            self.say("Invalid Move. Please Try Again")

class RookMove(object):
    def __init__(self, say, takes):
        self.say = say
        self.takes = takes
    def run(self, voice_command):
        voice_command = voice_command.lower()
        if "be" in voice_command:
            voice_command = voice_command[:-4] + "b" + voice_command[len(voice_command) - 1:]
        try:
            if len(voice_command) > 12:
                board.push_san(board.san(chess.Move.from_uci(voice_command[:2] + voice_commnad[-2:])))
            else:
                board.push_san("R" + "x" + voice_command[11:]) if self.takes else board.push_san("R" + voice_command[8:])
            self.say(engine())
            self.say("Your Move")
        except ValueError:
            self.say("Invalid Move. Please Try Again")

class QueenMove(object):
    def __init__(self, say, takes):
        self.say = say
        self.takes = takes
    def run(self, voice_command):
        voice_command = voice_command.lower()
        if "be" in voice_command:
            voice_command = voice_command[:-4] + "b" + voice_command[len(voice_command) - 1:]
        try:
            if len(voice_command) > 12:
                board.push_san(board.san(chess.Move.from_uci(voice_command[:2] + voice_commnad[-2:])))
            else:
                board.push_san("Q" + "x" + voice_command[12:]) if self.takes else board.push_san("Q" + voice_command[9:])
            self.say(engine())
        except ValueError:
            self.say("Invalid Move. Please Try Again")

class KingMove(object):
    def __init__(self, say, takes):
        self.say = say
        self.takes = takes
    def run(self, voice_command):
        voice_command = voice_command.lower()
        if "be" in voice_command:
            voice_command = voice_command[:-4] + "b" + voice_command[len(voice_command) - 1:]
        try:
            if len(voice_command) > 12:
                board.push_san(board.san(chess.Move.from_uci(voice_command[:2] + voice_commnad[-2:])))
            else:
                board.push_san("K" + "x" + voice_command[11:]) if self.takes else board.push_san("K" + voice_command[8:])
            self.say(engine())
        except ValueError:
            self.say("Invalid Move. Please Try Again")

class Castle(object):
    def __init__(self, say, kingside):
        self.say = say
        self.kingside = kingside
    def run(self, voice_command):
        try:
            board.push_san("O-O") if self.kingside else board.push_san("O-O-O")
            self.say(engine())
        except ValueError:
            self.say("Invalid Move. Please Try Again")

def engine():
    say = ""	
    engines.position(board)
    attributes = inspect.getmembers(engines.go(movetime=2000), lambda a:not(inspect.isroutine(a)))
    bestmove = [a[1] for a in attributes if a[0] == 'bestmove']
    comp_move = board.san(bestmove[0])
    board.push_san(comp_move)
    if comp_move == "O-O":
        say = "castle king side"
    elif comp_move == "O-O-O":
        say = "castle queen side"
    elif len(comp_move) == 2:
        say = comp_move
    elif len(comp_move) == 3:
        if comp_move[:1] == "N":
            say = "knight to " + comp_move[1:]
        elif comp_move[:1] == "B": 
            say = "bishop to " + comp_move[1:]
        elif comp_move[:1] == "Q": 
            say = "queen to " + comp_move[1:]
        elif comp_move[:1] == "K": 
            say = "king to " + comp_move[1:]
        elif comp_move[:1] == "R": 
            say = "rook to " + comp_move[1:]
    elif len(comp_move) == 4:
        if "x" in comp_move:
            if comp_move[:1] == "N":
                say = "knight takes " + comp_move[-2:]
            elif comp_move[:1] == "B": 
                say = "bishop takes " + comp_move[-2:]
            elif comp_move[:1] == "Q": 
                say = "queen takes " + comp_move[-2:]
            elif comp_move[:1] == "K": 
                say = "king takes " + comp_move[-2:]
            elif comp_move[:1] == "R": 
                say = "rook takes " + comp_move[-2:]
            else:
                say = comp_move[:1] + "    " + "Pawn takes " + comp_move[-2:]      
        else:
            if comp_move[:1] == "N":
                say = comp_move[1:-2] + "    " + "knight to " + comp_move[-2:]
            elif comp_move[:1] == "B":
                say = comp_move[1:-2] + "    " + "bishop to " + comp_move[-2:]
            elif comp_move[:1] == "Q":
                say = comp_move[1:-2] + "    " + "queen to " + comp_move[-2:]
            elif comp_move[:1] == "K":
                say = comp_move[1:-2] + "    " + "king to " + comp_move[-2:]
            elif comp_move[:1] == "R":
                say = comp_move[1:-2] + "    " + "rook to " + comp_move[-2:]   
    elif len(comp_move) == 5:
        if comp_move[:1] == "N":
            say = comp_move[1:-3] + "    " + "knight takes " + comp_move[-2:]
        elif comp_move[:1] == "B":
            say = comp_move[1:-3] + "    " + "bishop takes " + comp_move[-2:]
        elif comp_move[:1] == "Q":
            say = comp_move[1:-3] + "    " + "queen takes " + comp_move[-2:]
        elif comp_move[:1] == "K":
            say = comp_move[1:-3] + "    " + "king takes " + comp_move[-2:]
        elif comp_move[:1] == "R":
            say = comp_move[1:-3] + "    " + "rook takes " + comp_move[-2:]
    if board.is_check():    
        say = say + "           "  + "Check" 
    say = say + "           "  + "Your Move"
    if board.is_checkmate():
        say = "Checkmate"
    elif board.is_game_over():
        say = "Draw"
    return say


# =========================================
# Makers! Implement your own actions here.
# =========================================

def make_actor(say):
    """Create an actor to carry out the user's commands."""

    actor = actionbase.Actor()
    
    #actor.add_keyword(_('ip address'), SpeakShellCommandOutput(say, "ip -4 route get 1 | head -1 | cut -d' ' -f8",_('I do not have an ip address assigned to me.')))

    actor.add_keyword(_('set volume to'), VolumeChange(say))
    #actor.add_keyword(_('max volume'), VolumeControl(say, 100))
    #actor.add_keyword(_('mute'), VolumeControl(say, -100))
    actor.add_keyword(_('shut down'), SpeakShellCommandOutput(say, "poweroff",_('L')))    
    
    #actor.add_keyword(_('name'), SpeakShellCommandOutput(say, "hostname -I",_('L')))   
    
    #steps
    #new game
    actor.add_keyword(_('new game'), NewGame(say))
    #black or white
    #move
    actor.add_keyword(_('pawn to'), PawnMove(say, False))
    actor.add_keyword(_('knight to'), KnightMove(say, False))
    actor.add_keyword(_('bishop to'), BishopMove(say, False))
    actor.add_keyword(_('queen to'), QueenMove(say, False))
    actor.add_keyword(_('king to'), KingMove(say, False))
    actor.add_keyword(_('rook to'), RookMove(say, False))
    actor.add_keyword(_('pawn takes'), PawnMove(say, True))
    actor.add_keyword(_('knight takes'), KnightMove(say, True))
    actor.add_keyword(_('bishop takes'), BishopMove(say, True))
    actor.add_keyword(_('queen takes'), QueenMove(say, True))
    actor.add_keyword(_('king takes'), KingMove(say, True))
    actor.add_keyword(_('rook takes'), RookMove(say, True))
    actor.add_keyword(_('pawn cakes'), PawnMove(say, True))
    actor.add_keyword(_('knight cakes'), KnightMove(say, True))
    actor.add_keyword(_('bishop cakes'), BishopMove(say, True))
    actor.add_keyword(_('queen cakes'), QueenMove(say, True))
    actor.add_keyword(_('king cakes'), KingMove(say, True))
    actor.add_keyword(_('rook cakes'), RookMove(say, True))
    actor.add_keyword(_('king castle'), Castle(say, True))
    actor.add_keyword(_('queen castle'), Castle(say, False))
    actor.add_keyword(_('castle king'), Castle(say, True))
    actor.add_keyword(_('castle queen'), Castle(say, False))
    #check for legality
    #if legal move
    #if illegal ask for another move	
    
    # =========================================
    # Makers! Add your own voice commands here.
    # =========================================
    
    return actor


def add_commands_just_for_cloud_speech_api(actor, say):
    """Add simple commands that are only used with the Cloud Speech API."""
    def simple_command(keyword, response):
        actor.add_keyword(keyword, SpeakAction(say, response))

    simple_command('alexa', _("We've been friends since we were both starter projects"))
    simple_command(
        'beatbox',
        'pv zk pv pv zk pv zk kz zk pv pv pv zk pv zk zk pzk pzk pvzkpkzvpvzk kkkkkk bsch')
    simple_command(_('clap'), _('clap clap'))
    simple_command('google home', _('She taught me everything I know.'))
    simple_command(_('hello'), _('hello to you too'))
    simple_command(_('tell me a joke'),
                   _('What do you call an alligator in a vest? An investigator.'))
    simple_command(_('three laws of robotics'),
                   _("""The laws of robotics are
0: A robot may not injure a human being or, through inaction, allow a human
being to come to harm.
1: A robot must obey orders given it by human beings except where such orders
would conflict with the First Law.
2: A robot must protect its own existence as long as such protection does not
conflict with the First or Second Law."""))
    simple_command(_('where are you from'), _("A galaxy far, far, just kidding. I'm from Seattle."))
    simple_command(_('your name'), _('A machine has no name'))

    actor.add_keyword(_('time'), SpeakTime(say))
