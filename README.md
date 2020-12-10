# Baseball Data Analysis
## A work-in-progress collection of tools for gathering and analyzing baseball data.  

### Currently, modules exist for:

**1) Scraping player game logs from http://Baseball-Reference.com and pitch-level event data (through MLB Statcast) courtesy of http://baseballsavant.mlb.com** 

* Certain elements of this module are inspired by jldbc/pybaseball, with small adjustments made in order to improve performance.  Their work is cited when appropriate in my code comments.  
* If season-level stats are preferred, you can either aggregate them from the game logs or use the baseball-reference scraper provided in the pybaseball          library
    
    

**2) Pitch prediction model:  Uses historical Statcast data to predict what type of pitch (Fastball, Curveball, etc) will be thrown next given the context of game situation, hitter tendencies, etc.**

* The current version of this model uses a Random Forest classifier and is partially inspired by the work of Glenn Sidle & Hien Tran (https://projects.ncsu.edu/crsc/reports/ftp/pdf/crsc-tr17-10.pdf).  As far as I can tell, their model performance has been unmatched.
* The model included here has achieved an overall accuracy of 53.02% which is lower than the benchmark of 59.07% set by Sidle & Tran  
* In both models, the classifier struggles to predict certain pitch types--in particular, it often predicts a changeup when a fastball is actually thrown.  This is somewhat understandable, since the greatest hitters in the world often struggle with the same task.  
* There are various improvements that can be made in order to match and possibly even exceed this benchmark:
  * Refinements to pitcher and batter tendency features, including rolling averages for past 7 and past 28 days (i.e. recent performance vs historic performance) as well as individual matchup outcomes
  * Explore other model approaches, i.e. reinforcement learning instead of the more classical approach taken here

## Future Additions

**1) At-Bat and Game Simulators:  I am in the process of exploring the best approach to create at-bat and game simulators, which can be used to create player and team stat projections.

**2) Lineup Optimization:  As a follow-up to the previous point, I will work towards including a workflow to optimize Daily Fantasy Sports lineups.  This will be able to use the projection outputs from my game simulator, or from a DFS site such as Rotoworld

**3) Dashboard:  Will eventually work toward a Statcast dashboard, but will be a later-state.
