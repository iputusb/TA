from . import load_model, K
from . import os
from . import np 

class Denoising():
    def __init__(self, filename="best_denoising_conv_AE.h5", path="static\model-upload", fs=250, sample_size=6):
        root_path = os.path.dirname(os.path.dirname(__file__))
        if not os.path.exists(os.path.join(root_path, path, filename)):
            raise Exception('\n\n[ERROR] Cant find %s in %s, please upload your denoising model first with name `best_denoising_conv_AE`!\n\n' % (filename, path))

        print("\n\n[INFO] Load denoising model %s...\n\n" % filename)
        self.model = load_model(os.path.join(root_path, path, filename), custom_objects={'rmse': self.rmse})
        self.path = path
        self.sample_size = sample_size
        self.fs = fs
        
    def rmse(self, y_true, y_pred):
        return K.sqrt(K.mean(K.square(y_pred - y_true))) 

    def scaler(self, X):
        res = []
        for x in X :
            global_min = x.min()
            x = np.reshape(x, (2, self.sample_size*self.fs))
            for i in range(len(x)):
                idx = np.max(np.nonzero(x[i]))
                x[i][idx+1:] = global_min
            x = np.reshape(x, (self.sample_size*self.fs*2))
            res.append((x - x.min())/(x.max() - x.min()))
        return np.array(res)

    def transform(self, ecg_dfs):
        print("\n\n[INFO] Denoising all noised signal using Convolution Autoencoder...\n\n")
        X = ecg_dfs.iloc[:,:self.fs*self.sample_size*2].values
        X = self.scaler(X)
        X = X.reshape(len(X), X.shape[1], 1)
        X_denoised = self.model.predict(X)

        return X_denoised