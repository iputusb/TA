from app import app, build_sample_db
from app import os
# ####################################################################################################
#
#                                                ENTRY POINT
#
# ####################################################################################################
if __name__ == '__main__':

    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))

    database_path = os.path.join(app_dir, "app", app.config['DATABASE_FILE'])

    if not os.path.exists(database_path):
        print("_________ BUILD DB & SAMPLE __________")
        build_sample_db()

    #app.run(debug=True)
    app.run(host='0.0.0.0', threaded=False)