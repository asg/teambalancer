import urllib2
import re

class Scraper:
    def scrape(self, player):
        urlend = player.id.replace("#", "-")
        url_base = "https://playoverwatch.com/en-us/career/pc"
        urls = (url_base + "/us/" + urlend, url_base + "/eu/" + urlend)

        # <div class="competitive-rank"><img src="https://blzgdapipro-a.akamaihd.net/game/rank-icons/season-2/rank-3.png"/><div class="u-align-center h6">2183</div>

        parsed_rating = -1

        for url in urls:
            try:
                req = urllib2.urlopen(url)
                if req.getcode() != 404:
                    result = req.read()
                    match = re.search(
                        "\<div class=\"competitive-rank\"\>\<img src=\".+\"/\>\<div class=\"u-align-center h6\"\>([0-9]+)\</div\>",
                        result)
                    sr_maybe = match.group(1)
                    try:
                        parsed_rating = int(sr_maybe)
                    except Exception:
                        print ("-->Could not parse SR for %s, using %d" % (player.name, player.sr))
                break
            except urllib2.HTTPError:
                continue
        if parsed_rating != -1:
            print ("-->Got SR for %s: %d" % (player.name, parsed_rating))
            player.setSR(parsed_rating)
        else:
            print ("-->Rating not found for %s, using %d" % (player.name, player.sr))

        # Generating overbuff profile link and grabbing data
        try:
            profile_link = "https://www.overbuff.com/players/pc/" + urlend + "?mode=competitive"
            response = urllib2.urlopen(profile_link)
            if response.getcode() != 404:
                page_source = response.read()
            # Grab number of lines
            nlines = len(page_source.splitlines())

            # If competitive data is not found, collect quick play data
            if (nlines < 4):
                profile_link = "https://www.overbuff.com/players/pc/" + urlend
                response = urllib2.urlopen(profile_link)
                page_source = response.read()
                # Grab number of lines
                nlines = len(page_source.splitlines())

            # Main hero classes are on the last line
            mains = page_source.splitlines()[nlines - 1]
            # Parse and print sorted hero classes
            parsed_role = 'Flex'
            support = re.findall(r'Support</a><small><span data-time="(.*?)" data-time-format', mains)
            tank = re.findall(r'Tank</a><small><span data-time="(.*?)" data-time-format', mains)
            defense = re.findall(r'Defense</a><small><span data-time="(.*?)" data-time-format', mains)
            offense = re.findall(r'Offense</a><small><span data-time="(.*?)" data-time-format', mains)

            # Collect hero roles based on amount of time played
            heroMains = {}
            try:
                heroMains["Support"] = int(support[0])
                heroMains["Tank"] = int(tank[0])
                heroMains["Defense"] = int(defense[0])
                heroMains["Offense"] = int(offense[0])
                parsed_role = sorted(heroMains.items(), key=lambda (k, v): v, reverse=True)[0][0]
                parsed_backup_role = sorted(heroMains.items(), key=lambda (k, v): v, reverse=True)[1][0]
                print ("-->Got role for %s: %s/%s" % (player.name, parsed_role, parsed_backup_role))
                player.setRole(parsed_role)
            except IndexError:
                print ("-->Could not parse role for %s, using %s" % (player.name, player.role))
        except urllib2.HTTPError:
            print ("-->Could not parse role for %s, using %s" % (player.name, player.role))

    def __init__(self):
        pass


class Player:
    # Default role to flex, and sr to 2300
    def __init__(self, id):
        self.id = id
        self.sr = 2300
        self.role = "Flex"
        display = id.split('#')
        self.name = display[0]

    def getName(self):
        return self.name

    def setSR(self, sr):
        self.sr = sr

    def getWeightedSR(self):
        return float(self.sr) * getWeight(self.sr)

    def getSR(self):
        return self.sr

    def setRole(self, role):
        self.role = role


def readPlayers(fileName):
    filePlayers = []
    f = open(fileName, 'r')
    scraper = Scraper()
    for line in f:
        playerID = line[:-1]
        print playerID
        player = Player(playerID)
        filePlayers.append(player)
        scraper.scrape(player)
    f.close()
    return filePlayers


def getWeight(SR):
    weight = 0.2
    if SR > 1000:
        weight = 0.4
    if SR > 1500:
        weight = 0.6
    if SR > 2000:
        weight = 1
    if SR > 3000:
        weight = 1.2
    if SR > 3500:
        weight = 1.4
    if SR > 4000:
        weight = 1.6
    return weight


# Gonna make it look real nice
def printTeam(team):
    for p in team:
        print("| " + p.getName())


if __name__ == "__main__":
    # Initialize the players
    players = readPlayers('players.txt')
    players.sort(key=lambda x: x.getSR(), reverse=True)

    # Create the two teams
    redTeam = []
    redTeamAverageSR = 0
    redTeamWeightedSR = 0
    blueTeam = []
    blueTeamAverageSR = 0
    blueTeamWeightedSR = 0

    # Greedy algorithm. Sort by weighted SR and pop off
    print ("Begin Sorting")
    for p in players:
        print ("  Sorting " + p.getName())
        if redTeamWeightedSR < blueTeamWeightedSR:
            redTeam.append(p)
            redTeamWeightedSR += p.getWeightedSR()
            redTeamAverageSR += p.getSR()
            print ("    Sorted " + p.getName() + " to red team")
        else:
            blueTeam.append(p)
            blueTeamWeightedSR += p.getWeightedSR()
            blueTeamAverageSR += p.getSR()
            print ("    Sorted " + p.getName() + " to blue team")
    print("Sorting complete")
    print("-------------")

    # Print the teams
    print ("Red Team: " + str((redTeamAverageSR) / len(redTeam)))
    printTeam(redTeam)
    print ("------------")
    print ("Blue Team: " + str((blueTeamAverageSR) / len(blueTeam)))
    printTeam(blueTeam)
