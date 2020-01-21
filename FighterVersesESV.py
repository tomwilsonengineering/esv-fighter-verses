# coding: utf-8
import time
import sys
import os
import pickle
import signal
import multiprocessing
import logging
import argparse
import csv
import re
import json
import html2text
import requests
import textwrap
import RPi.GPIO as GPIO
import time
from datetime import date
from random import randint
import fighterversesdict as fv

BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
ENDC = '\033[0m'

##################################################################
#
# Set up a process that will receive True, False, and None in its
# queue and take the apropriate action.
#
#   True: Start blinking LED
#  False: Stop blinking LED
#   None: Turn off the LED and exit this process
#
# As a visual reminder to Pray, give thanks, and rejoice in the Lord,
# blink an LED after the Fighter Verse has been displayed for the
# specified amount of time.
#
class BlinkLED(multiprocessing.Process):

    _previousState = False

    def __init__(self, led_pin, enableState_queue, verbose):
        multiprocessing.Process.__init__(self)
        self.enableState_queue = enableState_queue
        self.led_pin = led_pin
        self.enableState = False
        self.verbose = verbose
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.led_pin, GPIO.OUT, initial=GPIO.LOW)


    def run(self):
        proc_name = self.name
        while True:
            # Check our queue to see if __main__ has sent us a new
            # enableState value
            if self.enableState_queue.empty() is True:
                # The queue is empty, continue with the previousState
                self.enableState = self._previousState
            else:
                # The queue is not empty, get the new enableState and
                # update previousState
                self.enableState = self.enableState_queue.get()
                self._previousState = self.enableState
                # Based on enableState, blink the LED, turn off the LED
                # or exit from this process.
            if self.enableState is True:
                # Turn LED ON, delay
                GPIO.output(self.led_pin, 1)
                time.sleep(0.2)
                # Turn LED OFF, (delay at the end of the loop)
                GPIO.output(self.led_pin, 0)
            elif self.enableState is False:
                # Turn LED OFF
                GPIO.output(self.led_pin, 0)
            elif self.enableState is None:
                # None is handled as a poison pill that means shutdown
                # this process. Turn LED OFF
                GPIO.output(self.led_pin, 0)
                GPIO.cleanup(self.led_pin)
                print('[INFO/{}] Exiting: blinkLED: {}'.format(proc_name, False))
                sys.stdout.flush()
                # Exit from this process
                break

            # If verbose, display this process name and the enableState
            if self.verbose is True:
                print('[INFO/{}] chargeEnable: {}'.format(proc_name, self.enableState))
                sys.stdout.flush()
                # This delay throttles this process loop
            time.sleep(0.2)


##################################################################
#
# The Fighter Verse will be displayed for the specified number of
# minutes. Display a countdown of the minutes beneath the verse.
#
#
def waitMinutes(delay):
    print('Waiting: ', end='')
    for i in range(delay, 0, -1):
        print(i ,end=' ')
        sys.stdout.flush()
        time.sleep(60.0)
        time.sleep(1.0)

    print()


##################################################################
#
# Make use of the Crossway ESV Bible API to request the specified
# Scripture passage text.
#
class esvFighterVerse:
    def __init__(self, token):
        self.token = token

    # Using one of the Fighter Verse entries, request the text
    # from the ESV Bible API
    def getVerseText(self, passage):
        token = 'Token ' + self.token
        esvBibleURL = 'https://api.esv.org/v3/passage/text'
        p1 = 'include-footnotes'
        p2 = 'indent-poetry-lines'
        p3 = 'include-footnotes-body'
        p4 = 'indent-poetry'
        p5 = 'include-passage-horizontal-lines'
        p6 = 'include-short-copyright'
        p7 = 'line-length'
        p8 = 'include-heading-horizontal-lines'
        p9 = 'include-headings'
        esvBibleParams = {'q':passage, p1:'false', p2:'3',
                          p3:'false', p4:'true', p5:'false',
                          p6:'true', p7:'70', p8:'false', p9:'false'}
        # Request Bible verse
        request = requests.get(url=esvBibleURL, params=esvBibleParams,
                               headers={'Authorization':token})

        j = json.loads(request.text)
        verseText = j['passages'][0]

        # Regex search and replace to fix the following:
        leftBracket = re.compile('\[')
        verseText = leftBracket.sub(GREEN, verseText)
        rightBracket = re.compile('\]')
        verseText = rightBracket.sub(ENDC, verseText)

        return verseText



