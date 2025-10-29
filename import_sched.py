# %% imports
import pandas as pd
sched = pd.read_csv('csv\\nfl-2025-UTC.csv')

# %% dates and times
sched.head()
sched['kick_utc'] = pd.to_datetime(sched['datetime'], dayfirst=True, utc=True)
sched['kick_est'] = sched['kick_utc'].dt.tz_convert('US/Eastern')
sched['kickdatestr'] = sched['kick_est'].dt.strftime("%m/%d/%Y")
sched['gameday'] = sched['kick_est'].dt.strftime("%a")
sched['home'] = sched['hometeam'].str.split().str[-1]
sched['away'] = sched['awayteam'].str.split().str[-1]
sched.head()
# %% pickchoices
matches = sched[['nflweek','kickdatestr','gameday','away','home']]
matches.head(35)

pickchoices=[]
for row in matches.itertuples(index=False):
    pickchoices.append(
        f"{row.away.upper()} (@ {row.home}, Wk {row.nflweek}, {row.gameday}, {row.kickdatestr})"
    )
    pickchoices.append(
        f"{row.home.upper()} (vs {row.away}), Wk {row.nflweek}, {row.gameday}, {row.kickdatestr})"
    )
print (pickchoices)


pd.Series(pickchoices).to_csv("pickchoices2.csv", index=False, header=False)
matches.to_csv('csv/schedfix.csv')
