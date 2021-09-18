import os


def save_model_h5(file_model, name):
        model_fn = name.lower().replace(" ", "_")
        root_path = os.path.dirname(os.path.dirname(__file__))
        full_path = os.path.join(root_path, 'static/model-upload', model_fn)

        file_model.save(full_path)
        return model_fn

def init_detection(feature, signal_img, label, proba, index_length, curr_index):
    feature_labels = {
        "rr_interval" : "RR Interval",
        "qt_interval" : "QT Interval",
        "qrs_complex" : "QRS Complex",
        "rr_interval,qt_interval" : "RR Interval & QT Interval",
        "rr_interval,qrs_complex" : "RR Interval & QRS Complex",
        "qt_interval,qrs_complex" : "QT Interval & QRS Complex",
        "rr_interval,qt_interval,qrs_complex" : "RR Interval, QT Interval & QRS Complex"
    }
    sampling_rates = {
        "250" : "250 hz",
        "128" : "128 hz"
    }
    signal = {}
    signal["feature"] = feature
    signal["index_length"] = index_length
    signal["curr_index"] = curr_index
    signal["signal_img"] = signal_img
    signal["predicted_label"] = label
    signal["predicted_proba"] = proba

    return feature_labels, signal, sampling_rates