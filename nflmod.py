# IMPORTS
import os, datetime as dt, pandas as pd, numpy as np, requests, gspread, csv, smtplib, ssl
from email.message import EmailMessage

# RESOURCES
teams = pd.read_csv('G:/My Drive/pers/nfl2025/csv/teams.csv')
with open('G:/My Drive/pers/nfl2025/csv/emails.csv', newline='') as e:
    reader = csv.reader(e)
    emailist = list(reader)
emails = [''.join(e) for e in emailist]

# FUNCTION FOR LINE RETRIEVAL, EMAILING TO PLAYERS AND PUBLISHING TO CONTEST SPREADSHEET 
def get_lines(write = 'N', send = 'N', recip = emails, nflweek=None):
    '''Retrieve lines from API, format, prepare and send lines email to players, write lines to contest spreadsheet.
    Arguments: (write, send, recip, nflweek).
    'write' defaults to 'N' and must be 'Y' to write to the contest spreadsheet. 
    'send' defaults to 'N' and must be 'Y' to email lines to players. 
    'recip' (default 'emails') takes the variable emails (current players), another list of emails, or a single email address in quotes.
    'nflweek' default is a calculation of current nfl week.
    A routine execution would be: get_lines(emails, 'Y'). nflweek is necessary only for non-current week.
    '''
    if nflweek == None:
        week = int((dt.datetime.today() - dt.timedelta(2)).strftime('%U'))
        nflweek = week - 34 if week > 34 else week + 18
    w = nflweek
    
    if send != 'Y': 
        recip = None
    
    # API CALL 
    url = "https://odds.p.rapidapi.com/v4/sports/americanfootball_nfl/odds"
    querystring = {"regions":"us","oddsFormat":"american","markets":"spreads","dateFormat":"iso"}
    headers = {
        'x-rapidapi-host': "odds.p.rapidapi.com",
        'x-rapidapi-key': "6205283aa4msh8f78a13b7f21888p1888c8jsn66fd82188693"
        }
    response = requests.request("GET", url, headers=headers, params=querystring)
    nfl_lines = response.json()

    # EXTRACT POINT SPREAD SIDES (From API results, retains FanDuel lines)
    lines = []
    for game in range(len(nfl_lines)):
        kickoff = (pd.to_datetime(nfl_lines[game]['commence_time'],utc=True)).tz_convert('US/Eastern')
        date = str(kickoff.date())
        day = dt.datetime.strptime(date, '%Y-%m-%d').strftime('%A')
        time = str(kickoff.time())
        NFLweek = (kickoff-dt.timedelta(1)).week-35
        away = nfl_lines[game]['away_team']
        home = nfl_lines[game]['home_team']
        g=[NFLweek,day,date,time,away,home]
        for book in range(len(nfl_lines[game]['bookmakers'])):
            sportsbook = nfl_lines[game]['bookmakers'][book]['title']
            for side in range(len(nfl_lines[game]['bookmakers'][book]['markets'][0]['outcomes'])):
                team = ((nfl_lines[game]['bookmakers'][book]['markets'][0]['outcomes'][side]['name']))
                line = ((nfl_lines[game]['bookmakers'][book]['markets'][0]['outcomes'][side]['point']))
                updated = ((nfl_lines[game]['bookmakers'][book]['last_update']))
                price = ((nfl_lines[game]['bookmakers'][book]['markets'][0]['outcomes'][side]['price']))
                if sportsbook == 'FanDuel':
                    g.append([sportsbook,team,line,price,updated])
        lines.append(g)

    # EXTRACT GAME AND LINE INFORMATION (SIDES)
    homegames=[]
    awaygames=[]
    for l in lines:
        if len(l) >= 7:
            away=[l[0],'away',l[3],l[1],l[2],l[6][2]]
            homegames.append(away)
        if len(l) >= 7:
            home=[l[0],'home',l[4],l[1],l[2],l[7][2]]
            awaygames.append(home)
    sides = homegames + awaygames 
    sidesdf = pd.DataFrame(sides, columns=['week','home_away','team','date','time','line'])

    # FLATTEN LINES FOR DISTRIBUTION, SEPARATE THURS/FRI
    linesflat=[]
    sendlines=[]
    for l in lines:
        if (l[0] == w) & (len(l) >= 7):
            if l[4] == l[6][1]:
                spread = str(l[6][2])
            if l[4] == l[7][1]:
                spread = str(l[7][2])
            linesflat.append([l[0],l[1],l[5], float(spread)*-1])
            if float(spread) > 0:
                spread = '+' + spread
            sendlines.append(str(f'{l[4]} {spread} @ {l[5]}, {l[1]} {l[2]}'))
    thursend=[]
    sunsend=[]
    for l in sendlines:
        if ("Thursday" in l) | ("Friday" in l):
            thursend.append(l)
        if ("Saturday" in l) | ("Sunday" in l) | ("Monday" in l):
            sunsend.append(l)
    # PREPARE EMAIL TO PLAYERS
    def email_lines(recip):
        if int(dt.datetime.today().weekday()) in ([1,2,3]):
            lineday = "Thursday"
        if int(dt.datetime.today().weekday()) in ([4,5,6,7]):
            lineday = "Sunday/Monday"

        if lineday == "Thursday":
            linesend = thursend
        if lineday == "Sunday/Monday":
            linesend = sunsend

        # Create the message
        msg = EmailMessage()
        
        # Prepare the email body with the clickable link
        html_content = f"""
        <html>
        <body>
            <p>{'<br>'.join(linesend)}</p>
            <p><a href="https://x.gd/sQUak">Make your picks here.</a></p>
            <p></p> <!-- Blank line -->
            <p><a href="https://x.gd/Ch1Z6">Standings are available here.</a></p>
        </body>
        </html>
        """
        
        # Set the content as HTML
        msg.add_alternative(html_content, subtype="html")

        # Subject, sender, and recipient
        msg["Subject"] = f"Week {w}: {lineday} Line(s)"
        msg["From"] = f"Degen Contest 2025 <degens2019@gmail.com>"
        msg["To"] = recip

        # Email sending process
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", port=587) as smtp:
            smtp.starttls(context=context)
            smtp.login("degens2019@gmail.com", "lerr oamv egga ofwp")
            smtp.send_message(msg)

        return linesend
    
    # SEND EMAIL TO PLAYERS            
    if recip != None: email_lines(recip)
    
    # PREPARE LINES FOR WRITING TO SCORESHEET
    linesdf = pd.DataFrame(linesflat, columns = ['nflweek','day','longteam','line'])
    linesdf = linesdf.merge(teams, on = 'longteam')
    linesdf['homekey'] = linesdf.team + (linesdf.nflweek).astype(str)
    linesdf = linesdf[['nflweek','day', 'homekey', 'line']]

    # Thurs/Fri
    thurslinesdf = linesdf[['nflweek','homekey','line']].loc[linesdf.day.isin(['Thursday','Friday'])].loc[linesdf.nflweek == w]

    # Sun/Mon
    sunlinesdf = linesdf[['nflweek','homekey','line']].loc[linesdf.day.isin(['Sunday','Monday'])].loc[linesdf.nflweek == w]

    if int(dt.datetime.today().weekday()) in ([4,5,6,7]): addl = sunlinesdf
    if int(dt.datetime.today().weekday()) in ([1,2,3]): addl = thurslinesdf

    # DEFINE FUNCTION TO ADD LINES TO CONTEST SPREADSHEET
    def add_lines():
        gc = gspread.service_account(filename="service_account.json")
        contestbeta = gc.open("NFL_Pool_2025")
        lineinput = contestbeta.worksheet("lineinput")
        linesgs = pd.DataFrame(lineinput.get_all_records())
        linesgs = pd.concat([linesgs, addl], axis = 0)
        linesgs = linesgs.drop_duplicates(subset = ['homekey'], keep = 'last', ignore_index = True)
        lineinput.update([linesgs.columns.values.tolist()] + linesgs.values.tolist())
        

    # WRITE LINES TO CONTEST SPREADSHEET
    if write == 'Y': 
        add_lines()
    
    return (linesdf)

