import os  
from datetime import datetime

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, url_for, render_template, request, flash, send_file, redirect

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy()
db.init_app(app)
db.app = app

from app.models.dl_models import DL_Model
from app.views.dl_models import DLModelsForm

from app.utils.table_utils import GetTableHeader, getTableRecords, initTableRecords
from app.utils.download_utils import getFullPath
from app.utils.models_utils import save_model_h5, init_detection

from app.core_service.preprocessing import Preprocessing
from app.core_service.denoising import  Denoising
from app.core_service.feature_extraction import FeatureExtraction
from app.core_service.detection import Detection

feature_labels, ___ = init_detection(None, None, None, None, 0, 0)
root_path = os.path.dirname(os.path.dirname(__file__))

Prepro = Preprocessing()
Denoise = Denoising()
Feature = FeatureExtraction()
Detector = Detection(list(feature_labels.keys()))

# ####################################################################################################
#
#                                        DETECTION PAGE CONTROLLER
#
# ####################################################################################################

def plot_handler(curr_index, root_path):
    filename = Prepro.filename
    selected_feature = Detector.selected_feature
    index_length = 0
    label = Detector.prediction_label[curr_index]
    proba = "%.2f" % (Detector.prediction_proba[curr_index] * 100)
    signal_data = Feature.X_signal[curr_index]

    # save plot image
    img_path = []
    for ft in selected_feature.split(",") :
        print("[INFO] generating plot for feature %s" % ft)
        if ft == 'rr_interval' :
            r_peaks = Feature.r_peak_list[curr_index]
            index_length = len(Feature.r_peak_list)
            for ch in range(0,2):
                print("[INFO] Save plot for channel %d..." % ch)
                path = Feature.plot_r_peaks("%s___%s_%d_%d.png" % (filename, ft, curr_index, ch), 
                                                r_peaks[ch], signal_data[ch], 
                                                root_path = root_path,
                                                label="Detected R Peaks - %s - index %d , channel %d" % 
                                                            (filename, curr_index, ch + 1))
                img_path.append(path.replace("\\", "/"))

        if ft == 'qrs_complex' :
            r_onsets = Feature.r_onset_list[curr_index]
            r_offsets = Feature.r_offset_list[curr_index]
            index_length = len(Feature.r_onset_list)
            for ch in range(0,2):
                print("[INFO] Save plot for channel %d..." % ch)
                path = Feature.plot_QRS_complex("%s___%s_%d_%d.png" % (filename, ft, curr_index, ch), 
                                                r_onsets[ch], r_offsets[ch], signal_data[ch], 
                                                root_path = root_path,
                                                label="Detected QRS Complex - %s - index %d , channel %d" % 
                                                            (filename, curr_index, ch + 1))
                img_path.append(path.replace("\\", "/"))

        if ft == 'qt_interval' :
            r_onsets = Feature.r_onset_list[curr_index]
            t_offsets = Feature.t_offset_list[curr_index]
            index_length = len(Feature.r_onset_list)
            for ch in range(0,2):
                print("[INFO] Save plot for channel %d..." % ch)
                path = Feature.plot_QT_Interval("%s___%s_%d_%d.png" % (filename, ft, curr_index, ch), 
                                                r_onsets[ch], t_offsets[ch], signal_data[ch], 
                                                root_path = root_path,
                                                label="Detected QT Interval - %s - index %d , channel %d" % 
                                                            (filename, curr_index, ch + 1))
                img_path.append(path.replace("\\", "/"))

    feature_labels, signal = init_detection(selected_feature, img_path, label, proba, index_length, curr_index)
    return feature_labels, signal



@app.route("/")
def index():
    feature_labels, signal = init_detection(None, None, None, None, 0, 0)
    return render_template("index.html",
                            feature_labels=feature_labels,
                            signal=signal)


@app.route('/', methods=['POST'])
def detect():
    try :
        uploaded_file = request.files['file']
        feature_labels, signal = init_detection(None, None, None, None, 0, 0)
        if uploaded_file.filename != '':
            if request.form['feature'] not in list(feature_labels.keys()):
                flash('Cannot detect signal for feature %s. Make sure to select feature first!' % request.form['feature'], 'danger')
                return render_template("index.html",
                            feature_labels=feature_labels,
                            signal=signal)

            full_path = os.path.join(root_path, 'app/static/csv-upload', uploaded_file.filename).replace("\\", "/")
            uploaded_file.save(full_path)
            
            print("\n\n\n")
            print("[INFO] Apply preprocessing data...")
            ecg_dfs = Prepro.transform(filename=full_path)

            print("\n\n\n")
            print("[INFO] Apply denoising data...")
            X = Denoise.transform(ecg_dfs)

            print("\n\n\n")
            print("[INFO] Apply feature extraction data...")
            Feature.reshape(X)
            for ft in request.form['feature'].split(","):
                if ft == 'rr_interval' :
                    Feature.rr_interval()
                if ft == 'qrs_complex' :
                    Feature.qrs_complex()
                if ft == 'qt_interval' :    
                    Feature.qt_interval()

            Feature.post_reshape(len(request.form['feature'].split(",")))

            print("\n\n\n")
            print("[INFO] Apply Detection data...")
            Detector.transform(Feature.X, request.form['feature'])

            print("\n\n\n")
            print("[INFO] Show data in index %d..." % 0)
            feature_labels, signal = plot_handler(curr_index=0, root_path=root_path)
            
            flash('File ' + uploaded_file.filename + ' has been detected successfully!', 'success')
        else : 
            flash('Cannot detect signal if no uploaded file!', 'danger')

        return render_template("index.html",
                            feature_labels=feature_labels,
                            signal=signal)

    except Exception as e :
        flash('Error %s' % e, 'danger')
        return redirect(url_for('index'))

