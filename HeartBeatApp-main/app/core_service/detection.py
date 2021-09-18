from . import np 
from . import pd  
from . import os
from . import load_model


class Detection():
    def __init__(self, selected_feature_list, fs = 250, sample_size = 6, pad_size = 15, label_name = ['AF', 'N'], path="static\model-upload"):
        self.fs = fs
        self.sample_size = sample_size
        self.label_name = label_name
        self.pad_size = pad_size
        self.prediction_proba = []
        self.prediction_label = []
        self.models = {}
        self.selected_feature = ""

        for selected_feature in selected_feature_list :
            filename = "%s_model.h5" % selected_feature
            root_path = os.path.dirname(os.path.dirname(__file__))
            if not os.path.exists(os.path.join(root_path, path, filename)):
                raise Exception('\n\n[ERROR] Cant find %s in %s, please upload your classification model for feature %s with name `%s`!\n\n' % (filename, path, selected_feature, filename))

            print("\n\n[INFO] Load classification model %s...\n\n" % filename)
            self.models[selected_feature] = load_model(os.path.join(root_path, path, filename))

    def transform(self, X, selected_feature):
        self.selected_feature = selected_feature
        print("[INFO] transforming data using model %s_model.h5..." % selected_feature)
        y_pred = self.models[selected_feature].predict(X)
        print("[INFO] find label & probability result...")
        prediction_index = y_pred.argmax(axis=1)
        self.prediction_proba = y_pred.max(axis=1)
        self.prediction_label = [ self.label_name[idx] for idx in prediction_index]