# FUNCTION TO READ IN PICKS FROM GOOGLE SHEETS, CHECK TIMESTAMPS AND RECORD ON THE SCORESHEET
def get_picks(picksday='X', w = None):
    ''' Retrieve picks from Form data, process picks, print late picks (if any), writes picks to contest spreasheet.
        Arguments = (picksday=None, w=nflweek). 
        'picksday' must be either 'T' (Thurs) or 'S' (all) to execute a spreadsheet write. Submit other character  or None to view only.
        'w' will be set to current nflweek if no value is entered
    '''
    try:
        w = int(w)
    except ValueError:
        w = None

    if w not in range(1, 19):
        w = None

    if w is None:
        w = int((dt.datetime.today() - dt.timedelta(2)).strftime('%U')) - 34
    # READ IN RESOURCES
    sched = pd.read_csv('./csv/sched.csv')
    sides = pd.read_csv('./csv/sides.csv')
    names = pd.read_csv('./csv/names.csv')

    gc = gspread.service_account(filename="service_account.json")
    contest = gc.open("NFL_Pool_2025")
    picksheet = gc.open("NFL 2025 (Responses)")
    gspicks = picksheet.worksheet("Form Responses 1")

    allpicks = pd.DataFrame(gspicks.get_all_records())
    # pull picks for selected week, break into columns and retain first word (team name)
    weekpicks = allpicks[['Timestamp','Name',f'Week {w} Picks']].dropna()
    weekpicks = weekpicks.mask(weekpicks == '').dropna()
    weekpicks = weekpicks.rename(columns ={'Timestamp':'timestamp','Name':'name',f'Week {w} Picks':'picks'})

    # split where '), ' is followed by ALL-CAPS team name and an opening parenthesis
    sep = r'\), (?=[A-Z0-9 .&-]+\s\()'

    parts = weekpicks['picks'].str.split(sep, expand=True)  # -> 5 columns for your example
    weekpicks = weekpicks[['timestamp','name']].merge(parts, left_index=True, right_index=True)
    weekpicks = weekpicks.rename(columns={0:'pick1',1:'pick2',2:'pick3',3:'pick4',4:'pick5'})

    weekpicks = weekpicks.rename(columns = {0:'pick1',1:'pick2',2:'pick3',3:'pick4',4:'pick5'})
    for p in ['pick1','pick2','pick3','pick4','pick5']:
        if p in weekpicks:
            weekpicks[p] = weekpicks[p].str.split().str[0].str.title() + str(w)
    weekpicks = weekpicks.replace(f'49Ers{w}',f'49ers{w}')
    weekpicks.sort_values(by='name')
    weekpicks.head(10)

    # MERGE PICKS TO SINGLE COLUMN AND COMBINE WITH SIDES DATAFRAME TO GET GAME DATES, MARK THU/FRI/SAT GAMES
    picks = pd.DataFrame()
    for p in ['pick1','pick2','pick3','pick4','pick5']:
        if p in weekpicks.columns:
            pickx = weekpicks[['timestamp','name',p]]
            pickx = pickx.rename(columns={p:'pick'})
            picks = pd.concat([picks,pickx])
    picks=picks.dropna().sort_values(by=["name","pick"])
    picks.head(20)

    picks = picks.merge(sides[['rotat','date','kickoff']], left_on = 'pick', right_on = 'rotat').drop(columns = ['rotat'])
    picks['weekday'] = pd.to_datetime(picks['date']).dt.dayofweek
    picks['thurs'] = np.where(np.isin(picks.weekday,(3)),1,0)
    picks['fri'] = np.where(np.isin(picks.weekday,(4)),1,0)
    picks['sat'] = np.where(np.isin(picks.weekday,(5)),1,0)

    # SPLIT PICKS INTO SEPARATE DAYS
    thupicks = picks[['timestamp','name','pick','date','kickoff']][picks.thurs == 1]
    fripicks = picks[['timestamp','name','pick','date','kickoff']][picks.fri == 1]
    satpicks = picks[['timestamp','name','pick','date','kickoff']][picks.sat == 1]

    # DEDUP AND COUNT OFF-DAY PICKS (COUNT SHOULD ALWAYS BE ONE EXCEPT HOLIDAY GAMES-- TXGVG & SOME YEARS XMAS)
    thupicks = thupicks.drop_duplicates(subset=['name','date','kickoff'], keep = 'last', ignore_index=True)
    thupicks = thupicks.merge((thupicks.groupby('name', as_index=False).size()),on='name')
    thupicks = thupicks.rename(columns = {'size':'thucnt'})

    fripicks.drop_duplicates(subset=['name','date','kickoff'], keep = 'last', ignore_index=True)
    fripicks = fripicks.merge((fripicks.groupby('name', as_index=False).size()),on='name')
    fripicks = fripicks.rename(columns = {'size':'fricnt'})

    satpicks.drop_duplicates(subset=['name','date','kickoff'], keep = 'last', ignore_index=True)
    satpicks = satpicks.merge((satpicks.groupby('name', as_index=False).size()),on='name')
    satpicks = satpicks.rename(columns = {'size':'satcnt'})

    # MERGE COUNTS OF OFF-DAY PICKS BACK TO PICKS DF
    picks = picks.merge(thupicks[['timestamp','name','pick','thucnt']], how='left', on=['timestamp','name','pick'])
    picks = picks.merge(fripicks[['timestamp','name','pick','fricnt']], how='left', on=['timestamp','name','pick'])
    picks = picks.merge(satpicks[['timestamp','name','pick','satcnt']], how='left', on=['timestamp','name','pick'])
    picks = picks.drop_duplicates(subset=['name','pick'], keep = 'last', ignore_index=True)

    picks.thucnt = picks.thucnt.fillna(0)
    picks.fricnt = picks.fricnt.fillna(0)
    picks.satcnt = picks.satcnt.fillna(0)
    picks = picks.sort_values(by=['name','timestamp'], ascending = [True,False])

    # SELECT EARLY-DAY PICKS AND MOST RECENT SUNDAY PICKS, DISCARD OTHERS
    picks['rank'] = picks.sort_values(by=['thurs','fri','sat','timestamp'], ascending = [False, False, False, False]).groupby('name').cumcount(ascending = True) + 1 
    picks = picks[picks['rank'] <=5]

    # PIVOT TO WIDE FORMAT FOR CONTEST WORKBOOK
    wl = len(str(w))

    picksout = picks
    picksout['pick'] = picksout.pick.str[:-wl]
    picksout = names.merge(picksout, how = 'left', on='name')
    picksout = picksout.pivot(values = 'pick', index='rank', columns=['name']).reset_index()
    picksout = picksout.drop(columns=['rank']).dropna(how='all').fillna('')

    thpicksout = picks[picks.thurs == 1]
    thpicksout = names.merge(thpicksout, how = 'left', on='name')
    thpicksout = thpicksout.pivot(values = 'pick', index='rank', columns=['name']).reset_index()
    thpicksout = thpicksout.drop(columns=['rank']).dropna(how='all').fillna('')

    picks['timestamp'] = pd.to_datetime(picks['timestamp']).dt.tz_localize('America/Los_Angeles')
    picks['kickstamp'] = (pd.to_datetime(picks['date'] + ' ' + picks['kickoff'])).dt.tz_localize('US/Eastern')
    picks['latepick'] = np.where((picks['timestamp'] - picks['kickstamp'] > dt.timedelta(minutes=2)), 1, 0)

    # PRINT LATE PICKS (IF PRESENT)
    if picks.latepick.sum() > 0: 
        print(picks[picks['latepick'] == 1])
    if picks.latepick.sum() == 0: 
        print('No late picks found.')
    
    # SPECIFY WORKSHEET WRITE SPACE
    pickinput = contest.worksheet("pickinput")
    startcell = 'B' + str(((w-1)*5)+2)
    endcell = 'X' + str(((w-1)*5)+6)
    #############################################################################
    # # THURSDAY
    # # WRITE PICKS TO INPUT SHEET OF CONTEST WORKOOK
    if picksday == 'T': pickinput.update(f'{startcell}:{endcell}', thpicksout.values.tolist())
    #############################################################################
    #############################################################################
    # # SUNDAY (ALL PICKS FOR WEEK -- INCLUDES THURS)
    # # WRITE PICKS TO INPUT SHEET OF CONTEST WORKOOK
    if picksday == 'S': pickinput.update(f'{startcell}:{endcell}', picksout.values.tolist())
    ############################################################################
    print (picks[['timestamp','name','pick','date','kickoff','latepick']])
    return picks[['timestamp','name','pick','date','kickoff','latepick']]

