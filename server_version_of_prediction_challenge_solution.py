# -*- coding: utf-8 -*-
"""server-version of prediction_challenge_solution.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WxoC16sYjbKcc_sal2zk-jb_4Es8gGWb

## Package Import
"""

import numpy as np
import random
import pandas as pd
import xgboost as xgb
import sys as sys
import csv, datetime
from datetime import datetime
from scipy.stats import uniform, randint
from sklearn.compose import ColumnTransformer
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import RandomizedSearchCV, cross_validate, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, LabelEncoder, OneHotEncoder

"""## Data Import"""

dataset = pd.read_csv(
    'https://raw.githubusercontent.com/saschaschworm/big-data-and-data-science/' +
    'master/datasets/prediction-challenge/dataset.csv', 
    index_col='identifier', parse_dates=['date'])

prediction_dataset = pd.read_csv(
    'https://raw.githubusercontent.com/saschaschworm/big-data-and-data-science/' +
    'master/datasets/prediction-challenge/prediction-dataset.csv', 
    index_col='identifier', parse_dates=['date'])

"""## Feature Engineering"""

def getYear(inDate):
  return inDate.year
def getMonth(inDate):
  return inDate.month
def getWeekday(inDate):
  return inDate.weekday
def getWeekendDay(inDate):
  if (inDate.weekday == 'Saturday') or (inDate.weekday == 'Sunday'):
    return True
  else:
    return False
def getAgeGroups(inAge):
  if (inAge < 28):
    return 'young'
  elif (49 > inAge > 27):
    return 'younger'
  elif (61 > inAge > 48):
    return 'older'
  else:
    return 'old'

dataset['date'] = pd.to_datetime(dataset['date'])
dataset.insert(1, "dateYear", dataset['date'], allow_duplicates=True)
dataset.insert(2, "dateMonth", dataset['date'], allow_duplicates=True)
dataset.insert(3, "dateWeekday", dataset['date'], allow_duplicates=True)
dataset.insert(4, "dateWeekendDay", dataset['date'], allow_duplicates=True)

dataset.insert(6, "ageGroups", dataset['age'], allow_duplicates=True)

dataset.dateYear = dataset['dateYear'].dt.year
dataset.dateMonth = dataset['dateMonth'].dt.month
dataset.dateWeekday = dataset['dateWeekday'].dt.day_name()
dataset.dateWeekendDay = dataset.dateWeekendDay.apply(getWeekendDay)
dataset.ageGroups = dataset.ageGroups.apply(getAgeGroups)

"""## Model, Pipeline and Scoring Initialization"""

X_default = dataset[['dateYear', 'dateMonth', 'dateWeekday', 'ageGroups', 'marital_status', 'education', 'job', 'credit_default', 'housing_loan', 'personal_loan', 'communication_type', 'n_contacts_campaign', 'days_since_last_contact', 'n_contacts_before', 'previous_conversion', 'duration']]
y = dataset['success']

X = X_default

x_reg_alpha = 0
x_reg_lambda = 0.007
x_rscv = 10
x_random_state = 1909
x_n_estimators_min = 100
x_n_estimators_max = 500
x_max_depth_min = 1
x_max_depth_max = 20
x_rsLearningRate = 0.0001
classifier = xgb.XGBClassifier(n_jobs=-1, random_state=x_random_state, objective='binary:logistic', reg_lambda=x_reg_lambda, reg_alpha=x_reg_alpha)

scorer = make_scorer(f1_score, pos_label='Yes')

numeric_features = ['n_contacts_campaign', 'days_since_last_contact', 'n_contacts_before', 'duration']
numeric_transformer = Pipeline([
    ('scaler', MinMaxScaler()),
])

categorical_features = ['dateYear', 'dateMonth', 'dateWeekday', 'ageGroups', 'marital_status', 'education', 'job', 'credit_default', 'housing_loan', 'personal_loan', 'communication_type', 'previous_conversion']
categorical_transformer = Pipeline([
    ('onehotencoder', OneHotEncoder(drop='first')),
])

preprocessor = ColumnTransformer([
    ('numeric_transformer', numeric_transformer, numeric_features),
    ('categorical_transformer', categorical_transformer, categorical_features)
])

pipeline = Pipeline([
    ('preprocessor', preprocessor), 
    ('classifier', classifier)
])

param_distributions = {}
def runAlgo(x):
  global param_distributions

  x_rscv = StratifiedKFold(n_splits=10, shuffle=True, random_state=x_random_state)
  x_rscv = x_rscv.split(X, y)

  param_distributions = {
                          "classifier__learning_rate": uniform.rvs(0.0001, 0.1, size=10),
                          "classifier__gamma" : uniform.rvs(0, 2, size=10),
                          "classifier__max_depth": randint.rvs(2, 100, size=10),
                          "classifier__colsample_bytree": uniform.rvs(0.1, 0.9, size=10),
                          "classifier__subsample": uniform.rvs(0.1, 0.9, size=10),
                          "classifier__reg_alpha": uniform.rvs(0, 0.9, size=10),
                          "classifier__reg_lambda": uniform.rvs(0.0001, 5, size=10),
                          "classifier__min_child_weight": randint.rvs(1, 7, size=10),
                          "classifier__n_estimators": randint.rvs(100, 1000, size=10)
                        }
  search = RandomizedSearchCV(
    pipeline, param_distributions=param_distributions, n_iter=3, scoring=scorer, 
    n_jobs=-1, cv=x_rscv, random_state=x_random_state, return_train_score=True)
  
  search = search.fit(X, y)


  training_score = search.cv_results_['mean_train_score'][search.best_index_] * 100
  test_score = search.cv_results_['mean_test_score'][search.best_index_] * 100

  logData = [[datetime.now()
              ,search.best_params_['classifier__learning_rate']
              ,search.best_params_['classifier__gamma']
              ,search.best_params_['classifier__max_depth']
              ,search.best_params_['classifier__colsample_bytree']
              ,search.best_params_['classifier__subsample']
              ,search.best_params_['classifier__reg_alpha']
              ,search.best_params_['classifier__reg_lambda']
              ,search.best_params_['classifier__min_child_weight']
              ,search.best_params_['classifier__n_estimators']
              ,training_score
              ,test_score
              ,search.cv_results_['std_train_score'][search.best_index_]
              ,search.cv_results_['std_test_score'][search.best_index_]
              ,x]]
  with open('log.csv', 'a') as csvfile:
    writer = csv.writer(csvfile, delimiter=';')
    writer.writerows(logData)

lenDataset = len(X.columns)
for x in range(7, lenDataset - 1):
  X.drop(X.columns[x], axis=1)
  print(datetime.now(), "Start Runde " , x, " von ", lenDataset)
  runAlgo(x)
  X = X_default