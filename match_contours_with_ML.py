import numpy as np
import pandas as pd
import sklearn
import sklearn.model_selection
import sklearn.neighbors
from joblib import dump, load

shape_matches = pd.read_csv('./data/shape_match_data.csv', index_col=0)

print(shape_matches.shape)
print(shape_matches.head(50))

X = shape_matches[["Shape similarity", "Ratio area", "Distance"]]
y = shape_matches["Label"]

X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(X,y)

knn = sklearn.neighbors.KNeighborsClassifier(n_neighbors=30)
knn.fit(X_train, y_train)
print(knn.score(X_test, y_test))
dump(knn, './data/contour_matcher_knn.joblib')