# %%
# FUNCTION TO RETRIEVE GAME SCORES AND WRITE TO CONTEST SPREADSHEET
def get_scores(day1=None, day2=None):
    """Retrieve scores, format scores, write to contest spreadsheet.
        Arguments:(day1, day2). Defaults: day1=current day, day2=previous day. Both accept 'YYYY-MM-DD' string values.
    """
    if day1 is None:
        day1 = str((dt.datetime.today()).strftime('%Y-%m-%d')) #set day1 to today
    if day2 is None:
        day2 = str((dt.datetime.today()-dt.timedelta(days=1)).strftime('%Y-%m-%d')) #set day2 to yesterday
        print(f"Day 1: {day1}, Day 2: {day2}")
    gamedates = f"{day1},{day2}"
    url = "https://sportspage-feeds.p.rapidapi.com/games"
    querystring = {"league":"NFL", "date":gamedates}
    headers = {
        "X-RapidAPI-Key": "6205283aa4msh8f78a13b7f21888p1888c8jsn66fd82188693",
        "X-RapidAPI-Host": "sportspage-feeds.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)

    # FORMAT RETRIEVED SCORES
    rawscore = response.json()
    games=[]
    for game in rawscore['results']:
        if game['status'] == 'final':
            games.append(game)

    scores=[]
    for g in range(len(games)):
        date = games[g]['schedule']['date']
        datefmt = dt.datetime.strptime(date,"%Y-%m-%dT%H:%M:%S.%fZ")
        away = games[g]['teams']['away']['mascot']
        home = games[g]['teams']['home']['mascot']
        awaypts = games[g]['scoreboard']['score']['away']
        homepts = games[g]['scoreboard']['score']['home']
        scores.append([date, away, awaypts, home, homepts])
    scoresdf = pd.DataFrame(scores, columns=['date','away','awaypts','home','homepts'])
    scoresdf.date = pd.to_datetime(scoresdf.date)

    # calculate schedule week by taking week of year, adding 52 for january games, then subtracting the 35wks before season
    scoresdf['nflweek'] = (scoresdf.date-dt.timedelta(days=3)).dt.isocalendar().week + ((scoresdf.date.dt.year-2025)*52) - 35
    scoresdf['awaykey'] = scoresdf.away + scoresdf.nflweek.astype(str)
    scoresdf['homekey'] = scoresdf.home + scoresdf.nflweek.astype(str)
    writescoresdf = scoresdf[['nflweek','awaykey','homekey','awaypts','homepts']]

    # OPEN CONTEST SPREADSHEET AND READ IN EXISTING SCORES
    gc = gspread.service_account(filename="service_account.json")
    contestbeta = gc.open("NFL_Pool_2025")
    scoreinput = contestbeta.worksheet("scoreinput")

    # ADD NEW SCORES TO DATAFRAME AND DEDUPLICATE
    allscores = pd.DataFrame(scoreinput.get_all_records())
    allscores = pd.concat([allscores, writescoresdf], axis = 0)
    allscores = allscores.drop_duplicates(keep = 'last', ignore_index = True).sort_values(by = 'nflweek')

    # UPDATE CONTEST SPREADSHEET
    scoreinput.update([allscores.columns.values.tolist()] + allscores.values.tolist())
    return (writescoresdf)