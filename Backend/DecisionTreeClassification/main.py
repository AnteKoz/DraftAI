import sqlite3
from sqlite3 import Error
from sklearn import tree
import matplotlib.pyplot as plt
from sklearn.naive_bayes import GaussianNB, CategoricalNB, MultinomialNB


def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(r"..\MatchCollector\matches.db")
        return conn
    except Error as e:
        print(e)

    return conn


def get_data_set():
    conn = create_connection()
    cursor = conn.cursor()
    all_matches = cursor.execute(
        "SELECT t1_top, t1_jng, t1_mid, t1_adc, t1_sup, t2_top, t2_jgl, t2_mid, t2_adc, t2_sup, win FROM all_matches").fetchall()

    data_set = []
    target = []
    # for match in all_matches:
    #     data_point = list(match)
    #     data_point.remove(data_point[len(data_point) - 1])
    #     # data_point = [str(e)+"A" for e in data_point]
    #     data_set.append(data_point)
    #     target.append(match[len(match) - 1])
    #     target = [str(e)+"A" for e in target]

    all_t1_champ_ids = []
    all_t2_champ_ids = []
    for match in all_matches:
        for i in range(0,5):
            if match[i] not in all_t1_champ_ids:
                all_t1_champ_ids.append(match[i])
        for i in range(5,10):
            if match[i] not in all_t2_champ_ids:
                all_t2_champ_ids.append(match[i])

    for match in all_matches:
        data_point = []
        for champ in all_t1_champ_ids:
            if champ in match[:5]:
                data_point.append(1)
            else:
                data_point.append(0)
        for champ in all_t2_champ_ids:
            if champ in match[-5:]:
                data_point.append(1)
            else:
                data_point.append(0)

        data_set.append(data_point)
        target.append(match[len(match) - 1])

    return data_set, target


if __name__ == '__main__':

    data_set, target = get_data_set()
    # print(str(data_set))
    print("Size: " + str(len(data_set)))

    training_size = int(len(data_set) * 0.9)
    test_size = len(data_set) - training_size

    training_set = data_set[:training_size]
    training_target = target[:training_size]

    test_set = data_set[-test_size:]
    test_target = target[-test_size:]

    # gnb = CategoricalNB()
    # gnb = gnb.fit(training_set, training_target)
    # results = gnb.predict(test_set)

    clf = tree.DecisionTreeClassifier()
    clf = clf.fit(training_set, training_target)

    results = clf.predict(test_set)
    correct = 0
    for i in range(0, test_size):
        if results[i] == test_target[i]:
            correct = correct + 1

    print("Accuracy: " + str(correct / test_size))

    tree.plot_tree(clf, max_depth=1)
    plt.figure(figsize=(64.0, 48.0))
    plt.show()