##################################################################
#
# This program is a console application written for execution on a
# Raspberry Pi. This is the first meaningful Python program that I
# wrote, after working through the tutorials. - Tom Wilson
#
# Display FighterVerses, weekly or random, with delay between and LED
# blink, as reminder to Pray, Rejoice, and Give Thanks to the Lord!
#
# This program retrieves and caches Scripture using the Crossway ESV
# Bible API. A token is required to access the ESV API. This token may
# be requested from https://api.esv.org/. The token must be provided
# with the -t command line argument. This is a one time
# requirement. Once entered, the token is pickled and saved. Please do
# not publish your plain text token or the pickled esv_token file. The
# retrieved Scripture verses are cached locally to reduce the load on
# the ESV server.
#
# Fighter Verses,
# https://fighterverses.com/the-verses/fighter-verses/, focus on
#
# 1) the character and worth of our great God,
# 2) battling against our fleshly desires, and
# 3) the hope of the Gospel.
#
# This five-year memory program is broken down into five sets with one
# verse or passage per week.
#
# The Fighter Verses were downloaded as a CSV file from the above
# link. This CSV file has been converted into a Python compound
# dictionary and is found in fighterversesdict.py.
#
def main():

    # If there are cached verse texts, as retrieved from the ESV API,
    # pickle.load them into the cached_verses dictionary. If not,
    # create a new dictionary.
    try:
        with open('FighterVersesESV.cached', 'rb') as cached_verses_file:
            cached_verses = pickle.load(cached_verses_file)
    except:
        cached_verses = {}

    # Set up command line argument parsing
    descriptionStr = 'FighterVerses, weekly or random, with delay between and LED blink as reminder to Pray, Rejoice, and Give Thanks!'
    parser = argparse.ArgumentParser(description=descriptionStr)

    # Add parser arguments
    parser.add_argument('-m', action="store", default=0,
                        dest='mins', type=int,
                        help='Delay in minutes')

    # The ESV API token is required only once.
    parser.add_argument('-t', action="store", default='',
                        dest='token', type=str,
                        help='ESV API Token')

    # The -r option will result in a random Fighter Verse selection.
    parser.add_argument('-r', action="store_true", default=False,
                        dest='randomVerse',
                        help='Choose a random Fighter Verse')

    # The -c option will display Fighter Verse one ofter the other,
    # without blinking the LED and waiting for the return key to be
    # pressed.
    parser.add_argument('-c', action="store_true", default=False,
                        dest='continuous',
                        help='Choose a random Fighter Verse')

    parser.add_argument('-v', '--verbose', action="store_true",
                        default=False,
                        dest='verbose',
                        help='verbose output')

    # Parse the command line arguments
    args=parser.parse_args(sys.argv[1:])

    # If a token has been provided for the first time, or the token is
    # being updated, save the token to a file.
    if len(args.token) > 10:
        with open('esv_token', 'wb') as token_file:
            pickle.dump(args.token, token_file)
    else:
        try:
            # If a token file exists, load it as the ESV API key.
            with open('esv_token', 'rb') as token_file:
                args.token = pickle.load(token_file)
        except:
            # If no token provided, exit
            print("")
            exit

    # Instansiate the esv_api with the ESV token
    esv_api = esvFighterVerse(args.token)

    # If no delay between verses was specified, pick a random delay
    if args.mins == 0:
        args.mins = randint(10, 30)

    # Establish a queue for communication with the BlinkLED process
    queue = multiprocessing.Queue()

    # Set logging level to stderr() if --verbose
    multiprocessing.log_to_stderr()
    logger = multiprocessing.get_logger()
    if args.verbose is True:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.NOTSET)

    # Ignore the keyboard interrupt until after our
    # BlinkLED process is started
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Instantiate the BlinkLED process
    consumer = BlinkLED(13, queue, args.verbose)
    # Start the process
    consumer.start()

    # Enable the keyboard interrupt and catch the exception it
    # raises. This is done so that there is time to send a message to
    # the ReceiveControlSender, informing it that it should
    # exit. Prior to its exit, it will send one last message to
    # socketcand to disable charging.
    signal.signal(signal.SIGINT, original_sigint_handler)
    try:

        while True:

            # From today's date, get the year and the week number
            dt = date.isocalendar(date.today())
            year = dt[0] - 2018
            week = dt[1]

            # Use 2018 as year 1 (0, index wise) and add the week to
            # create an index into the list of verses. Each of the 5
            # years of verses has 52 entries, one for each week.
            if args.randomVerse is False:
                # Use the date computed index. This is for verse
                # momorization as the same verse is display for the
                # entire week.
                index = repr(year * 52 + week)
            else:
                # Arg -r was specified, pick one of the verses as
                # random.
                index = repr(randint(0, (52 * 5) - 1))

            # Check the cached_verses{} dictionary for a cached
            # version of the indexed verse. If it exists, set the
            # topic color to BLUE to indicate a cache hit. Otherwise,
            # use the ESV API to retrieve the text for the verse, add
            # it to cached_verses{}, and set the topic color to RED.
            try:
                verse_text = cached_verses[index]['text']
                topic_color = BLUE
            except:
                verse_text = esv_api.getVerseText(fv.fighter_verses[index]['verse'])
                topic_color = RED
                cached_verses[index] = { 'topic': fv.fighter_verses[index]['topic'],
                                         'verse': fv.fighter_verses[index]['verse'],
                                         'text': verse_text }
                with open('FighterVersesESV.cached', 'wb') as cached_verses_file:
                    pickle.dump(cached_verses, cached_verses_file)

            # Praise God! This is what it's all about!
            os.system('clear')
            print()
            print(GREEN + 'Rejoice always, pray without ceasing, give thanks!' + ENDC)
            print()
            print(topic_color + cached_verses[index]['topic'] + ENDC)

            # Display the Fighter Verse text.
            print(verse_text)
            print()

            # Delay for minute count
            waitMinutes(args.mins)

            # If continuous mode is selected, skip the LED blinking
            # while waiting for a newline.
            if args.continuous is False:
                # Delay has ended, enable blinking of the LED while
                # waiting for the Enter key to be pressed. Note that the
                # LED blinking is done as a process because the readline()
                # is a blocking call.
                queue.put(True)
                sys.stdin.readline()

                # Disable blinking of the LED
                queue.put(False)

    # Keyboard interrupt caught. Provides a graceful exit.
    except KeyboardInterrupt:
        print()
        print('[INFO/MainProcess] Caught Keyboard Interrupt')
        # Send the BlinkLED process a poison pill. It will then turn
        # off the LED and then exit its process.
        queue.put(None)
        # Wait for the BlinkLED process to end before exiting.
        consumer.join()

# So that our spawned process, which receives the entire script, will
# not execute main again and thereby spawn processes until a lack of
# resources. This would be a messy...
if __name__ == '__main__':
    main()
