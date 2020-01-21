# esv-fighter-verses

This Python application, for the Raspberry Pi, displays FighterVerses, weekly or random, with delay between and LED blink, as reminder to Pray, Rejoice, and Give Thanks to the Lord!

The author has the LED, connected to the IO connector of the Raspberry Pi, mounted beneath one of his computer monitors. He usually sets the mode of operation to display a random Fighter Verse every 15 minutes. The verse will be displayed for the fiften minute interval. When the interval expires, the LED will blink to gain his attention, and to remind him to take a moment to read and prayerfully meditate on the Scripture. Pressing the return key will turn off the LED and randomly display a new Fighter Verse and start the countdown again.

This program retrieves and caches Scripture using the Crossway ESV Bible API. A token is required to access the ESV API. This token may be requested from https://api.esv.org/. The token must be provided with the -t command line argument. This is a one time requirement. Once entered, the token is pickled and saved. Please do not publish your plain text token or the pickled esv_token file. The retrieved Scripture verses are cached locally to reduce the load on the ESV server.

Fighter Verses, https://fighterverses.com/the-verses/fighter-verses/, focus on

 1) the character and worth of our great God,
 2) battling against our fleshly desires, and
 3) the hope of the Gospel.

This five-year memory program is broken down into five sets with one verse or passage per week.

The Fighter Verses were downloaded as a CSV file from the above link. This CSV file has been converted into a Python compound
dictionary and is found in fighterversesdict.py.

An enhancement to this program is being developed to act as a morning alarm clock. Upon the set time, the program will audibly play Scripture, based on the day's Discipleship Journal Bible Reading Plan, or a plan of your own. The audio will be retrieved from the Crossway ESV Bible API. The idea for a Scripture reading alarm clock is from an interview with John Piper on Desiring God https://www.desiringgod.org/interviews/dont-waste-your-mornings.
