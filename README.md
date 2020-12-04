
# Writeup Feed Filter

This repository contains the source code for the [Writeup Feed Filter](https://ctftime-writeups.herokuapp.com) mini-service, which is an online service for filtering the [CTFTime](https://ctftime.org/) writeups RSS feed. <span style="font-size: 0.7em">It's also an excuse for playing around with Firebase, Heroku and Flask.</span>

[CTFTime](https://ctftime.org/) is a website that contains information about Computer Security CTF (Capture the Flag) competitions: Dates, scoreboards, writeups (i.e. solutions) and so on. Once a competition is over, it's common to review other participants' writeups for the different challenges. One way to do this is by visiting CTFTime's CTF page for the given competition and reviewing the different writeups which were added for each challenge. However, using this method it's hard to identify new writeups, which keep getting added as time goes by. The alternative is to follow CTFTime's writeups RSS feed, but unfortunately it includes all the writeups for all the competitions and not just the ones the user might be interested in.

This service allows users to define a list of CTF names which are of interest to them, and receive a custom-tailored RSS feed including only writeups for these CTFs. The service works by fetching the original CTFTime RSS feed, filtering out anything which isn't on the user's list and returning the result. 

The service is build in Python as a Flask website, and uses Firebase for authenticating users and storing data. It's hosted at Heroku.

Suggestions, comments, issues and contributions are welcome.