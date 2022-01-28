# COVID-19 Claim Radar: A Structured Claim Extraction and Tracking System

## Table of Contents
=================
  * [Overview](#overview)
  * [Requirements](#requirements)
  * [Data](#data)
  * [Code](#code)

## Overview
The COVID-19 pandemic has received extensive media coverage, with a vast variety of claims made about different aspects of the virus. In order to track these claims,  we present [COVID-19 Claim Radar](http://18.221.187.153/), a system that automatically extracts claims relating to COVID-19 in news articles.
We provide a comprehensive structured view of such claims, with rich attributes (such as claimers and their affiliations) and associated knowledge elements (such as events, relations and entities). 
Further, we use this knowledge to identify inter-claim connections such as equivalent, supporting, or refuting relations, with shared structural evidence like  claimers, similar centroid events and arguments. 
In order to consolidate claim structures at the corpus-level, we leverage [Wikidata](https://www.wikidata.org) as the hub to merge coreferential knowledge elements, and apply machine translation to aggregate claims from news articles in multiple languages. The system provides users with a comprehensive exposure to COVID-19 related claims, their associated knowledge elements, and related connections to other claims. 
The system is publicly available on [GitHub](https://github.com/uiucnlp/covid-claim-radar) and [DockerHub](https://hub.docker.com/repository/docker/blendernlp/covid-claim-radar), with instructional [video](http://blender.cs.illinois.edu/aida/covid_claim_radar.mp4).

## Requirements

### Docker
The docker is `blendernlp/covid-claim-radar`. 

### GPU support
Please provide GPU ids in the running script `extract.sh`.

## Data

Our experimental data is LDC2021E11. 

## Code

Please find the claim extraction and claim-claim relation detection code under `claim_detection`, and knowledge extraction code under `knowledge_extraction`. 