@app.route('/<int:_index>', methods=["GET"])
def navigate_signal(_index):
    try : 
        print("\n\n\n")
        print("[INFO] Show data in index %d..." % _index)
        feature_labels, signal = plot_handler(curr_index=_index, root_path=root_path)

        return render_template("index.html",
                    feature_labels=feature_labels,
                    signal=signal)    
    except Exception as e :
        flash('Error %s' % e, 'danger')
        return redirect(url_for('index'))



# ####################################################################################################
#
#                                          MODELS PAGE CONTROLLER
#
# ####################################################################################################
@app.route("/models", methods=["GET", "POST"])
def models():
    # define initial variable
    page, per_page, table_search, search_key, _col, _type, sort_type = initTableRecords()

    # Create Table Record
    filters = ['name', 'file_name']
    tableRecords, min_page, max_page, count = getTableRecords(DL_Model, search_key, filters, sort_type, _col, page, per_page)

    # Create Table Header
    col_exclude = ['file_type', 'name']
    sort_exclude = ['id', 'is_used']
    overide_label = dict(
        id = 'No'
    )
    tableHeader = GetTableHeader(DL_Model, col_exclude, sort_exclude, overide_label)

    # Create Header Control
    headerCtrl = dict(
        name = 'Model',
        is_search = True,
        search_act = 'models',
        table_search = table_search,
        is_export = False,
        export_act = 'models_download',
        export_filename = 'Export - Model.csv',
        sort_act = 'models',
        delete_act = 'model_delete',
        detail_act = 'model_detail',
        is_add_new = True
    )

    # Create Footer Control
    footerCtrl = dict(
        min_page=min_page, 
        max_page=max_page, 
        count=count,
        _type=_type,
        _col=_col,
        pagination_act = 'models'
    )
    return render_template("models.html", 
                        tableRecords=tableRecords, 
                        tableHeader=tableHeader,
                        headerCtrl=headerCtrl,
                        footerCtrl=footerCtrl
                    )

@app.route("/models/download/<filename>")
def models_download( filename):
    model_path = getFullPath(filename, 'static/csv-download')
    return send_file(model_path, 
                    attachment_filename=filename, 
                    as_attachment=True, 
                    mimetype='application/octet-stream')

@app.route("/model/detail/<int:_id>", methods=["GET", "POST"])
def model_detail( _id):
    form = DLModelsForm()
    getDLModelById = DL_Model.query.get(_id)
    
    model_name = 'model.h5' # default model name

    # Update record
    if form.is_submitted() and getDLModelById:
        if form.file_model.data.filename != "" :
            file_model = form.file_model.data
            model_file_name = save_model_h5(file_model, form.name.data + ".h5")
            model_name = model_file_name
            getDLModelById.file_name = model_file_name
        getDLModelById.name = form.name.data
        getDLModelById.upload_by = "Admin"
        getDLModelById.is_used = form.is_used.data
        db.session.commit()
        flash('Model ' + getDLModelById.name + ' has been uploaded!', 'success')
        return redirect(url_for('models'))
    
    # Add new record
    if form.is_submitted() and form.validate_on_submit():
        file_model = form.file_model.data
        model_file_name = save_model_h5(file_model, form.name.data + ".h5")
        model_name = model_file_name
        dl_model = DL_Model(
            name = form.name.data,
            file_name = model_file_name,
            upload_by = "Admin",
            is_used = form.is_used.data
        )
        db.session.add(dl_model)
        db.session.commit()
        flash('Model ' + dl_model.name + ' has been uploaded!', 'success')
        return redirect(url_for('models'))

    elif request.method == 'GET' and getDLModelById:
        form.name.data = getDLModelById.name
        form.is_used.data = getDLModelById.is_used
        model_name = getDLModelById.file_name

    inputField = ['name', 'is_used', 'file_model']
    submitField = ['submit']
    indexField = ['id']

    formCtrl = dict(
        _id=_id,
        inputField = inputField,
        submitField = submitField,
        indexField=indexField,
        form_act = "model_detail",
        cancel_act = "models",
        download_act = "model_download",
        download_name = model_name,
        delete_act = "model_delete",
        form_name = 'Model Form', 
        is_multipart = True
    )
    return render_template("model_detail.html",
                        form=form,
                        formCtrl=formCtrl)

@app.route("/model/download/<filename>")
def model_download( filename):
    model_path = getFullPath(filename, 'static/model-upload')
    return send_file(model_path, 
                    attachment_filename=filename, 
                    as_attachment=True, 
                    mimetype='application/octet-stream')

@app.route("/model/delete/<int:_id>")
def model_delete( _id):
    getDLModelById = DL_Model.query.get(_id)
    db.session.delete(getDLModelById)
    db.session.commit()
    flash('Model ' + getDLModelById.name + ' has been deleted!', 'success')
    return redirect(url_for('models'))


# ####################################################################################################
#
#                                          ABOUT PAGE CONTROLLER
#
# ####################################################################################################
@app.route("/about")
def about():
    return render_template("about.html")





# ####################################################################################################
#
#                                          INITIALIZATION
#
# ####################################################################################################

# @app.cli.command()
def build_sample_db():
    """
    Populate a small db with some example entries.
    """
    import string
    import random

    db.drop_all()
    db.create_all()

    with app.app_context():
        db.session.commit()
    return