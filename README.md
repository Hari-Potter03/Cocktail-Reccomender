# Cocktail Recommender Web App
An end-to-end project that suggests cocktails based on a user’s taste preferences and ratings. It blends data engineering with full-stack development to show how to build, run, and interact with a personalized recommendation system.

It includes:

* A Python data pipeline to collect (TheCocktailDB API), curate, and featurize a catalog of cocktails (ingredients, spirit, tags, season).

* A hybrid recommender: content + taste vector scoring (optional ALS training script for collaborative filtering when ratings grow).

* A FastAPI backend exposing /recs, /search, /drinks, /similar, /ratings, and /profile.

* A React.js frontend with onboarding questionnaire, spirit tabs, search, drink detail pages, and a star-rating widget.

* Local JSON storage (no external DB) and a Makefile for one-command setup and run.