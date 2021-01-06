import numpy as np
import pandas as pd
import sklearn
import sklearn.model_selection
import sklearn.neighbors
import sklearn.tree
from joblib import dump, load


shape_matches = pd.read_csv('shape_match_data.csv', index_col=0)
clf_filepath = 'contour_matcher_knn.joblib'
print(shape_matches.shape)

X = shape_matches[["Shape similarity", "Ratio area", "Distance"]]
y = shape_matches["Label"]

X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(X,y)

def train_knn():
    clf = sklearn.neighbors.KNeighborsClassifier(n_neighbors=13)
    clf.fit(X_train, y_train)
    print(clf.score(X_test, y_test))
    dump(clf, clf_filepath)

def train_logistic():
    clf = sklearn.linear_model.LogisticRegression(C=50, solver='lbfgs')
    clf.fit(X_train, y_train)
    print(clf.score(X_test, y_test))
    print(clf.coef_)
    dump(clf, clf_filepath)

def train_kernalised_SVM():
    clf = sklearn.svm.SVC(kernel= 'rbf', gamma=5, probability=True)
    clf.fit(X_train, y_train)
    print(clf.score(X_test, y_test))
    dump(clf, clf_filepath)

def train_decision_tree():
    clf = sklearn.tree.DecisionTreeClassifier(splitter="best",min_samples_leaf=2)
    clf.fit(X_train, y_train)
    print(clf.score(X_test, y_test))
    dump(clf, clf_filepath)

train_decision_tree()